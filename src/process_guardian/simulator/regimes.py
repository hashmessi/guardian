"""Definitions and mathematical modifier generators for the 9 operational regimes."""

import math
from dataclasses import dataclass
from typing import Dict, Any, Optional
import numpy as np

from process_guardian.core.types import RegimeType
from process_guardian.core.constants import NOMINAL_PROCESS_NOISE


@dataclass
class RegimeConfig:
    """Configuration parameters for a specific operational regime."""
    regime: RegimeType
    thermal_slope_z3: float = 0.20        # °C per cycle
    thermal_slope_nozzle: float = 0.10    # °C per cycle
    pressure_slope_inj: float = -0.25     # bar per cycle
    pressure_slope_peak: float = -0.35    # bar per cycle
    moisture_slope: float = 0.005         # % per cycle
    noise_multiplier: float = 1.0         # Noise scale factor
    cycle_jitter_scale: float = 1.0       # Timing jitter scale


def get_regime_modifiers(
    regime: RegimeType,
    cycle_in_regime: int,
    rng: np.random.Generator,
    initial_drift_offsets: Optional[Dict[str, float]] = None,
) -> Dict[str, float]:
    """
    Compute parameter deltas from nominal for a given regime at the specified cycle index.
    
    Returns a dictionary of additive modifiers {param_name: delta_value}.
    """
    modifiers: Dict[str, float] = {}
    offsets = initial_drift_offsets or {}

    if regime == RegimeType.HEALTHY:
        # Stationary baseline: pure nominal with standard Gaussian variance
        for param, noise_std in NOMINAL_PROCESS_NOISE.items():
            modifiers[param] = float(rng.normal(0.0, noise_std))

    elif regime == RegimeType.THERMAL_DRIFT:
        # Linear/progressive heating on zone 3 and nozzle
        drift_z3 = 0.20 * cycle_in_regime
        drift_nozzle = 0.10 * cycle_in_regime
        for param, noise_std in NOMINAL_PROCESS_NOISE.items():
            modifiers[param] = float(rng.normal(0.0, noise_std))
        modifiers["barrel_temp_z3"] += drift_z3
        modifiers["nozzle_temp"] += drift_nozzle

    elif regime == RegimeType.PRESSURE_DRIFT:
        # Progressive pressure decay simulating hydraulic valve leak / check-ring wear
        drift_inj = -0.25 * cycle_in_regime
        drift_peak = -0.35 * cycle_in_regime
        for param, noise_std in NOMINAL_PROCESS_NOISE.items():
            modifiers[param] = float(rng.normal(0.0, noise_std))
        modifiers["injection_pressure"] += drift_inj
        modifiers["peak_pressure"] += drift_peak

    elif regime == RegimeType.MOISTURE_DRIFT:
        # Progressive moisture ingress from wet resin batch
        moisture_drift = min(0.16, 0.005 * cycle_in_regime)
        for param, noise_std in NOMINAL_PROCESS_NOISE.items():
            modifiers[param] = float(rng.normal(0.0, noise_std))
        modifiers["material_moisture"] += moisture_drift

    elif regime == RegimeType.CYCLE_INSTABILITY:
        # Erratic cooling water temperature fluctuations and mechanical jitter
        for param, noise_std in NOMINAL_PROCESS_NOISE.items():
            scale = 2.5 if "time" in param else 1.2
            modifiers[param] = float(rng.normal(0.0, noise_std * scale))
        # Large cycle and cooling time swings
        modifiers["cooling_time"] += float(rng.uniform(-2.5, 2.5))
        modifiers["cycle_time"] += float(rng.uniform(-3.0, 3.0))

    elif regime == RegimeType.COMBINED_DRIFT:
        # Simultaneous thermal and moisture drift (compound failure)
        drift_z3 = 0.20 * cycle_in_regime
        moisture_drift = min(0.14, 0.004 * cycle_in_regime)
        for param, noise_std in NOMINAL_PROCESS_NOISE.items():
            modifiers[param] = float(rng.normal(0.0, noise_std))
        modifiers["barrel_temp_z3"] += drift_z3
        modifiers["material_moisture"] += moisture_drift

    elif regime == RegimeType.SENSOR_NOISE:
        # High sensor jitter without underlying melt shift (testing false-positive avoidance)
        for param, noise_std in NOMINAL_PROCESS_NOISE.items():
            if param in ("barrel_temp_z3", "injection_pressure"):
                modifiers[param] = float(rng.normal(0.0, noise_std * 5.0))
            else:
                modifiers[param] = float(rng.normal(0.0, noise_std))

    elif regime == RegimeType.RECOVERY:
        # Exponential relaxation back to baseline from pre-existing drift offset
        decay_factor = math.exp(-cycle_in_regime / 4.0)
        for param, noise_std in NOMINAL_PROCESS_NOISE.items():
            initial_offset = offsets.get(param, 0.0)
            modifiers[param] = (initial_offset * decay_factor) + float(rng.normal(0.0, noise_std))

    elif regime == RegimeType.UNSEEN_DRIFT:
        # Sinusoidal hunting oscillation on zone-3 (period = 12 cycles, amplitude = 3.5°C)
        oscillation = 3.5 * math.sin(2.0 * math.pi * cycle_in_regime / 12.0)
        for param, noise_std in NOMINAL_PROCESS_NOISE.items():
            modifiers[param] = float(rng.normal(0.0, noise_std))
        modifiers["barrel_temp_z3"] += oscillation

    return modifiers
