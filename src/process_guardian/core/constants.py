"""Nominal process parameters and physical constants for automotive polypropylene molding."""

from typing import Dict

# Polypropylene Automotive Housing Nominal Parameters (Recipe PP-V2.1)
NOMINAL_PP_PARAMS: Dict[str, float] = {
    # Temperature profile (°C)
    "barrel_temp_z1": 210.0,   # Rear / Feed zone
    "barrel_temp_z2": 220.0,   # Transition zone
    "barrel_temp_z3": 230.0,   # Metering zone
    "barrel_temp_z4": 235.0,   # Front zone
    "barrel_temp_z5": 235.0,   # Transition to nozzle
    "nozzle_temp": 240.0,      # Injection nozzle
    # Pressure profile (bar)
    "injection_pressure": 110.0,  # Peak machine filling pressure
    "peak_pressure": 135.0,       # Cavity transfer peak pressure
    "hold_pressure": 65.0,        # Packing/holding pressure
    # Timing profile (seconds)
    "injection_time": 2.4,        # Filling duration
    "hold_time": 6.5,             # Packing duration
    "cooling_time": 14.0,         # In-mold cooling duration
    "cycle_time": 28.5,           # Complete dry-to-dry cycle time
    # Material & Environmental parameters
    "part_weight": 142.5,         # Target part weight (grams)
    "material_moisture": 0.02,    # Virgin pellet moisture content (%)
    "ambient_temp": 28.0,         # Shopfloor ambient temperature (°C)
    "ambient_humidity": 55.0,     # Shopfloor ambient relative humidity (%)
}

# Nominal standard deviations for healthy stationary process noise (~0.5% CV)
NOMINAL_PROCESS_NOISE: Dict[str, float] = {
    "barrel_temp_z1": 0.35,
    "barrel_temp_z2": 0.35,
    "barrel_temp_z3": 0.40,
    "barrel_temp_z4": 0.35,
    "barrel_temp_z5": 0.35,
    "nozzle_temp": 0.45,
    "injection_pressure": 0.85,
    "peak_pressure": 0.95,
    "hold_pressure": 0.50,
    "injection_time": 0.03,
    "hold_time": 0.05,
    "cooling_time": 0.12,
    "cycle_time": 0.18,
    "part_weight": 0.12,
    "material_moisture": 0.002,
    "ambient_temp": 0.20,
    "ambient_humidity": 0.50,
}
