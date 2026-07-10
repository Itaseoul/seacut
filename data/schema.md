# Data schema (CC BY 4.0) — Friendly Floaty standard (FF-ID)

시민이 만든 하천쓰레기 표류 관측의 표준·인용 가능 포맷. 데이터는 열려 있고(CC BY), 허브의 힘은 데이터를 가두는 데 있지 않고 **인용 표준·프로버넌스·실시간 지도·커뮤니티**에 있다. 누구나 내려받아 쓰되 인용한다.

**Schema version: 1.1** — v1.0 → 1.1 변경: 디바이스 fix 시각(`ts_fix`)·레코드 시퀀스(`seq`)·샘플링 간격(`sample_interval_s`)·측위 품질(`fix_quality`)·GNSS 출처·좌초 상태(`motion_state`)·**유닛 메타데이터 디렉토리**·**QC/store-and-forward 규칙**을 추가. 근거는 NOAA GDP 메타데이터 관행과 선행사례 연구(`docs/사례연구_기구제작_운영_데이터.md`).

> **정직 가드**: `medium=freshwater`·`link=cellular`(위성 아님)는 설계 고정값. 위치·상태는 물리 계산이지 학습 AI 예측 아님. 조립 트랙·모든 표류 수치는 추정(`is_estimate`).

---

## 1. Ping (디바이스 → 서버) — 최소 페이로드

디바이스는 웨이크마다 최소 페이로드만 보낸다. 서버가 인용 id·프로버넌스를 부여하고 트랙을 조립하며 QC를 돌린다.

`POST /api/observations/drift/ping` (번들 `ingest_server.py`는 `POST /api/ping`)

```json
{"device_id":"river-001","site_id":"nakdong-hakjang","seq":1487,"lat":35.10560,"lon":128.94310,"batt":4.02,"ts_fix":"2026-07-10T09:00:00Z","sample_interval_s":900,"fix_quality":1.4,"gnss_source":"l76k"}
```

| field | type | required | note |
|---|---|---|---|
| device_id | string | yes | 디바이스 식별자(공개 스냅샷에선 익명화) |
| site_id | string | no | 사이트 태그 (예: `nakdong-hakjang`) |
| **seq** | integer | **yes** | **디바이스별 단조증가 레코드 카운터.** store-and-forward 핵심 — 버퍼링돼 늦게 온 핑도 도착순이 아니라 seq로 정렬·중복제거 |
| lat | number | **yes** | **EPSG:4326(WGS84), 소수 ≥5자리(≈1m).** 저정밀 절단은 거부/플래그 |
| lon | number | **yes** | 동일 |
| batt | number | no | **볼트** 단위 |
| **ts_fix** | string | **yes\*** | **디바이스 GPS fix 시각, ISO8601 UTC.** 실제 관측 시각(서버 수신시각과 구분) |
| **sample_interval_s** | integer | **yes** | **공칭 핑 간격(초).** 혼합 주기 데이터를 가중·층화하려면 필수. "펌웨어 자유의 조건 = 핑 간격 신고" |
| **fix_quality** | number | no | HDOP(없으면 sat_count). 없으면 down-weight |
| **gnss_source** | string | no | `l76k` / `phone` / `other` |
| motion_state | string | no | 디바이스 힌트 `afloat`/`stranded`/`unknown`(서버도 추론) |

\* `ts_fix` 결측 핑은 거부하지 않고 §2 `ts_source=server_recv`로 **강등 수용**한다(`is_estimate` 상향; 버퍼 지연 전송 시 관측시각 신뢰 불가). 단 디바이스는 반드시 채워 보내는 것이 표준이다.

---

## 2. Observation record (서버 부여, 인용 가능)

서버가 수용된 핑마다 인용 레코드로 감싼다. 공개 스냅샷·다운로드가 노출하는 형태.

```json
{
  "obs_id": "FF-KR-BS-20260710-001524",
  "schema_version": "1.1",
  "ts_fix": "2026-07-10T09:00:00Z",
  "server_recv_ts": "2026-07-10T09:03:11Z",
  "ts_source": "device_fix",
  "seq": 1487,
  "device_id": "d1yo2o4q",
  "site_id": "nakdong-hakjang",
  "lat": 35.10560, "lon": 128.94310, "crs": "EPSG:4326",
  "batt": 4.02,
  "sample_interval_s": 900,
  "fix_quality": 1.4, "gnss_source": "l76k",
  "motion_state": "afloat",
  "qc": { "velocity_4sigma": "pass", "is_estimate": false },
  "provenance": { "source": "device", "verification": "raw", "operator": "gaa-kr-busan" },
  "calibration_ref": "ff-drifter-v1",
  "medium": "freshwater", "link": "cellular",
  "license": "CC BY 4.0"
}
```

