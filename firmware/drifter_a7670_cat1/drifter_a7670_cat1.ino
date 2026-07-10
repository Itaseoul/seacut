/*
 * SEA:CUT 드리프터 펌웨어 — LTE Cat.1 bis (A7670) + L76K GPS + 서버 전송
 * 대상 보드: LILYGO T-A7670G R2 (With GPS L76K), ESP32-WROVER-E
 *
 * 동작: 깨어남 → 모뎀 전원 → 망 접속(Cat.1 bis) → L76K GPS fix → 단건 ping POST → 딥슬립.
 *   기기는 좌표 한 점만 보내고 궤적 조립·저장·표시는 서버(openc)+R2가 한다(펌웨어 단순화).
 * 통신 규격은 한국 검증 결과에 따라 Cat.1 bis(표준 LTE망)로 확정. Cat-M1(SIM7080G)은
 * 한국 실접속 근거가 없어 사용하지 않는다.
 *
 * ★라이브러리 (반드시): lewisxhe/TinyGSM-fork (LILYGO 공식 포크). 스톡 vshymanskyy/TinyGSM
 *   에는 TINY_GSM_MODEM_A7670 매크로가 없어 컴파일이 깨진다. 스톡이 깔려 있으면 제거한다.
 *   그 외: TinyGPSPlus, ArduinoHttpClient. 보드: ESP32 Arduino core 3.0.x, "ESP32 Dev Module".
 *
 * ★GPS 주의: 이 보드의 GPS는 A7670 모뎀 내장 GNSS가 아니라 별도 Quectel L76K 칩이다.
 *   모뎀 AT(AT+CGNSSPWR/AT+CGNSSINFO)로 읽으면 ERROR가 난다. L76K 전용 UART(Serial2)의
 *   NMEA를 TinyGPSPlus로 파싱한다. 핀은 LILYGO 공식 예제 ExternalGPS_A7670G_Only 기준.
 *
 * ⚠ 법적: 자작 셀룰러 기기의 국내 실증은 전파법 적합성평가 대상이다. 다수 실증 전에
 *    국립전파연구원 연구·기술개발용 면제확인(별지 제12호, 1,500대 이하)을 받는다.
 *    1대 PoC는 국내 데이터 유심 또는 글로벌 IoT SIM으로 접속 테스트만 수행한다.
 */

// ── 전송 모드 토글 ──────────────────────────────────────────────────────────
// 1 = 벤치 검증(로컬 ingest_server.py, HTTP 평문, /api/ping 스키마).  ★처음엔 이걸로.
// 0 = 운영 전송(openc.caresea.kr, HTTPS 443, /api/observations/drift).
#define BENCH_HTTP 1

// ── CONFIG ────────────────────────────────────────────────────────────────
#define DEVICE_ID     "seacut-poc-001"      // 기기 식별자(벤치 /api/ping)
#define SITE_ID       "goejeong-boom"        // ping에 실어 보낼 사이트(서버가 궤적에 태그). openc OBS_SITES: "gamjeon-confluence"(감전천·학장천 합류) | "goejeong-boom"(괴정천 붐)
const char* APN       = "";                   // 유심 사업자 APN. 꽂은 유심에 맞게 채운다.
                                              //  Soracom(권장 1대 PoC): "soracom.io"  (USER "sora" / PASS "sora"). 한국 KT/SKT 로밍.
                                              //  1NCE:                   "iot.1nce.net" (USER/PASS 없음). 한국 KT/SKT 로밍.
                                              //  국내 KT 알뜰폰 데이터심:  "lte.ktfwing.com"   (USER/PASS 없음)
                                              //  국내 SKT 알뜰폰 데이터심: "lte.sktelecom.com" (USER/PASS 없음)
                                              //  ※ 1NCE/Soracom 모두 LG U+ 로밍 미지원. 글로벌 IoT SIM은 KT 또는 SKT로만 붙는다.
const char* GPRS_USER = "";                   // Soracom이면 "sora"
const char* GPRS_PASS = "";                   // Soracom이면 "sora"

#if BENCH_HTTP
  // ★로컬 ingest_server.py는 127.0.0.1:8770(루프백)에만 바인딩된다. 보드는 여기에 못 닿는다.
  //   이 BENCH_HTTP 경로는 평문 TinyGsmClient라 아래 둘 중 하나로 노출한다(둘 다 평문):
  //   (a) ingest_server.py 바인딩을 0.0.0.0으로 바꾸고 공유기 포트포워딩+공인IP(또는 같은 망이면 노트북 LAN IP).
  //   (b) `ngrok tcp 8770`(http가 아니라 tcp)으로 받은 host:port를 아래에 넣는다.
  //   ※ ngrok http(https 터널)는 TLS라 평문 클라이언트로 안 붙는다. 그 경우는 BENCH_HTTP 0(운영 HTTPS)로 간다.
  const char* SERVER_HOST = "192.168.0.10";   // ★노트북 LAN IP 또는 ngrok tcp 호스트로 교체
  const int   SERVER_PORT = 8770;             // ngrok tcp면 발급된 포트
  const char* SERVER_PATH = "/api/ping";      // ingest_server.py 스키마: device_id/lat/lon 필수, ts 선택
