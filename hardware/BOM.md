# Bill of Materials (BOM)

Parts by function and generic spec first, then a globally shipping reference part, then local substitution. Prices are rough retail USD and vary by country. Full context and regional tables: [../docs/OPEN_HARDWARE_BOM_global.md](../docs/OPEN_HARDWARE_BOM_global.md).

Reference board is the LILYGO T-A7670G R2 with onboard L76K GNSS. It is cellular (LTE Cat.1 bis) plus a separate GPS chip. It is not satellite. Do not substitute the SIM7080G (LTE-M/NB-IoT), which has no verified attach on Korean commercial networks.

## Tier 0 — Phone-in-a-Bottle (USD 5–35)

| Function | Generic spec | Reference | Local substitution | ~USD |
|---|---|---|---|---|
| Compute + GPS + modem | old Android phone with GPS and 3G/4G | reused phone | any working phone, ideally reused e-waste | 0–30 |
| Logger / uplink | app that POSTs GPS to a URL | GPSLogger (open source) | any GPS logger with custom URL POST | 0 |
| SIM | prepaid data SIM | local data SIM | global IoT SIM (1NCE / Soracom) | 5–15 |
| Housing | RF-transparent float, sealed | upcycled PET bottle + dry bag | any clear plastic bottle | 0–5 |
| Ballast + visibility + recovery | bottom weight, bright tape, contact label, loop | sinker + tape + QR | any dense non-toxic weight | 2–5 |

## Tier 1 — Cellular Bottle (default, USD 50–70)

| Function | Generic spec | Reference | Local substitution | ~USD |
|---|---|---|---|---|
| Compute + modem + GPS | ESP32 + LTE Cat.1/Cat.1 bis + onboard GNSS | LILYGO T-A7670G R2 "With GPS (L76K)" | ESP32 + A76xx board with real GNSS; pick A7670 band variant for your region | 27–33 |
| Battery | protected 18650, verify holder length | quality protected 18650 | any protected 18650 | 5–8 |
| SIM | global IoT roaming SIM or local data SIM | 1NCE 10-yr prepaid / Soracom | local data SIM | 5–14 |
| Antennas | LTE + GNSS, kept above water | board-included uFL antennas | extend outside if sealing | 0–8 |
| Housing | RF-transparent float, sealed, antenna above waterline | upcycled PET bottle | any clear plastic bottle | 0–5 |
| Ballast (self-righting) | low weight so antenna rights up | sinker at belly + printed keel | any dense non-toxic weight | 2–5 |
| Sealant | marine/silicone sealant + grommet | marine silicone | any waterproof sealant | 3–8 |
| Visibility + recovery | bright tape, waterproof QR/contact label, loop | tape + QR + paracord | local equivalents | 2–5 |
| Printed inserts | bracket + keel + loop | `cad/*.scad` | print locally | 1–3 |

## Tier 2 — Reusable Robust (upgrade, USD 90–130)

Adds on top of Tier 1: bolt-sealed IP-rated opaque enclosure with gasket, IP-rated cable glands, external waterproof antennas via bulkhead, temperature-protected charging (NTC/JEITA) for cold water, bulk capacitor plus supercap for the modem's ~2 A transmit peak, printed internal frame, cell-failure containment. Use only for repeated, cold, or harsh campaigns. Full specified robust build and cost breakdown: the Korea deep-audit doc in the parent repo (`50기_방류_BOM_최종검수.md`).

## Notes (all cellular tiers)

- The board's GNSS is a separate L76K chip read over its own UART (NMEA via TinyGPSPlus), not the modem's AT GNSS.
- Firmware library must be lewisxhe/TinyGSM-fork; stock TinyGSM lacks the A7670 macro.
- Always test with the battery installed. USB-only power browns out on the transmit peak and looks like a modem fault.
- Housing must be non-metallic and the antenna must stay above the waterline, or GPS and cellular both die.
- Power budget (ping interval vs 18650 endurance), mission device-classes (river / estuary / open-ocean), and the solar option: see [ELECTRONICS_POWER.md](ELECTRONICS_POWER.md). Battery-only + recover-to-recharge is the default; solar is a Tier-3 option, not the baseline.
