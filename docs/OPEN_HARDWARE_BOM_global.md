# SEA:CUT Drifter — Open Hardware BOM & Build Guide (global)

An open-source, non-profit river-to-sea litter drifter. A low-cost GPS+cellular float that you release into a river, track from anywhere, and recover. It maps how floating trash travels from source to sea so communities know where to place booms and cleanups.

This is a movement, not a product. In the spirit of Precious Plastic, we publish the design so anyone, anywhere can build one from locally available parts, adapt it, and share the data. We do not ship certified finished units. You build, you own your deployment, you follow your local rules. What keeps that trustworthy is not the absence of caveats but a few strong, universal ones. They are below.

- Firmware: MIT. Docs and data schema: CC BY 4.0. Hardware design: CERN-OHL-S (strongly reciprocal; see LICENSE-hardware.md).
- Reference build: `firmware/drifter_a7670_cat1/`, ingest server `ingest_server.py`, assembly notes `docs/구매제작_HOWTOMAKE_최종.md`.
- Contribute: fork, build, add your river, send trajectories back to the shared map.

---

## 1. The SEA:CUT ethic (the four rules that travel with the design)

Precious Plastic did not spread by ignoring safety. It spread because it paired open designs with a handful of simple, non-negotiable rules (ventilate, never burn) and pushed everything else to the local operator. These are ours. They are values, not regulations, and they are what make the open-source spread credible instead of reckless.

1. Recover what you release. This is a marine-litter project. A device left in the water is the exact problem we fight. Design every unit for recovery (high visibility, contact label, a grab loop), track it, and go get it. If you cannot recover it, do not release it. Recovery is not a rule imposed on us, it is our identity.

2. Safe power, no toxics. Use a protected Li-ion cell. Do not charge below 0 C or let the enclosure cook above 45 C. Contain a single-cell failure. No burning, no toxic materials, non-metallic RF-transparent housing. Account for the device's own footprint.

3. Do no harm to the water or its users. Smooth shapes that will not entangle wildlife or snag nets and propellers. Avoid protected or sensitive areas and breeding seasons unless locally cleared. Tell nearby water users you are there.

4. Own your deployment, follow your local rules. Releasing into shared water and transmitting on cellular or radio is regulated differently in every country. We give you the design; the deployment is yours. Start tiny (a few units), learn, then scale. See Section 8 for a generic localize checklist, with Korea as one worked example.

---

## 2. How it works

Wake on a timer, get a GPS fix, POST one small JSON ping over the cellular network, sleep. The device sends a single coordinate; a server assembles the track. No user-built gateway or infrastructure is required, the mobile network is the infrastructure.

```
[drifter] --GPS fix--> --cellular POST--> [ingest server] --> [public map / open data]
   sleep <------------------------------------ 200 OK
```

Ping body (schema, CC BY):
```json
{"device_id":"river-001","site_id":"my-river","lat":35.10,"lon":128.97,"batt":4.02,"ts":"2026-07-10T09:00:00Z"}
```

You can run your own ingest server (`ingest_server.py`, single file, no dependencies) or POST to a shared community endpoint. Data belongs to the community under CC BY.

---

## 3. Choose your tier

Pick the lowest tier that answers your question. A river survey with a handful of floats does not need the robust tier. Start cheap, prove the pipeline, then scale.

| | Tier 0 — Phone-in-a-Bottle | Tier 1 — Cellular Bottle (default) | Tier 2 — Reusable Robust |
|---|---|---|---|
| Brain | Reused smartphone + GPSLogger app | ESP32 cellular board | ESP32 cellular board |
| Housing | Upcycled PET bottle + dry bag | Upcycled PET bottle | Bolt-sealed IP-rated case |
| Reuse | Recover and reuse the phone | Single to few releases | Many releases, serviceable |
| Approx cost | USD 5–35 (phone reused) | USD 50–70 | USD 90–130 |
| Best for | First pipeline test, near-zero budget, any country | The movement default, on-mission upcycled float | Long or repeated campaigns, colder water |
| Barrier | Lowest possible | Low | Medium (needs sealing skill) |

The default is Tier 1: a cellular board inside an upcycled bottle. It is the most diffusible, the cheapest that still runs unattended, and it is literally the litter it studies. Tier 2 (sealed reusable case) is an upgrade for repeated or harsh deployments, not the starting point.

---

## 4. BOM by tier

Specify parts by function and generic spec first, then a globally shipping reference part, then how to substitute locally. Prices are rough retail in USD and vary by country.

### Tier 0 — Phone-in-a-Bottle