#else
  const char* SERVER_HOST = "openc.caresea.kr";
  const int   SERVER_PORT = 443;              // https
  const char* SERVER_PATH = "/api/observations/drift/ping"; // 서버가 단건 ping을 받아 궤적 조립·R2 스냅샷 bake. 기기는 좌표 한 점만
#endif

const uint32_t SLEEP_MINUTES  = 30;           // 전송 주기(분). 벤치 로깅은 5로 낮춰 확인
const uint32_t GPS_FIX_TIMEOUT_MS = 180000;   // L76K 콜드스타트 여유(야외 30초~수 분)
// ───────────────────────────────────────────────────────────────────────────

#define TINY_GSM_MODEM_A7670        // ★lewisxhe/TinyGSM-fork 전제. 스톡엔 이 매크로 없음
#define TINY_GSM_RX_BUFFER 1024
#include <TinyGsmClient.h>
#include <ArduinoHttpClient.h>
#include <TinyGPSPlus.h>

// LILYGO T-A7670G R2 핀맵 (공식 utilities.h / ExternalGPS_A7670G_Only 기준)
#define MODEM_TX          26
#define MODEM_RX          27
#define BOARD_PWRKEY      4
#define BOARD_POWERON     12   // 모뎀·주변 전원 게이트. 동작 내내 HIGH 유지
#define MODEM_RST         5
#define MODEM_DTR         25
#define BOARD_BAT_ADC     35   // 배터리 전압 분압 ADC
// L76K GPS(별도 칩, Serial2). begin(baud, cfg, RX, TX) 순서 주의
#define BOARD_GPS_RX_PIN      22   // ESP32가 GPS NMEA를 받는 핀
#define BOARD_GPS_TX_PIN      21   // ESP32가 GPS로 보내는 핀
#define BOARD_GPS_WAKEUP_PIN  19   // L76K wakeup(공식 예제는 미토글, 여기선 방어적 HIGH)
#define GPS_BAUDRATE          9600

#define SerialAT  Serial1
#define SerialGPS Serial2
TinyGsm        modem(SerialAT);
#if BENCH_HTTP
TinyGsmClient        client(modem);   // 평문 HTTP
#else
TinyGsmClientSecure  client(modem);   // HTTPS(포크 SSL). 벤치 통과 후 승격
#endif
HttpClient     http(client, SERVER_HOST, SERVER_PORT);
TinyGPSPlus    gps;

// 드리프터 단건 ping 본문. 기기는 좌표 한 점만 보내고 궤적 조립은 서버(openc)가 한다.
// 서버가 device_id·site_id로 묶어 시간순 DriftTrack을 만들고 R2에 공개 스냅샷(live.geojson)을
// 굽는다. 그래서 기기 쪽 RTC 누적·궤적 조립 로직이 필요 없다(펌웨어 단순화).
// 벤치(로컬 /api/ping)와 운영(openc /api/observations/drift/ping)이 같은 본문을 쓴다.
String buildPingBody(double lat, double lon, const char* ts, float batt) {
  String b = String("{\"device_id\":\"") + DEVICE_ID + "\",\"site_id\":\"" + SITE_ID + "\",";
  b += "\"lat\":" + String(lat, 6) + ",\"lon\":" + String(lon, 6);
  b += ",\"batt\":" + String(batt, 2);   // 원격 배터리 감시(V). 서버가 live.geojson 마지막점에 노출
  if (ts[0]) b += ",\"ts\":\"" + String(ts) + "\"";
  b += "}";
  return b;
}

// 배터리 전압(V): 100k/100k 분압 가정(보드별 계수 보정 필요)
float readBatteryV() {
  uint32_t raw = 0;
  for (int i = 0; i < 16; i++) raw += analogRead(BOARD_BAT_ADC);
  raw /= 16;
  return (raw / 4095.0f) * 3.3f * 2.0f;  // 분압 2배
}

void modemPowerOn() {
  pinMode(BOARD_POWERON, OUTPUT); digitalWrite(BOARD_POWERON, HIGH);
  pinMode(MODEM_RST, OUTPUT);     digitalWrite(MODEM_RST, LOW); delay(100);
  digitalWrite(MODEM_RST, HIGH);
  pinMode(BOARD_PWRKEY, OUTPUT);
  digitalWrite(BOARD_PWRKEY, LOW);  delay(100);
  digitalWrite(BOARD_PWRKEY, HIGH); delay(1000);  // PWRKEY 펄스
  digitalWrite(BOARD_PWRKEY, LOW);
}

