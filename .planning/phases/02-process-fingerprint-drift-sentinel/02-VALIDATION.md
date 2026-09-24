---
phase: 2
slug: process-fingerprint-drift-sentinel
status: verified
nyquist_compliant: true
wave_0_complete: true
created: 2026-09-24
verified: 2026-09-24
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution of Phase 2.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `pytest tests/test_fingerprint.py tests/test_drift_sentinel.py -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~2 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_fingerprint.py tests/test_drift_sentinel.py -q`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd-verify-work`:** Full suite must be green (100% pass)
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | FPRN-01 | unit | `pytest tests/test_fingerprint.py -k test_fingerprint_builder_and_envelope` | ✅ Yes | ✅ green |
| 02-01-02 | 01 | 1 | FPRN-02 | unit | `pytest tests/test_fingerprint.py -k test_context_specific_baselines` | ✅ Yes | ✅ green |
| 02-01-03 | 01 | 1 | FPRN-03 | unit | `pytest tests/test_fingerprint.py -k test_fingerprint_storage_and_retrieval` | ✅ Yes | ✅ green |
| 02-02-01 | 02 | 2 | DRFT-01 | unit | `pytest tests/test_drift_sentinel.py -k test_statistical_drift_detectors` | ✅ Yes | ✅ green |
| 02-02-02 | 02 | 2 | DRFT-02 | unit | `pytest tests/test_drift_sentinel.py -k test_structured_drift_output` | ✅ Yes | ✅ green |
| 02-02-03 | 02 | 2 | DRFT-04 | unit | `pytest tests/test_drift_sentinel.py -k test_false_alarm_rejection_on_noise` | ✅ Yes | ✅ green |
| 02-03-01 | 03 | 3 | DRFT-03 | benchmark | `pytest tests/test_drift_benchmark.py -k test_lead_time_in_demo_scenario` | ✅ Yes | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_fingerprint.py` — unit tests for baseline building and storage
- [x] `tests/test_drift_sentinel.py` — unit tests for EWMA, CUSUM, Mahalanobis, and output structure
- [x] `tests/test_drift_benchmark.py` — benchmark tests for lead-time and noise rejection

---

## Validation Sign-Off

- [x] All unit tests pass locally (`pytest tests/ -v`)
- [x] Zero false positives in 120-cycle sensor noise regime
- [x] Lead time benchmark $\ge 5$ cycles verified on demo scenario (actual: 9 cycles)
- [x] Multi-regime drift detection verified across pressure, moisture, and cycle instability
- [x] Nyquist compliance intact
