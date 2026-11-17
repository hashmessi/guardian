# Process Guardian

## What This Is

Process Guardian is a clamp-on drift-prevention and lot-containment system for plastic injection-molding presses. A non-invasive edge kit, made up of split-core current transformers on the barrel heater zones and a temperature/dew-point probe at the dryer outlet, streams live readings to a decision engine. The engine catches heater burnout and drying failure before bad parts are molded. It runs an enforced material-QC gate, quarantines only the cycles that could be affected (sized by barrel residence), and releases production after a stability window. It never writes to the press (SAFE-01). The first customer is Ragam Polymoulds (Ponneri, Tamil Nadu: PP/PA6 furniture parts, plus a PU foaming shop). The target market is Indian MSME molders, served as a per-press managed service.

## Core Value

**Stop bad parts before they are molded, and when drift does happen, quarantine 6 parts instead of a shift.** Clamp-on in under 30 minutes, no PLC access, cheaper per press than any competing PS02 kit. The loop: detect (heater current, dryer health) → diagnose (signature A/B) → soft-lock and QC gate → quarantine sized by barrel residence → 5-cycle stability release, all with an audit trail.

## Current Milestone: v2.0 Plant-Ready Guardian

**Goal:** Turn the simulator prototype into a clamp-on edge kit that runs live on a Ragam press, proves scrap reduction in a 2-week pilot, and scales to many plants as a managed service, at a lower cost per press than competing PS02 kits.

**Target features:**
- Edge kit: ESP32 + split-core CTs on heater zones + dryer-outlet temp/dew-point probe, offline buffering
- Live ingest + per-recipe live baseline (replaces the simulator fingerprint)
- Signature A heater burnout, Signature B dryer/moisture, cross-sensor fault check, drift countdown
- Soft-lock QC gate (tablet lockout + andon light), barrel-residence quarantine, 5-cycle release. Still read-only (SAFE-01)
- Tamil/English operator tablet; Tier 0 zero-hardware mode (QR recipe lock + screen photo) for old presses
- Multi-plant: auth/RBAC, Postgres, fleet view, device provisioning, OTA
- Pilot evidence pack: before/after scrap on one PA6 press, ROI with stated assumptions
- Commercial: per-press price, install SOP, service/SLA

**Cut from the strategy PDF (not defensible):** moisture detection from barrel vibration (2–8 kHz), crash detection from >15 g spikes, hard press interlock "without PLC changes", the virgin-PP moisture story, unverified company dossier.

## Requirements

### Validated

<!-- Shipped in v1.0 (Phases 1-8) and v1.1 (Phases 9-15). -->

- [x] Deterministic cycle-level process simulator with event injection (Phase 1)
- [x] Process Fingerprint engine (machine + mold + part + recipe + material baseline) (Phase 2)
- [x] Drift Sentinel: EWMA, CUSUM, trend, multivariate (Phase 2)
- [x] Quality Risk Engine with calibrated probabilities and Quality Contract (Phase 3)
- [x] Root-Cause Evidence Engine (Phase 3)
- [x] Constrained intervention candidates, surrogate, optimizer, ABSTAIN gate (Phase 4)
- [x] Recovery Verifier and Scrap Containment Engine (Phase 5)
- [x] 13-state state machine with transition validation and audit (Phase 5)
- [x] SQLite storage (17 tables) and FastAPI backend with tolerant `/cycles` ingest (Phase 6)
- [x] Industrial UI: Detect / Diagnose / Act and Verify (Phase 7)
- [x] 10-scenario validation suite, demo reset, SAFE-01..04 invariants (Phase 8)
- [x] External benchmark grounding and 4-level epistemic labels (Phase 9, EVID-01..03)
- [x] CoPQ and cost-of-waiting economics (Phase 10, ECON-01..02)
- [x] PS02 operational checkpoints: recipe lock, moisture, spray (Phase 11, QCHK-02)
- [x] Guardian OFF/ON counterfactual replay (Phase 12, CRPL-01..02)
- [x] Scenario engine and validation scorecard (Phase 13)
- [x] UI honesty and token sweep (Phase 14)
- [x] Hostile-review remediation; human-channel `QC_REQUIRED` hold (Phase 15)
- Note: QCHK-01 (`MANDATORY_QC_CHECKPOINT`) was removed in Phase 15 because it never gated. v2.0 rebuilds an enforced QC gate.

