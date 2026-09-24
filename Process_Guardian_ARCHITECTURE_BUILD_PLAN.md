# PROCESS GUARDIAN — ARCHITECTURE & BUILD PLAN
## Hack4Purpose PS02 — Locked 10/10 Product Version

**Build window:** 23 Sep 2026 → 2 Oct 2026  
**First-round preview/demo:** before 2 Oct 2026  
**Problem Statement:** PS02 — Real-time process/raw-material quality monitoring in injection molding  
**Initial industry wedge:** Automotive plastic-component manufacturing  
**Product category:** Industrial process intervention intelligence

---

# 1. EXECUTIVE LOCK

## Product

### Process Guardian

> **A vendor-neutral process intervention engine for injection molding that detects process drift before it becomes defective production, identifies the strongest evidence-backed cause, evaluates constrained corrective actions, recommends the minimum effective intervention, verifies recovery, and contains potentially affected cycles.**

## Core product question

> **“What is the smallest validated intervention we can make now to prevent the next bad cycles?”**

## PS02 alignment

PS02 explicitly identifies fluctuating barrel temperatures, injection pressures, raw-material moisture, clerical errors, inconsistent mold-release spray application, and setting drift as contributors to severe surface blemishes and 6–7% rejection, and sets an automotive target of ≤2% rejection. The solution direction calls for low-cost shop-floor sensing, moisture checks, and standardized checkpoints.

The product therefore does **not** pivot away from PS02. Automotive is the **initial application wedge explicitly embedded in PS02**.

## Strategic positioning

**Do not position as:**
- AI defect prediction
- IoT dashboard
- generic Industry 4.0 platform
- automotive analytics dashboard
- chatbot for factory operators

**Position as:**

> **A quality-decision and intervention layer above injection-molding machine data.**

---

# 2. BRUTAL COMPETITIVE LOCK

Generic monitoring is not differentiated enough.

Existing injection-molding systems already provide combinations of sensor-based process monitoring, quality prediction, OPC-UA connectivity, deviation detection, quality sorting, and closed-loop process control. Kistler documents monitoring/control using cavity pressure, temperatures and machine signals, quality prediction, OPC-UA connectivity and process/quality data management. Academic work has also demonstrated closed-loop injection-molding quality control with OPC-UA, inline measurements, predictive models and machine-parameter adjustment. Recent research also addresses operating-condition drift with drift detection and incremental model updating.

Sources:
- Kistler plastics monitoring/control: https://www.kistler.com/US/en/plastics-monitoring-and-control-systems/C00000049
- Kistler online quality prediction: https://www.kistler.com/US/en/cp/online-quality-prediction-system-comoneopredict-2824A/P0001195
- Closed-loop injection molding research: https://pmc.ncbi.nlm.nih.gov/articles/PMC9459821/
- Drift-aware dynamic quality monitoring (2025): https://www.mdpi.com/2073-4360/17/22/3025

## Therefore the differentiation is locked to the decision loop

```text
Observe
  ↓
Fingerprint
  ↓
Detect Drift
  ↓
Measure Quality Risk
  ↓
Explain Likely Cause
  ↓
Simulate Permitted Interventions
  ↓
Optimize Risk × Cost × Disruption
  ↓
Recommend One Action
  ↓
Verify Recovery
  ↓
Contain / Release Production
  ↓
Store Intervention Outcome
```

If the demo stops at **“anomaly detected”**, the product is generic.

If the demo reaches **“action selected + recovery verified + affected cycles contained”**, the product demonstrates a materially different operational workflow.

---

# 3. TARGET CUSTOMER LOCK

## Initial wedge

**Indian automotive Tier-2 / Tier-3 plastic injection molders**

### Production profile

Prioritize plants with:
- high-volume injection molding
- mixed-age or legacy machines
- recurring quality pressure from customers
- limited appetite for expensive machine replacement
- existing PLC/controller/process data where available
- quality checks that can be represented as measurable acceptance criteria

### Do not target initially

- OEM-wide enterprise transformation
- safety-critical components
- full MES replacement
- full machine-control replacement
- every plastic-processing method

The first product must solve **one narrow, expensive process problem extremely well**.

---

