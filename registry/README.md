# Variant Registry

Per [DIY_DIVERSITY.md §4.1](../docs/DIY_DIVERSITY.md), each build variant is one `*.yml` here.
Registering a variant **catalogs that it exists** — it does **not** grant data eligibility.
Data eligibility is the K2 provenance gate (evidence-anchored), separate from this catalog.
This separation is the first line of defence that self-registration does not become a
data-pool loophole.

## Badge states (shown in the gallery)

- **`self-declared`** — the 4 kernels self-attested **plus per-unit hash evidence** attached.
- **`unverified`** — declared but no evidence / no recovery session. Warning badge; the data
  does not pass the provenance gate.
- **`steward-verified`** — independent, plural stewards or authorities confirmed F1/F2 and the
  recovery reconciliation. The only tier allowed to emit `steward_verified` data.

## Reference seeds

Files prefixed `_reference-*` are the **project's reference designs, not field deployments**.
They carry **no unit evidence** and stay `status: reference` until someone builds one and logs
the bench tests. Do not cite their (empty) `results`/`evidence` as field data.

- [`_reference-tier1-bottle.yml`](_reference-tier1-bottle.yml) — the default Tier 1 cellular bottle.
- [`_reference-tier1.5-solar.yml`](_reference-tier1.5-solar.yml) — the Tier 1.5 solar-assisted long-dwell variant.

## Add your build

1. Copy a reference file. Set `variant_id` = `<country>-<region>-<form>-<rev>` (globally unique).
2. Set your `operator` (a registered operator, not a person), region, and local part swaps.
3. Run F1/F2 + cell-safety (and, for a solar build, the [Tier 1.5 gates](../hardware/TIER1_5_SOLAR_DRIFTER.md#4-벤치검증)).
4. Attach **per-unit** evidence (mass/soak logs) with `sha256` + timestamp. No evidence → `unverified`.
5. `remix_of` a parent variant → credit is inherited only with the parent operator's key signature.

License of the design/docs/data you reference stays as the repo declares: hardware CERN-OHL-S,
docs CC BY-SA 4.0, **data CC BY 4.0**, firmware MIT.
