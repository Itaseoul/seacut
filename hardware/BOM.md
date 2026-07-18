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

## Tier 1.5 — Solar-assisted (long-dwell / recovery-insurance, +USD 15–25 over Tier 1)

For missions where a unit **dwells in-coverage for weeks** (estuary retention — the Han-estuary study shows most litter lingers 1 month+), a battery-only unit dies before it can be recovered. Add **wrap-around thin-film solar** to extend reporting life so the unit stays trackable and recoverable. ★**Solar extends power, not coverage** — a unit that leaves cellular range goes silent regardless of charge (that is satellite / Class 3). Not for short recover-in-days missions (use Tier 1). Full spec, the self-righting-preserving design, and the extra bench gates (G5 solar harvest, T7 self-right with cells): [TIER1_5_SOLAR_DRIFTER.md](TIER1_5_SOLAR_DRIFTER.md).

| Function | Generic spec | Reference (orderable) | ~USD |
|---|---|---|---|
| Solar cells | flexible thin-film, 5–6 V, min-bend-radius ≤46 mm. ★**Non-metal RF-transparent substrate only** — a-Si (ETFE front) or Cd-free CIGS (polyimide); no stainless-backed CIGS / CdTe / perovskite (RF shield + toxicity) | PowerFilm-class flexible a-Si panel (ETFE front) | 8–15 |
| Charge control | ★**external low-Iq linear (default) to the BATTERY terminal**, zip-tied to the existing bracket; onboard-direct only a small-panel exception (buck-boost to 5.0–5.2 V); MPPT for clean/summer sites | CN3065 breakout module (linear) / CN3791 (MPPT) | 0–10 |
| Low-temp cutoff | ★**mandatory all modes, hardware latch** — <0 ℃ charge blocked (not firmware) | 10 kΩ B3435 NTC epoxy-bonded to the cell can | 0.5 |
| Isolation diode | reverse-block the panel | Schottky / ideal-diode module | 0.5 |
| Vent | pressure/heat equalise — **not** a printed boss | Gore-Tex ePTFE adhesive vent patch | 2–4 |
| Extra foam | buoyancy re-cut, ★**density-aware +6.7 cm³/10 g** (panel ρ≈1.64, NOT the ballast 11.7) | closed-cell EVA sheet | ~1 |
| Battery (optional 2nd) | ★**matched + isolation diode/balancing**, belly placement; else one larger protected cell | matched protected 18650 | 8–11 |

Everything else is identical to Tier 1. Keep the battery sized to survive the planned dwell on its own; solar is margin, not a design input, until bench G5 measures real harvest.

## Tier 2 — Reusable Robust (upgrade, USD 90–130)

Adds on top of Tier 1: bolt-sealed IP-rated opaque enclosure with gasket, IP-rated cable glands, external waterproof antennas via bulkhead, temperature-protected charging (NTC/JEITA) for cold water, bulk capacitor plus supercap for the modem's ~2 A transmit peak, printed internal frame, cell-failure containment. Use only for repeated, cold, or harsh campaigns. Full specified robust build and cost breakdown: the Korea deep-audit doc in the parent repo (`50기_방류_BOM_최종검수.md`).

## Notes (all cellular tiers)

- The board's GNSS is a separate L76K chip read over its own UART (NMEA via TinyGPSPlus), not the modem's AT GNSS.
- Firmware library must be lewisxhe/TinyGSM-fork; stock TinyGSM lacks the A7670 macro.
- Always test with the battery installed. USB-only power browns out on the transmit peak and looks like a modem fault.
- Housing must be non-metallic and the antenna must stay above the waterline, or GPS and cellular both die.
- Power budget (ping interval vs 18650 endurance), mission device-classes (river / estuary / open-ocean), and the solar option: see [ELECTRONICS_POWER.md](ELECTRONICS_POWER.md). Battery-only + recover-to-recharge is the default. Solar comes in two documented forms: a **fixed Tier-3** station and a **long-dwell drifter [Tier 1.5](TIER1_5_SOLAR_DRIFTER.md)** — neither is the short-mission baseline.
