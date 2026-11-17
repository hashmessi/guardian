# Requirements: Process Guardian

**Defined:** 2026-11-17
**Milestone:** v2.0 — Plant-Ready Guardian
**Core Value:** Stop bad parts before they are molded; when drift happens, quarantine 6 parts instead of a shift. Clamp-on, no PLC access, cheaper per press than competing kits.

Earlier milestones: `.planning/milestones/v1.1-REQUIREMENTS.md` (v1.0 + v1.1, all validated; QCHK-01 removed in Phase 15).

Every requirement has a **Done when** check that must be shown with evidence (test, measurement, or signed record), not stated.

---

## v2.0 Requirements

### EDGE — Clamp-on sensor kit and firmware

- [ ] **EDGE-01**: An installer can clamp split-core CTs onto up to 5 heater-zone feeds and 1 pump-motor feed in the press panel without opening the PLC or stopping the press.
  Done when: install SOP timed on a real press at ≤30 min; no PLC access logged.
- [ ] **EDGE-02**: The edge node detects each molding cycle from the pump-motor current pattern.
  Done when: cycle count matches the press shot counter within ±2% over ≥500 cycles on 2 different presses.
- [ ] **EDGE-03**: The edge node reports per-cycle RMS current for each heater zone and the pump motor.
  Done when: readings match a reference clamp meter within ±3% at 3 load levels.
- [ ] **EDGE-04**: A probe at the dryer outlet reports air temperature and dew point every cycle.
  Done when: compared against a reference hygrometer, temperature within ±1 °C and dew point within ±2 °C over 24 h.
- [ ] **EDGE-05**: The edge node buffers at least 12 hours of cycles offline and replays them in order on reconnect, with gaps reported, never silently dropped.
  Done when: test with Wi-Fi off for 12 h shows 0 lost cycles and the backend shows the gap window.
- [ ] **EDGE-06**: The edge node reports health (heartbeat, firmware version, per-sensor connected/disconnected).
  Done when: unplugging any sensor raises a SENSOR_FAULT within 3 cycles.
- [ ] **EDGE-07**: The kit drives a 3-colour andon light from its own relay, electrically isolated from the press.
  Done when: andon follows backend state within 2 s; isolation verified by an electrician.
- [ ] **EDGE-08**: The kit BOM costs ≤ ₹6,000 per press (excluding the shared tablet), backed by written supplier quotes at 10 and 100 units.
  Done when: costed BOM with quotes is committed; enclosure is IP54 with magnet/DIN mount.

### LIVE — Live data path

- [ ] **LIVE-01**: The backend accepts heater-zone currents, pump current, dryer temperature and dew point on `/cycles`, with physical bounds validation.
  Done when: API tests cover valid, out-of-bounds and missing values.
- [ ] **LIVE-02**: A supervisor can start a live baseline; after 30–50 good cycles the fingerprint is fitted from live data for that machine + mold + recipe, replacing the simulator baseline.
  Done when: test shows the live fingerprint is used and the simulator fingerprint is not.
- [ ] **LIVE-03**: A supervisor can re-baseline after a mold or recipe change, and earlier baselines are kept and versioned.
  Done when: two baselines for one press are stored and the active one is selected by context.
- [ ] **LIVE-04**: A press with only the clamp-on signals (no barrel thermocouples or pressures) is a valid live source; missing signals never block decisions or masquerade as readings.
  Done when: test with a heater + dryer-only payload runs the full loop without validity failures.
- [ ] **LIVE-05**: Every screen shows the data source (LIVE device ID or SIMULATOR); simulated numbers can never appear under a LIVE label.
  Done when: UI test asserts the badge in both modes.
- [ ] **LIVE-06**: A recorded live session file can be replayed through the same ingest path for demos and regression tests.
  Done when: replay of a recorded session produces identical state transitions twice.

### SIG — Failure signatures and sensor health

- [ ] **SIG-01**: Signature A: a sustained heater-zone current drop raises an advisory naming the zone, before part defects appear.
  Done when: bench test (one heater element disconnected) flags the correct zone within ≤5 cycles; threshold tuned on pilot data.
- [ ] **SIG-02**: Signature B: dryer outlet temperature below band or dew point above limit raises a material-risk soft lock before suspect resin reaches the barrel.
  Done when: bench test (dryer heater off / humid air) triggers the lock; timing accounts for hopper + barrel residence.
