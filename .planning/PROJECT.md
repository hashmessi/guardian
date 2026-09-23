# Process Guardian

## What This Is

Process Guardian is a vendor-neutral injection-molding intervention engine that detects temperature, pressure, moisture and operational drift early, predicts quality-contract risk, evaluates constrained corrective actions, recommends the minimum effective intervention, verifies recovery, and contains affected production — before process drift becomes uncontrolled scrap. Built for Indian automotive Tier-2/Tier-3 plastic injection molders under the Hack4Purpose PS02 problem statement.

## Core Value

**The closed operational decision loop: detect drift → diagnose cause → evaluate constrained interventions → recommend minimum-cost action → verify recovery → contain affected production.** If everything else fails, this complete loop — from early detection through verified recovery and scrap containment — must work end-to-end in the demo scenario.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

(None yet — ship to validate)

### Active

<!-- Current scope. Building toward these. -->

- [ ] Deterministic cycle-level process simulator with event injection
- [ ] Process Fingerprint engine (machine + mold + part + recipe + material + environment baseline)
- [ ] Drift Sentinel (EWMA, CUSUM, rolling stats, multivariate distance, lead-cycle detection)
- [ ] Quality Risk Engine (XGBoost/LightGBM, calibrated probabilities, temporal features, Quality Contract evaluation)
- [ ] Root-Cause Evidence Engine (feature contribution ranking, evidence chain, honest language)
- [ ] Constrained Intervention Simulator (4+ candidate actions, surrogate model, constraint checks)
- [ ] Cost/Risk Optimizer (risk × cost × disruption minimization under machine/recipe/envelope constraints)
- [ ] Recommendation Engine (action + why + evidence + expected effect + confidence + operating limit + recovery check)
- [ ] Recovery Verifier (post-action stability window, drift re-evaluation, Quality Contract re-check)
- [ ] Scrap Containment Engine (last-known-good, suspect window, quarantine/release logic)
- [ ] Intervention Memory (action + context + result storage, machine-specific learning)
- [ ] Core State Machine (HEALTHY → DRIFT_SUSPECTED → ... → RELEASE → INTERVENTION_MEMORY)
- [ ] FastAPI backend with ingestion, process-state, quality, intervention, recovery/containment endpoints
- [ ] SQLite storage with full schema (17 tables)
- [ ] Industrial UI — 3 primary screens (Live Process, Incident Diagnosis, Intervention + Recovery)
- [ ] Audit trail with full evidence chain
- [ ] Deterministic demo mode with one-click scenario reset
- [ ] 10-scenario validation suite (healthy, thermal/pressure/moisture drift, noise, combined, recovery, missing signal, unseen, sudden shift)

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- Chatbot — dilutes intervention focus, not core to decision loop
- Mobile app — web-first, desktop shop-floor display
- ERP/CRM/blockchain — enterprise integration deferred post-prototype
- Full MES replacement — too broad, not the product thesis
- Broad computer vision system — defer inline vision to V1.2
- Massive deep-learning model — XGBoost/LightGBM sufficient for MVP risk model
- 20+ intervention types — 4-5 validated actions for MVP (A0-A4)
- Autonomous machine-control write-back — read-only for safety, requires plant-specific validation
- Hardware-dependent demo — software-first, simulator-driven
- Decorative digital twin — not a 3D visualization product
- Multi-industry support — automotive injection-molding wedge only
- Cloud deployment — SQLite local-first, Postgres/cloud post-prototype
- OPC-UA/Modbus/PLC adapter — V1.1 post-prototype
- ONNX edge packaging — V2 scope

## Context

**Problem Statement (PS02):** Fluctuating barrel temperatures, injection pressures, raw-material moisture, clerical errors, inconsistent mold-release spray application, and setting drift contribute to severe surface blemishes and 6-7% rejection rates. Automotive target: ≤2% rejection. PS02 calls for low-cost shop-floor sensing, moisture checks, and standardized checkpoints.

**Competitive Landscape:** Kistler and academic research already provide sensor-based process monitoring, quality prediction, OPC-UA connectivity, deviation detection, quality sorting, and closed-loop process control. Generic monitoring is not differentiated. The differentiation is locked to the complete decision loop — from observation through intervention verification and production containment.

**Build Window:** 23 Sep 2026 → 2 Oct 2026. First demo before 2 Oct 2026.

**Target Customer:** Indian automotive Tier-2/Tier-3 plastic injection molders with high-volume injection molding, mixed-age/legacy machines, recurring quality pressure from customers, limited appetite for machine replacement.

**Strategic Positioning:** Quality-decision and intervention layer above injection-molding machine data. NOT AI defect prediction, IoT dashboard, generic Industry 4.0 platform, or chatbot.

**North-Star Metric:** ₹ Prevented Scrap / Machine / Shift (simulated economic estimate for prototype).

## Constraints

- **Timeline**: 10-day build window (23 Sep - 2 Oct 2026) — aggressive, requires daily exit conditions
- **Data source**: Software simulator only for prototype — no hardware dependency
- **Safety**: Read-only machine integration, no automatic PLC write-back, ABSTAIN mandatory
- **ML approach**: XGBoost/LightGBM with calibrated probabilities — no massive deep learning
- **Database**: SQLite for MVP — no cloud infrastructure first
- **Honesty**: All synthetic/modelled values clearly labeled as prototype results, never claimed factory results
- **Language**: "likely contributor", "evidence", "modeled effect", "confidence" — never "guaranteed cause" or "proven causal effect"
- **Tech stack**: Python (FastAPI backend), web frontend (React/Vite or similar), SQLite storage

## Key Decisions

<!-- Decisions that constrain future work. Add throughout project lifecycle. -->

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Software-first simulator | No hardware dependency for Oct 2 demo | — Pending |
| XGBoost/LightGBM over deep learning | Interpretable, fast, sufficient for calibrated risk with temporal features | — Pending |
| SQLite over Postgres/cloud | Local-first, zero infrastructure, sufficient for single-machine prototype | — Pending |
| 4-5 action types only (A0-A4) | Smallest validated action set that demonstrates constrained decision loop | — Pending |
| FastAPI for backend | Python ecosystem alignment with ML, fast development, typed contracts | — Pending |
| ABSTAIN as product feature | Industrial trust — system must refuse to act when confidence is low | — Pending |
| Quality Contract pattern | Every monitored context gets explicit measurable acceptance criteria, not vague "defect probability" | — Pending |
| Evidence chain over black-box | Every recommendation traceable: signal → drift → risk → cause → candidates → selected → outcome → recovery | — Pending |

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
*Last updated: 2026-09-23 after initialization*
