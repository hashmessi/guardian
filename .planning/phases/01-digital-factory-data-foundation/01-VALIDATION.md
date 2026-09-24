---
phase: 1
slug: digital-factory-data-foundation
status: approved
nyquist_compliant: true
wave_0_complete: false
created: 2026-09-24
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `pytest tests/test_simulator_core.py tests/test_data_adapter.py -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~2 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_simulator_core.py tests/test_data_adapter.py -q`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd-verify-work`:** Full suite must be green (100% pass)
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | SIM-01 | unit | `pytest tests/test_simulator_core.py -k test_telemetry_variables` | ✅ | ✅ green |
| 01-01-02 | 01 | 1 | SIM-02 | unit | `pytest tests/test_simulator_core.py -k test_all_regimes` | ✅ | ✅ green |
| 01-01-03 | 01 | 1 | SIM-05 | unit | `pytest tests/test_simulator_core.py -k test_deterministic_replay_and_reset` | ✅ | ✅ green |
| 01-02-01 | 02 | 2 | SIM-04 | unit | `pytest tests/test_event_injection.py -k test_causal_correlations` | ✅ | ✅ green |
| 01-02-02 | 02 | 2 | SIM-03 | unit | `pytest tests/test_event_injection.py -k test_inject_event_api` | ✅ | ✅ green |
| 01-03-01 | 03 | 1 | DADP-01 | unit | `pytest tests/test_data_adapter.py -k test_normalization_and_sequencing` | ✅ | ✅ green |
| 01-03-02 | 03 | 1 | DADP-02 | unit | `pytest tests/test_data_adapter.py -k test_bounds_validation_and_missing_signals` | ✅ | ✅ green |
| 01-03-03 | 03 | 1 | DADP-03 | unit | `pytest tests/test_data_adapter.py -k test_context_enrichment` | ✅ | ✅ green |
| 01-04-01 | 04 | 3 | SIM-01..05, DADP-01..03 | integration | `pytest tests/test_digital_factory_e2e.py` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `pyproject.toml` — package metadata, pytest configuration, pythonpath setup
- [x] `tests/conftest.py` — shared fixtures for simulator seeds and mock contexts
- [x] `tests/__init__.py` — test package initialization

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
