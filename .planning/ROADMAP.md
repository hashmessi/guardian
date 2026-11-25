# Roadmap: Process Guardian

**Milestone:** v2.0 — Plant-Ready Guardian
**Status:** Planning (Phase 16 not started)
**Phases:** 16–24 (9 phases)
**Requirements:** 42 v2.0 requirements (EDGE 8, LIVE 6, SIG 6, GATE 5, OPS 4, FLEET 6, PILOT 4, COMM 3), 42/42 mapped

---

## Previous Milestones

- v1.0 (Phases 1–8) and v1.1 (Phases 9–15): complete. Full roadmap in `.planning/milestones/v1.1-ROADMAP.md`; requirements in `.planning/milestones/v1.1-REQUIREMENTS.md`.

---

## Phases

- [ ] **Phase 16: Live Data Path & Replay** - Clamp-on signals flow through `/cycles` into a live, versioned baseline; recorded sessions replay deterministically
- [ ] **Phase 17: Edge Kit Bench Bring-up** - ESP32 kit measures heater/pump current and dryer air on the bench, buffers offline, reports health, drives the andon, at a quoted BOM
- [ ] **Phase 18: Failure Signatures & Sensor Health** - Signature A (heater burnout) and B (dryer/moisture) fire on live data; sensor faults are told apart from process faults
- [ ] **Phase 19: Enforced QC Gate, Quarantine & Release** - Signature B locks production behind a compliant QC reading; quarantine sized by barrel residence; 5-cycle verified release
- [ ] **Phase 20: Operator Tablet** - Tamil/English offline PWA on a budget tablet with QR golden-recipe check and shift handover
- [ ] **Phase 21: Plant-Network Security** - Authenticated, role-checked API; per-device credentials claimed by QR; TLS edge-to-cloud
- [ ] **Phase 22: Ragam Pilot** - Signed agreement, safe install on a PA6 press, 2 weeks shadow + 2 weeks active with QC rejection logs
- [ ] **Phase 23: Fleet Minimum Slice** - Postgres with tenant isolation and backups, plant-manager fleet view, signed OTA with rollback
- [ ] **Phase 24: Evidence & Commercial Pack** - Countersigned pilot evidence, Ragam-specific ROI, per-press pricing and SLA

### Parallelism

| Phase | Can run in parallel with | Hard dependency |
|---|---|---|
| 16 | 17 | none |
| 17 | 16, 21 | none (agree the `/cycles` payload contract with 16 on day one) |
| 18 | 21 | 16, 17 (bench rig for A/B tests) |
| 19 | 20, 21 | 18 (Signature B trigger) |
| 20 | 19, 21 | 16 (source badge); lock screens consume 19's states |
| 21 | 17, 18, 19, 20 | 16 |
| 22 | 23 (fleet work during the 4 pilot weeks) | 17, 18, 19, 20, 21 and PILOT-01 signed |
| 23 | 22, 24 | 21 |
| 24 | 23 | 22 (pilot data); COMM-01 can draft once 17's BOM is quoted |

**Long-lead, start now:** PILOT-01 (signed Ragam agreement) is mapped to Phase 22 but the conversation with Ragam should start alongside Phase 16; the pilot cannot begin without it. Supplier quotes for EDGE-08 (Phase 17) are also lead-time bound and should be requested on day one.

---

## Phase Details

### Phase 16: Live Data Path & Replay
**Goal**: The backend runs the full decision loop on real clamp-on signals (or a replay of them) instead of the simulator, with the source always visible.
**Depends on**: Nothing (first v2.0 phase; uses recorded/bench data, no hardware required)
**Requirements**: LIVE-01, LIVE-02, LIVE-03, LIVE-04, LIVE-05, LIVE-06
**Success Criteria** (what must be TRUE):
  1. `/cycles` accepts heater-zone currents, pump current, dryer heater/blower currents, hopper inlet and return-air temperatures, ambient temperature/RH and optional dew point; API tests cover valid, out-of-bounds and missing values (LIVE-01), and a heater + dryer-only payload runs the full loop with no validity failures (LIVE-04).
  2. A supervisor starts a live baseline; after 30–50 good cycles the fingerprint for that machine + mold + recipe is fitted from live data, and a test proves the simulator fingerprint is not used (LIVE-02).
  3. Two baselines for one press are stored and versioned, and the active one is selected by mold/recipe context (LIVE-03).
  4. Every screen shows LIVE device ID or SIMULATOR; a UI test asserts the badge in both modes (LIVE-05).
  5. Replaying a recorded session file through the same ingest path twice gives identical state transitions (LIVE-06).
**Plans**: TBD
**UI hint**: yes

