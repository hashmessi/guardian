# Phase 8: Validation + Hardening + Demo Freeze — Context

## Objective
Execute the full 10-scenario validation suite, harden the system (remove unnecessary features, enforce strict safety interlocks, ensure honest prototype labelling, and add isolated deterministic demo reset), and freeze the codebase for the October 2 demonstration.

## Target Requirements
- **DEMO-01**: Complete 10-step demo story: healthy production → hidden drift → early warning → quality risk escalation → root-cause evidence → candidate interventions → minimum-cost recommendation → recovery verification → scrap containment/release → economic interpretation.
- **DEMO-02**: One-click scenario reset for deterministic replay.
- **DEMO-03**: All synthetic/modelled values clearly labeled as prototype results.
- **SAFE-01**: Read-only machine integration — no automatic PLC write-back.
- **SAFE-02**: No recommendation outside validated operating limits.
- **SAFE-03**: No forced action when confidence is low — ABSTAIN mandatory.
- **SAFE-04**: All interventions are simulated/demo-applied only.

## User Decisions & Product Locks (from Discussion)

1. **One-Click Demo Reset Architecture (DEMO-02)**:
   - Reset creates a new isolated demo run (`run_id` / session checkpoint).
   - Previous audit records in SQLite remain immutable and history-preserved; audit trail integrity is strictly preserved.
   - Dedicated "Reset Demo" button in the AppShell persistent header with instant state reload, resetting both backend orchestrator state and frontend view to pristine baseline.

2. **Scenario Test Suite Execution & Reporting (DEMO-01, 10 Scenarios)**:
   - Automated pytest suite (`tests/test_validation_scenarios_suite.py`) validating deterministic behavior across all 10 scenarios.
   - Standalone CLI runner (`python -m process_guardian.validation`) with a concise terminal scorecard and machine-readable JSON artifact output (`.planning/validation_report.json`).

3. **Economic Interpretation & Avoided Scrap Value (Step 10 of Demo Story)**:
   - Configurable modeled scrap cost defaulting to ₹450/part (standard Tier-2 automotive bracket benchmark).
   - Prominently displays: **"Modeled Avoided Scrap Value"**.
   - Clear disclosure of assumptions: `"Assumes ₹450/part defect cost · Avoided defective cycles = post-intervention preserved volume"`.
   - Savings calculated strictly from estimated avoided defective cycles, rather than every potentially exposed cycle.

4. **Safety & Honesty Invariants (SAFE-01..04, DEMO-03)**:
   - Read-only machine integration: no hardware PLC write-back mechanisms exist; all interventions require operator authorization and are executed as demo/simulation adjustments.
   - 5-layer constraint enforcement: every candidate is strictly validated against safety limits, recipe limits, fingerprint envelopes, single-step limits, and physics directional logic.
   - Mandatory ABSTAIN gate triggered whenever confidence < 0.70 or anomaly signature is unseen/unexplained.
   - Explicit disclaimers on every UI screen and backend API response: `"SIMULATION · PROTOTYPE RESULTS ONLY"`.

## 10 Validation Scenarios Catalog

| # | Scenario | Injected Condition | Expected System Behavior | Feature Verified |
|---|----------|---------------------|--------------------------|------------------|
| 1 | Healthy Baseline | Normal stationary variation (60 cycles) | Stability >= 90%, Risk <= 15%, No drift alerts, No intervention | False-positive rejection |
| 2 | Thermal Drift | Zone 3 heater runaway (+0.35°C/cycle) | Detect early (EWMA/slope), isolate Z3 temp, recommend -3°C offset, verify 3-cycle cooling recovery | Full closed loop |
| 3 | Pressure Drift | Hydraulic line leak / pressure drop (-0.5 bar/cycle) | Detect pressure drift, isolate injection pressure, recommend pressure trim, verify stabilization | Pressure drift handling |
| 4 | Moisture Drift | Resin hygroscopic absorption (+0.02% moisture/cycle) | Detect moisture trend, isolate moisture, recommend material hopper dry-cycle escalation | Material-specific path |
| 5 | Sensor Noise | Random sensor white noise (+-3 sigma spikes, no trend) | EWMA/CUSUM filters reject noise; zero false drift alerts or interventions | Noise robustness |
| 6 | Combined Drift | Simultaneous thermal and pressure drift | Multivariate Mahalanobis detects early; root-cause attribution ranks Z3 temp and pressure accurately | Multi-signal attribution |
| 7 | Sustained Recovery | Post-intervention stabilization window | Recovery verifier monitors 3 consecutive stable cycles before lot release | Recovery verifier |
| 8 | Missing Signal | Single sensor dropout / null / NaN | Imputation / graceful degradation, reduced confidence score | Sensor failure resilience |
| 9 | Unseen Drift | Unmodeled oscillation / PID hunting | Anomaly detected, confidence < 0.70 -> Mandatory ABSTAIN gate triggered | Trust boundary & safety |
| 10 | Sudden Step Shift | Instant step jump (+15°C shift) | Fast-response CUSUM alert, immediate suspect quarantine window | Fast containment path |

## Technical Plan Outline

- **08-01-PLAN**: 10-Scenario Validation Suite & CLI Scorecard Runner (All 10 scenarios implemented and automated via pytest and CLI with machine-readable report).
- **08-02-PLAN**: Deterministic Isolated Demo Reset & Economic Avoided Scrap Engine (Backend `POST /api/demo/reset` with isolated `run_id`, immutable audit preservation, and configurable modeled avoided scrap calculation).
- **08-03-PLAN**: UI Integration & Disclaimers (AppShell "Reset Demo" button, Screen 3 economic value display with assumption callout, and comprehensive prototype disclosures).
- **08-04-PLAN**: System Hardening, Safety Interlock Verification & Demo Freeze (Comprehensive validation check, dead code pruning, automated smoke test, and demo freeze lock).
