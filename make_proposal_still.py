"""제안서(Word) 삽입용 정지 이미지 — 낙동강 하구 표류 예측 히어로컷.
감전천 합류부발 앙상블(평균경로·범위·도달분포) + 붐 후보 + 흐름.
라벨은 영문/기호로(한글 폰트 경고 회피). 제목·설명은 Word 본문에서 한글로."""
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPoly

LON0, LON1, LAT0, LAT1 = 128.82, 129.05, 35.00, 35.20
SEED_LON, SEED_LAT = 128.9706, 35.1326
N, RUN_H, DT_MIN, WINDAGE, Q, K = 320, 26, 15, 0.01, 0.4, 10.0
WIND_SPD, WIND_FROM = 5.0, 315.0
M_LAT = 111_000.0
M_LON = 111_000.0 * math.cos(math.radians(35))

# 개념 해안선(schematic) — 서/동 육지 폴리곤
WEST = [(128.82,35.20),(128.905,35.20),(128.895,35.15),(128.885,35.11),(128.865,35.075),(128.84,35.05),(128.82,35.04)]
EAST = [(128.99,35.20),(129.05,35.20),(129.05,35.00),(129.005,35.03),(128.995,35.06),(129.01,35.08),(128.995,35.11),(128.99,35.15)]
EULSUK = [(128.938,35.145),(128.953,35.145),(128.957,35.10),(128.949,35.075),(128.939,35.075),(128.933,35.10)]
BOOM = [(128.905,35.108),(128.986,35.104)]


def vel(t_h):
    # 제안서용 히어로컷: 조석 진동을 낮추고 외해행 잔차류를 키워 경로를 또렷하게.
    ph = 2*math.pi*t_h/12.42
    v = -(0.11+Q*0.18)+0.18*math.sin(ph)
    u = 0.06*math.sin(ph+1.0)
    to = math.radians(WIND_FROM+180)
    u += WINDAGE*WIND_SPD*math.sin(to); v += WINDAGE*WIND_SPD*math.cos(to)
    return u, v


def hull(pts):
    pts=sorted(set(map(tuple,pts)))
    if len(pts)<3: return pts
    cr=lambda o,a,b:(a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lo=[];up=[]
    for p in pts:
        while len(lo)>=2 and cr(lo[-2],lo[-1],p)<=0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up)>=2 and cr(up[-2],up[-1],p)<=0: up.pop()
        up.append(p)
    return lo[:-1]+up[:-1]


def main():
    rng=np.random.default_rng(7)
    r=350*np.sqrt(rng.random(N)); th=rng.random(N)*2*math.pi
    lon=SEED_LON+(r*np.cos(th))/M_LON; lat=SEED_LAT+(r*np.sin(th))/M_LAT
    dt_s=DT_MIN*60; steps=int(RUN_H*60/DT_MIN); sig=math.sqrt(2*K*dt_s)
    tracks=[[] for _ in range(N)]; mean=[]
    for s in range(steps+1):
        for i in range(N): tracks[i].append((lon[i],lat[i]))
        mean.append((lon.mean(),lat.mean()))
        u,v=vel(s*DT_MIN/60)
        lon=lon+(u*dt_s+rng.normal(0,sig,N))/M_LON
        lat=lat+(v*dt_s+rng.normal(0,sig,N))/M_LAT
    ends=[t[-1] for t in tracks]
    env=hull(ends+[t[len(t)//2] for t in tracks])

    fig,ax=plt.subplots(figsize=(7,6.2),dpi=150)
    ax.set_facecolor("#eaf4fb")
    for poly,fc in [(WEST,"#e7e5dc"),(EAST,"#e7e5dc"),(EULSUK,"#e7e5dc")]:
        ax.add_patch(MplPoly(poly,closed=True,facecolor=fc,edgecolor="#c3c2b7",lw=1,zorder=2))
    # forecast envelope
    if len(env)>2:
        ax.add_patch(MplPoly(env,closed=True,facecolor="#38bdf8",alpha=0.13,edgecolor="#0ea5e9",lw=1,zorder=3))
    # sample tracks
    for j in np.linspace(0,N-1,14).astype(int):
        xs,ys=zip(*tracks[j]); ax.plot(xs,ys,color="#2a78d6",lw=0.5,alpha=0.28,zorder=3)
    # endpoints
    ex,ey=zip(*ends); ax.scatter(ex,ey,s=5,c="#2563eb",alpha=0.55,edgecolors="none",zorder=4,label="24h reach (ensemble)")
    # mean path
    mx,my=zip(*mean); ax.plot(mx,my,color="#d97706",lw=2.6,zorder=5,label="mean forecast path")
    # boom candidate
    bx,by=zip(*BOOM); ax.plot(bx,by,color="#0f6e56",lw=3,ls=(0,(2,2)),zorder=5,label="boom candidate")
    # release
    ax.scatter([SEED_LON],[SEED_LAT],s=90,c="#4338ca",edgecolors="#fff",lw=1.5,zorder=6,label="release (Gamjeon confluence)")
    # flow arrow
    ax.annotate("",xy=(128.955,35.045),xytext=(128.96,35.115),
                arrowprops=dict(arrowstyle="-|>",color="#0284c7",lw=2,alpha=0.6),zorder=4)
    ax.text(128.968,35.08,"Nakdong → sea",color="#0369a1",fontsize=9,rotation=-78,zorder=6)
    ax.text(128.905,35.005,"South Sea",color="#1d4ed8",fontsize=9,fontweight="bold",zorder=6)
    ax.text(128.945,35.11,"Eulsukdo",color="#5f5e5a",fontsize=8,ha="center",zorder=6)

    ax.set_xlim(LON0,LON1); ax.set_ylim(LAT0,LAT1)
    ax.set_xlabel("longitude (°E)"); ax.set_ylabel("latitude (°N)")
    ax.set_title("Nakdong estuary floating-litter drift forecast",fontsize=12)
    ax.legend(loc="lower left",fontsize=7.5,framealpha=0.9)
    ax.grid(True,color="#ffffff",lw=0.6,alpha=0.7)
    fig.tight_layout()
    fig.savefig("proposal_drift.png",dpi=150)
    print("저장: proposal_drift.png")


if __name__=="__main__":
    main()
