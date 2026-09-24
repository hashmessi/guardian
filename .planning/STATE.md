# Project State: Process Guardian

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-23)

**Core value:** Complete closed-loop intervention decision system — detect drift → diagnose → evaluate constrained actions → recommend minimum-cost intervention → verify recovery → contain affected production
**Current focus:** Phase 6 — API + Storage Integration

## Current Milestone

**V1.0 — October 2 Prototype Demo**
- Total phases: 8
- Completed: 6
- Current: Phase 7 (Industrial UI + Audit Trail)
- Build window: 23 Sep - 2 Oct 2026

## Phase Status

| Phase | Name | Status |
|-------|------|--------|
| 1 | Digital Factory + Data Foundation | Complete (13/13 tests green) |
| 2 | Process Fingerprint + Drift Sentinel | Complete (21/21 tests green) |
| 3 | Quality Risk + Root-Cause Evidence | Complete (30/30 tests green) |
| 4 | Intervention Engine + Recommendation | Complete (44/44 tests green) |
| 5 | Recovery Verifier + Scrap Containment + State Machine | Complete (61/61 tests green) |
| 6 | API + Storage Integration | Complete (79/79 tests green) |
| 7 | Industrial UI + Audit Trail | Complete (Vite+React, 3 Screens, E2E Verified) |
| 8 | Validation + Hardening + Demo Freeze | Not Started |

## Key Decisions

- **Phase 1 Architecture**:
  - `01-01-PLAN.md`: Simulator Core & 9 Regimes (SIM-01, SIM-02, SIM-05)
  - `01-02-PLAN.md`: Causal Physics Dynamics & Event Injection API (SIM-03, SIM-04)
  - `01-03-PLAN.md`: Data Adapter, Normalization & Context Enrichment (DADP-01, DADP-02, DADP-03)
  - `01-04-PLAN.md`: Digital Factory Integration Harness, Scenario Runner & Verification (SIM-01..05, DADP-01..03)
- **Phase 2 Architecture**:
  - `02-01-PLAN.md`: Process Fingerprint Engine & Context Baseline Storage (FPRN-01, FPRN-02, FPRN-03)
  - `02-02-PLAN.md`: Drift Sentinel Multi-Method Statistical Engine (DRFT-01, DRFT-02, DRFT-04)
  - `02-03-PLAN.md`: Early Warning Benchmark & Lead-Cycle Verification (DRFT-03)
  - Multi-method fusion combining EWMA, tabular CUSUM, sliding linear trend ($R^2$ + slope), regularized Mahalanobis distance, and Student's t-statistic.
- **Phase 3 Architecture**:
  - `03-01-PLAN.md`: Quality Contract & 158-feature Temporal Pipeline (QRSK-02, QRSK-03)
  - `03-02-PLAN.md`: Calibrated Quality Risk Predictor & Operator Modes (QRSK-01, QRSK-04)
  - `03-03-PLAN.md`: Root Cause Attribution Engine & Honest Evidence Generator (ROOT-01, ROOT-02, ROOT-03)
  - `03-04-PLAN.md`: Phase 3 Integration Harness & Benchmark (QRSK-01..04, ROOT-01..03)
  - Calibrated probability inference via `CalibratedClassifierCV(method='sigmoid')`.
  - Exact 100.0% normalized root-cause attribution across individual signals and 4 subsystem categories.
  - Strict honest epistemic language policy banning non-empirical certainty claims.
