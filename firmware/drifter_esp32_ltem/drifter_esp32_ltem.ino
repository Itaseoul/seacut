/*
 * SEA:CUT GPS 드리프터 펌웨어 스켈레톤 — ESP32 + GPS + LTE-M(SIM7080G)
 * ===================================================================
 * 패턴: 깨어남 → GPS fix → LTE-M로 좌표 POST → deep sleep.
 *   간헐 전송(예: 5분 주기)으로 배터리를 아낀다. 상시연결을 버린 게 이득.
 *
 * 전송 대상(둘 중 택1, 아래 POST_URL):
 *   1) SEA:CUT 수신 서버  POST /api/ping
 *        body {"device_id","lat","lon","ts"}   (ingest_server.py 스키마)
 *   2) openc.caresea.kr   POST /api/observations/drift  (DriftTrack, 궤적 누적형)
 *   스켈레톤은 1)을 기본으로 한다.
 *
 * 라이브러리(Arduino 라이브러리 매니저):
 *   - TinyGPSPlus      (GPS NMEA 파싱)
 *   - TinyGSM          (SIM7080 등 셀룰러 모뎀 AT 래퍼)  #define 아래 참고
 *
 * ★하드웨어 주의: NodeMCU/데브보드는 잠들어도 USB칩·레귤레이터가 전류를 샌다.
 *   실운용은 베어 ESP32 모듈 + GPS/모뎀 전원 게이팅(MOSFET) + (선택) 소형 태양광.
 *   시연용은 보조배터리로 충분.
 *
 * ⚠ 스켈레톤이다. 핀맵·APN·URL·전원게이팅을 실제 보드에 맞춰 채우고 검증할 것.
 */

#define TINY_GSM_MODEM_SIM7080          // 모뎀 종류(SIM7080G = LTE-M/NB-IoT)
#include <TinyGsmClient.h>
#include <TinyGPSPlus.h>

// ---------- 설정(확정 필요) -------------------------------------------------
static const char* DEVICE_ID = "DRIFTER-01";
static const char* APN        = "lte-m.sktelecom.com";   // ★통신사 LTE-M APN으로 교체(SKT/KT)
static const char* POST_HOST  = "openc.caresea.kr";      // 또는 수신 서버 호스트/IP
static const int   POST_PORT  = 443;                     // https=443, 로컬 http=8770 등
static const char* POST_PATH  = "/api/observations/drift/ping"; // 엔드포인트 경로
static const bool  USE_TLS    = true;

static const uint64_t WAKE_INTERVAL_S = 300;   // 전송 주기(초). 5분=300
static const uint32_t GPS_FIX_TIMEOUT_MS = 90000;  // GPS fix 최대 대기(콜드스타트 여유)

// 핀맵(★보드에 맞게) — GPS=UART1, 모뎀=UART2, 전원 게이팅 핀
static const int PIN_GPS_RX = 16, PIN_GPS_TX = 17;
static const int PIN_MODEM_RX = 26, PIN_MODEM_TX = 27, PIN_MODEM_PWR = 4;
static const int PIN_GPS_EN = 2;   // GPS 전원 MOSFET 게이트(HIGH=on)

// ---------------------------------------------------------------------------
HardwareSerial SerialGPS(1);
HardwareSerial SerialModem(2);
TinyGPSPlus gps;
TinyGsm modem(SerialModem);
TinyGsmClient  gsmPlain(modem);
#ifdef TINY_GSM_MODEM_HAS_SSL
TinyGsmClientSecure gsmSecure(modem);
#endif

static void sleepNow() {
  digitalWrite(PIN_GPS_EN, LOW);       // GPS 끄기
  modem.poweroff();                    // 모뎀 끄기
  esp_sleep_enable_timer_wakeup(WAKE_INTERVAL_S * 1000000ULL);
  Serial.println("deep sleep...");
  Serial.flush();
  esp_deep_sleep_start();              // 여기서 잔다. 깨면 setup()부터 다시.
}

// GPS fix 대기 → 성공 시 lat/lon 채우고 true
static bool getFix(double& lat, double& lon) {
  digitalWrite(PIN_GPS_EN, HIGH);
  SerialGPS.begin(9600, SERIAL_8N1, PIN_GPS_RX, PIN_GPS_TX);
  uint32_t t0 = millis();
  while (millis() - t0 < GPS_FIX_TIMEOUT_MS) {
    while (SerialGPS.available()) gps.encode(SerialGPS.read());
    if (gps.location.isValid() && gps.location.age() < 3000 && gps.satellites.value() >= 4) {
      lat = gps.location.lat();
      lon = gps.location.lng();
      return true;
    }
    delay(20);
  }
  return false;
}

// 모뎀 켜기 → 망 접속
static bool modemConnect() {
  pinMode(PIN_MODEM_PWR, OUTPUT);
  digitalWrite(PIN_MODEM_PWR, HIGH); delay(1200); digitalWrite(PIN_MODEM_PWR, LOW);
  SerialModem.begin(115200, SERIAL_8N1, PIN_MODEM_RX, PIN_MODEM_TX);
  delay(3000);
  if (!modem.restart()) return false;
  if (!modem.waitForNetwork(60000)) return false;
  if (!modem.gprsConnect(APN, "", "")) return false;
  return true;
}

// 좌표를 JSON으로 POST. 성공 시 true
static bool postFix(double lat, double lon) {
  TinyGsmClient* client = &gsmPlain;
#ifdef TINY_GSM_MODEM_HAS_SSL
  if (USE_TLS) client = (TinyGsmClient*)&gsmSecure;
#endif
  if (!client->connect(POST_HOST, POST_PORT)) return false;

  // ISO8601 타임스탬프(UTC) — GPS 시각 사용
  char ts[32] = "";
  if (gps.date.isValid() && gps.time.isValid()) {
    snprintf(ts, sizeof(ts), "%04d-%02d-%02dT%02d:%02d:%02dZ",
             gps.date.year(), gps.date.month(), gps.date.day(),
             gps.time.hour(), gps.time.minute(), gps.time.second());
  }
  char body[160];
  int n = snprintf(body, sizeof(body),
    "{\"device_id\":\"%s\",\"lat\":%.6f,\"lon\":%.6f,\"ts\":\"%s\"}",
    DEVICE_ID, lat, lon, ts);

  client->printf("POST %s HTTP/1.1\r\n", POST_PATH);
  client->printf("Host: %s\r\n", POST_HOST);
  client->print("Content-Type: application/json\r\n");
  client->printf("Content-Length: %d\r\n", n);
  client->print("Connection: close\r\n\r\n");
  client->print(body);

  uint32_t t0 = millis();
  while (client->connected() && millis() - t0 < 15000) {
    if (client->available()) { String line = client->readStringUntil('\n'); if (line.startsWith("HTTP/")) { Serial.println(line); break; } }
  }
  client->stop();
  return true;
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_GPS_EN, OUTPUT);
  Serial.printf("\n[%s] wake\n", DEVICE_ID);

  double lat, lon;
  if (!getFix(lat, lon)) { Serial.println("GPS fix 실패 → sleep"); sleepNow(); }
  Serial.printf("fix %.6f, %.6f (sats %lu)\n", lat, lon, gps.satellites.value());

  if (modemConnect() && postFix(lat, lon)) Serial.println("POST 완료");
  else Serial.println("전송 실패(다음 주기 재시도)");

  sleepNow();
}

void loop() { /* deep sleep 패턴이라 loop는 비움 */ }