### Phase 17: Edge Kit Bench Bring-up
**Goal**: A clamp-on ESP32 kit produces trustworthy per-cycle readings on the bench, never loses data silently, and costs ≤ ₹6,000 per press with quotes on file.
**Depends on**: Nothing hard; parallel with Phase 16 (shares the `/cycles` payload contract)
**Requirements**: EDGE-02, EDGE-03, EDGE-04, EDGE-05, EDGE-06, EDGE-07, EDGE-08
**Success Criteria** (what must be TRUE):
  1. Per-cycle RMS current for each heater zone, the dryer heater, the blower and the pump motor matches a reference clamp meter within ±3% at 3 load levels (EDGE-03); hopper probes are within ±1 °C of a reference thermometer up to 100 °C and the ambient probe within ±1 °C / ±3% RH over 24 h (EDGE-04).
  2. Cycle detection from the pump-motor pattern counts within ±2% of the press shot counter over ≥500 cycles on 2 presses (EDGE-02). Bench rig proves the detector first; the 2-press count needs plant access and closes at the latest during Phase 22 install.
  3. With Wi-Fi off for 12 h the node loses 0 cycles, replays them in order, and the backend shows the gap window (EDGE-05); unplugging any sensor raises SENSOR_FAULT within 3 cycles, and heartbeat and firmware version are reported (EDGE-06).
  4. The andon follows backend state within 2 s from the kit's own isolated relay, with isolation signed off by an electrician (EDGE-07).
  5. A costed BOM with written supplier quotes at 10 and 100 units is committed at ≤ ₹6,000 per press, IP54 enclosure with magnet/DIN mount (EDGE-08).
**Plans**: TBD

### Phase 18: Failure Signatures & Sensor Health
**Goal**: Guardian names a failing heater zone or a failing dryer before defective parts appear, and never mistakes a broken sensor for a broken process.
**Depends on**: Phase 16 (live ingest), Phase 17 (bench rig)
**Requirements**: SIG-01, SIG-02, SIG-03, SIG-04, SIG-05
**Success Criteria** (what must be TRUE):
  1. With one heater element disconnected on the bench, an advisory names the correct zone within ≤5 cycles (SIG-01).
  2. Dryer heater off, a blocked blower filter, or throughput above dryer capacity triggers the material-risk soft lock, with timing that accounts for hopper + barrel residence (SIG-02).
  3. A burnt-out heater and a disconnected/failed sensor produce different outcomes in tests: the sensor case raises a maintenance ticket, never a production lock (SIG-03).
  4. On recorded ramps the drift countdown is within ±30% of actual cycles-to-limit, and is hidden when R² is below threshold (SIG-04).
  5. Dryer and moisture limits are configurable per material and recipe (PA6, filled/recycled PP), each with a datasheet reference; the hardcoded 0.15% constant is gone (SIG-05).
**Plans**: TBD
**UI hint**: yes

### Phase 19: Enforced QC Gate, Quarantine & Release
**Goal**: On a material-risk signal, production cannot resume without a compliant QC reading, only the cycles that could be affected are quarantined, and release requires a verified stability window.
**Depends on**: Phase 18 (Signature B)
**Requirements**: GATE-01, GATE-02, GATE-03, GATE-04, GATE-05
**Success Criteria** (what must be TRUE):
  1. On Signature B the tablet locks to the material QC checklist, and a test proves the state machine has no transition back to production without a compliant reading (GATE-01, closes the Phase 15 gap).
  2. A failed reading keeps the lock and shows corrective steps; a supervisor override needs a PIN and a reason and leaves an audit record (GATE-02).
  3. The quarantine window reproduces the 98–103 example from shot weight and barrel capacity, and a recipe without residence data falls back to a conservative window and says so (GATE-03).
  4. Release requires a 5-cycle stability pass, following cycles are tagged VERIFIED, and a failed window restarts (GATE-04).
  5. A supervisor exports a shift quarantine report (cycles, bins, disposition, who released) as PDF/CSV, validated by Ragam's QC lead (GATE-05).
**Plans**: TBD
**UI hint**: yes

### Phase 20: Operator Tablet
**Goal**: An operator on a budget Android tablet can work every lock, checklist and recipe check in Tamil or English, even when plant Wi-Fi drops.
**Depends on**: Phase 16; lock and checklist screens consume Phase 19 states (i18n, PWA shell and QR recipe check can start in parallel with 19)
**Requirements**: OPS-01, OPS-02, OPS-03, OPS-04
**Success Criteria** (what must be TRUE):
  1. All lock, checklist and alert screens switch between Tamil and English, with native-speaker sign-off on the wording (OPS-01).
  2. The app installs as a PWA on a budget Android tablet; entries made offline sync on reconnect without loss (OPS-02).
  3. Scanning a mold QR loads the golden recipe; a wrong setpoint blocks the start confirmation (OPS-03).
  4. A shift handover summary (locks, quarantines, open tickets) is generated at shift end from a replayed shift, ready to run in the pilot (OPS-04).
