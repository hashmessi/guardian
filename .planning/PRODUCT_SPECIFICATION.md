# PROCESS GUARDIAN — BUILD-READY PRODUCT SPECIFICATION

**Status:** LOCKED
**Author:** Principal Product Engineer (Brutal Product Engine)
**Date:** 2026-09-23
**Build Window:** 23 Sep 2026 → 2 Oct 2026

---

## 1. PRODUCT

**Process Guardian** — A vendor-neutral process intervention engine for injection molding.

Not an AI dashboard. Not a monitoring platform. Not a chatbot.

A **quality-decision and intervention layer** that sits above injection-molding machine data and completes one job: detect process drift before it becomes defective production, select the minimum effective corrective action within validated constraints, verify recovery, and contain potentially affected production.

---

## 2. TARGET USER

**Indian automotive Tier-2 / Tier-3 plastic injection molders**

### Profile
| Attribute | Value |
|-----------|-------|
| Industry | Automotive plastic components |
| Scale | High-volume injection molding |
| Machines | Mixed-age, legacy, limited digitization |
| Quality pressure | Customer-driven, OEM rejection targets |
| Budget | Limited appetite for machine replacement |
| Data availability | PLC/controller/process data where available |
| Quality workflow | Measurable acceptance criteria exist |

### Primary Persona: Process/Quality Engineer
- Monitors 2-8 injection molding machines per shift
- Currently reacts to defects after they appear
- Has domain knowledge of process relationships but limited analytical tooling
- Needs actionable recommendations, not dashboards

### NOT targeting (initially)
- OEM-wide enterprise transformation
- Safety-critical components
- Full MES/machine-control replacement
- Every plastic-processing method

---

## 3. CORE PROBLEM

**6-7% rejection rates in automotive injection molding** due to:
- Fluctuating barrel temperatures
- Injection pressure drift
- Raw-material moisture variation
- Clerical/operator errors
- Inconsistent mold-release spray
- Setting drift over production runs

**Current state:** Operators detect quality problems **after** defective parts are produced. Intervention is reactive, late, and unstructured. There is no system that connects process drift detection to constrained corrective action evaluation to recovery verification to production containment in a single operational loop.

**PS02 target:** ≤2% rejection (from current 6-7%).

---

## 4. VALUE PROPOSITION

> **"What is the smallest validated intervention we can make now to prevent the next bad cycles?"**

Process Guardian does not wait for the defective part. It:
1. Detects process drift **before** Quality Contract violation
2. Explains the **likely cause** with ranked evidence
3. Evaluates **constrained corrective actions** (only actions within validated operating limits)
4. Recommends the **minimum-cost, minimum-disruption** intervention
5. **Verifies recovery** through a stability window
6. **Contains** potentially affected production (inspect/quarantine/release)

**Differentiation:** Every competitor stops at "anomaly detected." Process Guardian completes the loop through **action selection + recovery verification + affected-cycle containment**.

---

## 5. PRIMARY USER JOURNEY

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        PROCESS GUARDIAN — USER JOURNEY                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. HEALTHY PRODUCTION                                                  │
│     Operator sees: Stability 96%, Risk 3%, Status HEALTHY               │
│     Action: None required                                               │
│                                                                         │
│  2. EARLY WARNING                                                       │
│     System detects: Temperature instability + pressure deviation        │
│     Operator sees: Risk 3% → 72%, Lead time 11 cycles                  │
│     Action: Alert acknowledged                                          │
│                                                                         │
│  3. DIAGNOSIS                                                           │
│     System shows: Temperature 68%, Pressure 21%, Cycle 8%, Other 3%    │
│     Operator sees: Ranked evidence, affected window #430-#441          │
│     Action: Review evidence                                             │
│                                                                         │
│  4. INTERVENTION OPTIONS                                                │
│     System shows: Do nothing 81%, Pressure 49%, Cycle 57%,             │
│                   Temperature 26%, Combined 18% (high disruption)       │
│     Operator sees: Recommendation = Temperature adjustment              │
│     Action: Clicks "Apply Demo Intervention"                            │
│                                                                         │
│  5. RECOVERY VERIFICATION                                               │
│     System checks: Parameter movement + stability window                │
│     Operator sees: Risk 72% → 16%, Stability 44% → 94%                │
│     Action: Views VERIFIED status                                       │
│                                                                         │
│  6. PRODUCTION DISPOSITION                                              │
│     System shows: Last good #418, Suspect #430-441, Released #447+     │
│     Operator sees: Clear containment window                             │
│     Action: Quarantine suspect cycles, release good production          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Journey duration:** Seconds-to-minutes from drift detection to verified recovery.
**Key insight:** Operator is never left at "anomaly detected" — always guided to action + verification.

