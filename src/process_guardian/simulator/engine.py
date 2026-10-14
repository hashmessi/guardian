"""Stateful deterministic injection molding simulator engine with causal physics and event injection."""

from typing import List, Dict, Optional, Any
import numpy as np

from process_guardian.core.types import RegimeType, MachineContext, RawCycleTelemetry
from process_guardian.core.constants import NOMINAL_PP_PARAMS, NOMINAL_PROCESS_NOISE
from process_guardian.simulator.regimes import get_regime_modifiers
from process_guardian.simulator.physics import PhysicsState, compute_causal_effects
from process_guardian.simulator.events import InjectionEvent, EventQueue


class InjectionMoldingSimulator:
    """
    Deterministic cycle-level injection molding machine simulator.
    
    Generates realistic, correlated telemetry records across 9 operational regimes
    and dynamic event injections using coupled polymer physics and seeded pseudo-random
    number generation.
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

        # Physics & Event queue
        self.event_queue = EventQueue()
        self.physics_state = PhysicsState()

    def inject_event(
        self,
        event_type: str,
        cycle: Optional[int] = None,
        severity: float = 1.0,
        duration: Optional[int] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> InjectionEvent:
        """
        Inject a specific process anomaly or operator action at a specific cycle number.
        
        If cycle is None, the event activates on the immediate next cycle.
        """
        start_cycle = self.current_cycle + 1 if cycle is None else cycle
        event = InjectionEvent(
            event_type=event_type,
            start_cycle=start_cycle,
            severity=severity,
            duration=duration,
            params=params or {},
        )
        self.event_queue.add_event(event)
        return event

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
        self.event_queue.clear()
        self.physics_state = PhysicsState()

    def step(self) -> RawCycleTelemetry:
        """Advance simulation by one cycle and return generated telemetry."""
        self.current_cycle += 1
        self.cycle_in_regime += 1

        # 1. Base modifiers from active regime
        modifiers = get_regime_modifiers(
            regime=self.active_regime,
            cycle_in_regime=self.cycle_in_regime,
            rng=self.rng,
            initial_drift_offsets=self._initial_drift_offsets,
        )

        # 2. Check for active scheduled events
        active_events = self.event_queue.get_active_events(self.current_cycle)
        regime_label = self.active_regime.value

        for event in active_events:
            offset = event.get_cycle_offset(self.current_cycle)
            regime_label = f"{regime_label}+{event.event_type}" if regime_label != event.event_type else regime_label

            if event.event_type == "thermal_drift":
                # Gradual progressive thermal drift
                drift_amount = 0.20 * offset * event.severity
                modifiers["barrel_temp_z3"] = modifiers.get("barrel_temp_z3", 0.0) + drift_amount
                modifiers["nozzle_temp"] = modifiers.get("nozzle_temp", 0.0) + (0.10 * offset * event.severity)

            elif event.event_type == "pressure_drift":
                # Pressure loss
                p_loss = -0.25 * offset * event.severity
                modifiers["injection_pressure"] = modifiers.get("injection_pressure", 0.0) + p_loss
                modifiers["peak_pressure"] = modifiers.get("peak_pressure", 0.0) + (-0.35 * offset * event.severity)

            elif event.event_type == "moisture_drift":
                # Hopper moisture surge
                m_surge = min(0.18, 0.006 * offset * event.severity)
                modifiers["material_moisture"] = modifiers.get("material_moisture", 0.0) + m_surge

            elif event.event_type == "intervention_temp_offset":
                # Operator or simulated controller adjustment (e.g. -3°C)
                delta_t = event.params.get("delta_temp_z3", -3.0) * event.severity
                modifiers["barrel_temp_z3"] = modifiers.get("barrel_temp_z3", 0.0) + delta_t

            elif event.event_type == "recovery":
                # Stabilization back toward baseline
                decay = np.exp(-offset / 3.0)
                # Dampen existing thermal, pressure, and moisture drift
                for sig in ("barrel_temp_z3", "nozzle_temp", "injection_pressure", "peak_pressure", "material_moisture"):
                    if sig in modifiers:
                        modifiers[sig] *= decay

            elif event.event_type == "sudden_shift":
                # Instantaneous step shift (e.g. +15°C heater runaway / sensor slip)
                step_val = float(event.params.get("delta_temp_z3", 15.0)) * event.severity
                modifiers["barrel_temp_z3"] = modifiers.get("barrel_temp_z3", 0.0) + step_val

            elif event.event_type == "signal_drift":
                # Generic linear signal drift on any telemetry parameter
                sig = event.params.get("signal", "barrel_temp_z3")
                rate = float(event.params.get("rate", 0.20))
                max_drift = event.params.get("max_drift")
                drift_val = rate * offset * event.severity
                if max_drift is not None:
                    drift_val = min(float(max_drift), drift_val) if rate > 0 else max(float(max_drift), drift_val)
                modifiers[sig] = modifiers.get(sig, 0.0) + drift_val

            elif event.event_type in ("parameter_offset", "parameter_step"):
                # Discrete parameter bias (e.g. clerical recipe entry error or fixed setting bias)
                sig = event.params.get("signal", "barrel_temp_z2")
                delta_val = float(event.params.get("delta", 0.0)) * event.severity
                modifiers[sig] = modifiers.get(sig, 0.0) + delta_val

            elif event.event_type == "intervention_pressure_offset":
                # Operator or controller pressure boost
                delta_p = float(event.params.get("delta_injection_pressure", 4.0)) * event.severity
                modifiers["injection_pressure"] = modifiers.get("injection_pressure", 0.0) + delta_p
                modifiers["peak_pressure"] = modifiers.get("peak_pressure", 0.0) + delta_p

            elif event.event_type == "persistent_drift":
                # Severe or recalcitrant failure that outpaces intervention
                sig = event.params.get("signal", "barrel_temp_z3")
                rate = float(event.params.get("rate", 0.35))
                modifiers[sig] = modifiers.get(sig, 0.0) + (rate * offset * event.severity)

            elif event.event_type == "noise_burst":
                # Temporary industrial electromagnetic/sensor noise burst
                scale = float(event.params.get("scale", 3.0))
                for param, noise_std in NOMINAL_PROCESS_NOISE.items():
                    modifiers[param] = modifiers.get(param, 0.0) + float(self.rng.normal(0.0, noise_std * scale))

        # 3. Compute causal coupled physics
        coupled_values = compute_causal_effects(
            base_params=NOMINAL_PP_PARAMS,
            active_modifiers=modifiers,
            cycle_index=self.current_cycle,
        )

        # 4. Add sensor noise (and physical clamping)
        # SENSOR_NOISE regime has higher variance, handled in get_regime_modifiers
        barrel_temp_z1 = max(150.0, coupled_values["barrel_temp_z1"] + float(self.rng.normal(0.0, NOMINAL_PROCESS_NOISE["barrel_temp_z1"])))
        barrel_temp_z2 = max(160.0, coupled_values["barrel_temp_z2"] + float(self.rng.normal(0.0, NOMINAL_PROCESS_NOISE["barrel_temp_z2"])))
        barrel_temp_z3 = max(170.0, coupled_values["barrel_temp_z3"] + float(self.rng.normal(0.0, NOMINAL_PROCESS_NOISE["barrel_temp_z3"])))
        barrel_temp_z4 = max(170.0, coupled_values["barrel_temp_z4"] + float(self.rng.normal(0.0, NOMINAL_PROCESS_NOISE["barrel_temp_z4"])))
        barrel_temp_z5 = max(170.0, coupled_values["barrel_temp_z5"] + float(self.rng.normal(0.0, NOMINAL_PROCESS_NOISE["barrel_temp_z5"])))
        nozzle_temp = max(180.0, coupled_values["nozzle_temp"] + float(self.rng.normal(0.0, NOMINAL_PROCESS_NOISE["nozzle_temp"])))

        injection_pressure = max(10.0, coupled_values["injection_pressure"] + float(self.rng.normal(0.0, NOMINAL_PROCESS_NOISE["injection_pressure"])))
        peak_pressure = max(15.0, coupled_values["peak_pressure"] + float(self.rng.normal(0.0, NOMINAL_PROCESS_NOISE["peak_pressure"])))
        hold_pressure = max(5.0, coupled_values["hold_pressure"] + float(self.rng.normal(0.0, NOMINAL_PROCESS_NOISE["hold_pressure"])))

        injection_time = max(0.5, coupled_values["injection_time"] + float(self.rng.normal(0.0, NOMINAL_PROCESS_NOISE["injection_time"])))
        hold_time = max(1.0, coupled_values["hold_time"] + float(self.rng.normal(0.0, NOMINAL_PROCESS_NOISE["hold_time"])))
        cooling_time = max(2.0, coupled_values["cooling_time"] + float(self.rng.normal(0.0, NOMINAL_PROCESS_NOISE["cooling_time"])))
        cycle_time = max(5.0, coupled_values["cycle_time"] + float(self.rng.normal(0.0, NOMINAL_PROCESS_NOISE["cycle_time"])))

        part_weight = max(50.0, coupled_values["part_weight"] + float(self.rng.normal(0.0, NOMINAL_PROCESS_NOISE["part_weight"])))
        material_moisture = max(0.001, coupled_values["material_moisture"] + float(self.rng.normal(0.0, NOMINAL_PROCESS_NOISE["material_moisture"])))
        ambient_temp = coupled_values["ambient_temp"] + float(self.rng.normal(0.0, NOMINAL_PROCESS_NOISE["ambient_temp"]))
        ambient_humidity = max(10.0, min(95.0, coupled_values["ambient_humidity"] + float(self.rng.normal(0.0, NOMINAL_PROCESS_NOISE["ambient_humidity"]))))

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
            sink_mark_depth=coupled_values["sink_mark_depth"],
            flash_observed=coupled_values["flash_observed"],
            defect_flag=coupled_values["defect_flag"],
            regime=regime_label,
            timestamp_offset_s=round((self.current_cycle - 1) * NOMINAL_PP_PARAMS["cycle_time"], 2),
        )

        self.history.append(record)
        return record

    def run_cycles(self, n: int) -> List[RawCycleTelemetry]:
        """Generate and return n consecutive simulation cycles."""
        return [self.step() for _ in range(n)]
