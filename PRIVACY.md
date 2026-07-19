# Privacy

The drifter observes **device positions on the water, not people.** Still, a few rules keep every
deployment privacy-preserving.

- **No personal data in the payload.** The ping schema ([data/schema.md](data/schema.md)) carries only
  `device_id`, position, time, battery, and QC fields — no personal fields. For **Tier 0
  (phone-in-a-bottle)**, never let the phone's SIM / IMEI / phone number reach the ingest server.
- **Release-point blurring.** Public snapshots blur exact release coordinates (k-anonymity) where a
  precise release point could identify a specific person or private property.
- **QR / contact labels.** The recovery QR points to an **organization** contact, not a personal phone.
  Handle any finder's contact details under local data-protection law (Korea PIPA / EU GDPR) and do not
  put them in the open data commons.
- **Retention.** Any cohort dataset has a stated retention window. If a deployment uses a recruitment or
  voice-application flow, that PII lives in a **separate private store** with a purge schedule — never in
  the CC BY data commons.

Data is CC BY (open); personal data is simply **not data we collect**. If in doubt, do not collect it.