**Plans**: TBD
**UI hint**: yes

### Phase 21: Plant-Network Security
**Goal**: Nothing reaches or controls Guardian without an identity: users are role-checked, each device has its own revocable credentials, and telemetry is encrypted, before any device joins a plant network.
**Depends on**: Phase 16
**Requirements**: FLEET-01, FLEET-03, FLEET-06
**Success Criteria** (what must be TRUE):
  1. Every endpoint requires authentication with roles operator / supervisor / plant manager / Guardian admin; tests show unauthenticated and wrong-role calls rejected, including `/containment/release`; CORS limited to known origins (FLEET-01).
  2. A Guardian admin claims a device to a plant and press by scanning its QR; each device gets its own credentials, and revoked credentials are rejected (FLEET-03).
  3. A traffic capture between edge and backend shows no plaintext telemetry (FLEET-06).
**Plans**: TBD

### Phase 22: Ragam Pilot
**Goal**: Guardian runs on a real Ragam PA6 press under a signed agreement, first silently, then live, with QC logging every rejection by cause.
**Depends on**: Phases 17, 18, 19, 20, 21; PILOT-01 signed (start the agreement in parallel with Phase 16)
**Requirements**: PILOT-01, EDGE-01, COMM-02, PILOT-02, SIG-06
**Success Criteria** (what must be TRUE):
  1. A signed pilot agreement covering one PA6 press, data use and consent is on file (PILOT-01).
  2. A licensed electrician installs the kit using the installer checklist and electrical safety SOP, timed at ≤30 min with no PLC access and the press running (EDGE-01, COMM-02).
  3. 2 weeks shadow mode (no alerts) then 2 weeks active complete, each with daily logs and Ragam QC rejection logs by cause (PILOT-02).
  4. False soft locks measured over the active weeks are ≤1 per press per shift (SIG-06).
**Plans**: TBD

### Phase 23: Fleet Minimum Slice
**Goal**: Guardian can serve more than one plant safely: isolated data, a manager view across presses, and firmware updates that cannot brick a kit.
**Depends on**: Phase 21; runs during the Phase 22 pilot weeks
**Requirements**: FLEET-02, FLEET-04, FLEET-05
**Success Criteria** (what must be TRUE):
  1. Data persists in Postgres with plant-level tenant isolation; a cross-tenant read test fails as expected, and restore from a daily backup is rehearsed (FLEET-02).
  2. A plant manager sees all presses (status, open locks, quarantines, device health, scrap avoided) for ≥2 plants with seeded data (FLEET-04).
  3. Firmware updates are signed and delivered over the air, and a bad image auto-rolls back on a bench device (FLEET-05).
**Plans**: TBD
**UI hint**: yes

### Phase 24: Evidence & Commercial Pack
**Goal**: The pilot's numbers are countersigned by Ragam, and a prospect can see what Guardian costs per press, what it saved, and what service they get.
**Depends on**: Phase 22 (pilot data); COMM-01 needs Phase 17's quoted BOM
**Requirements**: PILOT-03, PILOT-04, COMM-01, COMM-03
**Success Criteria** (what must be TRUE):
  1. The evidence pack reports rejection % before/after, incidents caught, false alarms, and parts quarantined vs the status-quo estimate, labelled as plant evidence and countersigned by Ragam's QC lead (PILOT-03).
  2. The ROI calculator uses Ragam's incident rate and part cost with every assumption visible and editable; no hardcoded ₹450 or incident count remains (PILOT-04).
  3. A committed pricing sheet (kit + monthly service) shows Guardian's 12-month TCO below the ₹10,700 kit, Trevoga ₹25,200 and MoldSense, or the gap justified by measured scrap avoided (COMM-01).
  4. A service SLA (response times, spare-kit swap, remote support hours) is published and accepted by Ragam (COMM-03).
**Plans**: TBD
**UI hint**: yes

---

## Progress

| Phase | Plans Complete | Status | Completed |
|---|---|---|---|
| 16. Live Data Path & Replay | 0/TBD | Not started | - |
| 17. Edge Kit Bench Bring-up | 0/TBD | Not started | - |
| 18. Failure Signatures & Sensor Health | 0/TBD | Not started | - |
| 19. Enforced QC Gate, Quarantine & Release | 0/TBD | Not started | - |
| 20. Operator Tablet | 0/TBD | Not started | - |
| 21. Plant-Network Security | 0/TBD | Not started | - |
| 22. Ragam Pilot | 0/TBD | Not started | - |
| 23. Fleet Minimum Slice | 0/TBD | Not started | - |
| 24. Evidence & Commercial Pack | 0/TBD | Not started | - |

---
*Created: 2026-11-17 for Milestone v2.0*