---

## 6. CORE FEATURES (with INPUT / PROCESS / OUTPUT / SUCCESS / FAILURE)

### F1: Digital Factory Simulator

**INPUT:**
- Scenario configuration (regime type, injection event, cycle number)
- Process variable baselines (temperature zones, pressure, cycle time, moisture)

**PROCESS:**
- Generate correlated cycle-level telemetry
- Apply causal-like relationships (moisture ↑ → pressure shift → cycle variation → quality variance)
- Support 9 baseline regimes (healthy, thermal/pressure/moisture drift, cycle instability, combined drift, sensor noise, recovery, unseen drift)
- Deterministic replay with seeded randomness

**OUTPUT:**
- Cycle-level telemetry stream with all process variables
- Correlated quality outcomes (part weight, defect probability)
- Injection event markers

**SUCCESS CONDITION:**
- A reviewer can trigger a known failure at a known cycle
- Demo scenario is fully deterministic and repeatable
- `inject_event("thermal_drift", cycle=420)` produces consistent results across runs

**FAILURE CONDITION:**
- Non-deterministic output across replays
- Uncorrelated variables (temperature drifts but pressure/quality don't respond)
- Unable to produce specific failure at specific cycle

---

### F2: Process Fingerprint Engine

**INPUT:**
- Cycle telemetry stream
- Machine/mold/part/recipe/material context
- Historical process data

**PROCESS:**
- Compute baseline mean/std per production context
- Build rolling distributions and operating envelope
- Track recent quality history
- Avoid global thresholds — learn per-context normal

**OUTPUT:**
- Fingerprint object: {machine, mold, part, recipe, material, environment, baseline_stats, operating_envelope, quality_history}

**SUCCESS CONDITION:**
- Different machine+mold+recipe combinations produce different fingerprints
- Fingerprint accurately represents "normal" for that production context
- Operating envelope boundaries derived from actual data, not hardcoded

**FAILURE CONDITION:**
- Single global threshold applied to all contexts
- Fingerprint does not update with new data
- Same fingerprint for materially different production setups

---

### F3: Drift Sentinel

**INPUT:**
- Current cycle telemetry
- Process Fingerprint (baseline reference)
- Historical cycle data (rolling window)

**PROCESS:**
- Apply EWMA (Exponentially Weighted Moving Average)
- Apply CUSUM (Cumulative Sum Control Chart)
- Compute rolling mean/variance
- Compute slope/trend features
- Compute multivariate distance from fingerprint
- Determine lead-cycle count (how many cycles before quality violation)

**OUTPUT:**
```json
{
  "drift": true,
  "severity": 0.78,
  "lead_cycles": 11,
  "signals": ["barrel_temp_z3", "injection_pressure", "cycle_time"]
}
```

**SUCCESS CONDITION:**
- Drift detected **before** Quality Contract violation in demo scenario
- No false drift alerts on healthy/noisy data
- Gradual drift detected with ≥5 cycles lead time
- Sudden shift detected within 1-2 cycles

**FAILURE CONDITION:**
- Drift detected only after quality violation (too late)
- False alarms on normal process noise
- Unable to distinguish gradual drift from sudden shift

---

### F4: Quality Risk Engine

**INPUT:**
- Current process state (cycle telemetry + drift status)
- Temporal features (rolling mean/std, trend, delta-from-fingerprint, lags, interactions)
- Quality Contract (part-specific targets and tolerances)
- Material context (moisture, batch)

**PROCESS:**
- Feature engineering: 10+ temporal feature categories
- XGBoost/LightGBM inference with calibrated probability output
- Evaluate against Quality Contract thresholds
- Classify risk state (LOW / MEDIUM / HIGH)

**OUTPUT:**
```json
{
  "quality_risk": 0.72,
  "confidence": 0.93,
  "quality_contract": "Automotive_Housing_A",
  "risk_state": "HIGH"
}
```

**SUCCESS CONDITION:**
- Risk probability is calibrated (predicted 70% = ~70% actual in test scenarios)
- Risk escalates ahead of actual quality violations
- Confidence decreases with missing signals
- Clear mapping between risk_state and operator action mode

**FAILURE CONDITION:**
- Uncalibrated probabilities (all predictions near 0.5)
- Risk does not escalate before violations
- Confidence stays high despite missing data
- Model predicts against vague "defect probability" instead of Quality Contract

---

### F5: Root-Cause Evidence Engine

**INPUT:**
- Quality risk assessment
- Feature contributions from ML model
- Current and historical process state
- Past similar event records

**PROCESS:**
- Compute feature contribution percentages (SHAP or permutation importance)
- Correlate with process trends
- Search historical events for similar fingerprint patterns
- Aggregate evidence into ranked contributor list

**OUTPUT:**
```
QUALITY RISK: 72%

Likely contributors:
Temperature instability     68%
Pressure deviation         21%
Cycle variation             8%
Other                       3%

Evidence:
- Zone-3 variance increased 3.2×
- Pressure distribution shifted +8.4 bar
- Cycle-time variance increased 2.1×
- Similar fingerprint events observed (2 prior)
```

**SUCCESS CONDITION:**
- Contributors sum to 100% (or explicitly show "Other")
- Evidence is specific and traceable to signal measurements
- Language is honest: "likely contributor", "evidence", "modeled effect"
- Never claims "guaranteed cause" or "proven causal effect"

**FAILURE CONDITION:**
- Black-box alert with no explanation
- Claims scientific causality from observational/synthetic data
- Evidence is generic ("something is wrong") not specific

---

### F6: Constrained Intervention Simulator

**INPUT:**
- Current process state and quality risk
- Root-cause evidence
- Action catalog (A0-A4)
- Constraint set (operating envelope, recipe limits, max parameter delta, machine safety bounds)

**PROCESS:**
- For each candidate action:
  - Check all constraint violations (reject if any violated)
  - Estimate post-intervention quality risk via surrogate model
  - Estimate intervention cost
  - Estimate process disruption level
- Optimize: minimize(risk + λ×cost + μ×disruption) subject to constraints

**OUTPUT:**
```
DO NOTHING       → 81% risk
PRESSURE         → 49% risk
CYCLE            → 57% risk
TEMPERATURE      → 26% risk
COMBINED         → 18% risk, but higher disruption

RECOMMENDATION: Temperature adjustment
```

**SUCCESS CONDITION:**
- At least 4 candidate actions evaluated
- No action recommended that violates operating envelope
- Recommended action has best risk/cost/disruption tradeoff
- ABSTAIN selected when no confident action available

**FAILURE CONDITION:**
- Recommendation violates operating limits
- Only one action ever recommended regardless of scenario
- ABSTAIN never triggered (system always acts)
- Optimizer ignores disruption cost

---

### F7: Recommendation Engine

**INPUT:**
- Intervention simulation results
- Root-cause evidence
- Quality risk assessment
- Confidence level

**PROCESS:**
- Select action based on optimizer output
- Package with full evidence chain
- Apply confidence threshold:
  - HIGH → Recommend action
  - MEDIUM → Request additional QC sample
  - LOW → ABSTAIN + monitor
- Assemble recommendation object

**OUTPUT:**
```
ACTION: Increase barrel zone-3 temperature by +3°C
WHY: Zone-3 instability is the strongest contributor to quality risk (68%)
EVIDENCE: Zone-3 variance 3.2× baseline, pressure shift correlated
EXPECTED EFFECT: Risk reduction from 72% to ~26% (modeled)
CONFIDENCE: 93%
OPERATING LIMIT: Zone-3 max 245°C — proposed 238°C (within limit)
RECOVERY CHECK: Monitor 5 cycles post-adjustment for stability
```

**SUCCESS CONDITION:**
- Every recommendation contains all 7 fields
- Confidence threshold gates are applied correctly
- ABSTAIN issued when confidence < threshold
- Expected effect clearly labeled as "modeled"

**FAILURE CONDITION:**
- Missing evidence or justification fields
- System recommends action at LOW confidence
- Expected effect presented as guaranteed outcome

---

### F8: Recovery Verifier

**INPUT:**
- Pre-intervention process state
- Post-intervention cycle telemetry (stability window)
- Quality Contract

**PROCESS:**
1. Confirm parameter moved in expected direction
2. Re-evaluate drift using Drift Sentinel
3. Recompute quality risk
4. Check stability window (N consecutive cycles within envelope)
5. Verify Quality Contract conditions
6. Release only after recovery criteria met

**OUTPUT:**
```
Risk                  72% → 16%
Process stability     44% → 94%
Recovery status       VERIFIED
Release               APPROVED
```

**SUCCESS CONDITION:**
- Recovery not marked immediately after action — stability window enforced
- Risk and stability recalculated from actual post-intervention data
- VERIFIED only after N stable cycles
- FAILED triggers reassessment, not blind retry

**FAILURE CONDITION:**
- Immediate recovery claim without stability window
- Recovery based on expected outcome, not actual measurement
- No path for FAILED recovery

---

### F9: Scrap Containment Engine

**INPUT:**
- Drift detection timeline (when drift started)
- Intervention timeline
- Recovery verification result
- Cycle-level production records

**PROCESS:**
- Identify last-known-good cycle (last cycle before drift)
- Identify suspect window (drift start to intervention)
- Identify intervention and recovery cycles
- Mark release cycle (first cycle after verified recovery)
- Generate containment disposition

**OUTPUT:**
```json
{
  "last_known_good": 418,
  "suspect_start": 430,
  "suspect_end": 441,
  "intervention_cycle": 442,
  "recovery_cycle": 446,
  "release_cycle": 447
}
```

**SUCCESS CONDITION:**
- Clear, non-overlapping cycle windows
- Last-known-good correctly identified from process history
- Suspect window accurately bounded
- Release only after verified recovery

**FAILURE CONDITION:**
- Suspect window includes known-good production
- No containment when drift occurred
- Release before recovery verification

---

### F10: Industrial UI (3 Screens)

**INPUT:**
- Real-time process state from API
- Intervention recommendations
- Recovery status
- Containment windows

**PROCESS:**
- Screen 1: Live dashboard — machine context, stability %, risk %, current cycle, drift status, signal bars
- Screen 2: Incident diagnosis — risk escalation, lead time, confidence, ranked contributors, affected window
- Screen 3: Intervention + Recovery — candidate comparison table, recommended action, apply button, recovery verification, containment window, release status

**OUTPUT:**
- 3 industrial-focused screens (not analytics dashboards)
- Event timeline
- Evidence panel
- Audit trail visibility

**SUCCESS CONDITION:**
- A judge can understand the complete intervention loop without explanation from the team
- No generic analytics walls — every element serves the decision loop
- Clear visual progression: healthy → drift → diagnosis → action → recovery → release

**FAILURE CONDITION:**
- Dashboard of charts without decision context
- Information overload with no action guidance
- UI disconnected from state machine transitions

---

## 7. MVP FEATURES (P0 — Must ship by Oct 2)

| Priority | Feature | Why |
|----------|---------|-----|
| P0 | Simulator + deterministic replay | Foundation — everything tests against this |
| P0 | Data Adapter | Normalization layer — decouples sources from engine |
| P0 | Process Fingerprint | Context-specific baselines — no global thresholds |
| P0 | Drift Sentinel | Core detection — early warning before quality violation |
| P0 | Quality Risk Engine | Risk quantification — calibrated probability + Quality Contract |
| P0 | Root-Cause Evidence | Explainability — ranked contributors with honest language |
| P0 | Constrained Intervention Simulator | Decision engine — evaluate 4+ actions under constraints |
| P0 | Cost/Risk Optimizer | Selection — minimum effective intervention |
| P0 | Recovery Verifier | Verification — stability window, not instant claim |
| P0 | Scrap Containment | Disposition — which cycles to inspect/quarantine/release |

## 8. P1 FEATURES (Build after all P0 complete)

| Priority | Feature | Why |
|----------|---------|-----|
| P1 | Intervention Memory | Learning — action/context/result storage per machine |
| P1 | Audit Trail | Trust — full evidence chain in database |
| P1 | Industrial UI (3 screens) | Presentation — demo visualization layer |
| P1 | Scenario Test Suite | Validation — 10 scenarios with expected behaviors |

## 9. OUT-OF-SCOPE FEATURES

See [REQUIREMENTS.md](file:///c:/Users/Hashvanth/Hack4purpose/.planning/REQUIREMENTS.md) § Out of Scope for full list with reasoning.

**Hard boundary:** Do not build chatbot, mobile app, ERP/CRM, blockchain, full MES, broad vision system, deep learning, 20+ interventions, autonomous PLC write-back, hardware-dependent demo, decorative digital twin, multi-industry support, cloud infra, or real-time streaming.

---

## 10. USER STATES

| State | Description | System Behavior |
|-------|-------------|-----------------|
| Observing | Operator monitoring healthy production | Show green indicators, stability %, low risk |
| Alerted | Drift detected, operator notified | Show risk escalation, lead time, switch to Diagnosis screen |
| Investigating | Operator reviewing evidence | Show ranked contributors, evidence details, affected window |
| Deciding | Operator reviewing intervention options | Show candidate comparison, recommendation, constraints |
| Acting | Operator applying recommended intervention | Execute demo intervention, transition to recovery monitoring |
| Verifying | Operator waiting for recovery confirmation | Show stability window progress, risk trajectory |
| Dispositioning | Operator reviewing containment | Show cycle windows, quarantine/release decisions |
| Reviewing | Operator reviewing audit trail | Show full evidence chain for past interventions |

---

## 11. SYSTEM STATES (Explicit State Machine)

```
HEALTHY
   ↓
DRIFT_SUSPECTED
   ↓
DRIFT_CONFIRMED
   ↓
QUALITY_RISK_HIGH
   ↓
DIAGNOSING
   ↓
INTERVENTION_EVALUATION
   ├── ABSTAIN → MONITOR (return to observation with elevated alertness)
   ├── QC_REQUIRED → SAMPLE (request operator quality check)
   └── RECOMMEND
          ↓
       APPLIED
          ↓
    RECOVERY_CHECK
      ├── FAILED → REASSESS / CONTAIN (re-enter evaluation or escalate)
      └── VERIFIED
             ↓
          RELEASE
             ↓
      INTERVENTION_MEMORY (store outcome for future learning)
```

**Transition rules:**
- HEALTHY → DRIFT_SUSPECTED: any drift signal exceeds detection threshold
- DRIFT_SUSPECTED → DRIFT_CONFIRMED: drift persists for N consecutive cycles
- DRIFT_CONFIRMED → QUALITY_RISK_HIGH: risk exceeds risk threshold
- QUALITY_RISK_HIGH → DIAGNOSING: automatic (immediate root-cause analysis)
- DIAGNOSING → INTERVENTION_EVALUATION: root-cause evidence assembled
- INTERVENTION_EVALUATION → ABSTAIN: confidence < low threshold
- INTERVENTION_EVALUATION → QC_REQUIRED: confidence medium, need more data
- INTERVENTION_EVALUATION → RECOMMEND: confidence ≥ high threshold
- RECOMMEND → APPLIED: operator clicks "Apply Demo Intervention"
- APPLIED → RECOVERY_CHECK: automatic (begin post-intervention monitoring)
- RECOVERY_CHECK → FAILED: stability window not met within timeout
- RECOVERY_CHECK → VERIFIED: N consecutive stable cycles within envelope
- VERIFIED → RELEASE: Quality Contract conditions satisfied
- RELEASE → INTERVENTION_MEMORY: automatic (store outcome)

---

## 12. FAILURE STATES

| Failure State | Trigger | System Response | Recovery Path |
|---------------|---------|-----------------|---------------|
| SENSOR_MISSING | Required signal absent from telemetry | Lower confidence, flag in UI, continue with available data | Operator checks sensor connection |
| CALIBRATION_STALE | Fingerprint baseline too old or too few samples | Warn operator, reduce confidence, suggest recalibration | Collect more baseline cycles |
| MODEL_UNCERTAIN | Risk model confidence below acceptable threshold | ABSTAIN — refuse to recommend, suggest monitoring | Collect more data or request QC sample |
| RECOVERY_FAILED | Post-intervention stability window not met | Re-enter DIAGNOSING with updated state, expand containment | Reassess root cause, try different action |
| CONSTRAINT_VIOLATION | All candidate actions violate operating limits | ABSTAIN — no safe action available, alert operator for manual assessment | Operator manual intervention or process stop |
| INTERVENTION_CONFLICT | Multiple simultaneous drift events with conflicting actions | Prioritize highest-risk contributor, defer secondary | Resolve primary before addressing secondary |
| SIMULATOR_DESYNC | Simulator state inconsistent with expected (demo mode) | Reset to last known checkpoint | One-click scenario reset |
| DB_WRITE_FAILURE | SQLite write fails (disk full, lock contention) | Buffer events in memory, retry, alert if persistent | Free disk space, restart |

**Critical design principle:** Every failure state has a defined response. The system never crashes silently or produces undefined behavior.

---

## 13. DATA REQUIREMENTS

### Process Variables (per cycle)
| Variable | Type | Unit | Source | Required |
|----------|------|------|--------|----------|
| barrel_temp_z1-z5 | float | °C | PLC/Simulator | Yes |
| nozzle_temp | float | °C | PLC/Simulator | Yes |
| injection_pressure | float | bar | PLC/Simulator | Yes |
| peak_pressure | float | bar | PLC/Simulator | Optional |
| injection_time | float | seconds | PLC/Simulator | Yes |
| screw_position | float | mm | PLC/Simulator | Optional |
| hold_pressure | float | bar | PLC/Simulator | Yes |
| hold_time | float | seconds | PLC/Simulator | Yes |
| cooling_time | float | seconds | PLC/Simulator | Yes |
| cycle_time | float | seconds | PLC/Simulator | Yes |

### Material/Environment Variables
| Variable | Type | Unit | Source | Required |
|----------|------|------|--------|----------|
| material_batch | string | — | Operator/Scanner | Yes |
| material_moisture | float | % | Moisture meter/Sim | Yes |
| ambient_temp | float | °C | Environment sensor/Sim | Optional |
| ambient_humidity | float | % | Environment sensor/Sim | Optional |

### Operational Variables
| Variable | Type | Unit | Source | Required |
|----------|------|------|--------|----------|
| recipe_version | string | — | PLC/Config | Yes |
| operator_change_event | event | — | Operator input | Optional |
| mold_release_checkpoint | boolean | — | Operator checklist | Optional |
| material_inspection_checkpoint | boolean | — | Operator checklist | Optional |
| maintenance_event | event | — | Maintenance system | Optional |

### Quality Feedback
| Variable | Type | Unit | Source | Required |
|----------|------|------|--------|----------|
| part_weight | float | g | Scale/Sim | When available |
| dimensions | float[] | mm | CMM/Sim | When available |
| surface_defect_label | string | — | Inspector/Vision | When available |
| pass_fail | boolean | — | Inspector | When available |

### Storage: SQLite — 17 tables
machines, molds, parts, recipes, materials, cycles, process_fingerprints, quality_contracts, drift_events, quality_predictions, intervention_candidates, intervention_recommendations, intervention_applications, recovery_events, containment_windows, checkpoints, audit_log

---

## 14. AI/ML REQUIREMENTS

| Component | Approach | Why |
|-----------|----------|-----|
| Drift Detection | EWMA + CUSUM + rolling stats + multivariate distance | Statistical process control — interpretable, no training data needed initially |
| Quality Risk | XGBoost/LightGBM with calibrated probabilities | Fast training, feature importance built-in, calibration via Platt scaling |
| Root Cause | Feature contribution (SHAP/permutation importance) | Interpretable, maps directly to process variables |
| Surrogate Model | Learned response surface / constrained regression | Estimates post-intervention risk without real machine experiments |
| Optimizer | Constrained risk/cost/disruption minimization | Grid search or scipy.optimize over small action space |

**Critical constraints:**
- All probabilities must be calibrated (not raw model outputs)
- Feature importance must map to physical process variables
- The ML model is one component — not the product
- All model outputs labeled as "modeled" or "estimated"
- No claims of causality from observational/synthetic data

---

## 15. INTEGRATIONS

### MVP (Oct 2)
| Integration | Type | Protocol | Purpose |
|-------------|------|----------|---------|
| Digital Simulator | Internal | Python API | Generate synthetic telemetry |
| SQLite | Internal | SQL | Store all system data |
| FastAPI | Internal | REST/HTTP | Expose engine to UI |

### Post-MVP (V1.1+)
| Integration | Type | Protocol | Purpose |
|-------------|------|----------|---------|
| OPC-UA | External | OPC-UA client | Live machine data |
| Modbus/PLC | External | Modbus TCP | Legacy machine data |
| Retrofit sensors | External | MQTT/HTTP | Temperature, humidity, moisture |
| Weighing station | External | Serial/HTTP | Part weight measurement |
| Vision system | External | HTTP/gRPC | Surface defect detection |

---

## 16. SECURITY REQUIREMENTS

| Requirement | Implementation | Rationale |
|-------------|----------------|-----------|
| Read-only machine integration | No PLC write-back in MVP | Safety — cannot actuate machine without plant validation |
| Operating envelope enforcement | Every action checked against validated limits | Safety — no parameter outside machine-safe bounds |
| ABSTAIN capability | Mandatory refusal at low confidence | Safety — system must not force action when uncertain |
| Audit immutability | Append-only audit_log table | Trust — complete evidence chain, no retroactive editing |
| Input validation | All API inputs validated (types, ranges, required fields) | Correctness — garbage in ≠ garbage out |
| No arbitrary parameter generation | Actions from validated catalog only (A0-A4) | Safety — no ML-generated novel machine settings |
| Demo isolation | Demo interventions simulated, not forwarded to real systems | Safety — prototype cannot affect physical machines |
| Honest labeling | All outputs marked "prototype/simulated/modeled" | Trust — no false claims of factory-validated results |

---

## 17. ACCEPTANCE CRITERIA

The prototype is **demo-ready** only when ALL are true:

| # | Criterion | Verification Method |
|---|-----------|-------------------|
| A | Detection: System detects injected drift before Quality Contract violation in primary demo scenario | Run demo scenario, verify drift alert fires ≥5 cycles before quality violation |
| B | Diagnosis: System provides ranked evidence, not black-box alert | Verify contributor percentages displayed with supporting evidence text |
| C | Intervention: At least 4 candidate actions evaluated under explicit constraints | Count actions in intervention comparison table, verify constraint checks |
| D | Decision: System selects one action using risk + cost + disruption optimization | Verify recommendation includes expected risk reduction and constraint compliance |
| E | Recovery: System verifies post-action stability window (not immediate claim) | Verify ≥3 post-intervention cycles checked before VERIFIED status |
| F | Containment: System identifies last-known-good and suspect production window | Verify cycle-level containment output with correct boundaries |
| G | Trust: System can ABSTAIN when confidence is low | Run "unseen drift" scenario, verify ABSTAIN response |
| H | Repeatability: Entire demo can be reset and rerun deterministically | Reset and rerun twice, verify identical results |
| I | Evidence: Every recommendation has traceable evidence chain | Verify audit_log contains full chain for each intervention |
| J | Honesty: Synthetic/modelled values clearly labeled | Visual inspection — no value presented as factory result |

---

## 18. VALIDATION SCENARIO SUITE

| # | Scenario | Expected Behavior | Tests Feature |
|---|----------|-------------------|---------------|
| 1 | Healthy | No intervention triggered | Drift false-positive avoidance |
| 2 | Thermal drift | Detect → diagnose temperature → temperature action | Full loop |
| 3 | Pressure drift | Detect → diagnose pressure → pressure action | Full loop |
| 4 | Moisture drift | Material check / escalation | Material-specific path |
| 5 | Sensor noise | Avoid false intervention | Noise robustness |
| 6 | Combined drift | Rank multiple contributors | Multi-signal diagnosis |
| 7 | Recovery | Verify post-intervention stabilization | Recovery verifier |
| 8 | Missing signal | Lower confidence, degrade gracefully | Sensor failure handling |
| 9 | Unseen drift | ABSTAIN / monitor | Trust boundary |
| 10 | Sudden shift | Immediate containment | Fast-response path |

---

## 19. DEMO STORY (LOCKED)

```
1. Healthy production          → Stability 96%, Risk 3%, HEALTHY
2. Hidden process drift        → Temperature instability + pressure deviation injected
3. Early warning               → Risk 3% → 72%, Lead time 11 cycles, Confidence 93%
4. Quality risk escalation     → Quality Contract violation imminent
5. Root-cause evidence         → Temperature 68%, Pressure 21%, Cycle 8%, Other 3%
6. Candidate interventions     → 4 options evaluated with constraint checks
7. Minimum-cost recommendation → Temperature adjustment selected
8. Recovery verification       → Risk 72% → 16%, Stability 44% → 94%, VERIFIED
9. Scrap containment / release → Suspect #430-441, Released #447+
10. Economic interpretation    → ₹ Prevented Scrap / Machine / Shift (simulated)
```

**Closing line:**
> **"We do not wait for the defective part. Process Guardian detects drift, selects the minimum effective intervention within validated limits, verifies recovery, and tells the plant exactly which production is safe to release."**

---

## 20. BUILD PRIORITY HIERARCHY

```
P0 — Simulator + deterministic replay         (Day 1-2)
P0 — Data Adapter + Fingerprint               (Day 2-3)
P0 — Drift Sentinel                           (Day 3)
P0 — Quality Contract + Risk Engine           (Day 4)
P0 — Root-Cause Evidence                      (Day 4-5)
P0 — Constrained Intervention Engine          (Day 5)
P0 — Cost/Risk Optimizer + Recommendation     (Day 5)
P0 — Recovery Verifier                        (Day 6)
P0 — Scrap Containment                        (Day 6)

P1 — Intervention Memory + Audit Trail        (Day 7)
P1 — FastAPI + Storage Integration            (Day 7)
P1 — Industrial UI (3 screens)                (Day 7-8)
P1 — Scenario Test Suite (10 scenarios)       (Day 8)

HARDEN — Remove unnecessary features, add deterministic demo mode   (Day 9)
FREEZE — No new features after this point                           (Day 9)
DEMO — Oct 2                                                        (Day 10)
```

> **Do not move to P1 until every P0 capability works end-to-end.**

---

*SPECIFICATION STATUS: LOCKED*
*Next action: `/gsd-plan-phase 1`*
