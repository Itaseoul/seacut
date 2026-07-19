# FF-ID ↔ international standards crosswalk

FF-ID (the Friendly Floaty observation format, [../data/schema.md](../data/schema.md)) is a **native, lightweight citizen-science format**. It is deliberately small so a hand-built device and a one-file server can speak it. But small does not mean isolated: a drifter trajectory is an ordinary geophysical object, and the recognized standards for "a thing that moves through water reporting time + position" already exist. This page maps FF-ID onto them so the data lands in the right registries and combines with professional datasets instead of sitting in a private silo.

**The one boundary that matters first.** A Friendly Floaty record is a **Lagrangian trajectory of a tracked object** — where it went, when. It is **not a biodiversity occurrence**. It therefore belongs in:

- **CF conventions** — Discrete Sampling Geometry, `featureType = "trajectory"` (the canonical NetCDF encoding for a moving platform)
- **OGC SensorThings API (STA)** — the OGC standard for IoT sensor observations
- **EMODnet Physics** — the European marine in-situ hub that already ingests drifter/float trajectories (via SeaDataNet/BODC vocabularies and CF-NetCDF)

…and it does **not** belong in **GBIF / Darwin Core / OBIS** (species-occurrence registries). Submitting a drifter track as an "occurrence" is a category error and pollutes those datasets. If a record ever carries *what object was tracked* (a PET bottle, a derelict net), that litter-type attribute uses marine-litter vocabularies (UNEP/GESAMP, OSPAR, the EMODnet Chemistry marine-litter categories) — never a taxonomic rank.

---

## 1. Field crosswalk

FF-ID field → CF standard_name (NetCDF) · OGC SensorThings element · EMODnet/SeaDataNet note. Blank means "no standard equivalent — FF-ID-native housekeeping, carried as an ancillary/parameter."

| FF-ID field | CF (NetCDF DSG trajectory) | OGC SensorThings (STA) | EMODnet Physics / SeaDataNet |
|---|---|---|---|
| `unit_id` | variable with `cf_role = "trajectory_id"` | **Thing** (`@iot.id` / `name`) | platform id; EDMO for the operator org |
| `obs_id` | (row identity within the trajectory) | **Observation** `@iot.id` | citation id (keep as-is; it is the DOI-able unit) |
| `lat` | `latitude`, units `degrees_north` | Observation `FeatureOfInterest` (GeoJSON Point) | P01 `ALATZZ01`, P06 `DEGN` |
| `lon` | `longitude`, units `degrees_east` | Observation `FeatureOfInterest` (GeoJSON Point) | P01 `ALONZZ01`, P06 `DEGE` |
| `ts_fix` | `time`, units `seconds since 1970-01-01T00:00:00Z` | Observation `phenomenonTime` | observation time (UTC) |
| `server_recv_ts` | ancillary time variable | Observation `resultTime` | ingestion time (distinct from phenomenonTime) |
| `crs` (`EPSG:4326`) | `grid_mapping` → `latitude_longitude` (WGS84) | CRS of the GeoJSON (CRS84) | WGS84 |
| `position_uncertainty_m` | ancillary variable, `standard_name = ...status_flag`-adjacent; carry as `*_uncertainty` | Observation `parameters.position_uncertainty_m` | quality/uncertainty parameter |
| `batt` | non-CF housekeeping variable (`long_name = "battery voltage"`, units `V`) | its own **Datastream** (ObservedProperty = battery voltage, Sensor = board ADC) | housekeeping parameter |
| `env.wind_u_ms` | `eastward_wind`, units `m s-1` | Observation `parameters.wind_u_ms` | joined covariate; keep source in `wind_source` |
| `env.wind_v_ms` | `northward_wind`, units `m s-1` | Observation `parameters.wind_v_ms` | joined covariate |
| `env.hs_m` | `sea_surface_wave_significant_height`, units `m` | Observation `parameters.hs_m` | wave covariate (may be null) |
| `sample_interval_s` | global/traj attribute (`sampling_interval`) | Datastream `parameters.sample_interval_s` | temporal resolution metadata |
| `fix_quality` (HDOP) | ancillary `hdop` variable | Observation `parameters.fix_quality` | quality parameter |
| `gnss_source` | traj attribute | Sensor (`metadata`: L76K / phone) | instrument metadata |
| `motion_state` | status flag variable (`flag_values`/`flag_meanings`) | Observation `parameters.motion_state` | quality/status flag |
| `qc.velocity_4sigma` | `status_flag` (`flag_meanings = "pass fail"`) | Observation `parameters.qc_velocity_4sigma` | QC flag (cf. SeaDataNet QC L20) |
| `qc.censoring` | status flag variable | Observation `parameters.qc_censoring` | selection-bias flag (FF-ID-specific) |
| `qc.is_estimate` | ancillary status flag | Observation `parameters.is_estimate` | derived-vs-measured flag |
| `provenance.verification` | traj/global attribute | Observation `parameters.verification` | provenance (`raw`/`auto_checked`/`steward_verified`) |
| `calibration_ref` | global attribute | Datastream `properties.calibration_ref` | method/calibration reference |
| `medium` (`freshwater`) | global attribute | Thing `properties.medium` | platform environment |
| `link` (`cellular`) | global attribute | Thing `properties.link` | telemetry class (not satellite) |
| `deploy` / `end` / `fate` | trajectory start/stop + `fate` attribute | Thing `Locations` / `HistoricalLocations`; fate in `properties` | deployment/recovery metadata (GDP-style) |