- **Phase 4 Architecture**:
  - `04-01-PLAN.md`: Candidate Action Generation & Multi-Constraint Boundary Checks (INTV-01, INTV-02)
  - `04-02-PLAN.md`: Surrogate Response Surface Risk Modeling & Cost-Disruption Optimization (INTV-03, INTV-04, INTV-05)
  - `04-03-PLAN.md`: 7-Field Recommendation Contract, Operator Modes & Mandatory ABSTAIN Safety Gate (RCMD-01, RCMD-02, RCMD-03)
  - `04-04-PLAN.md`: End-to-End Demo Benchmark & Pipeline Integration (INTV-01..05, RCMD-01..03)
  - Evaluates at least 5 operational candidates ($A_0-A_4$) screening against 5 boundary layers: safety limits, recipe limits, fingerprint envelopes, single-step limits, and directional logic.
  - Coupled forward polymer physics surrogate preserves live feature extraction state during what-if simulations.
  - Constrained multi-objective optimization minimizing $J(A_i) = \hat{P}_{\text{risk}}(A_i) + \lambda C(A_i) + \mu D(A_i)$ subject to feasibility.
  - **Phase 5 Architecture**:
  - `05-01-PLAN.md`: Explicit System State Machine Engine (STMC-01, STMC-02)
  - `05-02-PLAN.md`: Post-Intervention Recovery Verifier (RECV-01..05)
  - `05-03-PLAN.md`: Scrap Containment Engine & Milestone Tracking (CNTN-01..04)
  - `05-04-PLAN.md`: Closed-Loop Lifecycle Orchestrator & End-to-End Demo Benchmark (Full Phase 5)
  - Explicit 13-state finite state machine in pure Python with legal transition graph verification and full chronological audit trail.
  - Recovery verification enforcing parameter shift confirmation, real-time telemetry recalculation, and a mandatory 3-cycle cooling stability window before release.
  - Scrap containment partitioning production into mutually exclusive windows: pre-drift released, suspect quarantined (cycles 432-444, ~97.1% scrap reduction), and post-recovery released.
  - **Phase 6 Architecture**:
  - `06-01-PLAN.md`: Local SQLite Storage Schema & Repository (STOR-01, STOR-02)
  - `06-02-PLAN.md`: FastAPI Core, Ingestion & Process State Endpoints (API-01, API-02)
  - `06-03-PLAN.md`: Quality Risk, Intervention & Recovery Endpoints (API-03, API-04, API-05)
  - `06-04-PLAN.md`: End-to-End Demo Benchmark & API Integration (API-01..05, STOR-01, STOR-02)
  - Complete 17-table SQLite schema with unified event bus (`GuardianEvent`) and audit logs.
  - Complete 13 REST API endpoints covering ingestion (`/cycles`, `/events`, `/checkpoints`), process state (`/process/current`, `/process/fingerprint`, `/process/drift`), quality (`/quality/risk`, `/quality/contract`), interventions (`/interventions/simulate`, `/interventions/recommendation`, `/interventions/apply-demo`, `/interventions/history`), and recovery/containment (`/recovery/status`, `/containment/window`, `/containment/release`).
  - Full end-to-end demo benchmark over HTTP and SQLite validating all state transitions, 7-field recommendation contract, and scrap containment.
- **Phase 7 Architecture**:
  - `07-01-PLAN.md`: React+Vite scaffold, Warm Parchment design tokens (`tokens.css`), AppShell 3-zone header, and TabStrip (UI-01, UI-02, UI-03).
  - `07-02-PLAN.md`: Screen 1 (Live Process) with 4 instrument envelope gauges and 5-state lifecycle pipeline; Screen 2 (Incident Diagnosis) with risk escalation, 4-detector sentinel, suspect window, ranked root cause bars, and confidence arc dial.
  - `07-03-PLAN.md`: Screen 3 (Intervention + Recovery) with candidate comparison table, 7-field recommendation card (sole Midnight Wine primary action button), closed-loop recovery panel, and collapsible 10-event immutable audit drawer with JSON export (UI-03, TRST-01..03).
  - `07-04-PLAN.md`: Backend CORS configuration, live scenario seeding, end-to-end REST API verification, and automated browser subagent validation.

## Notes

- Build window is aggressive (10 days: 23 Sep - 2 Oct 2026)
- Core operational decision loop + API + SQLite Storage layer + Industrial UI (Phases 1-7) is 100% COMPLETE and end-to-end verified!
- Demo date: 2 Oct 2026, no feature additions after 1 Oct
- All 79 backend tests passing; full frontend visual and interactive suite verified in Chrome.

---
*Last updated: 2026-09-24 after Phase 7 execution*


