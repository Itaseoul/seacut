# Data schema (CC BY 4.0) — Friendly Floatee standard

This is the standard, citable format for river-litter drift observations. Data is open (CC BY): the hub's power is the citation standard, provenance, real-time map, and community, not gating the data. Anyone may download, copy, and build on it; please cite it (below).

Schema version: 1.0.

## 1. Ping (device to server)

The device sends the minimal payload. The server assigns the citable id and provenance and assembles the track.

`POST /api/observations/drift/ping` (or local `POST /api/ping` for the bundled `ingest_server.py`)

```json
{"device_id":"river-001","site_id":"nakdong-gamjeon","lat":35.10,"lon":128.97,"batt":4.02,"ts":"2026-07-10T09:00:00Z"}
```

| field | type | required | note |
|---|---|---|---|
| device_id | string | yes | device identifier (anonymized in public snapshot) |
| site_id | string | no | site tag, e.g. `nakdong-gamjeon` |
| lat | number | yes | latitude |
| lon | number | yes | longitude |
| batt | number | no | battery volts |
| ts | string | no | ISO8601 UTC; server fills receive time if absent |

## 2. Observation record (server-assigned, citable)

The server wraps each accepted ping into a citable observation. This is what the public snapshot and downloads expose.

```json
{
  "obs_id": "FF-KR-BS-20260910-001524",
  "schema_version": "1.0",
  "ts": "2026-09-10T09:28:04Z",
  "device_id": "d1yo2o4q",
  "site_id": "nakdong-gamjeon",
  "lat": 35.1056,
  "lon": 128.9431,
  "batt": 4.02,
  "provenance": {
    "source": "device",
    "verification": "raw",
    "operator": "gaa-kr-busan"
  },
  "calibration_ref": "ff-drifter-v1",
  "license": "CC BY 4.0"
}
```

| field | meaning |
|---|---|
| obs_id | globally unique, citable id. Format `FF-<country>-<region>-<YYYYMMDD>-<seq>`. Cite this. |
| schema_version | schema version for forward compatibility |
| device_id | anonymized (hashed) in the public snapshot; no personal data |
| provenance.source | `device` / `phone` / `manual` |
| provenance.verification | `raw` / `auto_checked` (server sanity checks) / `steward_verified` (a named steward or authority confirmed) |
| provenance.operator | organization or team id (not a person) |
| calibration_ref | which drifter calibration profile applies (see 4) |

Verification is honest: mark `steward_verified` only when a real steward or authority actually confirmed it. Do not invent verification marks.

## 3. Track and public snapshot

`GET /api/observations/drift/ping` returns `live.geojson`: per device, a time-ordered LineString (the track) and a Point (last position, batt). Assembled tracks carry a `track_id` and `is_estimate: true` (a single track is a sample).

## 4. Calibration commons

The transferable science asset. Each drifter shape has windage/drag coefficients that are a property of the object, not the river, so they carry across rivers.

```json
{"calibration_id":"ff-drifter-v1","windage":0.003,"drag_area_ratio":25.6,"validated_sites":["nakdong-gamjeon"],"notes":"1L PET bottle, horizontal, self-righting"}
```

New sites reuse this profile and need fewer drifters to calibrate locally. Contribute your site's validation back to grow the commons.

## 5. Self-host or share

Run your own server (`ingest_server.py`) or POST to the shared community map. Both keep the same schema so data stays interoperable.

## 6. Citation

Cite observations by `obs_id`, e.g.:

> SEA:CUT / Friendly Floatee Open Data (2026), observation FF-KR-BS-20260910-001524, CC BY 4.0.

Standard, provenance, real-time, and citation make this a hub without closing anything.