Notes:
- **CF trajectory identity.** The whole track is one `featureType = "trajectory"` feature; the per-fix rows share one `cf_role = "trajectory_id"` variable (`unit_id`). This is exactly how NOAA GDP and Argo-adjacent drifter data are encoded — it is why FF-ID keeps a unit directory (§3 of the schema) instead of only loose pings.
- **SensorThings shape.** One drifter = one `Thing`; each measured quantity (position, battery) = a `Datastream`; each ping = an `Observation` with `phenomenonTime = ts_fix` and `resultTime = server_recv_ts`. The split of those two times (a store-and-forward requirement in FF-ID) maps *natively* onto STA — most formats lose it.
- **EMODnet reality check.** EMODnet Physics ingests professional in-situ platforms; a citizen drifter is accepted on its data-quality and metadata completeness, not by right. The crosswalk is what makes a submission *possible*; a DOI-deposited dataset (Zenodo/SEANOE) with these fields is the realistic first step, with EMODnet as a later goal once provenance is `steward_verified`.

---

## 2. Honest scope (carried from the schema)

The crosswalk does not upgrade the science. Everything in [../data/schema.md](../data/schema.md) §4.5 still holds after export:

- The data is an **effort/path signal and a Lagrangian trajectory**, not a pollution flux, total, or concentration.
- Coverage is **river / estuary / near-coast, fair-weather, surface** — right-censored at the cellular edge, nearshore-biased by recover-first, and blind to the flood regime that actually dominates river litter transport.
- Windage/Stokes covariates are **joined, not measured by the drifter**; keep them separate from the trajectory itself.
- Positions are GNSS fixes (~2.5 m CEP), not sub-meter survey; `position_uncertainty_m` propagates into any derived velocity.

Exporting to CF/STA/EMODnet **must not** silently drop these flags. The `qc.*`, `provenance.*`, `is_estimate`, and `position_uncertainty_m` fields are first-class in every target format above precisely so the caveats travel with the numbers.

---

## 3. Exporter

[../data/export_standards.py](../data/export_standards.py) — a zero-hard-dependency reference exporter. It reads FF-ID observation records (JSON, one per line) and emits:

1. **OGC SensorThings Observations** (JSON) — pure standard library, always available.
2. **CF-1.11 trajectory CDL** (`.cdl` text) — feed to `ncgen -o out.nc in.cdl` to get a real CF-NetCDF file with no Python NetCDF dependency. If `netCDF4` *is* importable, the exporter writes the `.nc` directly as well.

```
python3 data/export_standards.py observations.jsonl --sta out.sta.json --cdl out.cdl
# then, if you have the netCDF tools:  ncgen -o out.nc out.cdl
```

The exporter is a **starting point, not a certification**: it produces standards-shaped output that a domain data manager can validate (CF-checker, an STA endpoint, EMODnet's ingestion checks) before any real submission.

---

## References (external — not repo links)

- CF Conventions, Discrete Sampling Geometries, `featureType = trajectory` and `cf_role`.
- OGC SensorThings API Part 1: Sensing (Thing / Datastream / Sensor / ObservedProperty / Observation / FeatureOfInterest).
- EMODnet Physics — in-situ platforms incl. drifters/floats; SeaDataNet / BODC NERC vocabularies (P01 parameters, P06 units, EDMO organizations).
- NOAA Global Drifter Program metadata practice (unit directory, deploy/end/fate).
- Marine-litter categories: UNEP/GESAMP, OSPAR, EMODnet Chemistry marine-litter — for *object type*, never taxonomy.
