"""Unit tests for simulator core, baseline regimes, and deterministic reset (SIM-01, SIM-02, SIM-05)."""

import pytest
import numpy as np
from process_guardian.core.types import RegimeType, RawCycleTelemetry
from process_guardian.simulator.engine import InjectionMoldingSimulator
from process_guardian.core.constants import NOMINAL_PP_PARAMS


def test_telemetry_variables():
    """Verify that all 18 required process and quality variables are present with physically valid values (SIM-01)."""
    sim = InjectionMoldingSimulator(seed=42)
    cycles = sim.run_cycles(15)
    assert len(cycles) == 15

    for cycle in cycles:
        assert isinstance(cycle, RawCycleTelemetry)
        assert cycle.cycle_index >= 1

        # Check temperatures (°C)
        assert 150.0 < cycle.barrel_temp_z1 < 300.0
        assert 160.0 < cycle.barrel_temp_z2 < 300.0
        assert 170.0 < cycle.barrel_temp_z3 < 320.0
        assert 170.0 < cycle.barrel_temp_z4 < 320.0
        assert 170.0 < cycle.barrel_temp_z5 < 320.0
        assert 180.0 < cycle.nozzle_temp < 320.0

        # Check pressures (bar)
        assert 50.0 < cycle.injection_pressure < 250.0
        assert 70.0 < cycle.peak_pressure < 300.0
        assert 20.0 < cycle.hold_pressure < 150.0

        # Check timings (s)
        assert 0.5 < cycle.injection_time < 10.0
        assert 1.0 < cycle.hold_time < 30.0
        assert 2.0 < cycle.cooling_time < 60.0
        assert 5.0 < cycle.cycle_time < 120.0

        # Check material & environmental
        assert 50.0 < cycle.part_weight < 250.0
        assert 0.001 <= cycle.material_moisture < 1.0
        assert 10.0 < cycle.ambient_temp < 50.0
        assert 10.0 <= cycle.ambient_humidity <= 95.0

        # Ground truth
        assert isinstance(cycle.defect_flag, bool)
        assert isinstance(cycle.flash_observed, bool)
        assert cycle.sink_mark_depth >= 0.0


def test_all_regimes():
    """Verify that all 9 operational regimes execute with expected statistical signatures (SIM-02)."""
    for regime in RegimeType:
        sim = InjectionMoldingSimulator(seed=100, base_regime=regime)
        cycles = sim.run_cycles(20)
        assert len(cycles) == 20
        assert all(c.regime == regime.value for c in cycles)

        if regime == RegimeType.HEALTHY:
            # Mean temperature zone 3 should stay within 0.5°C of nominal 230.0
            z3_temps = [c.barrel_temp_z3 for c in cycles]
            assert abs(np.mean(z3_temps) - NOMINAL_PP_PARAMS["barrel_temp_z3"]) < 0.5

        elif regime == RegimeType.THERMAL_DRIFT:
            # End temperature should be higher than beginning
            assert cycles[-1].barrel_temp_z3 > cycles[0].barrel_temp_z3 + 2.0

        elif regime == RegimeType.PRESSURE_DRIFT:
            # End injection pressure should be lower than beginning
            assert cycles[-1].injection_pressure < cycles[0].injection_pressure - 3.0

        elif regime == RegimeType.MOISTURE_DRIFT:
            # End moisture should be higher than beginning
            assert cycles[-1].material_moisture > cycles[0].material_moisture + 0.05

        elif regime == RegimeType.CYCLE_INSTABILITY:
            # Variance in cycle time should be elevated
            times = [c.cycle_time for c in cycles]
            assert np.std(times) > 0.8

        elif regime == RegimeType.SENSOR_NOISE:
            # Standard deviation should be elevated, while mean is near nominal
            z3_temps = [c.barrel_temp_z3 for c in cycles]
            assert np.std(z3_temps) > 1.2
            assert abs(np.mean(z3_temps) - NOMINAL_PP_PARAMS["barrel_temp_z3"]) < 1.5


def test_deterministic_replay_and_reset():
    """Verify bitwise identical repeatability across runs and after reset() (SIM-05)."""
    sim1 = InjectionMoldingSimulator(seed=777)
    sim2 = InjectionMoldingSimulator(seed=777)

    run1 = sim1.run_cycles(50)
    run2 = sim2.run_cycles(50)

    # Assert bitwise identical records across independent instances
    for c1, c2 in zip(run1, run2):
        assert c1.cycle_index == c2.cycle_index
        assert c1.barrel_temp_z3 == c2.barrel_temp_z3
        assert c1.injection_pressure == c2.injection_pressure
        assert c1.part_weight == c2.part_weight

    # Assert reset restores identical sequence
    sim1.reset()
    assert sim1.current_cycle == 0
    assert len(sim1.history) == 0

    re_run = sim1.run_cycles(50)
    for c_orig, c_re in zip(run1, re_run):
        assert c_orig.cycle_index == c_re.cycle_index
        assert c_orig.barrel_temp_z3 == c_re.barrel_temp_z3
        assert c_orig.injection_pressure == c_re.injection_pressure
        assert c_orig.part_weight == c_re.part_weight
