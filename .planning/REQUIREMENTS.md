# Requirements: Process Guardian

**Defined:** 2026-09-23
**Core Value:** Complete closed-loop intervention decision system — detect drift → diagnose → evaluate constrained actions → recommend minimum-cost intervention → verify recovery → contain affected production

## v1 Requirements

Requirements for October 2 prototype demo. Each maps to roadmap phases.

### Simulator

- [x] **SIM-01**: System can generate realistic cycle-level telemetry with correlated process variables (temperature, pressure, cycle time, moisture, part weight)
- [x] **SIM-02**: System supports deterministic baseline regimes (healthy, thermal drift, pressure drift, moisture drift, cycle instability, combined drift, sensor noise, recovery, unseen drift)
- [x] **SIM-03**: Operator can inject specific events at specific cycle numbers via `inject_event("thermal_drift", cycle=420)` API
- [x] **SIM-04**: Simulator produces correlated causal-like relationships (moisture ↑ → melt behavior → pressure shift → cycle variation → quality variance)
- [x] **SIM-05**: Demo scenario is deterministic and fully repeatable with one-click reset

### Data Adapter

- [x] **DADP-01**: System normalizes units, timestamps, and sequences cycles from simulator telemetry
- [x] **DADP-02**: System validates signal ranges and flags missing signals
- [x] **DADP-03**: System attaches machine/mold/recipe/material context to each cycle record

### Process Fingerprint

- [x] **FPRN-01**: System builds context-specific baseline (machine + mold + part + recipe + material + environment) using rolling distributions and operating envelope
- [x] **FPRN-02**: System avoids global thresholds — learns what normal looks like for each production context
- [x] **FPRN-03**: System stores and retrieves fingerprints per production context

### Drift Detection

- [x] **DRFT-01**: System detects process-state change (not merely threshold violation) using EWMA, CUSUM, rolling mean/variance, slope/trend, multivariate distance
- [x] **DRFT-02**: System produces structured drift output: drift boolean, severity score, lead-cycle count, contributing signal list
- [x] **DRFT-03**: System detects injected drift before Quality Contract violation in the primary demo scenario
- [x] **DRFT-04**: System avoids false drift alerts on healthy/noisy data

### Quality Risk

- [x] **QRSK-01**: System produces calibrated quality risk probability (0-1) with confidence score using XGBoost/LightGBM
- [x] **QRSK-02**: System uses temporal feature engineering (current value, rolling mean/std, trend/slope, delta from fingerprint, lag features, interaction features, process-phase features, material moisture, machine context)
- [x] **QRSK-03**: System evaluates risk against a defined Quality Contract (part-specific targets and tolerances)
- [x] **QRSK-04**: System classifies risk state (LOW / MEDIUM / HIGH) with corresponding operator modes

### Root Cause

- [x] **ROOT-01**: System provides ranked likely contributors with percentage contribution (e.g., Temperature 68%, Pressure 21%, Cycle 8%, Other 3%)
- [x] **ROOT-02**: System provides supporting evidence for each contributor (variance changes, distribution shifts, similar past events)
- [x] **ROOT-03**: System uses honest language: "likely contributor", "evidence", "modeled effect", "confidence" — never "guaranteed cause"

### Intervention

- [ ] **INTV-01**: System evaluates at least 4 candidate actions (A0: continue monitoring, A1: temperature adjustment, A2: pressure adjustment, A3: cycle/process adjustment, A4: material inspection/check)
- [ ] **INTV-02**: Every candidate action is checked against operating envelope, recipe limits, max permitted parameter delta, machine safety bounds, intervention policy
- [ ] **INTV-03**: System uses surrogate model (learned response surface / constrained regression) to estimate post-intervention quality risk for each candidate
- [ ] **INTV-04**: System optimizes minimize(predicted_quality_risk + λ×intervention_cost + μ×process_disruption) subject to machine/recipe/envelope constraints
- [ ] **INTV-05**: System outputs comparison table (Do nothing → X% risk, Pressure → Y% risk, Temperature → Z% risk, etc.) with recommended action

### Recommendation

- [ ] **RCMD-01**: Every recommendation contains: ACTION, WHY, EVIDENCE, EXPECTED EFFECT, CONFIDENCE, OPERATING LIMIT, RECOVERY CHECK
- [ ] **RCMD-02**: System supports 3 operator modes — HIGH CONFIDENCE → recommend action; MEDIUM → request additional QC sample; LOW → ABSTAIN + monitor
- [ ] **RCMD-03**: ABSTAIN is a product feature — system must refuse to act when confidence is low

### Recovery

