"""
SEA:CUT — 낙동강 하구 부유쓰레기 표류 예측 최소 실행 데모
==========================================================
OpenDrift(입자추적) + 국립해양조사원(KHOA) 격자 해양정보 forcing.

목적
----
낙동강 하구에 입자(부유쓰레기 대리물)를 뿌려 24~48시간 표류 경로를
시뮬레이션하고, 드리프터 실측 궤적과 겹쳐 검증할 수 있는 최소 골격.

두 가지 모드
-----------
  A. STANDALONE  : 외부 API 없이 도식 조류·바람장으로 즉시 실행(설치 확인용).
  B. KHOA_FORCING: 국립해양조사원 격자별 해양정보 API로 실제 유속장을 받아 구동.
                   (data.go.kr 서비스키 필요 — 무료 신청)

설치
----
  pip install opendrift        # 핵심 (numpy/scipy/xarray 등 동반 설치)
  pip install requests
  # OpenDrift는 conda 설치도 지원: conda install -c opendrift opendrift

실행
----
  python opendrift_nakdong_demo.py                 # A 모드(도식)
  KHOA_KEY=발급키 python opendrift_nakdong_demo.py  # B 모드(실데이터)

산출물
------
  nakdong_drift.nc   : 궤적 원자료(NetCDF) — 드리프터 실측과 비교/검증용
  nakdong_drift.png  : 표류 경로 지도
  nakdong_track.csv  : 입자별 (time, lon, lat) — ita.city 지도 레이어 입력

주의
----
  * KHOA 격자 API는 특정 시각·격자의 유속(u,v)을 점 단위로 제공합니다.
    OpenDrift에 먹이려면 시공간 격자(reader)로 재구성해야 하며, 아래
    build_khoa_reader()가 그 최소 변환을 보여줍니다(관측 가용 범위에 맞게
    격자 해상도·시간축을 조정하세요).
  * 소하천 물길(학장천 내부)은 이 해상도로는 못 풉니다 — 하구~외해 구간용.
"""

import os
import sys
from datetime import datetime, timedelta

import numpy as np

# --- 낙동강 하구 관심영역(ROI) -------------------------------------------
LON_MIN, LON_MAX = 128.80, 129.06
LAT_MIN, LAT_MAX = 34.99, 35.22

# 투하 지점: 하구둑 하류(을숙도 상단 채널) — 위젯의 release 지점과 동일
SEED_LON, SEED_LAT = 128.945, 35.16
SEED_RADIUS_M = 1500          # 투하 반경(m)
SEED_NUMBER = 500             # 입자 수
RUN_HOURS = 36                # 예측 시간(h)
TIME_STEP_MIN = 15            # 적분 스텝(min)

WINDAGE = 0.01                # windage 계수(1% = 페트병류). 쓰레기 유형별 튜닝.


# =========================================================================
# A 모드: 도식 forcing (외부 API 불필요, 설치·파이프라인 확인용)
# =========================================================================
def run_standalone():
    from opendrift.models.oceandrift import OceanDrift
    from opendrift.readers import reader_constant

    o = OceanDrift(loglevel=20)

    # 하구 평균 잔차류(외해 방향, 남향) + 약한 동서 성분 — 도식값
    r = reader_constant.Reader({
        'x_sea_water_velocity': -0.02,   # east(m/s)
        'y_sea_water_velocity': -0.18,   # north(m/s), 음수=남향(외해행)
        'x_wind': 3.0, 'y_wind': -3.0,   # 북서풍 도식값
    })
    o.add_reader(r)
    o.set_config('environment:constant:horizontal_diffusivity', 12)   # 난류 확산(m^2/s)
    o.set_config('drift:advection_scheme', 'runge-kutta4')
    o.set_config('general:coastline_action', 'stranding')  # 해안 좌초 처리

    _seed_and_run(o, start_time=datetime(2026, 7, 2, 6, 0, 0))
    return o