| field | 의미 |
|---|---|
| obs_id | 전역 유일·인용 id. 형식 `FF-<country>-<region>-<YYYYMMDD>-<seq>`. **서버가 부여**(자체생성 금지). 이걸 인용 |
| ts_fix / server_recv_ts | 디바이스 fix 시각 / 서버 수신 시각. **분리 저장** |
| ts_source | `device_fix`(ts_fix 있음) / `server_recv`(없어 수신시각 대체 → `is_estimate` 상향). ★큰 지연은 Tier0 배치덤프의 "순간이동 가짜궤적" 신호 |
| qc.velocity_4sigma | 2단계 4σ 속도 QC 결과(§4) |
| motion_state | `afloat`/`stranded`/`unknown` — stranded는 표류 통계서 제외/태깅 |
| provenance.verification | `raw` / `auto_checked` / `steward_verified`(실제 스튜어드·기관 확인 시에만, 날조 금지) |
| medium/link | 고정값 `freshwater`/`cellular`(위성 아님) |

---

## 3. Unit metadata directory (유닛별, GDP식) — 신설

NOAA Global Drifter Program 관행 채택: 각 물리 유닛은 **방류·종료·운명(fate)·하드웨어** 디렉토리 레코드를 갖는다. 그래야 트랙 통계가 "조용한 유실"로 편향되지 않는다(회수-우선 정산과 연동).

```json
{
  "unit_id": "FF-KR-BS-U0042",
  "hardware": { "tier": "T1", "board": "lilygo-t-a7670g-r2", "housing": "pet-1L",
                "calibration_ref": "ff-drifter-v1", "verified_build": true },
  "deploy": { "ts": "2026-07-10T09:00:00Z", "lat": 35.132, "lon": 128.968,
              "session_id": "busan-hakjang-2026-07-10", "access_class": "B" },
  "end":    { "ts": "2026-07-10T16:30:00Z", "lat": 35.071, "lon": 128.947,
              "fate": "recovered", "recovery_evidence": { "last_gps": true, "heartbeat_ceased": true } },
  "epoch": "seconds since 1970-01-01T00:00:00Z"
}
```

- **fate 어휘**(회수 체크리스트와 통일): `recovered` · `stranded` · `sunk` · `signal_lost` · `drifted_out` · `retrieved_damaged`.
- ★`fate=recovered`는 **증거 필수**(마지막 GPS 종점 + heartbeat 소거). 증거 없으면 `unverified_recovery`로 표기(정산 위조 차단).
- `verified_build=true`는 [FLOAT_STANDARD.md](../hardware/FLOAT_STANDARD.md) F1·F2 통과 유닛만.

---

## 4. 품질관리(QC) — 신설/확장

- **2단계 4σ 속도 QC**(NOAA GDP, Hansen & Poulain 방식): 연속 fix 간 속도를 **전진·후진 유한차분** 양쪽으로 계산해, **둘 다** 국지 속도분포의 4σ를 넘으면 그 점을 bad로 플래그. GPS·셀룰러 이상치 점프에 강건.
- **좌초 탐지**: 지속적 근제로 변위 → `motion_state=stranded`. stranded 점군은 태깅·표류/이송 통계서 제외(둔치 좌초 유닛의 정적 점군이 분산·이동 통계를 오염시키지 않게).
- **store-and-forward 정렬**: 서버는 `ts_fix`로 정렬하고 `seq`로 중복제거·결측 탐지. **도착 순서를 신뢰하지 않음**(Duncan·Merlino·Kang 공통 검증).
- 원시 fix 저장 우선(GPS ≈ 10m 규칙 측위이므로 무거운 크리깅 생략, gap/error 플래그만 공개).

---

## 5. Calibration commons

전이 가능한 과학 자산. 각 드리프터 형상은 하천이 아니라 물체의 성질인 windage/drag 계수를 가져 하천 간 이동한다.

```json
{"calibration_id":"ff-drifter-v1","windage":0.012,"drag_area_ratio":25.6,"validated_sites":[{"site":"nakdong-hakjang","windage_alpha":0.013,"alpha_sd":0.003}],"notes":"1L PET bottle, horizontal, self-righting"}
```

- windage 초기값은 **Kang 2025 제주 하구 실증(α 0.012~0.014, 저건현 PET는 해류 지배)** 을 근거로 낮게 잡고, 정점별 α를 실증 보정해 커먼즈에 되돌린다. 새 사이트는 이 프로파일을 재사용해 적은 드리프터로 보정한다.

---

## 6. Self-host / share

자체 서버(`ingest_server.py`)를 돌리거나 공유 커뮤니티 지도에 POST한다. 둘 다 같은 스키마라 데이터가 상호운용된다. **스키마 미준수 = 공유 데이터셋 미포함**(강제 아님, 게이트).

## 7. Citation

`obs_id`로 인용한다. 예:

> Friendly Floaty (SEA:CUT) Open Data (2026), observation FF-KR-BS-20260710-001524, CC BY 4.0.

## 8. Changelog · 하위호환

- **1.0 → 1.1**: `ts`(모호) → `ts_fix`+`server_recv_ts`로 분리(1.0 `ts`는 `ts_fix`로 매핑). 신규 필수 `seq`·`sample_interval_s`; 신규 선택 `fix_quality`·`gnss_source`·`motion_state`·`qc`·`crs`. 유닛 메타데이터 디렉토리(§3)·QC(§4) 신설.
- 혼합 버전 집계 규칙: `schema_version` 별로 필드 매핑 후 합친다. 1.0 레코드는 `ts_source=device_fix` 가정하되 `sample_interval_s` 없으면 `raw`로 강등(가중 불가).