| Function | Generic spec | Reference | Local substitution | ~USD |
|---|---|---|---|---|
| Compute + GPS + modem | Any old Android phone with GPS and 3G/4G | Reused Galaxy/any | Any working phone, ideally reused e-waste | 0–30 |
| Logger/uplink | App that POSTs GPS to a URL | GPSLogger (open source) | Any GPS-logging app with custom URL POST | 0 |
| SIM | Any prepaid data SIM | Local data SIM | Global IoT SIM (1NCE/Soracom) | 5–15 |
| Housing | RF-transparent float, sealed | Upcycled PET bottle + dry bag | Any clear plastic bottle, sealed jar | 0–5 |
| Ballast + visibility + recovery | Bottom weight, bright tape, contact label, grab loop | Fishing sinker + tape + QR | Any dense non-toxic weight | 2–5 |

Tier 0 proves the whole chain (device to server to map) for almost nothing, anywhere, using e-waste. Use it first.

### Tier 1 — Cellular Bottle (default)

| Function | Generic spec | Reference | Local substitution | ~USD |
|---|---|---|---|---|
| Compute + modem + GPS | ESP32 + LTE Cat-1/Cat-1bis + onboard GNSS | LILYGO T-A7670x R2 "With GPS (L76K)" | Any ESP32+A76xx board with real GNSS; pick the A7670 band variant for your region (Sec 5) | 27–33 |
| Battery | Protected 18650 Li-ion, verify holder length | Samsung/LG 18650 protected | Any quality protected 18650 | 5–8 |
| SIM | Global IoT roaming SIM, or local data SIM | 1NCE 10-yr prepaid / Soracom | Any local data SIM that works with a hand-built device | 5–14 |
| Antennas | LTE + GNSS, kept above water | uFL antennas included with board | Board-included; extend outside housing if sealing | 0–8 |
| Housing | RF-transparent float, sealed, antenna above waterline | Upcycled PET bottle | Any clear plastic bottle | 0–5 |
| Ballast (self-righting) | Low weight so antenna always rights up | Fishing sinker at belly | Any dense non-toxic weight, low and centered | 2–5 |
| Sealant | Marine/silicone sealant + grommet at pass-throughs | Marine silicone | Any waterproof sealant | 3–8 |
| Visibility + recovery | Bright tape, waterproof contact/QR label, short recovery loop | Orange tape + QR sticker + paracord | Local equivalents | 2–5 |

### Tier 2 — Reusable Robust (upgrade)

Adds, on top of Tier 1: bolt-sealed IP-rated opaque enclosure with gasket; IP-rated cable glands at pass-throughs; external waterproof antennas via bulkhead; temperature-protected charging (NTC/JEITA) for cold water; bulk capacitor plus supercap to survive the modem's ~2 A transmit peak; foam/printed internal frame; cell-failure containment. Choose this only for repeated or cold or harsh campaigns. See `docs/50기_방류_BOM_최종검수.md` for the fully specified robust build and its cost breakdown.

Notes that apply to all cellular tiers:
- The board's GNSS is a separate L76K chip read over its own UART (NMEA via TinyGPSPlus), not the modem's AT GNSS. Firmware library must be lewisxhe/TinyGSM-fork (stock TinyGSM lacks the A7670 macro).
- Always test with the battery installed. USB-only power browns out on the transmit peak and looks like a modem fault.
- Housing must be non-metallic and the antenna must stay above the waterline, or GPS and cellular both die.

---

## 5. Communications: pick your backhaul by region

Cellular is the simplest global option because the mobile network is already everywhere people are. Two things are regional: the LTE bands and the SIM.

Cellular board variant by region (A7670 family, pick for your bands):

| Variant | Typical LTE-FDD bands | Fits |
|---|---|---|
| A7670E | B1/B3/B5/B7/B8/B20 | Europe, Middle East, Africa, Korea, most of Asia, Australia |
| A7670G | global multiband (adds Americas bands, e.g. B2/B4/B12/B25/B66) | Americas and worldwide roaming |
| A7670SA | Latin America bands | South/Central America |

If unsure, the G (global) variant maximizes band coverage. Match the variant to your carrier's bands; do not assume one variant is region-locked without checking the band list.

SIM options, easiest first:
- Global IoT SIM (1NCE, Soracom): one SIM works across 100+ countries, ideal for a hand-built device because it roams and sidesteps local device-registration. Confirm which local carriers it roams onto in your country (for example, in Korea it roams on KT/SKT, not LG U+).
- Local prepaid data SIM: cheapest per-country; confirm a hand-built (non-certified) device is allowed to attach to data.

No cellular coverage (remote/rural rivers)? Use LoRa instead. Meshtastic runs license-exempt ISM bands, region-selectable:

