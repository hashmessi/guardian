# Roadmap: Process Guardian

**Created:** 2026-09-23
**Milestone:** V1.0 — October 2 Prototype Demo
**Phases:** 8
**Requirements:** 61 mapped

---

## Phase 1: Digital Factory + Data Foundation
**Goal:** Build the deterministic cycle-level simulator with event injection and the data adapter layer that normalizes telemetry for all downstream engines.

**Requirements:** SIM-01, SIM-02, SIM-03, SIM-04, SIM-05, DADP-01, DADP-02, DADP-03

**UI hint**: no

**Success Criteria:**
1. Simulator generates correlated cycle-level telemetry across all 9 baseline regimes
2. `inject_event("thermal_drift", cycle=420)` produces consistent, deterministic results
3. Causal-like relationships visible (moisture ↑ → pressure → cycle → quality)
4. Data adapter normalizes units, timestamps cycles, validates ranges, flags missing signals
5. A reviewer can trigger a known failure at a known cycle and see correlated downstream effects

**Build days:** 23-24 Sep (Day 1-2)

---

## Phase 2: Process Fingerprint + Drift Sentinel
**Goal:** Build context-specific process baselines and the multi-method drift detection engine that identifies process-state changes before quality violations.

**Requirements:** FPRN-01, FPRN-02, FPRN-03, DRFT-01, DRFT-02, DRFT-03, DRFT-04

**UI hint**: no

**Success Criteria:**
1. Fingerprints are context-specific (different machine+mold+recipe = different baselines)
2. EWMA, CUSUM, rolling stats, and multivariate distance all produce drift signals
3. Drift detected ≥5 cycles before Quality Contract violation in demo scenario
4. No false drift alerts on healthy baseline or sensor noise scenarios
5. Drift output includes severity score, lead-cycle count, and contributing signal list

**Build days:** 25 Sep (Day 3)

---

## Phase 3: Quality Risk + Root-Cause Evidence
**Goal:** Build the quality risk model with calibrated probabilities and the root-cause evidence engine that provides ranked, honest contributor analysis.

**Requirements:** QRSK-01, QRSK-02, QRSK-03, QRSK-04, ROOT-01, ROOT-02, ROOT-03

**UI hint**: no

**Success Criteria:**
1. XGBoost/LightGBM produces calibrated risk probabilities against Quality Contract
2. Temporal features (10+ categories) feed into risk model
3. Risk state classification (LOW/MEDIUM/HIGH) maps to operator action modes
4. Root-cause contributors sum to 100% with percentage breakdown
5. Evidence uses honest language only ("likely contributor", "evidence", "modeled effect")

**Build days:** 26 Sep (Day 4)

---

## Phase 4: Intervention Engine + Recommendation
**Goal:** Build the constrained intervention simulator, cost/risk optimizer, and recommendation engine that evaluates candidate actions and selects the minimum-cost intervention.

**Requirements:** INTV-01, INTV-02, INTV-03, INTV-04, INTV-05, RCMD-01, RCMD-02, RCMD-03

**UI hint**: no

**Success Criteria:**
1. At least 4 candidate actions (A0-A4) evaluated with constraint checks
2. Surrogate model estimates post-intervention quality risk for each candidate
3. Optimizer minimizes risk + λ×cost + μ×disruption subject to machine/recipe/envelope
4. Recommendation contains all 7 required fields (ACTION, WHY, EVIDENCE, EXPECTED EFFECT, CONFIDENCE, OPERATING LIMIT, RECOVERY CHECK)
5. ABSTAIN triggered at low confidence — system refuses to act

**Build days:** 27 Sep (Day 5)

---

## Phase 5: Recovery Verifier + Scrap Containment + State Machine
**Goal:** Build the post-intervention recovery verification, scrap containment logic, and the explicit system state machine that governs the complete intervention lifecycle.

**Requirements:** RECV-01, RECV-02, RECV-03, RECV-04, RECV-05, CNTN-01, CNTN-02, CNTN-03, CNTN-04, STMC-01, STMC-02

**UI hint**: no

**Success Criteria:**
1. Recovery requires stability window (not immediate claim after intervention)
2. Risk and stability recalculated from actual post-intervention data
3. Containment identifies last-known-good, suspect window, intervention/recovery/release cycles
4. State machine transitions match specification (13 states, explicit transition rules)
5. Demo can move: drift → intervention → verified recovery → production release

**Build days:** 28 Sep (Day 6)

---

## Phase 6: API + Storage Integration
**Goal:** Build the FastAPI backend with all endpoints and SQLite storage with full schema, connecting the engine components into a service layer.

**Requirements:** API-01, API-02, API-03, API-04, API-05, STOR-01, STOR-02

**UI hint**: no

**Success Criteria:**
1. All 13 API endpoints functional (3 ingestion, 3 process state, 2 quality, 4 intervention, 3 recovery/containment)
2. SQLite database with 17 tables created and populated during demo run
3. Event model uses consistent schema (event_id, machine_id, etc.)
4. Full demo scenario executable via API calls
5. Data persists across demo resets

**Build days:** 29 Sep (Day 7, AM)

---

## Phase 7: Industrial UI + Audit Trail
**Goal:** Build the 3 primary screens (Live Process, Incident Diagnosis, Intervention + Recovery) and the audit trail system that provides full evidence-chain transparency.

**Requirements:** UI-01, UI-02, UI-03, TRST-01, TRST-02, TRST-03

**UI hint**: yes

**Success Criteria:**
1. Screen 1 shows machine context, stability %, risk %, current cycle, drift status, signal bars
2. Screen 2 shows risk escalation, lead time, confidence, ranked contributors, affected window
3. Screen 3 shows candidate comparison, recommendation, apply button, recovery, containment
4. Audit trail shows full evidence chain for every intervention
5. A judge can understand the complete loop without explanation

**Build days:** 29-30 Sep (Day 7 PM - Day 8)

---

## Phase 8: Validation + Hardening + Demo Freeze
**Goal:** Run full 10-scenario validation suite, harden the system (remove unnecessary features, add deterministic demo mode, one-click reset), and freeze for demo.

**Requirements:** DEMO-01, DEMO-02, DEMO-03, SAFE-01, SAFE-02, SAFE-03, SAFE-04

**UI hint**: no

**Success Criteria:**
1. All 10 validation scenarios produce expected behavior
2. Deterministic demo mode with one-click scenario reset works
3. All synthetic values clearly labeled as prototype results
4. No PLC write-back, no recommendations outside validated limits, ABSTAIN works
5. Complete 10-step demo story runs end-to-end without manual intervention

**Build days:** 30 Sep - 1 Oct (Day 8-9), Demo 2 Oct (Day 10)

---

## Coverage Summary

| Phase | Requirements | Count |
|-------|-------------|-------|
| Phase 1 | SIM-01..05, DADP-01..03 | 8 |
| Phase 2 | FPRN-01..03, DRFT-01..04 | 7 |
| Phase 3 | QRSK-01..04, ROOT-01..03 | 7 |
| Phase 4 | INTV-01..05, RCMD-01..03 | 8 |
| Phase 5 | RECV-01..05, CNTN-01..04, STMC-01..02 | 11 |
| Phase 6 | API-01..05, STOR-01..02 | 7 |
| Phase 7 | UI-01..03, TRST-01..03 | 6 |
| Phase 8 | DEMO-01..03, SAFE-01..04 | 7 |
| **Total** | | **61** |

**Unmapped:** 0 ✓
**All v1 requirements covered** ✓

---
*Roadmap created: 2026-09-23*
*Last updated: 2026-09-23 after initial creation*
