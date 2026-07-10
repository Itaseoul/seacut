# Firmware

ESP32 + A7670 (LTE Cat.1 bis) + L76K GNSS. Wake on a timer, get a GPS fix, POST one ping, deep sleep. The device sends one coordinate; the server assembles the track.

Reference firmware: `drifter_a7670_cat1/drifter_a7670_cat1.ino` (in the SEA:CUT source tree). License MIT.

## Toolchain

- Arduino IDE, ESP32 Arduino core 3.0.x, board "ESP32 Dev Module"
- Libraries: **lewisxhe/TinyGSM-fork** (required; stock TinyGSM lacks the A7670 macro), TinyGPSPlus, ArduinoHttpClient

## Configure

- `APN` for your SIM (Soracom `soracom.io` user/pass `sora`; 1NCE `iot.1nce.net`; or your local carrier)
- `SERVER_HOST` / `SERVER_PATH` for your ingest server (self-host `ingest_server.py`, or the shared endpoint)
- `SLEEP_MINUTES` interval. Default 30 gives multi-week battery life. Shorter intervals need a measured positive energy balance before deploying a fleet.

## Gotchas

- GPS is the separate L76K chip on its own UART (NMEA via TinyGPSPlus), not the modem's AT GNSS.
- Test with the 18650 installed. USB-only power browns out on the transmit peak (~2 A) and looks like a modem fault.
- Start with plain HTTP, promote to HTTPS after the pipeline works end to end.

## Deprecated

`drifter_esp32_ltem/` is an earlier SIM7080 (LTE-M/NB-IoT) skeleton kept only for reference of the TinyGPSPlus GPS logic. SIM7080G has no verified attach on Korean commercial networks; use `drifter_a7670_cat1/`.
