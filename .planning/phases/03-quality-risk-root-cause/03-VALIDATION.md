---
phase: 3
slug: quality-risk-root-cause
status: verified
nyquist_compliant: true
wave_0_complete: true
created: 2026-09-24
verified: 2026-09-24
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution of Phase 3.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `pytest tests/test_quality_risk.py tests/test_root_cause.py -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~6 seconds |

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | QRSK-02 | unit | `pytest tests/test_quality_features.py -k test_temporal_feature_extractor` | ✅ Yes | ✅ green |
| 03-01-02 | 01 | 1 | QRSK-03 | unit | `pytest tests/test_quality_features.py -k test_quality_contract_tolerances` | ✅ Yes | ✅ green |
| 03-02-01 | 02 | 2 | QRSK-01 | unit | `pytest tests/test_quality_risk.py -k test_calibrated_risk_probabilities` | ✅ Yes | ✅ green |
| 03-02-02 | 02 | 2 | QRSK-04 | unit | `pytest tests/test_quality_risk.py -k test_risk_state_classification_and_escalation` | ✅ Yes | ✅ green |
| 03-03-01 | 03 | 2 | ROOT-01 | unit | `pytest tests/test_root_cause.py -k test_ranked_contributors_sum_100` | ✅ Yes | ✅ green |
| 03-03-02 | 03 | 2 | ROOT-02 | unit | `pytest tests/test_root_cause.py -k test_supporting_evidence_generation` | ✅ Yes | ✅ green |
| 03-03-03 | 03 | 2 | ROOT-03 | unit | `pytest tests/test_root_cause.py -k test_honest_epistemic_language` | ✅ Yes | ✅ green |
| 03-04-01 | 04 | 3 | QRSK-01..04, ROOT-01..03 | benchmark | `pytest tests/test_quality_e2e.py -k test_end_to_end_demo_risk_escalation` | ✅ Yes | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_quality_features.py` — unit tests for temporal feature extraction and physics interactions
- [x] `tests/test_quality_risk.py` — unit tests for Quality Contract, calibrated probabilities, and risk states
- [x] `tests/test_root_cause.py` — unit tests for contributor attribution, 100% sum, evidence, and honest language
- [x] `tests/test_quality_e2e.py` — end-to-end integration benchmark on demo scenario progression