# =========================================================================
# B 모드: 해양수산부 격자 forcing(해수유동+해상풍) → OpenDrift reader
# =========================================================================
# -------------------------------------------------------------------------
# 해양수산부 격자 서비스 (data.go.kr org 1192000) — 기술문서 기반 확정치.
#   계정 승인 2026-07-03 ~ 2028-07-03. 기존 KMA_SERVICE_KEY(=MOF_KEY)로 호출.
#   요청: serviceKey · numOfRows · pageNo · analsYmd(분석일자) · analsHhs(분석시간) · gridCd(옵션)
#   응답: XML <item> 반복. 파랑은 lo(경도)/la(위도) 포함 확인 → 격자 디코딩 불필요.
#   ★해수유동 값 태그(유속/유향)는 활성화 후 첫 호출로 확정(파서가 미매칭 시 실제 태그를 출력).
# -------------------------------------------------------------------------
MOF = {
    # 해수유동 3분 → 입자 이송 (필수). 실호출로 응답 스키마 확정(2026-07-03).
    #   요청 샘플: analsYmd=20201231 analsHhs=03 gridCd=GR3_G1E23_P  (★샘플 날짜가 2020)
    #   응답 item: analsHhs analsYmd creatDt gridCd la lo ocdrct ocspd
    'currents': {
        'url': 'http://apis.data.go.kr/1192000/apVhdService_ContOc3/getOpnContOc3',
        'item_tag': 'item',
        'lon': ('lo',), 'lat': ('la',),        # ✅ 응답에 경위도 포함 → 격자 디코딩 불필요
        'a': ('ocspd',), 'b': ('ocdrct',),     # ✅ 유속(m/s) · 유향(deg, 흐르는 방향=toward)
        'is_vector': True, 'dir_from': False,   # 유향=toward → 그대로 u,v
    },
    # 해상풍 3분 → windage. 값 태그 확인(wnspd/wndrct). 풍향=from → +180.
    'wind': {
        'url': 'http://apis.data.go.kr/1192000/apVhdService_Tgcsz3/getOpnTgcsz3',
        'item_tag': 'item',
        'lon': ('lo', 'lon'), 'lat': ('la', 'lat'),
        'a': ('wnspd',), 'b': ('wndrct',),
        'is_vector': True, 'dir_from': True,    # 풍향=from → +180 후 u,v
    },
}


def _dir_to_uv(speed, deg):
    """유속·유향(또는 풍속·풍향, deg=흘러가는/불어가는 방향) → (u_east, v_north)."""
    rad = np.radians(deg)
    return speed * np.sin(rad), speed * np.cos(rad)


def fetch_mof_grid(cfg, service_key, when, gridcd=None):
    """해양수산부 1192000 격자 서비스(XML) 조회 → (lon[], lat[], a[], b[]).

    a,b=(u,v). is_vector면 (유속,유향)→u,v. 응답 lo/la로 ROI(낙동강 하구) 필터.
    필드 미매칭 시 첫 <item>의 실제 태그를 출력해 스키마를 자기문서화한다.
    """
    import requests
    import xml.etree.ElementTree as ET

    params = {
        'serviceKey': service_key,      # Decoding 키(requests가 인코딩)
        'numOfRows': 99999, 'pageNo': 1, 'type': 'xml',
        'analsYmd': when.strftime('%Y%m%d'),
        'analsHhs': when.strftime('%H'),
    }
    if gridcd:
        params['gridCd'] = gridcd
    resp = requests.get(cfg['url'], params=params, timeout=60)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)

    items = list(root.iter(cfg['item_tag']))
    if not items:
        msg = root.findtext('.//resultMsg') or root.findtext('.//returnAuthMsg') or resp.text[:200]
        raise RuntimeError(f"레코드 0건 — 활성화/파라미터 확인: {msg}")

    def g(it, tags):
        for t in (tags if isinstance(tags, tuple) else (tags,)):
            e = it.find(t)
            if e is not None and e.text not in (None, ''):
                return float(e.text)
        return None

    lon, lat, a, b = [], [], [], []
    for it in items:
        x, y = g(it, cfg['lon']), g(it, cfg['lat'])
        va, vb = g(it, cfg['a']), g(it, cfg['b'])
        if None in (x, y, va, vb):
            continue
        if not (LON_MIN <= x <= LON_MAX and LAT_MIN <= y <= LAT_MAX):
            continue          # 낙동강 하구 ROI 밖은 버림
        lon.append(x); lat.append(y); a.append(va); b.append(vb)

    if len(lon) == 0:
        sample = [c.tag for c in items[0]]
        raise RuntimeError(
            "ROI 내 매칭 0건. 첫 item의 실제 태그로 MOF 설정 확정 필요:\n  " + ", ".join(sample))
    lon, lat, a, b = map(np.array, (lon, lat, a, b))
    if cfg.get('is_vector'):
        deg = b + 180.0 if cfg.get('dir_from') else b   # 풍향(from)만 반전, 유향(toward)은 그대로
        a, b = _dir_to_uv(a, deg)
    return lon, lat, a, b


