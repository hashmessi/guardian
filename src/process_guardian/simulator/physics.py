"""Causal physics transfer functions for polymer melt injection dynamics."""

import math
from dataclasses import dataclass
from typing import Dict, Any, Tuple


@dataclass
class PhysicsState:
    """Internal thermodynamic and rheological state of the polymer melt."""
    effective_viscosity: float = 1.0
    cushion_position_mm: float = 8.5
    thermal_gradient_c: float = 0.0


def compute_causal_effects(
    base_params: Dict[str, float],
    active_modifiers: Dict[str, float],
    cycle_index: int,
) -> Dict[str, float]:
    """
    Compute correlated causal adjustments based on polymer pvT injection dynamics.
    
    Couplings modeled:
    - Moisture ingress lowers melt viscosity and drops peak injection cavity resistance.
    - Barrel heating lowers melt viscosity, reducing injection pressure and increasing flash risk.
    - Inadequate cavity packing pressure directly causes sink marks and reduced part weight.
    - Elevated melt temperature requires longer cooling time.
    """
    results = dict(base_params)

    # Raw intended parameter shifts from regime or events
    delta_z1 = active_modifiers.get("barrel_temp_z1", 0.0)
    delta_z2 = active_modifiers.get("barrel_temp_z2", 0.0)
    delta_z3 = active_modifiers.get("barrel_temp_z3", 0.0)
    delta_z4 = active_modifiers.get("barrel_temp_z4", 0.0)
    delta_z5 = active_modifiers.get("barrel_temp_z5", 0.0)
    delta_nozzle = active_modifiers.get("nozzle_temp", 0.0)

    delta_p_inj = active_modifiers.get("injection_pressure", 0.0)
    delta_p_peak = active_modifiers.get("peak_pressure", 0.0)
    delta_p_hold = active_modifiers.get("hold_pressure", 0.0)

    delta_moisture = active_modifiers.get("material_moisture", 0.0)
    delta_t_cool = active_modifiers.get("cooling_time", 0.0)
    delta_t_cycle = active_modifiers.get("cycle_time", 0.0)

    # 1. Effective melt temperature shift
    delta_t_eff = 0.50 * delta_z3 + 0.30 * delta_z4 + 0.20 * delta_nozzle

    # 2. Polymer relative melt viscosity (η_rel)
    # Higher temperature -> lower viscosity (-0.012 per °C)
    # Excess moisture -> hydrolysis/viscosity drop (-1.8 per % moisture)
    moisture_effect = -1.8 * delta_moisture
    eta_rel = max(0.50, 1.0 - 0.012 * delta_t_eff + moisture_effect)

    # 3. Peak cavity pressure & injection pressure response
    # Pressure required to fill drops as melt flows more easily
    nom_peak = base_params["peak_pressure"]
    nom_inj = base_params["injection_pressure"]

    # Causal pressure response
    causal_p_peak = (nom_peak * eta_rel) + delta_p_peak
    causal_p_inj = (nom_inj * (0.65 * eta_rel + 0.35)) + delta_p_inj
    causal_p_hold = base_params["hold_pressure"] + delta_p_hold

    # 4. Fill timing & Cooling dynamics
    nom_inj_time = base_params["injection_time"]
    nom_cool_time = base_params["cooling_time"]
    nom_cycle_time = base_params["cycle_time"]

    # Lower viscosity allows slightly faster cavity fill
    causal_inj_time = max(0.8, nom_inj_time * math.sqrt(eta_rel) + active_modifiers.get("injection_time", 0.0))
    # Hotter melt takes longer to solidify below HDT (Heat Deflection Temp)
    causal_cool_time = max(4.0, nom_cool_time * (1.0 + 0.005 * delta_t_eff) + delta_t_cool)
    causal_cycle_time = max(10.0, nom_cycle_time + (causal_cool_time - nom_cool_time) + delta_t_cycle)

    # 5. Part weight & Volumetric shrinkage
    nom_weight = base_params["part_weight"]
    # Effective packing density responds positively to hold pressure and inversely to high melt temp
    p_transfer_delta = causal_p_peak - nom_peak
    weight_shift = (
        0.0007 * delta_t_eff
        + 0.0006 * p_transfer_delta
        + 0.0012 * delta_p_hold
        - 1.5 * delta_moisture  # Moisture vaporization leads to internal voids
    )
    causal_weight = max(80.0, nom_weight * (1.0 + weight_shift))

    # Apply computed values
    results["barrel_temp_z1"] = base_params["barrel_temp_z1"] + delta_z1
    results["barrel_temp_z2"] = base_params["barrel_temp_z2"] + delta_z2
    results["barrel_temp_z3"] = base_params["barrel_temp_z3"] + delta_z3
    results["barrel_temp_z4"] = base_params["barrel_temp_z4"] + delta_z4
    results["barrel_temp_z5"] = base_params["barrel_temp_z5"] + delta_z5
    results["nozzle_temp"] = base_params["nozzle_temp"] + delta_nozzle

    results["injection_pressure"] = causal_p_inj
    results["peak_pressure"] = causal_p_peak
    results["hold_pressure"] = causal_p_hold

    results["injection_time"] = causal_inj_time
    results["hold_time"] = base_params["hold_time"] + active_modifiers.get("hold_time", 0.0)
    results["cooling_time"] = causal_cool_time
    results["cycle_time"] = causal_cycle_time

    results["part_weight"] = causal_weight
    results["material_moisture"] = base_params["material_moisture"] + delta_moisture
    results["ambient_temp"] = base_params["ambient_temp"] + active_modifiers.get("ambient_temp", 0.0)
    results["ambient_humidity"] = base_params["ambient_humidity"] + active_modifiers.get("ambient_humidity", 0.0)

    # Ground truth defect evaluation
    defect_flag = False
    sink_mark = 0.0
    flash = False

    if causal_p_peak < 120.0 or causal_weight < 141.2:
        defect_flag = True
        sink_mark = max(0.0, (142.5 - causal_weight) * 0.05)
    elif delta_z3 > 8.0 and causal_p_peak > 138.0:
        defect_flag = True
        flash = True

    results["defect_flag"] = defect_flag
    results["sink_mark_depth"] = sink_mark
    results["flash_observed"] = flash

    return results
