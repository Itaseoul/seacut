"""
SEA:CUT — openc 예측 레이어를 '실측 해수유동' 기반으로 교체
==========================================================
nakdong_gridcells.json(해양수산부 해수유동 3분, 낙동강 하구 ROI 실측 셀)을
읽어 실제 유속장으로 입자를 이송하고, 같은 스키마의 drift-forecast.geojson을
낸다. 추가로 실측 유속 벡터(current_field)를 얹어 지도에 표시한다.

주의: 단일 시각(2020-12-31 03시) 스냅샷 = 정상류 이송 데모(시변동 아님).
      OpenDrift B모드가 다중시각 격자를 먹이면 진짜 예보가 된다.

실행: python make_forecast_real.py   (fetch_nakdong_cells.py 완료 후)
출력: openc-caresea/public/data/drift-forecast.geojson  (schematic본 대체)
"""
import json
import math
import os

import numpy as np
from scipy.interpolate import griddata

CELLS = r"D:\ita-claude-cowork\seacut_drifter\nakdong_gridcells.json"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "openc-caresea", "public", "data", "drift-forecast.geojson")
SEED_LON, SEED_LAT = 128.9706, 35.1326   # 감전천 합류부
SEED_R_M, N, RUN_H, DT_MIN, K_DIFF = 350, 300, 12, 15, 8.0
M_LAT = 111_000.0
M_LON = 111_000.0 * math.cos(math.radians(35))


def dir_to_uv(spd, deg):        # 유향=흐르는 방향(toward)
    r = math.radians(deg)
    return spd * math.sin(r), spd * math.cos(r)


def hull(pts):
    pts = sorted(set(map(tuple, pts)))
    if len(pts) < 3:
        return pts
    cr = lambda o, a, b: (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def main():
    d = json.load(open(CELLS, encoding="utf-8"))
    cells = d["cells"]
    if not cells:
        raise SystemExit("ROI 셀 0개 — fetch_nakdong_cells.py 먼저 완료 필요")
    clon = np.array([c["lon"] for c in cells])
    clat = np.array([c["lat"] for c in cells])
    cu = np.array([dir_to_uv(c["ocspd"], c["ocdrct"])[0] for c in cells])
    cv = np.array([dir_to_uv(c["ocspd"], c["ocdrct"])[1] for c in cells])

    def field(lon, lat):
        u = griddata((clon, clat), cu, (lon, lat), method="linear")
        v = griddata((clon, clat), cv, (lon, lat), method="linear")
        un = griddata((clon, clat), cu, (lon, lat), method="nearest")
        vn = griddata((clon, clat), cv, (lon, lat), method="nearest")
        u = np.where(np.isnan(u), un, u)
        v = np.where(np.isnan(v), vn, v)
        return u, v

    rng = np.random.default_rng(7)
    r = SEED_R_M * np.sqrt(rng.random(N))
    th = rng.random(N) * 2 * math.pi
    lon = SEED_LON + (r * np.cos(th)) / M_LON
    lat = SEED_LAT + (r * np.sin(th)) / M_LAT
    dt_s = DT_MIN * 60
    steps = int(RUN_H * 60 / DT_MIN)
    sig = math.sqrt(2 * K_DIFF * dt_s)

    tracks = [[] for _ in range(N)]
    mean = []
    for s in range(steps + 1):
        for i in range(N):
            tracks[i].append([round(float(lon[i]), 5), round(float(lat[i]), 5)])
        mean.append([round(float(lon.mean()), 5), round(float(lat.mean()), 5)])
        u, v = field(lon, lat)
        lon = lon + (u * dt_s + rng.normal(0, sig, N)) / M_LON
        lat = lat + (v * dt_s + rng.normal(0, sig, N)) / M_LAT

    endpoints = [t[-1] for t in tracks]
    env = hull(endpoints + [t[len(t)//2] for t in tracks])
    if env and env[0] != env[-1]:
        env.append(env[0])

    # 실측 유속 벡터(current_field) — 셀당 짧은 화살표 선분
    vecs = []
    for c in cells:
        u, v = dir_to_uv(c["ocspd"], c["ocdrct"])
        scale = 900.0  # m per (m/s) 표시 배율
        elon = c["lon"] + (u * scale) / M_LON
        elat = c["lat"] + (v * scale) / M_LAT
        vecs.append({"type": "Feature",
                     "properties": {"kind": "current_vec", "ocspd": c["ocspd"], "ocdrct": c["ocdrct"]},
                     "geometry": {"type": "LineString",
                                  "coordinates": [[round(c["lon"], 5), round(c["lat"], 5)],
                                                  [round(elon, 5), round(elat, 5)]]}})

    idx = np.linspace(0, N-1, 10).astype(int)
    feats = [
        {"type": "Feature", "properties": {"kind": "mean_path"},
         "geometry": {"type": "LineString", "coordinates": mean}},
        {"type": "Feature", "properties": {"kind": "envelope"},
         "geometry": {"type": "Polygon", "coordinates": [env]}},
        {"type": "Feature", "properties": {"kind": "endpoints", "count": len(endpoints)},
         "geometry": {"type": "MultiPoint", "coordinates": endpoints}},
    ] + vecs + [
        {"type": "Feature", "properties": {"kind": "sample_track"},
         "geometry": {"type": "LineString", "coordinates": tracks[j]}} for j in idx
    ]

    gj = {"type": "FeatureCollection",
          "properties": {
              "model": "mof-current-snapshot-v1 (해양수산부 해수유동 3분 실측 격자)",
              "forcing": "data.go.kr 1192000 apVhdService_ContOc3 · 실측 유속/유향",
              "anals": {"ymd": d["analsYmd"], "hhs": d["analsHhs"]},
              "site_id": "gamjeon-confluence",
              "release": {"lon": SEED_LON, "lat": SEED_LAT},
              "run_hours": RUN_H, "particles": N, "roi_cells": len(cells),
              "note": "실측 해수유동 1스냅샷 정상류 이송(시변동 아님). 다중시각 격자 시 진짜 예보.",
          },
          "features": feats}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(gj, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"저장: {os.path.abspath(OUT)}")
    print(f"  실측셀 {len(cells)} · 벡터 {len(vecs)} · mean {len(mean)}p · endpoints {len(endpoints)}")


if __name__ == "__main__":
    main()
