"""
SEA:CUT — ita.city 수신 파이프라인 (3단계, stdlib 전용)
=======================================================
맨 처음 다이어그램의 구현:

  드리프터(LTE-M) ──POST /api/ping──> 이 서버 ──> 지도 궤적 레이어
                                            └──> 예측(OpenDrift) 궤적과 오버레이

엔드포인트
---------
  POST /api/ping             LTE-M 단말이 좌표 1점 전송
                             body: {"device_id","lat","lon","ts"(선택)}
  GET  /api/live.geojson     실측 드리프터 궤적(단말별 LineString)
  GET  /api/predicted.geojson 예측 결과: 최종위치 점군 + 앙상블 평균 경로
  GET  /                     Leaflet 지도(실측 + 예측 오버레이, 자동 새로고침)

데이터
------
  data/pings.ndjson          실측 ping 누적(한 줄 = 한 관측)
  nakdong_track.csv          예측 궤적(OpenDrift 또는 lite 데모 산출)

실행:  python ingest_server.py           # http://127.0.0.1:8770
의존성 없음(표준 라이브러리만) — 실제 배포 시 Next.js /api 라우트로 이식.
"""
import csv
import json
import os
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE = os.path.dirname(os.path.abspath(__file__))
PINGS = os.path.join(BASE, "data", "pings.ndjson")
PRED_CSV = os.path.join(BASE, "nakdong_track.csv")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get("SEACUT_PORT", 8770))
os.makedirs(os.path.dirname(PINGS), exist_ok=True)


def _read_pings():
    if not os.path.exists(PINGS):
        return []
    out = []
    with open(PINGS, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return out


def live_geojson():
    """단말별로 시간순 LineString + 마지막 위치 Point."""
    by_dev = {}
    for p in _read_pings():
        by_dev.setdefault(p["device_id"], []).append(p)
    feats = []
    for dev, pts in by_dev.items():
        pts.sort(key=lambda r: r.get("ts", ""))
        coords = [[float(p["lon"]), float(p["lat"])] for p in pts]
        if len(coords) >= 2:
            feats.append({"type": "Feature", "properties": {"device_id": dev, "kind": "live_track"},
                          "geometry": {"type": "LineString", "coordinates": coords}})
        if coords:
            feats.append({"type": "Feature",
                          "properties": {"device_id": dev, "kind": "live_now", "ts": pts[-1].get("ts")},
                          "geometry": {"type": "Point", "coordinates": coords[-1]}})
    return {"type": "FeatureCollection", "features": feats}


def predicted_geojson():
    """예측 CSV → 최종위치 점군 + 시간별 앙상블 평균 경로."""
    if not os.path.exists(PRED_CSV):
        return {"type": "FeatureCollection", "features": [],
                "properties": {"note": "nakdong_track.csv 없음 — 먼저 표류 데모 실행"}}
    last = {}          # pid -> (time, lon, lat)
    by_time = {}       # time -> [lon_sum, lat_sum, n]
    with open(PRED_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pid = row["particle_id"]; t = row["time"]
            lon = float(row["lon"]); lat = float(row["lat"])
            last[pid] = (t, lon, lat)
            a = by_time.setdefault(t, [0.0, 0.0, 0])
            a[0] += lon; a[1] += lat; a[2] += 1
    endpoints = [{"type": "Feature", "properties": {"kind": "pred_endpoint", "particle_id": pid},
                  "geometry": {"type": "Point", "coordinates": [round(lon, 6), round(lat, 6)]}}
                 for pid, (t, lon, lat) in last.items()]
    mean = [[round(s[0] / s[2], 6), round(s[1] / s[2], 6)] for t, s in sorted(by_time.items())]
    feats = endpoints + [{"type": "Feature", "properties": {"kind": "pred_mean_path"},
                          "geometry": {"type": "LineString", "coordinates": mean}}]
    return {"type": "FeatureCollection", "features": feats,
            "properties": {"particles": len(last), "steps": len(mean)}}


class H(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass

    def do_POST(self):
        if self.path.rstrip("/") != "/api/ping":
            return self._send(404, json.dumps({"error": "not found"}))
        n = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
            rec = {"device_id": str(body["device_id"]),
                   "lat": float(body["lat"]), "lon": float(body["lon"]),
                   "ts": body.get("ts") or datetime.now(timezone.utc).isoformat()}
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            return self._send(400, json.dumps({"error": f"bad ping: {e}"}))
        with open(PINGS, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        self._send(200, json.dumps({"ok": True, "stored": rec}))

    def do_GET(self):
        p = self.path.split("?")[0].rstrip("/")
        if p in ("", "/"):
            return self._send(200, MAP_HTML, "text/html; charset=utf-8")
        if p == "/api/live.geojson":
            return self._send(200, json.dumps(live_geojson()))
        if p == "/api/predicted.geojson":
            return self._send(200, json.dumps(predicted_geojson()))
        self._send(404, json.dumps({"error": "not found"}))


MAP_HTML = """<!doctype html><html><head><meta charset="utf-8">
<title>SEA:CUT — 낙동강 하구 드리프터</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>html,body,#map{height:100%;margin:0}#hud{position:absolute;z-index:1000;top:10px;left:10px;
background:#fff;padding:8px 12px;border-radius:8px;font:13px sans-serif;box-shadow:0 1px 6px rgba(0,0,0,.2)}</style>
</head><body><div id="map"></div>
<div id="hud">SEA:CUT 낙동강 하구<br><span id="s">불러오는 중…</span></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const map=L.map('map').setView([35.09,128.95],12);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'© OpenStreetMap'}).addTo(map);
let predL,liveL;
async function refresh(){
  const [pred,live]=await Promise.all([
    fetch('/api/predicted.geojson').then(r=>r.json()),
    fetch('/api/live.geojson').then(r=>r.json())]);
  if(predL)map.removeLayer(predL); if(liveL)map.removeLayer(liveL);
  predL=L.geoJSON(pred,{pointToLayer:(f,ll)=>L.circleMarker(ll,{radius:3,color:'#2a78d6',weight:0,fillOpacity:.5}),
    style:f=>f.properties.kind==='pred_mean_path'?{color:'#d85a30',weight:3}:{}}).addTo(map);
  liveL=L.geoJSON(live,{pointToLayer:(f,ll)=>L.circleMarker(ll,{radius:7,color:'#fff',weight:2,fillColor:'#0f6e56',fillOpacity:1}),
    style:f=>f.properties.kind==='live_track'?{color:'#0f6e56',weight:4}:{}}).addTo(map);
  document.getElementById('s').textContent=
    `예측 입자 ${pred.properties?.particles||0} · 실측 ping ${live.features.filter(f=>f.geometry.type==='Point').length}대`;
}
refresh(); setInterval(refresh,4000);
</script></body></html>"""


if __name__ == "__main__":
    print(f"SEA:CUT ingest server → http://127.0.0.1:{PORT}")
    print(f"  POST /api/ping  ·  GET /api/live.geojson  ·  GET /api/predicted.geojson")
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