def build_mof_reader(service_key, when):
    """해수유동(+해상풍)을 같은 정규격자로 보간해 결합 reader 생성.

    해상풍 취득 실패 시 해류만으로도 동작(경고 후 진행).
    """
    import xarray as xr
    from scipy.interpolate import griddata
    from opendrift.readers.reader_netCDF_CF_generic import Reader as NCReader

    nx, ny = 60, 55
    glon = np.linspace(LON_MIN, LON_MAX, nx)
    glat = np.linspace(LAT_MIN, LAT_MAX, ny)
    GX, GY = np.meshgrid(glon, glat)
    rg = lambda p, q, val: griddata((p, q), val, (GX, GY), method='linear', fill_value=0.0)

    clon, clat, u, v = fetch_mof_grid(MOF['currents'], service_key, when)
    data_vars = {
        'x_sea_water_velocity': (('time', 'lat', 'lon'), rg(clon, clat, u)[None]),
        'y_sea_water_velocity': (('time', 'lat', 'lon'), rg(clon, clat, v)[None]),
    }
    try:
        wlon, wlat, wu, wv = fetch_mof_grid(MOF['wind'], service_key, when)
        data_vars['x_wind'] = (('time', 'lat', 'lon'), rg(wlon, wlat, wu)[None])
        data_vars['y_wind'] = (('time', 'lat', 'lon'), rg(wlon, wlat, wv)[None])
    except Exception as e:
        print('해상풍 생략(해류만 사용):', e)

    ds = xr.Dataset(data_vars, coords={'time': [np.datetime64(when)], 'lat': glat, 'lon': glon})
    for name in data_vars:
        ds[name].attrs['standard_name'] = name
    ds['lon'].attrs.update(standard_name='longitude', units='degrees_east')
    ds['lat'].attrs.update(standard_name='latitude', units='degrees_north')

    tmp = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_mof_grid.nc')
    ds.to_netcdf(tmp)
    return NCReader(tmp)


def run_khoa(service_key):
    from opendrift.models.oceandrift import OceanDrift

    start = datetime(2026, 7, 2, 6, 0, 0)
    o = OceanDrift(loglevel=20)
    o.add_reader(build_mof_reader(service_key, start))
    o.set_config('environment:constant:horizontal_diffusivity', 10)
    o.set_config('drift:advection_scheme', 'runge-kutta4')
    o.set_config('general:coastline_action', 'stranding')
    _seed_and_run(o, start_time=start)
    return o


# =========================================================================
# 공통: 투하 → 적분 → 산출
# =========================================================================
def _seed_and_run(o, start_time):
    o.seed_elements(
        lon=SEED_LON, lat=SEED_LAT,
        radius=SEED_RADIUS_M, number=SEED_NUMBER,
        time=start_time,
        wind_drift_factor=WINDAGE,   # windage matching (seed 속성)
    )
    o.run(
        duration=timedelta(hours=RUN_HOURS),
        time_step=timedelta(minutes=TIME_STEP_MIN),
        time_step_output=timedelta(minutes=30),
        outfile='nakdong_drift.nc',
    )

    print(o)
    _export_csv(o, 'nakdong_track.csv')
    try:
        o.plot(fast=True, filename='nakdong_drift.png',
               corners=[LON_MIN, LON_MAX, LAT_MIN, LAT_MAX])
        print('지도 저장: nakdong_drift.png')
    except Exception as e:
        print('플롯 생략(백엔드 없음):', e)


def _export_csv(o, path):
    """입자별 (time, id, lon, lat) → ita.city 지도 레이어용 CSV.

    OpenDrift 1.10+ 는 결과를 o.result(xarray Dataset, dims: trajectory×time)로
    노출한다. 구버전 o.history(masked array)로도 폴백.
    """
    import csv
    try:
        ds = o.result
        lon = np.asarray(ds['lon'].values); lat = np.asarray(ds['lat'].values)
        times = [str(t)[:19] for t in np.asarray(ds['time'].values)]
        masked = np.isnan(lon)
    except (AttributeError, KeyError):
        lon = o.history['lon']; lat = o.history['lat']
        times = [t.isoformat() for t in o.get_time_array()[0]]
        masked = np.ma.getmaskarray(lon)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(['time', 'particle_id', 'lon', 'lat'])
        for pid in range(lon.shape[0]):
            for t in range(lon.shape[1]):
                if masked[pid, t]:
                    continue
                w.writerow([times[t], pid, f'{lon[pid, t]:.6f}', f'{lat[pid, t]:.6f}'])
    print('궤적 CSV 저장:', path)


if __name__ == '__main__':
    key = os.environ.get('MOF_KEY') or os.environ.get('KHOA_KEY')
    if key:
        print('== B 모드: 해양수산부 실데이터 forcing (해수유동+해상풍) ==')
        run_khoa(key)
    else:
        print('== A 모드: 도식 forcing (MOF_KEY 미설정) ==')
        print('   실데이터로 돌리려면: MOF_KEY=data.go.kr키 python', os.path.basename(__file__))
        run_standalone()