# 4. PRODUCT CONTRACT

## Inputs

### Process variables

- barrel temperature zones
- nozzle temperature
- injection pressure / peak pressure
- injection time
- screw position / velocity where available
- hold pressure
- hold time
- cooling time
- cycle time

### Material/environment variables

- material batch
- raw-material moisture
- ambient temperature
- ambient humidity

### Operational variables

- recipe/settings version
- operator/manual-change events
- mold-release checkpoint
- material-inspection checkpoint
- maintenance/setup events

### Quality feedback

Where available:
- part weight
- dimensions
- surface defect label
- pass/fail inspection
- inline vision output
- QC sample results

---

# 5. QUALITY CONTRACT

The system must never optimize against a vague “defect probability.”

Every monitored production context gets a **Quality Contract**.

Example prototype contract:

```yaml
part: Automotive_Housing_A
quality_features:
  part_weight:
    target_g: 42.0
    tolerance_g: 0.30
  cycle_time:
    max_s: 18.5
process_envelope:
  validated_temperature_min: <demo-calibrated>
  validated_temperature_max: <demo-calibrated>
  validated_pressure_min: <demo-calibrated>
  validated_pressure_max: <demo-calibrated>
```

All prototype numbers are **simulation parameters**, not factory claims.

Long-term Quality Contracts can support:
- weight
- dimension
- surface quality
- short-shot risk
- flash risk
- warpage
- customer-specific CTQs

---

# 6. SYSTEM ARCHITECTURE

```text
                 ┌──────────────────────────────┐
                 │      SHOP-FLOOR SOURCES      │
                 │                              │
                 │ PLC / OPC-UA / Sensors       │
                 │ Retrofit Gateway             │
                 │ Material Moisture Check      │
                 │ Operator Checkpoints         │
                 │ Quality Measurement          │
                 │ Digital Process Simulator    │
                 └──────────────┬───────────────┘
                                │
                                ▼
                 ┌──────────────────────────────┐
                 │        DATA ADAPTER          │
                 │ normalize / validate / time  │
                 │ sequence / missing signals   │
                 └──────────────┬───────────────┘
                                │
                                ▼
                 ┌──────────────────────────────┐
                 │      PROCESS FINGERPRINT     │
                 │ machine + mold + part +     │
                 │ recipe + material + context  │
                 └──────────────┬───────────────┘
                                │
                                ▼
                 ┌──────────────────────────────┐
                 │       DRIFT SENTINEL         │
                 │ EWMA / CUSUM / multivariate │
                 │ trend + change detection     │
                 └──────────────┬───────────────┘
                                │
                                ▼
                 ┌──────────────────────────────┐
                 │       QUALITY RISK ENGINE    │
                 │ temporal features + ML       │
                 │ risk + calibration           │
                 └──────────────┬───────────────┘
                                │
                                ▼
                 ┌──────────────────────────────┐
                 │      ROOT-CAUSE EVIDENCE     │
                 │ contribution + trend + past  │
                 │ event similarity             │
                 └──────────────┬───────────────┘
                                │
                                ▼
         ┌────────────────────────────────────────────────┐
         │       CONSTRAINED INTERVENTION ENGINE         │
         │                                                │
         │ candidate actions → surrogate outcomes →      │
         │ constraint checks → risk/cost optimization    │
         └────────────────────┬───────────────────────────┘
                              │
                              ▼
                 ┌──────────────────────────────┐
                 │       RECOMMENDATION         │
                 │ one permitted action         │
                 │ expected effect             │
                 │ confidence + evidence       │
                 └──────────────┬───────────────┘
                                │
                                ▼
                 ┌──────────────────────────────┐
                 │       RECOVERY VERIFIER      │
                 │ post-action drift/risk       │
                 │ stability confirmation       │
                 └──────────────┬───────────────┘
                                │
                                ▼
                 ┌──────────────────────────────┐
                 │       SCRAP CONTAINMENT      │
                 │ last-known-good / suspect    │
                 │ window / quarantine / release│
                 └──────────────┬───────────────┘
                                │
                                ▼
                 ┌──────────────────────────────┐
                 │       INTERVENTION MEMORY    │
                 │ action / context / result   │
                 │ machine-specific learning   │
                 └──────────────────────────────┘
```