// L76K GPS(Serial2)에서 NMEA를 읽어 위경도 취득. 성공 시 true.
// ★모뎀 AT가 아니라 L76K UART다. 실내에서는 대부분 fix 안 됨 → 창가/야외에서 확인.
bool getFix(double &lat, double &lon, uint32_t timeoutMs = GPS_FIX_TIMEOUT_MS) {
  pinMode(BOARD_GPS_WAKEUP_PIN, OUTPUT); digitalWrite(BOARD_GPS_WAKEUP_PIN, HIGH);
  SerialGPS.begin(GPS_BAUDRATE, SERIAL_8N1, BOARD_GPS_RX_PIN, BOARD_GPS_TX_PIN);
  uint32_t start = millis();
  while (millis() - start < timeoutMs) {
    while (SerialGPS.available()) gps.encode(SerialGPS.read());
    if (gps.location.isValid() && gps.location.age() < 3000 && gps.satellites.value() >= 4) {
      lat = gps.location.lat();
      lon = gps.location.lng();
      return true;
    }
    delay(10);
  }
  return false;
}

// GPS UTC 시각을 ISO8601로. 유효하지 않으면 빈 문자열.
void gpsIso8601(char* buf, size_t n) {
  if (gps.date.isValid() && gps.time.isValid()) {
    snprintf(buf, n, "%04d-%02d-%02dT%02d:%02d:%02dZ",
             gps.date.year(), gps.date.month(), gps.date.day(),
             gps.time.hour(), gps.time.minute(), gps.time.second());
  } else {
    buf[0] = '\0';
  }
}

void deepSleep() {
  modem.poweroff();
  // (개선 여지) L76K 저전력: 딥슬립 전 GPS 전원/wakeup 정리 시 약 133µA 추가 절감.
  esp_sleep_enable_timer_wakeup((uint64_t)SLEEP_MINUTES * 60ULL * 1000000ULL);
  esp_deep_sleep_start();
}

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
  modemPowerOn();
  SerialAT.begin(115200, SERIAL_8N1, MODEM_RX, MODEM_TX);  // 공식 예제와 동일(RX,TX 순서)
  delay(3000);

  Serial.println("[SEACUT] 모뎀 초기화");
  if (!modem.testAT(10000)) {
    // 무응답이면: (1) 18650 배터리 장착(USB만 급전 금지) (2) BOARD_POWERON HIGH (3) baud 115200
    //   위를 확인해도 안 될 때만 마지막 수단으로 26/27 교체. 배선 자체는 공식 예제와 동일하다.
    Serial.println("모뎀 무응답 → 슬립");
    deepSleep();
  }

  Serial.println("[SEACUT] 망 접속 대기");
  if (!modem.waitForNetwork(60000)) { Serial.println("망 등록 실패 → 슬립"); deepSleep(); }
  if (!modem.gprsConnect(APN, GPRS_USER, GPRS_PASS)) { Serial.println("PDP 실패(APN 확인) → 슬립"); deepSleep(); }
  Serial.print("[SEACUT] 접속 IP "); Serial.println(modem.getLocalIP());

  double lat = 0, lon = 0;
  bool fixed = getFix(lat, lon);
  float batt = readBatteryV();
  Serial.printf("[SEACUT] GPS fix=%d lat=%.6f lon=%.6f sats=%lu batt=%.2fV\n",
                fixed, lat, lon, gps.satellites.value(), batt);

  if (!fixed) {
    // /api/ping은 lat/lon 필수라 fix 없으면 400. 전송 생략하고 다음 주기 재시도.
    Serial.println("[SEACUT] GPS fix 실패(실내면 창가/야외로) → 전송 생략, 슬립");
    modem.gprsDisconnect();
    deepSleep();
  }

  char ts[24]; gpsIso8601(ts, sizeof(ts));
  String body = buildPingBody(lat, lon, ts, batt);         // 벤치·운영 공통 단건 ping(batt 포함). 조립은 서버가

  Serial.println("[SEACUT] POST " + body);
  http.beginRequest();
  http.post(SERVER_PATH);
  http.sendHeader("Content-Type", "application/json");
  http.sendHeader("Content-Length", body.length());
  http.beginBody();
  http.print(body);
  http.endRequest();
  int status = http.responseStatusCode();
  Serial.print("[SEACUT] 서버 응답 "); Serial.println(status);  // 벤치 성공=200, {"ok":true,...}

  modem.gprsDisconnect();
  Serial.println("[SEACUT] 완료 → 딥슬립");
  deepSleep();
}

void loop() { /* 딥슬립 사용, loop 미사용 */ }
