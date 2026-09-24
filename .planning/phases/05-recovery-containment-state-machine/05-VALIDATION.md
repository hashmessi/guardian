---
phase: 5
slug: recovery-containment-state-machine
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-09-24
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution of Phase 5.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `pytest tests/test_state_machine.py tests/test_recovery_verifier.py tests/test_scrap_containment.py -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~14 seconds |

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | STMC-01 | unit | `pytest tests/test_state_machine.py -k test_state_machine_transition_lifecycle` | ✅ exists | ✅ green |
| 05-01-02 | 01 | 1 | STMC-02 | unit | `pytest tests/test_state_machine.py -k test_state_machine_explicit_code_architecture` | ✅ exists | ✅ green |
| 05-02-01 | 02 | 2 | RECV-01 | unit | `pytest tests/test_recovery_verifier.py -k test_parameter_movement_confirmation` | ✅ exists | ✅ green |
| 05-02-02 | 02 | 2 | RECV-02 | unit | `pytest tests/test_recovery_verifier.py -k test_dynamic_telemetry_and_risk_recomputation` | ✅ exists | ✅ green |
| 05-02-03 | 02 | 2 | RECV-03 | unit | `pytest tests/test_recovery_verifier.py -k test_stability_window_enforcement` | ✅ exists | ✅ green |
| 05-02-04 | 02 | 2 | RECV-04 | unit | `pytest tests/test_recovery_verifier.py -k test_quality_contract_release_verification` | ✅ exists | ✅ green |
| 05-02-05 | 02 | 2 | RECV-05 | unit | `pytest tests/test_recovery_verifier.py -k test_structured_recovery_status_output` | ✅ exists | ✅ green |
| 05-03-01 | 03 | 2 | CNTN-01 | unit | `pytest tests/test_scrap_containment.py -k test_last_known_good_identification` | ✅ exists | ✅ green |
| 05-03-02 | 03 | 2 | CNTN-02 | unit | `pytest tests/test_scrap_containment.py -k test_suspect_window_boundary_calculation` | ✅ exists | ✅ green |
| 05-03-03 | 03 | 2 | CNTN-03 | unit | `pytest tests/test_scrap_containment.py -k test_milestone_cycles_tracking` | ✅ exists | ✅ green |
| 05-03-04 | 03 | 2 | CNTN-04 | unit | `pytest tests/test_scrap_containment.py -k test_production_disposition_partitioning` | ✅ exists | ✅ green |
| 05-04-01 | 04 | 3 | Full Phase 5 | benchmark | `pytest tests/test_closed_loop_e2e_benchmark.py -k test_full_primary_demo_scenario_closed_loop` | ✅ exists | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_state_machine.py` — unit tests for 13-state transitions and explicit code state machine
- [x] `tests/test_recovery_verifier.py` — unit tests for parameter movement, stability window, and recovery report
- [x] `tests/test_scrap_containment.py` — unit tests for last-known-good, suspect window, and batch disposition
- [x] `tests/test_closed_loop_e2e_benchmark.py` — end-to-end benchmark verifying complete closed-loop lifecycle from drift through verified release
