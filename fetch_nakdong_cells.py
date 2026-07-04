"""해양수산부 해수유동 3분 전국격자 → 낙동강 하구 ROI 셀만 추출·저장.
API가 느려 페이지네이션은 백그라운드로 실행(완료 시 nakdong_gridcells.json).
샘플 가용일자 2020-12-31 03시 기준(데이터 존재 확인된 시각)."""
import os
import json
import requests
import xml.etree.ElementTree as ET

# data.go.kr 서비스키는 환경변수로 주입 (공개 저장소에 키를 넣지 않음)
KEY = os.environ.get("MOF_KEY") or os.environ.get("KMA_SERVICE_KEY", "")
if not KEY:
    raise SystemExit("환경변수 MOF_KEY(또는 KMA_SERVICE_KEY)를 설정하세요.")
URL = "http://apis.data.go.kr/1192000/apVhdService_ContOc3/getOpnContOc3"
YMD, HHS = "20201231", "03"
LON = (128.80, 129.06)
LAT = (34.99, 35.22)
OUT = r"D:\ita-claude-cowork\seacut_drifter\nakdong_gridcells.json"

roi, total, got = [], None, 0
for page in range(1, 20):
    p = {"serviceKey": KEY, "numOfRows": 1000, "pageNo": page,
         "analsYmd": YMD, "analsHhs": HHS, "type": "xml"}
    r = requests.get(URL, params=p, timeout=90)
    root = ET.fromstring(r.content)
    if total is None:
        total = root.findtext(".//totalCount")
    items = list(root.iter("item"))
    got += len(items)
    for it in items:
        lo = float(it.findtext("lo")); la = float(it.findtext("la"))
        if LON[0] <= lo <= LON[1] and LAT[0] <= la <= LAT[1]:
            roi.append({"gridCd": it.findtext("gridCd"), "lon": lo, "lat": la,
                        "ocspd": float(it.findtext("ocspd")),
                        "ocdrct": float(it.findtext("ocdrct"))})
    print(f"p{page}: +{len(items)} (누적 {got}/{total}) · ROI {len(roi)}", flush=True)
    # 매 페이지 부분저장(중단 대비)
    json.dump({"analsYmd": YMD, "analsHhs": HHS, "roi_lon": list(LON), "roi_lat": list(LAT),
               "pages_done": page, "count": len(roi), "cells": roi},
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if len(items) < 1000:
        break

print(f"\n완료 — 낙동강 ROI 격자 {len(roi)}개 → {OUT}", flush=True)
for c in sorted(roi, key=lambda x: (-x["lat"], x["lon"])):
    print(f"  {c['gridCd']:14} {c['lon']:.3f},{c['lat']:.3f}  유속{c['ocspd']:.3f} 유향{c['ocdrct']:.0f}", flush=True)
