"""
SEA:CUT — 경량 표류 검증본 (numpy 전용, 의존성 최소)
====================================================
OpenDrift 설치가 무거워 막힐 때를 대비한 '파이프라인 증명용' 최소 구현.
A 모드(도식 forcing)와 동일한 물리를 numpy만으로 적분하고, OpenDrift 데모와
'동일한 산출물 스키마'(nakdong_track.csv)를 내보낸다 → 3단계 ita.city 입력을
OpenDrift 설치 여부와 무관하게 진행할 수 있게 한다.

물리: 잔차류(외해행) + 조류(반일주조) + 바람 windage + 난류확산(random walk),
      해안/경계 좌초 처리. 위젯·OpenDrift 데모와 동일한 투하 지점·계수.

실행:  python lite_drift_demo.py
산출:  nakdong_track.csv  (time, particle_id, lon, lat)
       lite_drift.png     (경로 지도; matplotlib 있으면)
"""
import csv
import math
from datetime import datetime, timedelta

import numpy as np

LON_MIN, LON_MAX = 128.80, 129.06
LAT_MIN, LAT_MAX = 34.99, 35.22
SEED_LON, SEED_LAT = 128.945, 35.16
SEED_RADIUS_M = 1500
N = 500
RUN_HOURS = 36
DT_MIN = 15
WINDAGE = 0.01
Q = 0.4                       # 하천 방류(0~1)
WIND_SPEED, WIND_FROM = 5.0, 315.0   # m/s, 북서
K_DIFF = 12.0                 # 수평 확산(m^2/s)

M_PER_DEG_LAT = 111_000.0
M_PER_DEG_LON = 111_000.0 * math.cos(math.radians(35))


def seed(rng):
    r = SEED_RADIUS_M * np.sqrt(rng.random(N))
    th = rng.random(N) * 2 * math.pi
    lon = SEED_LON + (r * np.cos(th)) / M_PER_DEG_LON
    lat = SEED_LAT + (r * np.sin(th)) / M_PER_DEG_LAT
    return lon, lat


def velocity(t_h):
    """(u, v) m/s — 도식 forcing. A 모드 reader_constant과 같은 계열."""
    ph = 2 * math.pi * t_h / 12.42
    v_res = -(0.05 + Q * 0.20)
    v_tide = 0.55 * math.sin(ph)
    u_tide = 0.18 * math.sin(ph + 1.0)
    to = math.radians(WIND_FROM + 180)
    u_w = WINDAGE * WIND_SPEED * math.sin(to)
    v_w = WINDAGE * WIND_SPEED * math.cos(to)
    return u_tide + u_w, v_res + v_tide + v_w


def main():
    rng = np.random.default_rng(42)
    lon, lat = seed(rng)
    status = np.zeros(N, dtype=int)          # 0 float,1 sea,2 beach
    start = datetime(2026, 7, 2, 6, 0, 0)
    dt_s = DT_MIN * 60
    steps = int(RUN_HOURS * 60 / DT_MIN)
    sig = math.sqrt(2 * K_DIFF * dt_s)       # random-walk 표준편차(m)

    rows = []
    for s in range(steps + 1):
        t_h = s * DT_MIN / 60.0
        tstamp = (start + timedelta(minutes=s * DT_MIN)).isoformat()
        for pid in range(N):
            if status[pid] == 0:
                rows.append((tstamp, pid, round(float(lon[pid]), 6), round(float(lat[pid]), 6)))

        u, v = velocity(t_h)
        live = status == 0
        n = int(live.sum())
        if n == 0:
            break
        du = (u * dt_s + rng.normal(0, sig, N)) / M_PER_DEG_LON
        dv = (v * dt_s + rng.normal(0, sig, N)) / M_PER_DEG_LAT
        nlon = lon + du
        nlat = lat + dv

        beached = live & ((nlon <= LON_MIN + 0.003) | (nlon >= LON_MAX - 0.003))
        to_sea = live & (nlat <= LAT_MIN + 0.006)
        status[beached] = 2
        status[to_sea] = 1
        moved = live & ~beached & ~to_sea
        lon[moved] = nlon[moved]
        lat[moved] = nlat[moved]

    c = {0: int((status == 0).sum()), 1: int((status == 1).sum()), 2: int((status == 2).sum())}
    print(f"입자 {N}개 · {RUN_HOURS}h 적분 완료")
    print(f"  외해 유출 {c[1]} ({c[1]*100//N}%) · 좌초 {c[2]} ({c[2]*100//N}%) · 표류중 {c[0]}")

    with open("nakdong_track.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["time", "particle_id", "lon", "lat"])
        w.writerows(rows)
    print(f"  궤적 CSV 저장: nakdong_track.csv ({len(rows):,} rows)")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(6, 5.4))
        by = {}
        for tm, pid, x, y in rows:
            by.setdefault(pid, []).append((x, y))
        for pid, tr in by.items():
            xs, ys = zip(*tr)
            ax.plot(xs, ys, lw=0.4, alpha=0.25, color="#2a78d6")
            ax.plot(xs[-1], ys[-1], ".", ms=2, color="#e24b4a")
        ax.plot(SEED_LON, SEED_LAT, "o", ms=7, color="#26215c", label="release")
        ax.set_xlim(LON_MIN, LON_MAX); ax.set_ylim(LAT_MIN, LAT_MAX)
        ax.set_xlabel("lon"); ax.set_ylabel("lat")
        ax.set_title("Nakdong estuary drift (lite, schematic forcing)")
        ax.legend(loc="upper right", fontsize=8)
        fig.tight_layout(); fig.savefig("lite_drift.png", dpi=120)
        print("  지도 저장: lite_drift.png")
    except Exception as e:
        print("  플롯 생략:", e)


if __name__ == "__main__":
    main()