- [ ] **RECV-01**: After intervention, system confirms parameter movement in expected direction
- [ ] **RECV-02**: System re-evaluates drift and recomputes quality risk post-intervention
- [ ] **RECV-03**: System checks stability window (not immediate release — verifies sustained recovery)
- [ ] **RECV-04**: System verifies Quality Contract conditions before releasing production
- [ ] **RECV-05**: System produces recovery status output: risk before/after, stability before/after, recovery status (VERIFIED/FAILED), release decision

### Containment

- [ ] **CNTN-01**: System identifies last-known-good cycle
- [ ] **CNTN-02**: System identifies suspect window (potentially affected cycles between drift detection and recovery)
- [ ] **CNTN-03**: System identifies intervention cycle, recovery cycle, and release cycle
- [ ] **CNTN-04**: System answers "which production should we inspect, quarantine, or release?"

### State Machine

- [ ] **STMC-01**: System implements explicit state machine: HEALTHY → DRIFT_SUSPECTED → DRIFT_CONFIRMED → QUALITY_RISK_HIGH → DIAGNOSING → INTERVENTION_EVALUATION → (ABSTAIN|QC_REQUIRED|RECOMMEND) → APPLIED → RECOVERY_CHECK → (FAILED→REASSESS|VERIFIED→RELEASE) → INTERVENTION_MEMORY
- [ ] **STMC-02**: State machine exists explicitly in code, not hidden inside UI logic

### API

- [ ] **API-01**: FastAPI ingestion endpoints: POST /api/cycles, POST /api/events, POST /api/checkpoints
- [ ] **API-02**: Process state endpoints: GET /api/process/current, GET /api/process/fingerprint, GET /api/process/drift
- [ ] **API-03**: Quality endpoints: GET /api/quality/risk, GET /api/quality/contract
- [ ] **API-04**: Intervention endpoints: POST /api/interventions/simulate, GET /api/interventions/recommendation, POST /api/interventions/apply-demo, GET /api/interventions/history
- [ ] **API-05**: Recovery/containment endpoints: GET /api/recovery/status, GET /api/containment/window, POST /api/containment/release

### Storage

- [ ] **STOR-01**: SQLite database with tables: machines, molds, parts, recipes, materials, cycles, process_fingerprints, quality_contracts, drift_events, quality_predictions, intervention_candidates, intervention_recommendations, intervention_applications, recovery_events, containment_windows, checkpoints, audit_log
- [ ] **STOR-02**: Event model uses consistent event object schema (event_id, machine_id, mold_id, part_id, recipe_id, cycle_id, timestamp, event_type, severity, signals, quality_risk, confidence)

### UI

- [ ] **UI-01**: Screen 1 — Live Process: shows machine/mold/part/recipe context, process stability %, quality risk %, current cycle, drift status, and signal bars (temperature, pressure, moisture, cycle time)
- [ ] **UI-02**: Screen 2 — Incident Diagnosis: shows risk escalation (3% → 72%), lead time, confidence, ranked contributors with percentages, affected cycle window
- [ ] **UI-03**: Screen 3 — Intervention + Recovery: shows candidate actions with risk percentages, recommended action with expected effect and envelope compliance, "Apply Demo Intervention" button, recovery verification (risk before/after, stability before/after, release status)

### Trust & Audit

- [ ] **TRST-01**: Every event creates auditable chain: signal change → drift evidence → risk estimate → cause evidence → candidate actions → selected action → expected outcome → observed outcome → recovery decision → production disposition
- [ ] **TRST-02**: Audit log stored in database
- [ ] **TRST-03**: Operator can answer: What happened? Why did the system act? What did it recommend? What changed? Did recovery occur? Which cycles were exposed?

### Demo

- [ ] **DEMO-01**: Complete 10-step demo story: healthy production → hidden drift → early warning → quality risk escalation → root-cause evidence → candidate interventions → minimum-cost recommendation → recovery verification → scrap containment/release → economic interpretation
- [ ] **DEMO-02**: One-click scenario reset for deterministic replay
- [ ] **DEMO-03**: All synthetic/modelled values clearly labeled as prototype results

### Safety

- [ ] **SAFE-01**: Read-only machine integration — no automatic PLC write-back
- [ ] **SAFE-02**: No recommendation outside validated operating limits
- [ ] **SAFE-03**: No forced action when confidence is low — ABSTAIN mandatory
- [ ] **SAFE-04**: All interventions are simulated/demo-applied only

## v2 Requirements

Deferred to post-October-2 releases. Tracked but not in current roadmap.

### V1.1 — Real Plant Adapter

- **PLNT-01**: OPC-UA adapter for live machine data
- **PLNT-02**: Modbus / PLC adapter
- **PLNT-03**: Retrofit sensor gateway integration
- **PLNT-04**: Real moisture measurement integration

### V1.2 — Quality Feedback Loop

- **QFDB-01**: Weighing station integration
- **QFDB-02**: Inline vision / surface QC integration
- **QFDB-03**: Dimensional inspection integration

### V1.3 — Adaptive Learning

