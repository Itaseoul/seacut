# Firmware

ESP32 + A7670 (LTE Cat.1 bis) + L76K GNSS. **FF-ID schema v1.1** ([data/schema.md](../data/schema.md)).

Wake on a timer → **GPS fix first** (so an observation is kept even with no coverage) → append to an RTC store-and-forward buffer with a monotonic `seq` → modem on → network → POST buffered records oldest-first → deep sleep. The device sends points; the server assembles the track and never trusts arrival order (it orders by `ts_fix`/`seq`).

Reference firmware: [`drifter_a7670_cat1/drifter_a7670_cat1.ino`](drifter_a7670_cat1/drifter_a7670_cat1.ino) (MIT).

## v1.1 payload (what each ping carries)

```json
{"device_id":"ff-kr-bs-u0001","site_id":"nakdong-hakjang","seq":1487,
 "lat":35.105600,"lon":128.943100,"batt":4.02,
 "sample_interval_s":1800,"fix_quality":1.4,"gnss_source":"l76k",
 "ts_fix":"2026-07-10T09:00:00Z","ts":"2026-07-10T09:00:00Z"}
```

- `seq` — monotonic per-device counter. Survives deep sleep (RTC memory) **and** power loss (NVS). The server dedups and detects gaps by `seq`.
- `ts_fix` — the GPS UTC time of the fix (the observation time). Legacy `ts` is sent with the same value for older ingest servers (schema 1.0→1.1 mapping).
- `sample_interval_s` — declared nominal cadence (required by the schema for mixed-cadence weighting).
- `fix_quality` — HDOP from the L76K (omitted when invalid); `gnss_source:"l76k"`.
- **Store-and-forward**: up to 16 records buffer in RTC memory across sleep cycles; a cellular dead zone does not lose observations. Power loss drops the buffer (documented tradeoff) but never reuses a `seq`.

## Toolchain

- Arduino IDE, ESP32 Arduino core 3.0.x, board "ESP32 Dev Module"
- Libraries: **lewisxhe/TinyGSM-fork** (required; stock TinyGSM lacks the A7670 macro — uninstall stock), TinyGPSPlus, ArduinoHttpClient. `Preferences` ships with the core.

## Configure

- `DEVICE_ID` — pair it with the unit metadata directory `unit_id` (schema §3).
- `APN` for your SIM (Soracom `soracom.io` user/pass `sora`; 1NCE `iot.1nce.net`; KT MVNO `lte.ktfwing.com`; SKT MVNO `lte.sktelecom.com`). Global IoT SIMs roam on KT/SKT only — no LG U+.
- `SERVER_HOST` / `SERVER_PATH` — bench with the bundled `ingest_server.py` (`BENCH_HTTP 1`), then promote to HTTPS (`BENCH_HTTP 0`).
- `SLEEP_MINUTES` — see [hardware/ELECTRONICS_POWER.md](../hardware/ELECTRONICS_POWER.md) for the honest endurance table (all figures estimates pending bench measurement).

## Gotchas

- GPS is the separate L76K chip on its own UART (NMEA via TinyGPSPlus), not the modem's AT GNSS.
- Test with the 18650 installed. USB-only power browns out on the ~2 A transmit peak and looks like a modem fault.
- The v1.1 flow order (GPS → modem) differs from the original bench-validated v1.0 order (modem → GPS). Primitives are unchanged, but **re-run the bench sequence before deploying a fleet** (honesty: no improvement claims before measurement).
- Start with plain HTTP, promote to HTTPS after the pipeline works end to end.

## Bench re-verification checklist (v1.1, after the adversarial-review fixes)

1. **GPS power gate**: with `BENCH_HTTP 1`, confirm NMEA bytes arrive **before** the modem PWRKEY runs (serial shows a fix, or on failure `NMEA chars=` > 0). If `chars=0`, the L76K rail depends on modem power-on → move `modemPowerOn()` before `getFix()` but keep network registration after the fix (modem *power* and *network attach* stay separated so store-and-forward intent holds).
2. **Full cycle**: fix → buffer → POST 200 → deep sleep → wake, `seq` +1 each wake. Then kill coverage (unscrew LTE antenna) for 2–3 cycles and confirm the buffer flushes in one batch on recovery.
3. **HTTPS build**: `BENCH_HTTP 0` compiles under `TINY_GSM_MODEM_A76XXSSL` and POSTs over 443 (the modem class changes — re-verify attach; check the SSL client's CA-validation default).
4. **Sleep current**: measure before/after the GPIO-hold fix and update [hardware/ELECTRONICS_POWER.md](../hardware/ELECTRONICS_POWER.md) estimates with measured values.
