# SEA:CUT — 소하천 Physical AI

[English](README.en.md) · 한국어

도시 하천과 하구의 부유쓰레기가 강우 때 바다로 유입되기 전에, 어디를 막아야 하는지를 데이터로 찾는 시민과학 오픈소스 프로젝트입니다. 저비용 드리프터가 부유쓰레기와 같은 속도로 흐르며 어디서 멈추는지를 기록하고, 반복된 정체 지점(퇴적 핫스팟)을 공간 클러스터링으로 찾아냅니다.

운영: 사단법인 이타서울 · [GAA(Global Adopt-a-Beach Alliance)](https://team.caresea.kr)

## 라이브 데모

| | 링크 |
|---|---|
| 프로젝트 홈 | https://uploads.caresea.kr/seacut |
| SLM 시뮬레이션 (핫스팟 발견·강수량 예측) | https://uploads.caresea.kr/seacut/slm |
| 낙동강 하구 표류 지도 | https://uploads.caresea.kr/seacut/drift |
| 참여자 앱 (PWA) | https://uploads.caresea.kr/seacut/app |

## 정직한 지능

이 프로젝트는 "온디바이스 마법"을 주장하지 않습니다. 지능은 기기 하나의 판단이 아니라 여러 궤적을 모을 때 드러납니다.

1. **지각** — 다수 드리프터가 흐르고 멈춘 궤적을 수집합니다.
2. **세계 모델** — 반복 정체 구역을 공간 클러스터링으로 찾고, 강수량과 유량에 따른 거동을 학습한 이 하천만의 작은 모델(Small Logical Model)을 만듭니다. 예측을 실제 궤적으로 겹쳐 검증합니다.
3. **행동 (로드맵)** — 현재 단계는 환경 디지털 트윈입니다. 여기에 예측에 따라 조정하는 스마트 차단막과 모델이 유도하는 자율 회수를 더하면 지각·세계모델·행동을 갖춘 Physical AI로 진화합니다.

방법의 계보는 The Ocean Cleanup의 데이터 기반 정화 위치 결정과 같습니다.

## 저장소 구성

```
opendrift_nakdong_demo.py   OpenDrift 라그랑주 입자추적 (낙동강 하구, A/B 모드)
lite_drift_demo.py          numpy 전용 경량 표류 시뮬 (OpenDrift 설치 불필요)
make_forecast_geojson.py    예측 앙상블 → GeoJSON
make_forecast_real.py       실측 forcing 연결 시 실행하는 예측 생성
fetch_nakdong_cells.py      해양수산부 해수유동 격자 → ROI 셀 추출
ingest_server.py            드리프터 ping 수신 + 실측/예측 지도 (stdlib)
make_proposal_still.py      정지 이미지 렌더

demo/                       웹 데모 (홈·SLM 시뮬·표류 지도)
pwa/                        참여자용 PWA (지도·위치기록·오프라인)
firmware/                   드리프터 펌웨어 (ESP32 + A7670 LTE + L76K GPS) 와 BOM
hardware/                   티어별 부품표·3D 부품(OpenSCAD)·도면
docs/                       제작 가이드·책임 있는 배포·글로벌 오픈 BOM(국영문)
data/                       ping·궤적 데이터 스키마
```

## 실행 방법

```bash
# 경량 표류 시뮬 (의존성 최소)
python lite_drift_demo.py

# OpenDrift 데모 (opendrift 설치 필요)
pip install opendrift
python opendrift_nakdong_demo.py

# 해양수산부 격자 API 호출 시 서비스키를 환경변수로 주입
export MOF_KEY="발급받은_data.go.kr_서비스키"
python fetch_nakdong_cells.py
```

API 키는 저장소에 포함하지 않습니다. `data.go.kr`에서 발급받아 `MOF_KEY` 환경변수로 넣으세요.

## 하드웨어

대당 저비용 오픈 하드웨어 드리프터입니다. 하우징은 폐페트병 업사이클을 기본으로 하고, 통신은 도심·연안에서 셀룰러(LTE Cat.1 bis, LILYGO T-A7670G + 온보드 L76K GPS)로, 셀룰러가 없는 산간·개활 하천에서는 사설 저전력망(Meshtastic, KR920)으로 운영합니다.

- 티어별 부품표: [hardware/BOM.md](hardware/BOM.md) · 전 세계 제작 가이드 [docs/OPEN_HARDWARE_BOM_global.md](docs/OPEN_HARDWARE_BOM_global.md) ([한국어](docs/OPEN_HARDWARE_BOM_global_ko.md))
- 3D 부품 (파라메트릭 OpenSCAD): [hardware/cad/](hardware/cad/) — 브래킷·밸러스트 킬·회수 고리
- 제작 순서: [docs/BUILD.md](docs/BUILD.md) · 책임 있는 배포(지역 규정 localize): [docs/DEPLOY_responsibly.md](docs/DEPLOY_responsibly.md)

기존 단일 부품표는 [firmware/BOM.md](firmware/BOM.md)에 있습니다.

## 안전·윤리 원칙

- 사람이 물에 들어가지 않습니다. 방류와 회수는 제방·다리에서 뜰채로, 접근이 어려운 곳은 소형 보트로 합니다. 학생의 입수는 금지합니다.
- 강우·증수·강풍 시 활동을 중단합니다.
- 기기는 회수를 전제로 설계합니다. 고정밀 좌표, 눈에 띄는 색, 연락 QR, 완전 밀봉으로 회수율을 높이고 유실률을 예산에 반영합니다.
- 개인정보를 수집하지 않습니다. 참여는 팀 코드로만 이루어집니다.

## 라이선스

펌웨어·소프트웨어는 MIT([LICENSE](LICENSE)), 하드웨어 설계는 CERN-OHL-P([LICENSE-hardware.md](LICENSE-hardware.md)), 문서·데이터는 CC BY 4.0([LICENSE-docs.md](LICENSE-docs.md))입니다. 오픈소스 하드웨어 정의를 따르며 OSHWA 인증을 지향합니다.
