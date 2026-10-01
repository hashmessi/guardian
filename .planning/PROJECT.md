# Process Guardian

## What This Is

Process Guardian is a vendor-neutral injection-molding dynamic quality reaction and containment engine that detects temperature, pressure, moisture, and operational drift early, evaluates the financial cost of waiting versus cost of acting, executes constrained corrective reactions, verifies recovery with physical quality checkpoints, and contains suspect production lots — before process drift becomes uncontrolled scrap. Built for Indian automotive Tier-2/Tier-3 plastic injection molders under the Hack4Purpose PS02 problem statement.

## Core Value

**The closed operational decision loop: detect drift → diagnose cause → evaluate cost of waiting vs cost of acting → recommend minimum-effective action → verify recovery via physical QC sample → contain affected suspect lot.** The product is judged on measurable evidence that this reaction policy prevents scrap and minimizes suspect containment compared to unmitigated production.

## Current Milestone: v1.1 Dynamic Quality Reaction & Counterfactual Evidence Engine

**Goal:** Prove to automotive industry evaluators that Process Guardian's dynamic quality reaction policy reduces modeled scrap exposure and suspect containment using real-world measured molding benchmarks, cost-of-waiting economics, and controlled counterfactual replay.

**Core Proof Pillars:**
- **Real Measured Evidence Grounding**: External industrial dataset integration (SKZ/Fraunhofer 564-part PP/ABS and 2026 automotive component study) validating process-quality relationships.
- **Controlled Counterfactual Replay**: Side-by-side comparative execution on identical process streams: Guardian OFF (Status Quo) vs Guardian ON (Process Guardian).
- **Cost of Waiting vs Cost of Acting Economics**: Mathematical evaluation of real-time financial risk ($ExpectedLoss_{wait} - Cost_{act} = DecisionValue$) justifying line intervention.
- **Post-Intervention Quality Checkpoint**: Mandatory physical CTQ verification gate (e.g. part weight / visual inspection) ensuring quality recovery before lot release.
- **Physical Scrap Containment Boundaries**: Visual and auditable containment boundaries from Last Verified Good cycle to QC release cycle.
- **Strict Epistemic Evidence Separation**: Defensible 4-level evidence chain separating external measured data, simulated digital factory dynamics, and prototype benchmark results.

## Requirements

### Validated

<!-- Shipped and confirmed valuable in Milestone v1.0 (Phases 1-8). -->

- [x] Deterministic cycle-level process simulator with event injection (Phase 1)
- [x] Process Fingerprint engine (machine + mold + part + recipe + material baseline) (Phase 2)
- [x] Drift Sentinel multi-method statistical detector (EWMA, CUSUM, Hotelling $T^2$, lead-cycle verification) (Phase 2)
- [x] Quality Risk Engine (calibrated probabilities, temporal feature extraction, Quality Contract evaluation) (Phase 3)
- [x] Root-Cause Evidence Engine (feature contribution ranking, honest epistemic evidence generator) (Phase 3)
- [x] Constrained Intervention Simulator (A0-A4 candidate actions, forward surrogate modeling) (Phase 4)
- [x] Cost/Risk Optimizer (risk × cost × disruption minimization under machine/envelope constraints) (Phase 4)
- [x] 7-Field Recommendation Contract & Mandatory ABSTAIN Safety Gate (Phase 4)
- [x] Post-Intervention Recovery Verifier (parameter shift confirmation & stability window) (Phase 5)
- [x] Scrap Containment Engine (last-known-good, suspect window, quarantine/release logic) (Phase 5)
- [x] Explicit 13-state system state machine with full transition validation (Phase 5)
- [x] Local SQLite storage schema (17 tables) with unified event bus and audit trail (Phase 6)
- [x] FastAPI REST backend (14 operational endpoints covering ingestion, state, quality, intervention, recovery, containment) (Phase 6)
- [x] Industrial UI (3 primary screens: Live Process, Incident Diagnosis, Intervention + Recovery) (Phase 7)
- [x] Automated 10-scenario operational validation suite (100% pass) (Phase 8)
- [x] Deterministic demo reset API and isolated run management (Phase 8)
- [x] Automated safety invariants continuous verification (`SAFE-01` through `SAFE-04`) (Phase 8)
- [x] Demo freeze manifesto and 10-step judge walkthrough playbook (Phase 8)

