/*
 * Friendly Floaty (SEA:CUT) 드리프터 펌웨어 — LTE Cat.1 bis (A7670) + L76K GPS
 * 대상 보드: LILYGO T-A7670G R2 (With GPS L76K), ESP32-WROVER-E
 * FF-ID 스키마 v1.1 (data/schema.md) 준수.
 *
 * 동작(v1.1, store-and-forward):
 *   깨어남 → L76K GPS fix(+UTC 시각) → 레코드를 RTC 버퍼에 적재(seq 부여)
 *         → 모뎀 전원 → 망 접속(Cat.1 bis) → 버퍼의 미전송 레코드를 오래된 것부터 POST
 *         → 성공분 제거 → 딥슬립.
 *   ★망이 안 잡혀도 fix는 버퍼에 남는다(하천 음영 구간). 다음 웨이크에 몰아 보낸다.
 *   ★도착 순서를 서버가 신뢰하지 않도록 각 레코드는 자기 ts_fix(GPS UTC)와 seq를 갖고 간다.
 *   (선행사례 공통 교훈: Duncan·Merlino·Kang 모두 store-and-forward가 필수였다.
 *    docs/사례연구_기구제작_운영_데이터.md §3-16 참조.)
 *
 * ⚠ 흐름 변경 고지: 초기 벤치 검증본(v1.0)은 "모뎀 접속 → GPS" 순서였다. v1.1은
 *   버퍼링 정합(망 없어도 fix 저장)과 모뎀 유휴 소모 절감을 위해 "GPS → 모뎀" 순서다.
 *   프리미티브(핀맵·전원 시퀀스·라이브러리)는 검증본과 동일하나, 순서 변경분은
 *   벤치 재검증 후 방류에 쓴다(정직 원칙: 측정 전 개선 주장 금지).
 *
 * ★라이브러리 (반드시): lewisxhe/TinyGSM-fork (LILYGO 공식 포크). 스톡 vshymanskyy/TinyGSM
 *   에는 TINY_GSM_MODEM_A7670 매크로가 없어 컴파일이 깨진다. 스톡이 깔려 있으면 제거한다.
 *   그 외: TinyGPSPlus, ArduinoHttpClient, Preferences(ESP32 코어 내장).
 *   보드: ESP32 Arduino core 3.0.x, "ESP32 Dev Module".
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
// 1 = 벤치 검증(로컬 ingest_server.py, HTTP 평문, /api/ping).  ★처음엔 이걸로.
// 0 = 운영 전송(openc.caresea.kr, HTTPS 443, /api/observations/drift/ping).
#define BENCH_HTTP 1

// ── CONFIG ────────────────────────────────────────────────────────────────
#define DEVICE_ID     "ff-kr-bs-u0001"        // 기기 식별자(유닛 메타디렉토리 unit_id와 짝)
#define SITE_ID       "nakdong-hakjang"       // 사이트 태그(서버가 궤적에 태그)
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
  //   (a) 바인딩을 0.0.0.0으로 바꾸고 같은 망 노트북 LAN IP, 또는 (b) `ngrok tcp 8770`.
  //   ※ ngrok http(https 터널)는 TLS라 평문 클라이언트로 안 붙는다 → BENCH_HTTP 0으로.
  const char* SERVER_HOST = "192.168.0.10";   // ★노트북 LAN IP 또는 ngrok tcp 호스트로 교체
  const int   SERVER_PORT = 8770;             // ngrok tcp면 발급된 포트
  const char* SERVER_PATH = "/api/ping";
#else
  const char* SERVER_HOST = "openc.caresea.kr";
  const int   SERVER_PORT = 443;              // https
  const char* SERVER_PATH = "/api/observations/drift/ping";
#endif

const uint32_t SLEEP_MINUTES      = 30;        // 전송 주기(분). 벤치 확인은 5로 낮춰서
const uint32_t GPS_FIX_TIMEOUT_MS = 180000;    // L76K 콜드스타트 여유(야외 30초~수 분)
// ───────────────────────────────────────────────────────────────────────────

// ★lewisxhe/TinyGSM-fork 전제(스톡엔 A7670 매크로 없음). TinyGsmClientSecure는
//   A76XXSSL 매크로에서만 typedef된다 → 벤치/운영을 매크로로 분기(검수에서 잡은 컴파일 불능).
#if BENCH_HTTP
  #define TINY_GSM_MODEM_A7670      // 벤치: v1.0 검증본과 동일(평문 HTTP)
#else
  #define TINY_GSM_MODEM_A76XXSSL   // 운영: TinyGsmClientSecure 포함(HTTPS). 모뎀 클래스가 바뀌므로 벤치 재검증 필수
#endif
#define TINY_GSM_RX_BUFFER 1024
#include <TinyGsmClient.h>
#include <ArduinoHttpClient.h>
#include <TinyGPSPlus.h>
#include <Preferences.h>
#include <driver/gpio.h>

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
Preferences    prefs;
bool           modem_on = false;   // SerialAT.begin 전 modem.poweroff() 방지 가드

// ── FF-ID v1.1 store-and-forward 버퍼 (RTC slow memory: 딥슬립 생존, 전원상실 시 소실) ──
// 전원상실(브라운아웃·배터리 교체)엔 버퍼가 사라진다 — seq는 NVS로 복원되므로 서버가
// seq 갭으로 결측을 안다(스키마 §4). NVS에 매 레코드 저장은 마모·복잡도 대비 이득이 작아
// 채택하지 않는다(정직 트레이드오프).
struct PingRec {
  double   lat, lon;
  float    batt;
  float    hdop;        // <0 = 무효(필드 생략)
  uint32_t seq;
  char     ts_fix[24];  // GPS UTC ISO8601. 빈 문자열 = 시각 무효
};
#define BUF_MAX 16
RTC_DATA_ATTR PingRec  rtc_buf[BUF_MAX];
RTC_DATA_ATTR uint8_t  rtc_buf_n = 0;
RTC_DATA_ATTR uint32_t rtc_seq   = 0;   // 단조증가 레코드 카운터(딥슬립 생존)

// seq를 NVS와 동기화: 전원상실 후에도 단조증가 유지(중복 seq 방지가 목적, 갭은 허용)
uint32_t nextSeq() {
  prefs.begin("ffid", false);
  uint32_t nv = prefs.getUInt("seq", 0);
  if (nv > rtc_seq) rtc_seq = nv;       // 전원상실 직후: NVS가 최신
  rtc_seq++;
  prefs.putUInt("seq", rtc_seq);
  prefs.end();
  return rtc_seq;
}

// FF-ID v1.1 ping 본문 (data/schema.md §1).
// ts_fix = 디바이스 GPS fix 시각(관측 시각). 구서버 호환 위해 legacy "ts"도 같은 값으로 병송
// (스키마 1.0→1.1 매핑: ts → ts_fix). 서버 수신시각은 서버가 server_recv_ts로 따로 채운다.
String buildPingBody(const PingRec &r) {
  String b = String("{\"device_id\":\"") + DEVICE_ID + "\",\"site_id\":\"" + SITE_ID + "\"";
  b += ",\"seq\":" + String(r.seq);
  b += ",\"lat\":" + String(r.lat, 6) + ",\"lon\":" + String(r.lon, 6);
  b += ",\"batt\":" + String(r.batt, 2);
  b += ",\"sample_interval_s\":" + String(SLEEP_MINUTES * 60);
  if (r.hdop >= 0) b += ",\"fix_quality\":" + String(r.hdop, 1);
  b += ",\"gnss_source\":\"l76k\"";
  if (r.ts_fix[0]) { b += ",\"ts_fix\":\"" + String(r.ts_fix) + "\",\"ts\":\"" + String(r.ts_fix) + "\""; }
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
  // ★T-A7670 계열 RST는 HIGH=리셋 어서트(공식 utilities.h MODEM_RESET_LEVEL=HIGH). 유휴=LOW.
  //   (검수에서 잡은 v1.0 계승 버그: HIGH로 방치하면 모뎀이 리셋에 잡혀 testAT 전패)
  pinMode(MODEM_RST, OUTPUT);
  digitalWrite(MODEM_RST, LOW);  delay(100);
  digitalWrite(MODEM_RST, HIGH); delay(2600);   // 하드 리셋 펄스(공식 시퀀스)
  digitalWrite(MODEM_RST, LOW);                 // 반드시 LOW로 종료
  pinMode(BOARD_PWRKEY, OUTPUT);
  digitalWrite(BOARD_PWRKEY, LOW);  delay(100);
  digitalWrite(BOARD_PWRKEY, HIGH); delay(1000);  // PWRKEY 펄스
  digitalWrite(BOARD_PWRKEY, LOW);
  modem_on = true;
}

// L76K GPS(Serial2)에서 NMEA를 읽어 위경도 취득. 성공 시 true.
// ★모뎀 AT가 아니라 L76K UART다. 실내에서는 대부분 fix 안 됨 → 창가/야외에서 확인.
// ★GPS 전원은 BOARD_POWERON 레일에 걸려 있어 fix 전에 POWERON을 먼저 HIGH로 올린다.
bool getFix(double &lat, double &lon, uint32_t timeoutMs = GPS_FIX_TIMEOUT_MS) {
  pinMode(BOARD_POWERON, OUTPUT); digitalWrite(BOARD_POWERON, HIGH);  // GPS 레일 확보(모뎀보다 먼저 필요)
  pinMode(BOARD_GPS_WAKEUP_PIN, OUTPUT); digitalWrite(BOARD_GPS_WAKEUP_PIN, HIGH);
  SerialGPS.begin(GPS_BAUDRATE, SERIAL_8N1, BOARD_GPS_RX_PIN, BOARD_GPS_TX_PIN);
  uint32_t start = millis();
  while (millis() - start < timeoutMs) {
    while (SerialGPS.available()) gps.encode(SerialGPS.read());
    bool locOk  = gps.location.isValid() && gps.location.age() < 3000 && gps.satellites.value() >= 4;
    bool timeOk = gps.date.isValid() && gps.time.isValid() && gps.date.year() >= 2025;
    if (locOk && timeOk) {           // RMC(날짜)는 같은 에포크에 오므로 지연 최대 ~1초.
      lat = gps.location.lat();      // 날짜 검증 없이 리턴하면 ts_fix가 비어 서버가 server_recv로
      lon = gps.location.lng();      // 강등 — 버퍼 지연 레코드는 관측시각이 통째로 틀어짐(검수 발견)
      return true;
    }
    delay(10);
  }
  // 타임아웃 폴백: 위치만이라도 유효하면 관측은 살린다(ts_fix만 결측 → 서버가 server_recv 강등)
  if (gps.location.isValid() && gps.location.age() < 3000 && gps.satellites.value() >= 4) {
    lat = gps.location.lat(); lon = gps.location.lng();
    return true;
  }
  // 진단: chars=0이면 GPS 무전원/배선(POWERON 레일 전제 확인 — 벤치 1차 관문), >0이면 단순 미픽스
  Serial.printf("[FF] GPS fix 실패: NMEA chars=%lu\n", (unsigned long)gps.charsProcessed());
  return false;
}

// GPS UTC 시각을 ISO8601로. 유효하지 않으면 빈 문자열.
void gpsIso8601(char* buf, size_t n) {
  if (gps.date.isValid() && gps.time.isValid() && gps.date.year() >= 2025) {
    snprintf(buf, n, "%04d-%02d-%02dT%02d:%02d:%02dZ",
             gps.date.year(), gps.date.month(), gps.date.day(),
             gps.time.hour(), gps.time.minute(), gps.time.second());
  } else {
    buf[0] = '\0';
  }
}

// 버퍼 적재. 가득 차면 가장 오래된 것을 버리고 최신을 지킨다(현재 위치 우선, 스키마 §4가
// seq 갭으로 결측을 안다). GDP식 운명 기록은 서버·정산 로그가 담당.
void bufPush(const PingRec &r) {
  if (rtc_buf_n >= BUF_MAX) {
    memmove(&rtc_buf[0], &rtc_buf[1], sizeof(PingRec) * (BUF_MAX - 1));
    rtc_buf_n = BUF_MAX - 1;
  }
  rtc_buf[rtc_buf_n++] = r;
}

// 버퍼 앞에서부터(오래된 순) POST. 2xx면 제거, 실패하면 중단(남은 건 다음 웨이크에).
// 반환: 보낸 개수.
int flushBuffer() {
  int sent = 0;
  while (rtc_buf_n > 0) {
    String body = buildPingBody(rtc_buf[0]);
    Serial.println("[FF] POST " + body);
    http.beginRequest();
    http.post(SERVER_PATH);
    http.sendHeader("Content-Type", "application/json");
    http.sendHeader("Content-Length", body.length());
    http.beginBody();
    http.print(body);
    http.endRequest();
    int status = http.responseStatusCode();
    if (status > 0) http.responseBody();   // 유효 응답만 소진(오류코드면 재차 30초 대기 회피)
    Serial.print("[FF] 서버 응답 "); Serial.println(status);
    if (status >= 200 && status < 300) {
      memmove(&rtc_buf[0], &rtc_buf[1], sizeof(PingRec) * (rtc_buf_n - 1));
      rtc_buf_n--; sent++;
    } else {
      http.stop();
      break;               // 실패: 배터리 아끼고 다음 주기에 재시도
    }
  }
  return sent;
}

void deepSleep() {
  if (modem_on) modem.poweroff();
  // 딥슬립 중 일반 GPIO는 플로팅 → GPS_WAKEUP이 HIGH로 남으면 L76K가 슬립 내내 켜져
  // 배터리를 지배할 수 있다(공식 DeepSleep 예제 방식으로 홀드). 절감폭은 실측 전.
  pinMode(BOARD_GPS_WAKEUP_PIN, OUTPUT); digitalWrite(BOARD_GPS_WAKEUP_PIN, LOW);
  gpio_hold_en((gpio_num_t)BOARD_GPS_WAKEUP_PIN);
  pinMode(MODEM_RST, OUTPUT);            digitalWrite(MODEM_RST, LOW);
  gpio_hold_en((gpio_num_t)MODEM_RST);
  pinMode(BOARD_POWERON, OUTPUT);        digitalWrite(BOARD_POWERON, LOW);
  gpio_hold_en((gpio_num_t)BOARD_POWERON);
  gpio_deep_sleep_hold_en();
  esp_sleep_enable_timer_wakeup((uint64_t)SLEEP_MINUTES * 60ULL * 1000000ULL);
  esp_deep_sleep_start();
}

void setup() {
  // 웨이크 직후 홀드 해제(없으면 이후 digitalWrite가 홀드에 막혀 무효)
  gpio_deep_sleep_hold_dis();
  gpio_hold_dis((gpio_num_t)BOARD_GPS_WAKEUP_PIN);
  gpio_hold_dis((gpio_num_t)MODEM_RST);
  gpio_hold_dis((gpio_num_t)BOARD_POWERON);
  Serial.begin(115200);
  analogReadResolution(12);

  // ① GPS fix 먼저(망 없어도 관측은 남긴다 — store-and-forward의 요점)
  double lat = 0, lon = 0;
  bool fixed = getFix(lat, lon);
  if (fixed) {
    PingRec r;
    r.lat = lat; r.lon = lon;
    r.batt = readBatteryV();
    r.hdop = gps.hdop.isValid() ? (float)gps.hdop.hdop() : -1.0f;
    r.seq  = nextSeq();
    gpsIso8601(r.ts_fix, sizeof(r.ts_fix));
    bufPush(r);
    Serial.printf("[FF] fix seq=%lu lat=%.6f lon=%.6f hdop=%.1f sats=%lu batt=%.2fV buf=%u\n",
                  (unsigned long)r.seq, lat, lon, r.hdop, gps.satellites.value(), r.batt, rtc_buf_n);
  } else {
    Serial.println("[FF] GPS fix 실패(실내면 창가/야외로). 버퍼 있으면 전송만 시도");
  }

  if (rtc_buf_n == 0) {         // 보낼 것도 없음 → 바로 슬립
    Serial.println("[FF] 전송할 레코드 없음 → 슬립");
    deepSleep();
  }

  // ② 모뎀 → 망 → 버퍼 플러시
  modemPowerOn();
  SerialAT.begin(115200, SERIAL_8N1, MODEM_RX, MODEM_TX);  // 공식 예제와 동일(RX,TX 순서)
  delay(3000);

  Serial.println("[FF] 모뎀 초기화");
  if (!modem.testAT(10000)) {
    // 무응답이면: (1) 18650 배터리 장착(USB만 급전 금지) (2) BOARD_POWERON HIGH (3) baud 115200
    Serial.println("[FF] 모뎀 무응답 → 관측은 버퍼에 보존, 슬립");
    deepSleep();
  }
  if (!modem.waitForNetwork(60000)) { Serial.println("[FF] 망 등록 실패 → 버퍼 보존, 슬립"); deepSleep(); }
  if (!modem.gprsConnect(APN, GPRS_USER, GPRS_PASS)) { Serial.println("[FF] PDP 실패(APN 확인) → 버퍼 보존, 슬립"); deepSleep(); }
  Serial.print("[FF] 접속 IP "); Serial.println(modem.getLocalIP());

  int sent = flushBuffer();
  Serial.printf("[FF] 전송 %d건, 잔여 %u건\n", sent, rtc_buf_n);

  modem.gprsDisconnect();
  Serial.println("[FF] 완료 → 딥슬립");
  deepSleep();
}

void loop() { /* 딥슬립 사용, loop 미사용 */ }