---

# 7. COMPONENT SPECIFICATION

## 7.1 Data Adapter

### Responsibilities
- ingest simulator or live-like telemetry
- normalize units
- timestamp and sequence cycles
- validate ranges
- flag missing signals
- attach machine/mold/recipe/material context

### Interfaces

```text
SimulatorAdapter
OPCUAAdapter
CSVReplayAdapter
RetrofitSensorAdapter
```

### Rule

The data source may change. The core decision engine must not.

---

# 7.2 Process Fingerprint

```text
Fingerprint =
Machine
+ Mold
+ Part
+ Recipe
+ Material batch
+ Environment
+ Historical process state
+ Historical quality
```

### Purpose

Avoid global thresholds.

The system learns what **normal looks like for this production context**.

### MVP

Use:
- baseline mean/std
- rolling distributions
- operating envelope
- recent quality history

---

# 7.3 Drift Sentinel

### MVP methods

- EWMA
- CUSUM
- rolling mean/variance
- slope/trend features
- multivariate distance

### Output

```json
{
  "drift": true,
  "severity": 0.78,
  "lead_cycles": 11,
  "signals": [
    "barrel_temp_z3",
    "injection_pressure",
    "cycle_time"
  ]
}
```

### Design principle

Detect **process-state change**, not merely threshold violation.

---

# 7.4 Quality Risk Engine

### Model

Start with:
- XGBoost or LightGBM
- calibrated probabilities
- temporal feature engineering

### Features

```text
current value
rolling mean
rolling std
trend/slope
delta from fingerprint
lag features
interaction features
process-phase features
material moisture
machine context
```

### Output

```json
{
  "quality_risk": 0.72,
  "confidence": 0.93,
  "quality_contract": "Automotive_Housing_A",
  "risk_state": "HIGH"
}
```

The ML model is **not** the product. It is one component inside the decision system.

---

# 7.5 Root-Cause Evidence Engine

Required output:

```text
QUALITY RISK: 72%

Likely contributors:
Temperature instability     68%
Pressure deviation         21%
Cycle variation             8%
Other                       3%

Evidence:
- Zone-3 variance increased
- Pressure distribution shifted
- Cycle-time variance increased
- Similar fingerprint events observed
```

Avoid claiming scientifically proven causality from observational/synthetic data.

Language must remain:
- likely contributor
- evidence
- modeled effect
- confidence

Not:
- guaranteed cause
- proven causal effect

---

# 7.6 Constrained Intervention Simulator

## Purpose

Evaluate a **small, validated action set**.

### MVP actions

```text
A0 — Continue monitoring
A1 — Temperature adjustment
A2 — Pressure adjustment
A3 — Cycle/process adjustment
A4 — Material inspection/check
```

### Action constraints

Every candidate action must satisfy:
- operating envelope
- recipe limits
- max permitted parameter delta
- machine safety bounds
- intervention policy

### Surrogate model

Prototype can use:
- learned response surface
- synthetic simulator relationship
- historical event data
- constrained regression / boosted-tree response model

The prototype must call this a **constrained intervention model/simulator**, not causal AI.

---

# 7.7 Cost / Risk Optimizer

Conceptual objective:

```text
minimize:
    predicted_quality_risk
  + λ * intervention_cost
  + μ * process_disruption

subject to:
    machine limits
    recipe limits
    validated operating envelope
```

### Example output

```text
DO NOTHING       → 81% risk
PRESSURE         → 49% risk
CYCLE            → 57% risk
TEMPERATURE      → 26% risk
COMBINED         → 18% risk, but higher disruption

RECOMMENDATION:
Temperature adjustment
```

Numbers above are illustrative demo values.

---

# 7.8 Recommendation Engine

Every recommendation must contain:

```text
ACTION
WHY
EVIDENCE
EXPECTED EFFECT
CONFIDENCE
OPERATING LIMIT
RECOVERY CHECK
```

### Operator modes

```text
HIGH CONFIDENCE
→ Recommend action

MEDIUM CONFIDENCE
→ Request additional QC sample

LOW CONFIDENCE
→ ABSTAIN + monitor
```

