"""Standard scenario catalogs and builders for repeatable demonstration and testing."""

from typing import List, Dict, Any, Optional
from process_guardian.core.types import RegimeType
from process_guardian.simulator.engine import InjectionMoldingSimulator


def build_demo_scenario(seed: int = 42) -> InjectionMoldingSimulator:
    """
    Build the standard 10-step primary demo scenario:
    - Cycles 1 - 419: Stationary healthy baseline
    - Cycle 420: Injected thermal drift begins (zone 3 heater runaway)
    - Cycles 420 - 441: Thermal drift progresses, cavity pressure drops, flash/defect risks escalate
    - Cycle 442: Simulated corrective action applied (-3.0°C zone 3 temperature offset)
    - Cycle 443 - 446: Post-intervention parameter stabilization and recovery
    - Cycle 447+: Verified recovery and production release
    """
    sim = InjectionMoldingSimulator(seed=seed, base_regime=RegimeType.HEALTHY)

    # 1. Thermal drift event at cycle 420
    sim.inject_event(
        event_type="thermal_drift",
        cycle=420,
        severity=1.0,
        duration=None,
    )

    # 2. Simulated intervention at cycle 442 (reducing zone 3 by 3°C)
    sim.inject_event(
        event_type="intervention_temp_offset",
        cycle=442,
        severity=1.0,
        duration=None,
        params={"delta_temp_z3": -3.0},
    )

    # 3. Recovery stabilization beginning at cycle 443
    sim.inject_event(
        event_type="recovery",
        cycle=443,
        severity=1.0,
        duration=None,
    )

    return sim


def build_regime_scenario(
    regime: RegimeType,
    cycles: int = 100,
    seed: int = 42,
) -> InjectionMoldingSimulator:
    """Instantiate a simulator pre-configured for a single operational regime."""
    return InjectionMoldingSimulator(seed=seed, base_regime=regime)


def list_available_scenarios() -> List[str]:
    """Return available pre-configured scenario names."""
    return [
        "demo_thermal_drift",
        "healthy_baseline",
        "pressure_drift",
        "moisture_drift",
        "cycle_instability",
        "combined_drift",
        "sensor_noise",
        "recovery_demonstration",
        "unseen_pid_hunting",
    ]
