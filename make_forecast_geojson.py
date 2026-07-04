"""
SEA:CUT — openc.caresea 예측 오버레이용 표류 GeoJSON 생성기
==========================================================
감전천 합류부(openc OBS_SITES 'gamjeon-confluence')에서 입자를 뿌려
라그랑주 표류를 돌리고, NakdongMap이 얹을 예측 레이어를 GeoJSON으로 낸다.
(OpenDrift B모드 실forcing이 붙기 전까지의 예측 표출본. 실측 DriftTrack과
 겹쳐 "예측-실측 폐루프"의 예측 쪽을 담당.)

출력: openc-caresea/public/data/drift-forecast.geojson
  - Feature mean_path (LineString) : 앙상블 평균 경로
  - Feature envelope  (Polygon)    : 불확실성 범위(볼록껍질)
  - Feature endpoints (MultiPoint) : 24h 후 입자 도달 분포
  - Feature sample_track ×N (LineString) : 대표 궤적 몇 개

실행: python make_forecast_geojson.py
"""
import json
import math
import os
from datetime import datetime, timezone, timedelta

import numpy as np

# 감전천 합류부 — openc OBS_SITES 'gamjeon-confluence' 좌표와 일치
SEED_LON, SEED_LAT = 128.9706, 35.1326
SEED_R_M = 350
N = 300
RUN_H = 30
DT_MIN = 15
WINDAGE = 0.01
Q = 0.4
WIND_SPD, WIND_FROM = 5.0, 315.0
K_DIFF = 10.0
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "openc-caresea", "public", "data", "drift-forecast.geojson")

M_LAT = 111_000.0
M_LON = 111_000.0 * math.cos(math.radians(35))


def vel(t_h):
    ph = 2 * math.pi * t_h / 12.42
    v = -(0.05 + Q * 0.20) + 0.55 * math.sin(ph)
    u = 0.18 * math.sin(ph + 1.0)
    to = math.radians(WIND_FROM + 180)
    u += WINDAGE * WIND_SPD * math.sin(to)
    v += WINDAGE * WIND_SPD * math.cos(to)
    return u, v


def hull(pts):
    pts = sorted(set(map(tuple, pts)))
    if len(pts) < 3:
        return pts
    cr = lambda o, a, b: (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    lo = []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    up = []
    for p in reversed(pts):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def main():
    rng = np.random.default_rng(7)
    r = SEED_R_M * np.sqrt(rng.random(N))
    th = rng.random(N) * 2 * math.pi
    lon = SEED_LON + (r * np.cos(th)) / M_LON
    lat = SEED_LAT + (r * np.sin(th)) / M_LAT
    alive = np.ones(N, bool)
    dt_s = DT_MIN * 60
    steps = int(RUN_H * 60 / DT_MIN)
    sig = math.sqrt(2 * K_DIFF * dt_s)

    tracks = [[] for _ in range(N)]
    mean_path = []
    for s in range(steps + 1):
        for i in range(N):
            if alive[i]:
                tracks[i].append([round(float(lon[i]), 5), round(float(lat[i]), 5)])
        if alive.any():
            mean_path.append([round(float(lon[alive].mean()), 5),
                              round(float(lat[alive].mean()), 5)])
        u, v = vel(s * DT_MIN / 60)
        lon = lon + (u * dt_s + rng.normal(0, sig, N)) / M_LON
        lat = lat + (v * dt_s + rng.normal(0, sig, N)) / M_LAT
        alive &= lat > 35.02          # 남해 경계 이남은 유출 처리(종점 고정)

    endpoints = [t[-1] for t in tracks if t]
    env = hull(endpoints + [t[len(t) // 2] for t in tracks if len(t) > 3])
    if env and env[0] != env[-1]:
        env.append(env[0])

    idx = np.linspace(0, N - 1, 10).astype(int)
    feats = [
        {"type": "Feature", "properties": {"kind": "mean_path"},
         "geometry": {"type": "LineString", "coordinates": mean_path}},
        {"type": "Feature", "properties": {"kind": "envelope"},
         "geometry": {"type": "Polygon", "coordinates": [env]}},
        {"type": "Feature", "properties": {"kind": "endpoints", "count": len(endpoints)},
         "geometry": {"type": "MultiPoint", "coordinates": endpoints}},
    ]
    for j in idx:
        if tracks[j]:
            feats.append({"type": "Feature", "properties": {"kind": "sample_track"},
                          "geometry": {"type": "LineString", "coordinates": tracks[j]}})

    gj = {
        "type": "FeatureCollection",
        "properties": {
            "model": "lagrangian-lite-v1 (OpenDrift B모드 실forcing 전 표출본)",
            "site_id": "gamjeon-confluence",
            "release": {"lon": SEED_LON, "lat": SEED_LAT},
            "run_hours": RUN_H, "particles": N,
            "windage": WINDAGE, "wind": {"speed_ms": WIND_SPD, "from_deg": WIND_FROM},
            "note": "예측 궤적(앙상블) — 실측 DriftTrack과 겹쳐 예측·실측 폐루프의 예측 축.",
        },
        "features": feats,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(gj, f, ensure_ascii=False)
    print(f"저장: {os.path.abspath(OUT)}")
    print(f"  features: mean_path({len(mean_path)}p) · envelope({len(env)}p) · "
          f"endpoints({len(endpoints)}) · sample_track×{len(idx)}")


if __name__ == "__main__":
    main()