**ABSTAIN is a product feature, not a failure state.**

---

# 7.9 Recovery Verifier

After intervention:

1. confirm parameter movement
2. re-evaluate drift
3. recompute quality risk
4. check stability window
5. verify Quality Contract conditions
6. release only after recovery criteria are met

Example:

```text
Risk                  72% → 16%
Process stability     44% → 94%
Recovery status       VERIFIED
Release                APPROVED
```

---

# 7.10 Scrap Containment Engine

This is a priority differentiator.

```text
Cycle #418 → last known good
Cycle #429 → drift begins
Cycle #430–441 → potentially affected
Cycle #442 → intervention
Cycle #446 → recovery verified
Cycle #447+ → released
```

### Output

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

The system therefore answers not only:

> “Is the process drifting?”

but also:

> “Which production should we inspect, quarantine, or release?”

---

# 8. DIGITAL FACTORY / SIMULATOR

The October 2 prototype should be **software-first**.

Do not make hardware the dependency.

## Simulator requirements

Generate realistic cycle-level telemetry with correlated behavior.

### Baseline regimes

```text
healthy
thermal drift
pressure drift
moisture drift
cycle instability
combined drift
sensor noise
recovery
unseen drift
```

### Example causal-like process relationship for simulation

```text
moisture ↑
   ↓
melt behavior changes
   ↓
pressure profile shifts
   ↓
cycle variation increases
   ↓
part-weight / quality variance rises
```

This is a **simulator relationship**, not a claim that the deployed model can infer causality from raw observations alone.

### Required control

```text
inject_event("thermal_drift", cycle=420)
inject_event("pressure_drift", cycle=510)
inject_event("moisture_drift", cycle=700)
```

The demo must be deterministic and repeatable.

---

# 9. CORE STATE MACHINE

```text
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
   ├── ABSTAIN → MONITOR
   ├── QC_REQUIRED → SAMPLE
   └── RECOMMEND
          ↓
       APPLIED
          ↓
    RECOVERY_CHECK
      ├── FAILED → REASSESS / CONTAIN
      └── VERIFIED
             ↓
          RELEASE
             ↓
      INTERVENTION_MEMORY
```

This state machine should exist explicitly in code rather than being hidden inside UI logic.

---

# 10. EVENT MODEL

Use a consistent event object.

```json
{
  "event_id": "evt_00421",
  "machine_id": "IMM_07",
  "mold_id": "MOLD_18",
  "part_id": "AUTO_HOUSING_A",
  "recipe_id": "RCP_12",
  "cycle_id": 429,
  "timestamp": "2026-09-29T10:21:14Z",
  "event_type": "PROCESS_DRIFT",
  "severity": "HIGH",
  "signals": [
    "barrel_temp_z3",
    "injection_pressure",
    "cycle_time"
  ],
  "quality_risk": 0.72,
  "confidence": 0.93
}
```

---

# 11. API SURFACE

## FastAPI MVP

### Ingestion

```text
POST /api/cycles
POST /api/events
POST /api/checkpoints
```

### Process state

```text
GET /api/process/current
GET /api/process/fingerprint
GET /api/process/drift
```

### Quality

```text
GET /api/quality/risk
GET /api/quality/contract
```

### Intervention

```text
POST /api/interventions/simulate
GET /api/interventions/recommendation
POST /api/interventions/apply-demo
GET /api/interventions/history
```

### Recovery / containment

```text
GET /api/recovery/status
GET /api/containment/window
POST /api/containment/release
```

---

# 12. DATABASE / STORAGE

## MVP

SQLite.

Tables:

```text
machines
molds
parts
recipes
materials
cycles
process_fingerprints
quality_contracts
drift_events
quality_predictions
intervention_candidates
intervention_recommendations
intervention_applications
recovery_events
containment_windows
checkpoints
audit_log
```

## Do not build cloud infrastructure first.

Cloud/Postgres can come after the vertical slice is stable.

---

# 13. UI — ONLY 3 PRIMARY SCREENS

## Screen 1 — Live Process