- [ ] **SIG-03**: Cross-sensor fault check tells a burnt-out heater apart from a disconnected or failed sensor; sensor faults raise a maintenance ticket, not a production lock.
  Done when: tests for both cases give different outcomes; pilot logs show 0 production locks caused by sensor faults.
- [ ] **SIG-04**: Drift countdown shows estimated cycles until a limit is crossed, only when the trend fit is confident.
  Done when: on recorded ramps, estimate is within ±30% of actual; hidden when R² is below threshold.
- [ ] **SIG-05**: Dryer and moisture limits are set per material and recipe from the resin datasheet (PA6, filled/recycled PP), not hardcoded.
  Done when: limits configurable per recipe, each with a datasheet reference; the 0.15% constant removed.
- [ ] **SIG-06**: False soft locks stay at or below 1 per press per shift.
  Done when: measured over the pilot's active weeks.

### GATE — Enforced QC gate, quarantine, release

- [ ] **GATE-01**: On Signature B the operator tablet locks to the material QC checklist (dryer temp, moisture reading, purge check), and production view returns only after a compliant reading is logged — enforced by the state machine, with no path around it.
  Done when: test proves no transition to production without a compliant reading (closes the Phase 15 gap).
- [ ] **GATE-02**: A failed reading keeps the lock and shows corrective steps; a supervisor override needs a PIN and a reason, and is audited.
  Done when: tests cover failed reading, override and audit record.
- [ ] **GATE-03**: The quarantine window runs from (detection cycle − barrel residence in shots) to the hold cycle, with residence computed from shot weight and barrel capacity per recipe.
  Done when: unit test reproduces the 98–103 example; recipe without residence data falls back to a conservative window and says so.
- [ ] **GATE-04**: A 5-cycle stability window must pass before release; following cycles are tagged VERIFIED.
  Done when: tests for pass, fail-and-restart.
- [ ] **GATE-05**: A supervisor can export a shift quarantine report (cycles, bins, disposition, who released) as PDF/CSV for ISO 9001 records.
  Done when: export validated by Ragam QC lead.

### OPS — Operator experience

- [ ] **OPS-01**: Operators can switch all lock, checklist and alert screens between Tamil and English.
  Done when: native-speaker review signs off on wording.
- [ ] **OPS-02**: The operator app runs as an offline-tolerant PWA on a budget Android tablet and survives Wi-Fi drops without losing entries.
  Done when: entries made offline sync on reconnect in test.
- [ ] **OPS-03**: An operator scans a mold QR code to load the golden recipe and confirms setpoints; mismatches are flagged before the run starts (Tier 0, extends the existing R-12 recipe lock).
  Done when: test with a wrong setpoint blocks the start confirmation.
- [ ] **OPS-04**: Supervisors get a shift handover summary (locks, quarantines, open tickets).
  Done when: generated at shift end in pilot.

### FLEET — Multi-plant platform (minimum slice)

- [ ] **FLEET-01**: Every endpoint requires authentication, with roles operator / supervisor / plant manager / Guardian admin; CORS restricted to known origins.
  Done when: tests show unauthenticated and wrong-role calls rejected, including `/containment/release`.
- [ ] **FLEET-02**: Data persists in Postgres with plant-level tenant isolation and daily backups.
  Done when: cross-tenant read test fails as expected; restore from backup rehearsed.
- [ ] **FLEET-03**: A Guardian admin can claim a new device to a plant and press by scanning its QR code; each device gets its own credentials.
  Done when: revoked device credentials are rejected.
- [ ] **FLEET-04**: A plant manager sees all presses: status, open locks, quarantines, device health, scrap avoided.
  Done when: view works for ≥2 plants with seeded data.
- [ ] **FLEET-05**: Firmware updates are signed, delivered over the air, and roll back on failed boot.
  Done when: a bad image auto-rolls back on a bench device.
- [ ] **FLEET-06**: Edge-to-cloud traffic is TLS-encrypted.
  Done when: traffic capture shows no plaintext telemetry.

### PILOT — Ragam pilot and evidence

- [ ] **PILOT-01**: Ragam signs a pilot agreement covering one PA6 press, data use and consent.
  Done when: signed copy on file.
- [ ] **PILOT-02**: Guardian runs 2 weeks in shadow mode (no alerts) then 2 weeks active, while Ragam QC logs rejections by cause.
  Done when: both periods complete with daily logs.
