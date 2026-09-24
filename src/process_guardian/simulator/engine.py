"""Stateful deterministic injection molding simulator engine."""

from typing import List, Dict, Optional, Any
import numpy as np

from process_guardian.core.types import RegimeType, MachineContext, RawCycleTelemetry
from process_guardian.core.constants import NOMINAL_PP_PARAMS
from process_guardian.simulator.regimes import get_regime_modifiers


class InjectionMoldingSimulator:
    """
    Deterministic cycle-level injection molding machine simulator.
    
    Generates realistic, correlated telemetry records across 9 operational regimes
    using seeded pseudo-random number generation for 100% reproducible execution.
    """

    def __init__(
        self,
        seed: int = 42,
        context: Optional[MachineContext] = None,
        base_regime: RegimeType = RegimeType.HEALTHY,
    ):
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.current_cycle = 0
        self.active_regime = base_regime
        self.cycle_in_regime = 0
        self.context = context or MachineContext()
        self.history: List[RawCycleTelemetry] = []
        self._initial_drift_offsets: Dict[str, float] = {}

    def set_regime(self, regime: RegimeType, initial_offsets: Optional[Dict[str, float]] = None) -> None:
        """Switch operational regime and reset within-regime cycle counter."""
        self.active_regime = regime
        self.cycle_in_regime = 0
        if initial_offsets is not None:
            self._initial_drift_offsets = dict(initial_offsets)

    def reset(self, new_seed: Optional[int] = None) -> None:
        """Reset simulator to pristine initial state at cycle 0."""
        if new_seed is not None:
            self.seed = new_seed
        self.rng = np.random.default_rng(self.seed)
        self.current_cycle = 0
        self.active_regime = RegimeType.HEALTHY
        self.cycle_in_regime = 0
        self.history.clear()
        self._initial_drift_offsets.clear()

    def step(self) -> RawCycleTelemetry:
        """Advance simulation by one cycle and return generated telemetry."""
        self.current_cycle += 1
        self.cycle_in_regime += 1

        # Base nominal parameters
        params = dict(NOMINAL_PP_PARAMS)

        # Get regime modifiers
        modifiers = get_regime_modifiers(
            regime=self.active_regime,
            cycle_in_regime=self.cycle_in_regime,
            rng=self.rng,
            initial_drift_offsets=self._initial_drift_offsets,
        )

        # Apply modifiers with physical clamping
        barrel_temp_z1 = max(150.0, params["barrel_temp_z1"] + modifiers.get("barrel_temp_z1", 0.0))
        barrel_temp_z2 = max(160.0, params["barrel_temp_z2"] + modifiers.get("barrel_temp_z2", 0.0))
        barrel_temp_z3 = max(170.0, params["barrel_temp_z3"] + modifiers.get("barrel_temp_z3", 0.0))
        barrel_temp_z4 = max(170.0, params["barrel_temp_z4"] + modifiers.get("barrel_temp_z4", 0.0))
        barrel_temp_z5 = max(170.0, params["barrel_temp_z5"] + modifiers.get("barrel_temp_z5", 0.0))
        nozzle_temp = max(180.0, params["nozzle_temp"] + modifiers.get("nozzle_temp", 0.0))

        injection_pressure = max(10.0, params["injection_pressure"] + modifiers.get("injection_pressure", 0.0))
        peak_pressure = max(15.0, params["peak_pressure"] + modifiers.get("peak_pressure", 0.0))
        hold_pressure = max(5.0, params["hold_pressure"] + modifiers.get("hold_pressure", 0.0))

        injection_time = max(0.5, params["injection_time"] + modifiers.get("injection_time", 0.0))
        hold_time = max(1.0, params["hold_time"] + modifiers.get("hold_time", 0.0))
        cooling_time = max(2.0, params["cooling_time"] + modifiers.get("cooling_time", 0.0))
        cycle_time = max(5.0, params["cycle_time"] + modifiers.get("cycle_time", 0.0))

        part_weight = max(50.0, params["part_weight"] + modifiers.get("part_weight", 0.0))
        material_moisture = max(0.001, params["material_moisture"] + modifiers.get("material_moisture", 0.0))
        ambient_temp = params["ambient_temp"] + modifiers.get("ambient_temp", 0.0)
        ambient_humidity = max(10.0, min(95.0, params["ambient_humidity"] + modifiers.get("ambient_humidity", 0.0)))

        # Ground truth inspection flags
        defect_flag = False
        sink_mark_depth = 0.0
        flash_observed = False

        if peak_pressure < 118.0 or part_weight < 141.5:
            defect_flag = True
            sink_mark_depth = round((142.5 - part_weight) * 0.06, 3)
        elif barrel_temp_z3 > 240.0 and peak_pressure > 142.0:
            defect_flag = True
            flash_observed = True

        record = RawCycleTelemetry(
            cycle_index=self.current_cycle,
            barrel_temp_z1=round(barrel_temp_z1, 2),
            barrel_temp_z2=round(barrel_temp_z2, 2),
            barrel_temp_z3=round(barrel_temp_z3, 2),
            barrel_temp_z4=round(barrel_temp_z4, 2),
            barrel_temp_z5=round(barrel_temp_z5, 2),
            nozzle_temp=round(nozzle_temp, 2),
            injection_pressure=round(injection_pressure, 2),
            peak_pressure=round(peak_pressure, 2),
            hold_pressure=round(hold_pressure, 2),
            injection_time=round(injection_time, 2),
            hold_time=round(hold_time, 2),
            cooling_time=round(cooling_time, 2),
            cycle_time=round(cycle_time, 2),
            part_weight=round(part_weight, 2),
            material_moisture=round(material_moisture, 4),
            ambient_temp=round(ambient_temp, 2),
            ambient_humidity=round(ambient_humidity, 2),
            sink_mark_depth=max(0.0, sink_mark_depth),
            flash_observed=flash_observed,
            defect_flag=defect_flag,
            regime=self.active_regime.value,
            timestamp_offset_s=round((self.current_cycle - 1) * params["cycle_time"], 2),
        )

        self.history.append(record)
        return record

    def run_cycles(self, n: int) -> List[RawCycleTelemetry]:
        """Generate and return n consecutive simulation cycles."""
        return [self.step() for _ in range(n)]