### Active

<!-- Scoped for Milestone v1.1. Building toward these. -->

- [ ] **EVID-01**: External measured injection-molding benchmark dataset adapter (e.g. SKZ/Fraunhofer 564-part PP/ABS dataset) mapping real machine/quality features.
- [ ] **EVID-02**: Grounding benchmark report comparing simulator drift dynamics against real industrial automotive study findings (non-linear moisture sensitivity, within-envelope visual scrap).
- [ ] **ECON-01**: Parametric Cost of Poor Quality (CoPQ) engine modeling resin weight, machine hourly rate, energy kWh tariff, and secondary sorting.
- [ ] **ECON-02**: Real-time Cost of Waiting vs Cost of Acting decision evaluator ($ExpectedLoss_{wait} - Cost_{act} = DecisionValue$).
- [ ] **QCHK-01**: State machine integration of `MANDATORY_QC_CHECKPOINT` requiring physical CTQ verification (weight/visual) post-parameter stabilization before `RELEASE`.
- [ ] **QCHK-02**: PS02 shop-floor operational checkpoints (recipe lock check, resin moisture batch check, mold-release spray interval tracking).
- [ ] **CRPL-01**: Controlled counterfactual replay engine running identical event streams in dual mode: Guardian OFF (Status Quo) vs Guardian ON (Intervention Policy).
- [ ] **CRPL-02**: Side-by-side counterfactual comparative evidence view displaying timeline divergence, suspect lot reduction (>75%), and avoided financial loss.
- [ ] **CNTN-01**: Physical scrap containment boundary card tracing exact cycle milestones (Last Good, Drift Start, Suspect Lot, Action Applied, Stabilized, QC Passed, Released).
- [ ] **EVID-03**: Explicit 4-level epistemic evidence audit tagging every UI element and API metric as Level 1 (Challenge), Level 2 (External Measured), Level 3 (Software Invariant), or Level 4 (Controlled Counterfactual).

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- Hardware or physical sensor rigs (DHT11, ESP32, breadboards) — prototype is software decision layer; hardware is not needed for judge evidence.
- New generic dashboards or extra sensor charts — UI is strictly an evidence canvas for decisions, not passive graphing.
- Chatbots, LLMs, or generative AI explanations — deterministic epistemic contracts and math are required for automotive auditability.
- Autonomous machine PLC write-back — safety violation; all machine adjustments remain operator-advised.
- Complex cloud microservices or message queues — local-first SQLite and in-memory replay preserve determinism and demo reliability.
- Computer vision edge cameras — downstream visual inspection is represented as a verified QC checkpoint input, not a custom camera hardware build.

## Context

**Target Customer:** Indian automotive Tier-2/Tier-3 plastic injection molders operating high-volume lines under customer quality contracts (IATF 16949 / AIAG-VDA).

**The Core Battle:** 1 Problem Statement, 20+ teams, 1 evaluation room. Competing teams will display standard sensor dashboards with arbitrary accuracy claims. Process Guardian wins by demonstrating undeniable industrial proof: real-world external molding data validation, mathematical cost-of-waiting justification, physical QC recovery verification, and side-by-side counterfactual evidence proving scrap containment.

**Epistemic Honesty:** Never claim unverified plant trials. The distinction is maintained across: (1) Challenge problem, (2) External measured industrial datasets, (3) Software invariants, and (4) Controlled counterfactual replay.

## Constraints

- **Timeline**: 4 days remaining before final evaluation.
- **Safety**: Read-only machine integration, no automatic PLC write-back, mandatory ABSTAIN gate.
- **Validation**: 100% test coverage on all new business logic; zero regressions on existing 97 tests.
- **Tech Stack**: Python (FastAPI backend), React/Vite frontend, SQLite local storage.

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
*Last updated: 2026-10-01 after initializing Milestone v1.1*
