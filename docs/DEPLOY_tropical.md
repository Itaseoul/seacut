# Locale profile — tropical / monsoon (worked example: Da Nang, Vietnam)

A second locale profile, the way [OPEN_HARDWARE_BOM_global.md](OPEN_HARDWARE_BOM_global.md) §5 invites: keep the
universal rules, swap the locale-specific lines. This one collects what changes when you move the reference
design from a Korean temperate river to a **warm, monsoon-driven, high-UV** coast.

> **Honesty first.** The reference design has **not been validated anywhere yet** (see
> [VALIDATION_CAMPAIGN.md](VALIDATION_CAMPAIGN.md)), let alone in the tropics. Everything here is **planning
> guidance, not tested results** — treat each item as a hypothesis to confirm on your own bench and first
> release. The four rules (recover-first, safe power, do-no-harm, own-your-deployment) are unchanged.

## What changes in warm water

- **Heat, not cold, is the battery limit.** The temperate build worries about charging below 0 °C; here the
  risk is the opposite — a sealed dark enclosure in tropical sun can pass the **45 °C** upper charge/float
  limit and cook the cell. Keep the housing light-coloured or shaded, watch the JEITA upper taper, and for the
  solar variant the NTC cutoff ([../hardware/cad/params.scad](../hardware/cad/params.scad) `solar_ntc`) does the
  high-temp stop. Li-ion calendar aging also accelerates with temperature — do not leave charged units baking
  between deployments.
- **Biofouling is faster.** Warm, productive water fouls a hull in days, not weeks; fouling adds drag and mass
  and shifts the drift signal. Plan **shorter dwell before recovery**, inspect for growth, and note fouling in
  the unit `fate`/notes. This makes recover-first even more central.
- **UV ages the bottle faster.** Tropical UV embrittles PET quicker. For anything beyond a short release,
  prefer a UV-stable housing (Tier 2) or expect the PET to be single-use — and never let an embrittled unit
  become the litter you fight.
- **The flood regime dominates even more.** River litter transport is already flood-driven (schema §4.5); a
  monsoon coast concentrates that into the wet season. A fair-weather drifter under-samples the very events
  that matter — so scope claims tightly and time releases against the monsoon, not against the calendar.
- **Monsoon reversal is real and measurable.** Off Da Nang the surface drift reverses seasonally (roughly
  south-ish in winter, north-ish in summer). That is a genuine physical signal a drifter can help *observe* —
  but it is **not** a "trash flows from A to B" story on its own; keep windage/Stokes covariates separate
  (schema §4.5) and never fabricate a single cross-basin trajectory.

## Locale-specific lines to swap

- **Radio / SIM.** Use the **A7670G** global band variant. Vietnamese carriers (Viettel / Vinaphone /
  MobiFone) — confirm the LTE bands your carrier uses, or use a global IoT roaming SIM and confirm which local
  network it attaches to. A hand-built transmitter is regulated in Vietnam as elsewhere; check the local
  type-approval / research-exemption path before a multi-unit release.
- **Water authority.** Identify who manages your reach (river basin authority, provincial DONRE, coastal/port
  authority) and get sign-off; start on an ordinary tributary, not a protected or heritage stretch.
- **★ Data-residency (Vietnam).** Vietnam's data law can require personal/location data on Vietnamese
  citizens to be **stored in-country**. Coordinates of a drifter are not personal data, but any deployment
  that links coordinates to people (participants, addresses) must keep that linkage in-country. Follow the GAA
  Vietnam practice: **store coordinate/participant data on Vietnamese infrastructure**, and keep the open FF-ID
  export (CC BY) to non-personal trajectory fields only. Confirm current law before collecting.

## Bench additions before a tropical release

On top of the standard Stage-0 gates ([VALIDATION_CAMPAIGN.md](VALIDATION_CAMPAIGN.md)):

- [ ] **Hot-soak the charge cutoff:** confirm the unit stops charging as the enclosure approaches 45 °C (heat it, watch the NTC/JEITA behaviour). Do not skip this — it is the tropical-specific safety gate.
- [ ] **Short-dwell fouling check:** leave a unit in local water for the planned dwell and inspect drag/mass change before trusting a longer release.
- [ ] **UV / housing:** decide single-use PET vs UV-stable housing for your dwell, honestly.
- [ ] **Recovery is harder in monsoon flow:** rehearse recovery at the flow you actually expect, not calm water.

Add your measured tropical notes back here (and to [DIY_DIVERSITY.md](DIY_DIVERSITY.md)) so the next builder in a warm-water basin starts from data, not from this hypothesis.