```text
Machine: IMM-07
Mold: MOLD-18
Part: AUTO-HOUSING-A
Recipe: RCP-12

Process Stability     96%
Quality Risk            3%
Current Cycle         #421
Drift                   NONE

Temperature   ████████
Pressure      ████████
Moisture      ███████
Cycle Time    ████████
```

## Screen 2 — Incident Diagnosis

```text
PROCESS DRIFT DETECTED

Risk: 3% → 72%
Lead time: 11 cycles
Confidence: 93%

Contributors
Temperature   68%
Pressure      21%
Cycle          8%
Other          3%

Affected window:
#430–#441
```

## Screen 3 — Intervention + Recovery

```text
CANDIDATE ACTIONS

Do nothing       81% risk
Pressure         49%
Cycle            57%
Temperature      26%
Combined         18% / high disruption

RECOMMENDED
Temperature adjustment

Expected risk reduction: modeled
Within operating envelope: YES

[ APPLY DEMO INTERVENTION ]

RECOVERY VERIFIED
Risk: 72% → 16%
Production RELEASED: #447+
```

No generic analytics wall.

---

# 14. REPOSITORY STRUCTURE

```text
process-guardian/
│
├── apps/
│   ├── api/
│   │   ├── main.py
│   │   ├── routes/
│   │   └── services/
│   └── web/
│       ├── src/
│       └── components/
│
├── engine/
│   ├── fingerprint/
│   ├── drift/
│   ├── quality/
│   ├── rootcause/
│   ├── intervention/
│   ├── recovery/
│   └── containment/
│
├── simulator/
│   ├── generator.py
│   ├── scenarios.py
│   └── injector.py
│
├── models/
│   ├── risk/
│   └── response_surface/
│
├── data/
│   ├── synthetic/
│   └── fixtures/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── scenarios/
│
├── docs/
│   ├── PRODUCT_CONTRACT.md
│   ├── ARCHITECTURE.md
│   ├── QUALITY_CONTRACT.md
│   ├── MODEL_CARD.md
│   └── DEMO_RUNBOOK.md
│
└── README.md
```

---

# 15. BUILD PLAN — 23 SEP TO 2 OCT

## 23 SEP — LOCK

### Deliver
- repository
- product contract
- architecture
- Quality Contract
- event schema
- state machine
- simulator design

### Exit condition
The team can explain the product in one sentence without saying “AI dashboard.”

---

## 24 SEP — DIGITAL FACTORY

### Build
- cycle-level simulator
- healthy baseline
- event injection
- telemetry schema
- deterministic replay

### Exit condition
A reviewer can trigger a known failure at a known cycle.

---

## 25 SEP — DRIFT SENTINEL

### Build
- EWMA
- CUSUM
- rolling statistics
- multivariate drift score
- lead-cycle detection

### Test
- healthy/noise
- gradual drift
- sudden drift
- recovery

### Exit condition
Drift detection works before quality-risk escalation in the demo scenario.

---

## 26 SEP — QUALITY RISK

### Build
- temporal features
- XGBoost/LightGBM risk model
- probability calibration
- Quality Contract evaluation
- confidence

### Exit condition
Process state produces interpretable quality risk against a defined quality contract.

---

## 27 SEP — ROOT CAUSE + INTERVENTION ENGINE

### Build
- feature contribution evidence
- action catalog
- constrained response model
- candidate simulation
- optimizer

### Exit condition
System can evaluate at least four candidate actions and select one using risk + cost + disruption constraints.

---

## 28 SEP — RECOVERY + CONTAINMENT

### Build
- intervention application simulator
- recovery verifier
- last-known-good logic
- suspect window
- release logic
- intervention memory

### Exit condition
Demo can move from drift → intervention → verified recovery → production release.

---

## 29 SEP — UI + INTEGRATION

### Build
- three primary screens
- event timeline
- evidence panel
- intervention comparison
- containment visualization
- audit trail

### Exit condition
A judge can understand the complete loop without explanation from the team.

---

## 30 SEP — VALIDATION

### Required scenario suite

| Scenario | Expected behaviour |
|---|---|
| Healthy | No intervention |
| Thermal drift | Detect + diagnose + temperature action |
| Pressure drift | Detect + diagnose + pressure action |
| Moisture drift | Material check / escalation |
| Sensor noise | Avoid false intervention |
| Combined drift | Rank contributors |
| Recovery | Verify stabilization |
| Missing signal | Lower confidence |
| Unseen drift | ABSTAIN / monitor |
| Sudden shift | Immediate containment |

