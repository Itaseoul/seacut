# Data schema (CC BY 4.0)

Two endpoints. Devices send single pings; the server assembles tracks and bakes a public GeoJSON snapshot.

## Ping (device to server)

`POST /api/observations/drift/ping` (or local `POST /api/ping` for the bundled `ingest_server.py`)

```json
{"device_id":"river-001","site_id":"my-river","lat":35.10,"lon":128.97,"batt":4.02,"ts":"2026-07-10T09:00:00Z"}
```

| field | type | required | note |
|---|---|---|---|
| device_id | string | yes | device identifier |
| site_id | string | no | site tag for the track |
| lat | number | yes | latitude |
| lon | number | yes | longitude |
| batt | number | no | battery volts, surfaced on the live snapshot |
| ts | string | no | ISO8601 UTC; server fills receive time if absent |

Success `200 {"ok":true,...}`. Missing lat/lon/device_id returns `400`.

## Public snapshot (server to map)

`GET /api/observations/drift/ping` returns `live.geojson`: per device_id, a time-ordered LineString (the track) plus a Point (last position, with batt). device_id is anonymized in the public snapshot.

## Self-host or share

Run your own server (`ingest_server.py`, single file, no dependencies) or POST to the shared community map. Data is CC BY: attribute SEA:CUT / Friendly Floatee and the contributor.
