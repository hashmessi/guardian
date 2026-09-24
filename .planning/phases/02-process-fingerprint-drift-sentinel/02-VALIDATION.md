---
phase: 2
slug: process-fingerprint-drift-sentinel
status: approved
nyquist_compliant: true
wave_0_complete: false
created: 2026-09-24
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
| 02-01-01 | 01 | 1 | FPRN-01 | unit | `pytest tests/test_fingerprint.py -k test_fingerprint_builder_and_envelope` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | FPRN-02 | unit | `pytest tests/test_fingerprint.py -k test_context_specific_baselines` | ❌ W0 | ⬜ pending |
| 02-01-03 | 01 | 1 | FPRN-03 | unit | `pytest tests/test_fingerprint.py -k test_fingerprint_storage_and_retrieval` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 2 | DRFT-01 | unit | `pytest tests/test_drift_sentinel.py -k test_statistical_drift_detectors` | ❌ W0 | ⬜ pending |
| 02-02-02 | 02 | 2 | DRFT-02 | unit | `pytest tests/test_drift_sentinel.py -k test_structured_drift_output` | ❌ W0 | ⬜ pending |
| 02-02-03 | 02 | 2 | DRFT-04 | unit | `pytest tests/test_drift_sentinel.py -k test_false_alarm_rejection_on_noise` | ❌ W0 | ⬜ pending |
| 02-03-01 | 03 | 3 | DRFT-03 | benchmark | `pytest tests/test_drift_benchmark.py -k test_lead_time_in_demo_scenario` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_fingerprint.py` — unit tests for baseline building and storage
- [ ] `tests/test_drift_sentinel.py` — unit tests for EWMA, CUSUM, Mahalanobis, and output structure
- [ ] `tests/test_drift_benchmark.py` — benchmark tests for lead-time and noise rejection

---

## Manual-Only Verifications

*None — All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 5s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-09-24