### Metrics

Track prototype metrics:
- detection lead time
- false alert rate
- false intervention rate
- recovery verification rate
- containment-window accuracy
- calibration error
- abstention rate

Do not present prototype metrics as factory performance.

---

## 1 OCT — HARDEN + FREEZE

### Remove
- unnecessary features
- fake claims
- decorative AI
- brittle demo dependencies
- unsupported automation

### Add
- audit log
- evidence chain
- failure-safe behaviour
- deterministic demo mode
- offline fallback
- one-click scenario reset

### Freeze
No new product features after this point.

---

## 2 OCT — DEMO

### Demo story

```text
1. Healthy production
2. Hidden process drift
3. Early warning
4. Quality risk escalation
5. Root-cause evidence
6. Candidate interventions
7. Minimum-cost recommendation
8. Recovery verification
9. Scrap containment / release
10. Economic interpretation
```

### Closing line

> **“We do not wait for the defective part. Process Guardian detects drift, selects the minimum effective intervention within validated limits, verifies recovery, and tells the plant exactly which production is safe to release.”**

---

# 16. DEMO SCENARIO — LOCKED

## Phase 1: Healthy

```text
Process stability: 96%
Quality risk: 3%
Status: HEALTHY
```

## Phase 2: Inject hidden drift

Inject:
- temperature instability
- pressure deviation
- cycle-time variation

## Phase 3: Detect

```text
Risk: 3% → 72%
Detection lead: 11 cycles
Confidence: 93%
```

## Phase 4: Diagnose

```text
Temperature instability: 68%
Pressure deviation:      21%
Cycle variation:          8%
Other:                    3%
```

## Phase 5: Evaluate

```text
Do nothing:      81%
Pressure:        49%
Cycle:           57%
Temperature:     26%
Combined:        18% (higher disruption)
```

## Phase 6: Recommend

```text
RECOMMENDED:
Temperature adjustment

Reason:
Strongest modeled risk reduction within validated envelope with lower modeled disruption than combined action.
```

## Phase 7: Verify

```text
Risk: 72% → 16%
Stability: 44% → 94%
Recovery: VERIFIED
```

## Phase 8: Contain

```text
Last known good: #418
Potentially affected: #430–#441
Intervention: #442
Recovery: #446
Released: #447+
```

All values above are **controlled prototype simulation values**.

---

# 17. BUSINESS / ECONOMIC LAYER

Never make model accuracy the main business metric.

## Headline metric

### ₹ Prevented Scrap / Machine / Shift

Conceptual formula:

```text
Prevented Loss =
Expected Scrap Loss Without Intervention
- Expected Scrap Loss With Intervention
- Intervention Cost
```

For the prototype, label monetary outputs:

> **Simulated economic estimate — requires plant calibration before production use.**

This prevents unsupported ROI claims.

---

# 18. INDUSTRIAL TRUST MODEL

Every event creates an auditable chain:

```text
Signal change
   ↓
Drift evidence
   ↓
Risk estimate
   ↓
Cause evidence
   ↓
Candidate actions
   ↓
Selected action
   ↓
Expected outcome
   ↓
Observed outcome
   ↓
Recovery decision
   ↓
Production disposition
```

Store this in `audit_log`.

The operator must be able to answer:

> What happened?
> Why did the system act?
> What did it recommend?
> What changed?
> Did recovery occur?
> Which cycles were exposed?

---

# 19. HARD SAFETY BOUNDARIES

For October 2:

- **Read-only machine integration**
- no automatic PLC write-back
- no arbitrary parameter generation
- no recommendation outside validated limits
- no forced action when confidence is low
- ABSTAIN is mandatory
- all interventions are simulated/demo-applied

Production deployment would require plant-specific validation, safety review, controls engineering and authorization before automatic machine control.

---

# 20. WHAT MUST NOT BE BUILT

Do not build before the core loop is complete:

