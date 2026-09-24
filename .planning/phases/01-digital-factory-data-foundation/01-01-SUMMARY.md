---
phase: 01-digital-factory-data-foundation
plan: 01
subsystem: simulator
tags: [simulation, injection-molding, numpy, pytest, deterministic-replay]

requires: []
provides:
  - InjectionMoldingSimulator stateful engine with seeded pseudo-random generation
  - Definitions and implementations for 9 baseline regimes
  - Nominal PP parameters and physical limits
  - Full suite of 18 telemetry signals per cycle
affects: [01-02, 01-03, 01-04, phase-2]

tech-stack:
  added: [numpy, pydantic, pytest]
  patterns: [stateful seeded RNG, factory pattern for regimes, reset-to-zero lifecycle]

key-files:
  created:
    - pyproject.toml
    - src/process_guardian/core/types.py
    - src/process_guardian/core/constants.py
    - src/process_guardian/simulator/regimes.py
    - src/process_guardian/simulator/engine.py
    - tests/conftest.py
    - tests/test_simulator_core.py

key-decisions:
  - "Used NumPy PCG64 default_rng for bitwise reproducible simulation across platforms."
  - "Implemented all 9 regimes with physical parameters calibrated to automotive polypropylene housing."
  - "Reset restores cycle to 0 and clears mutable history while retaining seed."

patterns-established:
  - "Regime modifiers computed via get_regime_modifiers(regime, cycle_in_regime, rng)."
  - "Simulator outputs strongly-typed RawCycleTelemetry records with physical clamping."

requirements-completed: [SIM-01, SIM-02, SIM-05]

duration: 10min
completed: 2026-09-24
---

# Phase 01: Plan 01 Summary — Simulator Core & 9 Regimes

**Deterministic injection molding simulation engine built with seeded RNG, 9 baseline operational regimes, nominal automotive PP parameters, and verified bitwise replayability.**

## Performance
- **Tasks:** 4 completed
- **Files created:** 7
- **Verification:** 3/3 tests passed in 0.10s (`test_telemetry_variables`, `test_all_regimes`, `test_deterministic_replay_and_reset`)

## Accomplishments
- Verified SIM-01: Generates cycle-level telemetry containing all 18 required process, material, and quality variables.
- Verified SIM-02: Supports all 9 operational regimes (`HEALTHY`, `THERMAL_DRIFT`, `PRESSURE_DRIFT`, `MOISTURE_DRIFT`, `CYCLE_INSTABILITY`, `COMBINED_DRIFT`, `SENSOR_NOISE`, `RECOVERY`, `UNSEEN_DRIFT`).
- Verified SIM-05: Confirmed bitwise identical repeatability across runs with `seed=777` and verified `sim.reset()` returns the system to cycle 0.

## Files Created
- `pyproject.toml` - Project dependencies, packaging, and pytest configuration
- `src/process_guardian/core/types.py` - RegimeType enum, MachineContext, and RawCycleTelemetry
- `src/process_guardian/core/constants.py` - Nominal parameters for Recipe PP-V2.1 and noise profiles
- `src/process_guardian/simulator/regimes.py` - Modifier calculations for 9 regimes
- `src/process_guardian/simulator/engine.py` - InjectionMoldingSimulator stateful runner
- `tests/conftest.py` - Standard fixtures
- `tests/test_simulator_core.py` - Pytest unit test suite