- **ADPT-01**: Drift-triggered sample request
- **ADPT-02**: Incremental model updates
- **ADPT-03**: Machine-specific recalibration

### V1.4 — Multi-Machine

- **MULT-01**: Plant-level process fingerprinting
- **MULT-02**: Cross-machine pattern search

### V2 — Controlled Automation

- **AUTO-01**: Approved machine-control hooks
- **AUTO-02**: Policy engine with role-based authorization
- **AUTO-03**: Safety interlocks
- **AUTO-04**: Shadow-mode validation before automatic action

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Chatbot / conversational AI | Dilutes intervention focus, not core to decision loop |
| Mobile application | Web-first, desktop shop-floor display |
| ERP / CRM / blockchain integration | Enterprise integration deferred post-prototype |
| Full MES replacement | Too broad, not the product thesis |
| Broad computer vision system | Defer inline vision to V1.2 |
| Deep learning models | XGBoost/LightGBM sufficient for MVP risk |
| 20+ intervention types | 4-5 validated actions demonstrate the loop |
| Autonomous PLC write-back | Safety — requires plant-specific validation |
| Hardware-dependent demo | Software-first, simulator-driven |
| Decorative digital twin / 3D viz | Not a visualization product |
| Multi-industry support | Automotive injection-molding wedge only |
| Cloud / Postgres deployment | SQLite local-first for prototype |
| Real-time streaming (Kafka etc.) | Cycle-level batch sufficient for demo |
| Multi-language i18n | English prototype only |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| SIM-01 | Phase 1 | Pending |
| SIM-02 | Phase 1 | Pending |
| SIM-03 | Phase 1 | Pending |
| SIM-04 | Phase 1 | Pending |
| SIM-05 | Phase 1 | Pending |
| DADP-01 | Phase 1 | Pending |
| DADP-02 | Phase 1 | Pending |
| DADP-03 | Phase 1 | Pending |
| FPRN-01 | Phase 2 | Pending |
| FPRN-02 | Phase 2 | Pending |
| FPRN-03 | Phase 2 | Pending |
| DRFT-01 | Phase 2 | Pending |
| DRFT-02 | Phase 2 | Pending |
| DRFT-03 | Phase 2 | Pending |
| DRFT-04 | Phase 2 | Pending |
| QRSK-01 | Phase 3 | Pending |
| QRSK-02 | Phase 3 | Pending |
| QRSK-03 | Phase 3 | Pending |
| QRSK-04 | Phase 3 | Pending |
| ROOT-01 | Phase 3 | Pending |
| ROOT-02 | Phase 3 | Pending |
| ROOT-03 | Phase 3 | Pending |
| INTV-01 | Phase 4 | Pending |
| INTV-02 | Phase 4 | Pending |
| INTV-03 | Phase 4 | Pending |
| INTV-04 | Phase 4 | Pending |
| INTV-05 | Phase 4 | Pending |
| RCMD-01 | Phase 4 | Pending |
| RCMD-02 | Phase 4 | Pending |
| RCMD-03 | Phase 4 | Pending |
| RECV-01 | Phase 5 | Pending |
| RECV-02 | Phase 5 | Pending |
| RECV-03 | Phase 5 | Pending |
| RECV-04 | Phase 5 | Pending |
| RECV-05 | Phase 5 | Pending |
| CNTN-01 | Phase 5 | Pending |
| CNTN-02 | Phase 5 | Pending |
| CNTN-03 | Phase 5 | Pending |
| CNTN-04 | Phase 5 | Pending |
| STMC-01 | Phase 5 | Pending |
| STMC-02 | Phase 5 | Pending |
| API-01 | Phase 6 | Pending |
| API-02 | Phase 6 | Pending |
| API-03 | Phase 6 | Pending |
| API-04 | Phase 6 | Pending |
| API-05 | Phase 6 | Pending |
| STOR-01 | Phase 6 | Pending |
| STOR-02 | Phase 6 | Pending |
| UI-01 | Phase 7 | Pending |
| UI-02 | Phase 7 | Pending |
| UI-03 | Phase 7 | Pending |
| TRST-01 | Phase 7 | Pending |
| TRST-02 | Phase 7 | Pending |
| TRST-03 | Phase 7 | Pending |
| DEMO-01 | Phase 8 | Pending |
| DEMO-02 | Phase 8 | Pending |
| DEMO-03 | Phase 8 | Pending |
| SAFE-01 | Phase 8 | Pending |
| SAFE-02 | Phase 8 | Pending |
| SAFE-03 | Phase 8 | Pending |
| SAFE-04 | Phase 8 | Pending |

**Coverage:**
- v1 requirements: 61 total
- Mapped to phases: 61
- Unmapped: 0 ✓

---
*Requirements defined: 2026-09-23*
*Last updated: 2026-09-23 after initial definition*
