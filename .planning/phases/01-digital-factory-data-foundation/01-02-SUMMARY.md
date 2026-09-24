---
phase: 01-digital-factory-data-foundation
plan: 02
subsystem: simulator
tags: [simulation, causal-physics, event-injection, polymer-pvT, pytest]

requires:
  - plan: "01-01"
    provides: InjectionMoldingSimulator core engine and 9 regimes
provides:
  - Causal polymer physics transfer functions (moisture, temperature, pressure, weight couplings)
  - EventQueue and InjectionEvent scheduling architecture
  - Programmatic inject_event() API
affects: [01-04, phase-2, phase-3]

tech-stack:
  added: []
  patterns: [coupled causal state-space modeling, event interceptor pattern]

key-files:
  created:
    - src/process_guardian/simulator/physics.py
    - src/process_guardian/simulator/events.py
    - tests/test_event_injection.py
  modified:
    - src/process_guardian/simulator/engine.py

key-decisions:
  - "Coupled polymer relative melt viscosity directly to moisture ingress (-1.8/%) and effective barrel temperature (-0.012/°C)."
  - "Peak and injection pressures dynamically respond to melt viscosity changes rather than drifting independently."
  - "inject_event API supports pre-scheduled cycles as well as dynamic next-cycle triggers."

patterns-established:
  - "Active scheduled events intercept regime modifiers and pass through compute_causal_effects()."

requirements-completed: [SIM-03, SIM-04]

duration: 12min
completed: 2026-09-24
---

# Phase 01: Plan 02 Summary — Causal Physics & Event Injection API

**Polymer pvT causal dynamics and event injection scheduler implemented, enabling realistic cross-variable propagation and targeted drift injection at exact cycle counts.**

## Performance
- **Tasks:** 4 completed
- **Files created/modified:** 4
- **Verification:** 6/6 tests passed in 0.12s (`test_inject_event_api`, `test_causal_correlations`, `test_event_reset_repeatability`, plus core tests)

## Accomplishments
- Verified SIM-03: `inject_event("thermal_drift", cycle=420)` accurately activates at cycle 420 and initiates progressive drift while prior cycles remain stationary.
- Verified SIM-04: Causal correlation verified — moisture ingress directly lowers melt viscosity, reducing peak cavity pressure and inducing part weight variance and sink mark risks.
- Verified SIM-05: Reset cleans event queues and restores bitwise identical output sequence.

## Files Created/Modified
- `src/process_guardian/simulator/physics.py` - Polymer melt rheology and thermodynamic coupling equations
- `src/process_guardian/simulator/events.py` - EventQueue and InjectionEvent data structures
- `src/process_guardian/simulator/engine.py` - Integrated event queue and physics dynamic modifiers
- `tests/test_event_injection.py` - Pytest verification suite for injection and physics