- [ ] **PILOT-03**: An evidence pack reports rejection % before/after, incidents caught, false alarms, and parts quarantined vs the status-quo estimate, labelled as plant evidence.
  Done when: Ragam's QC lead reviews and countersigns the numbers.
- [ ] **PILOT-04**: The ROI calculator uses Ragam's own incident rate and part cost, with every assumption visible.
  Done when: no hardcoded ₹450 or incident count remains; assumptions editable.

### COMM — Commercial and service

- [ ] **COMM-01**: Price per press (one-time kit + monthly service) with a 12-month cost comparison against the ₹10,700 kit, Trevoga ₹25,200 and MoldSense.
  Done when: pricing sheet committed; Guardian 12-month TCO is lower or the gap is justified by measured scrap avoided.
- [ ] **COMM-02**: Installer checklist and electrical safety SOP (CTs on live panels fitted only by a licensed electrician).
  Done when: SOP used on pilot install.
- [ ] **COMM-03**: Service SLA (response times, spare-kit swap, remote support hours).
  Done when: published and accepted by pilot customer.

---

## Future Requirements (v2.1+)

- Screen-photo OCR of press setpoints for old presses (Tier 0 extension)
- PU/RIM foaming line: fluid temperature and metering-ratio drift
- Optional OEM/integrator-installed dry contact to the press alarm input
- Reject-chute segregation signal where presses already have one
- Hardware certification path (check BIS/CE applicability before volume sales)
- Fleet analytics across plants (benchmarks by material and machine age)

## Out of Scope

| Feature | Reason |
|---|---|
| Software-driven PLC write-back or hard press interlock | Safety and OEM-warranty risk; breaks SAFE-01 |
| Moisture detection from barrel vibration | No defensible physical basis |
| Crash detection from impact spikes | Fires after the damage; presses already have mold protection |
| Computer-vision part inspection | Reactive; dark PP defeats it |
| Message broker / microservices on day one | Add only when measured load requires it |

---

## Traceability

| Requirement | Phase | Status |
|---|---|---|
| EDGE-01 | Phase 22 | Pending |
| EDGE-02 | Phase 17 | Pending |
| EDGE-03 | Phase 17 | Pending |
| EDGE-04 | Phase 17 | Pending |
| EDGE-05 | Phase 17 | Pending |
| EDGE-06 | Phase 17 | Pending |
| EDGE-07 | Phase 17 | Pending |
| EDGE-08 | Phase 17 | Pending |
| LIVE-01 | Phase 16 | Pending |
| LIVE-02 | Phase 16 | Pending |
| LIVE-03 | Phase 16 | Pending |
| LIVE-04 | Phase 16 | Pending |
| LIVE-05 | Phase 16 | Pending |
| LIVE-06 | Phase 16 | Pending |
| SIG-01 | Phase 18 | Pending |
| SIG-02 | Phase 18 | Pending |
| SIG-03 | Phase 18 | Pending |
| SIG-04 | Phase 18 | Pending |
| SIG-05 | Phase 18 | Pending |
| SIG-06 | Phase 22 | Pending |
| GATE-01 | Phase 19 | Pending |
| GATE-02 | Phase 19 | Pending |
| GATE-03 | Phase 19 | Pending |
| GATE-04 | Phase 19 | Pending |
| GATE-05 | Phase 19 | Pending |
| OPS-01 | Phase 20 | Pending |
| OPS-02 | Phase 20 | Pending |
| OPS-03 | Phase 20 | Pending |
| OPS-04 | Phase 20 | Pending |
| FLEET-01 | Phase 21 | Pending |
| FLEET-02 | Phase 23 | Pending |
| FLEET-03 | Phase 21 | Pending |
| FLEET-04 | Phase 23 | Pending |
| FLEET-05 | Phase 23 | Pending |
| FLEET-06 | Phase 21 | Pending |
| PILOT-01 | Phase 22 | Pending |
| PILOT-02 | Phase 22 | Pending |
| PILOT-03 | Phase 24 | Pending |
| PILOT-04 | Phase 24 | Pending |
| COMM-01 | Phase 24 | Pending |
| COMM-02 | Phase 22 | Pending |
| COMM-03 | Phase 24 | Pending |

**Coverage:** 42/42 v2.0 requirements mapped, no duplicates.
