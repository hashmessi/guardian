"""Unit tests for event injection API and causal physics transfer functions (SIM-03, SIM-04)."""

import pytest
import numpy as np
from process_guardian.simulator.engine import InjectionMoldingSimulator
from process_guardian.core.constants import NOMINAL_PP_PARAMS


def test_inject_event_api():
    """Verify that inject_event schedules and executes events at the specified cycle (SIM-03)."""
    sim = InjectionMoldingSimulator(seed=42)
    # Schedule event at cycle 420
    event = sim.inject_event("thermal_drift", cycle=420, severity=1.0)
    assert event.start_cycle == 420

    # Run up to cycle 430
    cycles = sim.run_cycles(430)
    assert len(cycles) == 430

    # Before cycle 420 (e.g. cycle 418), process is stationary healthy
    c_pre = cycles[418]  # cycle 419
    assert abs(c_pre.barrel_temp_z3 - NOMINAL_PP_PARAMS["barrel_temp_z3"]) < 1.2
    assert "thermal_drift" not in c_pre.regime

    # At cycle 420 and beyond, thermal drift is active
    c_420 = cycles[419]  # cycle 420
    assert "thermal_drift" in c_420.regime

    c_post = cycles[429]  # cycle 430 (11 cycles into drift)
    # Zone 3 temp should be noticeably higher than nominal (approx +2.0°C)
    assert c_post.barrel_temp_z3 > NOMINAL_PP_PARAMS["barrel_temp_z3"] + 1.5


def test_causal_correlations():
    """Verify causal coupling: moisture spike -> viscosity drop -> pressure reduction -> weight variance (SIM-04)."""
    sim = InjectionMoldingSimulator(seed=99)
    # Inject heavy moisture drift at cycle 10
    sim.inject_event("moisture_drift", cycle=10, severity=2.0)

    cycles = sim.run_cycles(30)

    # Initial healthy cycle (cycle 5)
    c_healthy = cycles[4]
    # Saturated moisture cycle (cycle 25)
    c_moist = cycles[24]

    # 1. Moisture should rise
    assert c_moist.material_moisture > c_healthy.material_moisture + 0.05

    # 2. Peak pressure should drop due to reduced melt flow resistance
    assert c_moist.peak_pressure < c_healthy.peak_pressure - 4.0

    # 3. Part weight should reflect shrinkage/void dynamics
    assert c_moist.part_weight < c_healthy.part_weight - 0.5


def test_event_reset_repeatability():
    """Verify that event injection schedule clears on reset() and reproduces bitwise identical data (SIM-05)."""
    sim = InjectionMoldingSimulator(seed=123)
    sim.inject_event("thermal_drift", cycle=15, severity=1.0)
    run1 = sim.run_cycles(25)

    sim.reset()
    assert len(sim.event_queue.events) == 0

    sim.inject_event("thermal_drift", cycle=15, severity=1.0)
    run2 = sim.run_cycles(25)

    for c1, c2 in zip(run1, run2):
        assert c1.cycle_index == c2.cycle_index
        assert c1.barrel_temp_z3 == c2.barrel_temp_z3
        assert c1.peak_pressure == c2.peak_pressure
        assert c1.part_weight == c2.part_weight
