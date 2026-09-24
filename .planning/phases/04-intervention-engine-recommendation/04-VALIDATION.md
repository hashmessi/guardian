---
phase: 4
slug: intervention-engine-recommendation
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-09-24
verified: 2026-09-24
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution of Phase 4.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `pytest tests/test_intervention_optimizer.py tests/test_recommendation.py -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~12 seconds |

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | INTV-01 | unit | `pytest tests/test_intervention_candidates.py -k test_candidate_action_generation` | ✅ | ✅ green |
| 04-01-02 | 01 | 1 | INTV-02 | unit | `pytest tests/test_intervention_candidates.py -k test_multi_constraint_boundary_checks` | ✅ | ✅ green |
| 04-02-01 | 02 | 2 | INTV-03 | unit | `pytest tests/test_intervention_optimizer.py -k test_surrogate_model_risk_prediction` | ✅ | ✅ green |
| 04-02-02 | 02 | 2 | INTV-04 | unit | `pytest tests/test_intervention_optimizer.py -k test_cost_risk_disruption_optimization` | ✅ | ✅ green |
| 04-02-03 | 02 | 2 | INTV-05 | unit | `pytest tests/test_intervention_optimizer.py -k test_candidate_comparison_table` | ✅ | ✅ green |
| 04-03-01 | 03 | 2 | RCMD-01 | unit | `pytest tests/test_recommendation.py -k test_seven_field_recommendation_contract` | ✅ | ✅ green |
| 04-03-02 | 03 | 2 | RCMD-02 | unit | `pytest tests/test_recommendation.py -k test_operator_mode_selection` | ✅ | ✅ green |
| 04-03-03 | 03 | 2 | RCMD-03 | unit | `pytest tests/test_recommendation.py -k test_mandatory_abstain_on_low_confidence` | ✅ | ✅ green |
| 04-04-01 | 04 | 3 | INTV-01..05, RCMD-01..03 | benchmark | `pytest tests/test_intervention_demo_benchmark.py -k test_demo_scenario_intervention_recommendation` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_intervention_candidates.py` — unit tests for candidate action generation & multi-constraint checks
- [x] `tests/test_intervention_optimizer.py` — unit tests for surrogate evaluation, objective minimization & comparison table
- [x] `tests/test_recommendation.py` — unit tests for 7-field contract, operator modes & ABSTAIN gate
- [x] `tests/test_intervention_demo_benchmark.py` — end-to-end benchmark on primary demo scenario