| Region | LoRa band |
|---|---|
| Europe, Africa | 868 MHz |
| Americas, Australia | 915 MHz |
| Most of Asia | 923 MHz |
| Korea | 920–923 MHz (KR920) |

LoRa needs one or two community gateways with line of sight, but then transmission is free. See `docs/meshtastic_kr920_setup.md` for a worked LoRa setup.

---

## 6. Housing and ballast (bottle-first)

The default housing is an upcycled PET bottle. It is free, available everywhere, it is the litter we study (highest drift representativeness), and it fits the movement's use-what-is-around ethos. A clear 0.5–1 L bottle: cut a small hatch, mount electronics dry in the top, seal, done.

Two rules, universal:
- Antenna always above water. Mount the antenna at the top and keep the tip above the waterline. If it submerges, GPS and cellular both die.
- Self-righting. Put the weight low and to one side (the belly), so the float lies on its side and rights itself antenna-up no matter how it rolls. Weight goes only at the bottom, never near the antenna (metal near the antenna shields the signal).

Upgrade to a sealed IP-rated case (Tier 2) only when you need repeated reuse or cold-water robustness; that adds external antennas, glands, temperature-protected charging, and a self-righting keel (see the robust build doc).

---

## 7. Firmware

Reference firmware is in `firmware/drifter_a7670_cat1/`. Toolchain: Arduino IDE, ESP32 core 3.0.x, libraries lewisxhe/TinyGSM-fork + TinyGPSPlus + ArduinoHttpClient. Set your APN, your server URL, and your transmit interval. Default interval 30 minutes gives multi-week battery life; shorter intervals need a verified positive energy balance (measure it before deploying a fleet). Send one ping per wake; let the server assemble the track.

---

## 8. Deploy responsibly — localize (generic, with one worked example)

We give you the design. The release is yours. Before you put units in the water, walk this generic checklist and apply your own country's rules. This is the "attach the caveats" step that lets an open-source project spread without becoming reckless. It is not a wall, it is a habit.

Generic checklist (applies everywhere):
- Radio/telecom. A hand-built cellular or radio transmitter is regulated somewhere. Check whether your country needs a type-approval, exemption, or license for a small research/DIY transmitter, and whether your SIM/band is allowed. Global IoT roaming SIMs often simplify this.
- Water access. Someone manages the water you release into (municipal river, national river, protected wetland, harbor, coastal zone). Find out who and ask. Protected/heritage/wetland areas usually need extra consent, so prefer an ordinary local stream for a first pilot.
- Battery and e-waste. Li-ion in water is a fire and pollution risk if lost. Protect, contain, and above all recover (Rule 1). Have a plan for cells at end of life.
- Wildlife and other users. Smooth, non-entangling shapes. Avoid breeding seasons and protected species areas. Tell fishers, harbor authority, and coastguard so an unknown sealed electronic box washing ashore does not become an alarm.
- Start small and honest. A few units, recover them all, learn recovery rate and drift behavior, then size a larger release from what you measured, not from a round number.

Worked example — Korea (one locale among many):
- Radio: a hand-built cellular device for outdoor multi-unit use is subject to conformity assessment; obtain a research/development exemption confirmation from the national radio agency (RRA, form 12, up to 1,500 units) before releasing. A global IoT roaming SIM (KT/SKT) avoids local device-registration.
- Water: the Nakdong main channel and estuary are a national river plus a natural-monument/wetland protected zone (national-level consent). An ordinary tributary stream (managed by the city/district) is the low-friction pilot site and is still genuinely "source to sea" because the tributary flows to the estuary.
- The rest (battery safety, recovery-first, wildlife, notify water users) is the same universal set above.

Other countries: replace the two locale-specific lines (radio authority, water manager) with your own, keep everything else. If you build one, add your locale's notes back to this file so the next person in your country starts faster. That is how the movement compounds.

---

## 9. Join, contribute, share data

- Build a unit, release and recover it in your river, and POST trajectories to your own ingest server or the shared map.
- Add your river to the community river list (see the friendlyFloaty river set, CC BY) and your locale notes to Section 8.
- Improve the design: better self-righting bottle geometry, cheaper regional part swaps, translations. Open a pull request.
- Data is CC BY. Attribution: SEA:CUT / GAA (Global Adopt-a-Beach Alliance) and the contributor.

## 10. License and attribution

Firmware MIT. Documentation and data schema CC BY 4.0. Hardware design CERN-OHL-S (see LICENSE-hardware.md). Built by 사단법인 이타서울 / GAA and contributors. Inspired by the open-hardware movement, including Precious Plastic and OpenMetBuoy.