### Active

<!-- Scoped for v2.0. See REQUIREMENTS.md for REQ-IDs and checklists. -->

- [ ] Edge sensor kit and firmware (EDGE)
- [ ] Live ingest and live baseline (LIVE)
- [ ] Failure signatures A/B with sensor-health checks (SIG)
- [ ] Enforced QC gate, quarantine and release on live data (GATE)
- [ ] Operator tablet, Tamil/English, Tier 0 mode (OPS)
- [ ] Multi-plant platform: auth, Postgres, fleet, provisioning, OTA (FLEET)
- [ ] Pilot and evidence pack (PILOT)
- [ ] Commercial and service model (COMM)

### Out of Scope

- Automatic PLC write-back or hard press interlock — safety and OEM-warranty risk; any machine-level stop is a later, OEM/integrator-installed dry contact, never software-driven.
- Moisture detection from barrel vibration and crash detection from impact spikes — no physical basis or acts too late; presses already have low-pressure mold protection.
- PU/RIM foaming-line monitoring — different physics (ratio, fluid temperature); revisit after the injection pilot proves value.
- Computer-vision part inspection — reactive and struggles with dark PP; QC stays a logged checkpoint.
- Open-ended chatbots — deterministic decision surface remains; Laya stays bounded and optional.
- Microservices/message brokers beyond what fleet scale actually requires — start with one backend + Postgres; add a broker only when measured load needs it.

## Context

**Customer reality (Ragam Polymoulds):** PP and PA6 furniture parts (chair shells, castor and fitting parts), presses 250–800 T, mixed old and new controllers, coastal humidity 70–85% RH. PS02 cites 6–7% rejection against a ≤2% target. Main failure chains to prove: dryer fault → wet PA6 → splay/brittleness; heater-band burnout → cold zone → short shots/warp.

**Competition (PS02 finalists):** MoldSense (phone-first, QR recipe, screen OCR, zero capex), ₹10,700 ESP32 kit (drift countdown, cross-sensor fault check, drying checks, bilingual), DriftGuard (ESP32 thermocouples/pressure/humidity), Trevoga (₹25,200 DIN-rail ESP32-S3, TinyML, SSR shot diversion). Our wedge: clamp-on non-invasive install + enforced QC gate + barrel-residence quarantine + verified release, at a lower per-press price.

**Epistemic honesty:** No plant claims until the pilot produces them. BOM prices and resin moisture limits must be sourced (datasheet or quote) before they appear in a pitch.

## Constraints

- **Safety:** Read-only (SAFE-01), ABSTAIN gate (SAFE-03), honest labels (SAFE-04) carry forward.
- **Non-invasive:** No drilling, no PLC access, install ≤30 min per press, press keeps running during install.
- **Cost:** Edge kit BOM target ≤ ₹6,000 per press (excluding shared tablet), sourced quotes required; must undercut the ₹10,700 kit.
- **Reliability:** Plant Wi-Fi is unreliable; edge must buffer offline and never lose cycles silently.
- **Tech stack:** Python/FastAPI, React/Vite, ESP32 (Arduino/ESP-IDF), SQLite on edge/gateway, Postgres in the cloud.
- **Validation:** Zero regressions on the existing test suite; every new decision path gets a test.

## Key Decisions

| Decision | Why | Date |
|---|---|---|
| Own ESP32 clamp-on kit, not an off-the-shelf gateway | Lowest per-press cost and the main competitive edge | 2026-11-17 |
| Sense heater current + dryer dew point, not vibration | Physically defensible; dryer health is a leading indicator | 2026-11-17 |
| Soft lock (tablet + andon), not press interlock | Keeps SAFE-01 and OEM warranties | 2026-11-17 |
| Lead the moisture story with PA6, not virgin PP | PP barely absorbs water; PA6 is hygroscopic | 2026-11-17 |
| Skip upfront research; verify BOM prices and limits inside the phases | User choice; prices verified as phase tasks | 2026-11-17 |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-11-17 after starting Milestone v2.0*