- chatbot
- mobile app
- ERP
- CRM
- blockchain
- generic cloud platform
- full MES
- broad computer vision system
- massive deep-learning model
- 20 intervention types
- autonomous machine-control write-back
- hardware-dependent demo
- decorative digital twin
- multi-industry support

These features dilute the central thesis.

---

# 21. ACCEPTANCE CRITERIA

The build is considered **locked / demo-ready** only when all are true:

### A. Detection

The system detects the injected drift before the Quality Contract violation in the primary demo scenario.

### B. Diagnosis

The system provides ranked evidence rather than a black-box alert.

### C. Intervention

At least four candidate actions can be evaluated under explicit constraints.

### D. Decision

The system selects one action using risk + intervention cost + disruption.

### E. Recovery

The system does not mark recovery immediately after action application; it verifies a post-action stability window.

### F. Containment

The system identifies last-known-good and potentially affected production.

### G. Trust

The system can ABSTAIN.

### H. Repeatability

The entire demo can be reset and rerun deterministically.

### I. Evidence

Every recommendation has a traceable evidence chain.

### J. Honesty

Synthetic/modelled values are clearly labeled as prototype results, not claimed factory results.

---

# 22. FINAL 10/10 PRODUCT THESIS

## One sentence

> **Process Guardian is a vendor-neutral injection-molding intervention engine that detects temperature, pressure, moisture and operational drift early, predicts quality-contract risk, evaluates constrained corrective actions, verifies recovery, and contains affected production before process drift becomes uncontrolled scrap.**

## The product is NOT the model.

The product is the **closed operational decision loop**.

## The moat is NOT the dashboard.

The future moat is the accumulated:

```text
Machine
+ Mold
+ Material
+ Recipe
+ Drift
+ Intervention
+ Outcome
+ Recovery
```

forming an **intervention memory** for each production context.

## The demo is NOT:

> “Here is our AI predicting defects.”

## The demo is:

> **“The process is drifting. Here is the evidence. Here is the quality risk. Here are the permitted interventions. Here is the lowest-disruption option. We applied it. Recovery is verified. These cycles are contained. These cycles are released.”**

---

# 23. POST-OCT-2 PRODUCT ROADMAP

Only after the core prototype is validated:

## V1.1 — Real plant adapter
- OPC-UA
- Modbus / PLC adapter
- sensor gateway
- real moisture measurement

## V1.2 — Quality feedback
- weighing station
- inline vision / surface QC
- dimensional inspection integration

## V1.3 — Adaptive learning
- drift-triggered sample request
- incremental model updates
- machine-specific recalibration

## V1.4 — Multi-machine deployment
- plant-level process fingerprinting
- intervention memory
- cross-machine pattern search

## V2 — Controlled automation
- approved machine-control hooks
- policy engine
- role-based authorization
- safety interlocks
- shadow-mode validation before automatic action

---

# 24. FINAL BUILD PRIORITY

```text
P0 — Simulator + deterministic replay
P0 — Drift Sentinel
P0 — Quality Contract + risk
P0 — Root-cause evidence
P0 — Constrained Intervention Engine
P0 — Cost/risk optimizer
P0 — Recovery verification
P0 — Scrap containment

P1 — Intervention memory
P1 — Audit trail
P1 — Industrial UI
P1 — Scenario test suite

P2 — ONNX edge packaging
P2 — OPC-UA adapter
P2 — physical sensor demo
P2 — cloud deployment
```

### Rule

> **Do not move to P1 until every P0 capability works end-to-end.**

---

# 25. FINAL STRATEGIC LOCK

**PS02 remains the problem statement.**  
**Temperature, pressure and moisture remain the core process signals.**  
**Automotive is the initial application wedge because PS02 explicitly defines an automotive rejection target.**  
**The product differentiator is intervention + recovery + containment, not monitoring alone.**  
**The prototype is software-first and vendor-neutral.**  
**The October 2 objective is a credible industrial proof-of-concept, not a feature-heavy hackathon dashboard.**

## North-star prototype metric

### **Prevented Defective Cycles → translated to ₹ Prevented Scrap / Machine / Shift**

## North-star product action

### **Minimum effective intervention**

## North-star trust mechanism

### **Evidence + constraints + recovery verification + ABSTAIN**

