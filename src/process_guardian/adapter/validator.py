"""Validation of signal physical plausibility bounds and sensor quality detection."""

from dataclasses import dataclass
from typing import Dict, Tuple, Optional
from process_guardian.adapter.schemas import QualityFlag


@dataclass
class PhysicalBound:
    """Acceptable physical limits for an injection molding signal."""
    min_val: float
    max_val: float


# Physical plausibility boundaries for injection molding (broad bounds to avoid false rejections)
PHYSICAL_BOUNDS: Dict[str, PhysicalBound] = {
    "barrel_temp_z1": PhysicalBound(100.0, 420.0),
    "barrel_temp_z2": PhysicalBound(100.0, 420.0),
    "barrel_temp_z3": PhysicalBound(100.0, 420.0),
    "barrel_temp_z4": PhysicalBound(100.0, 420.0),
    "barrel_temp_z5": PhysicalBound(100.0, 420.0),
    "nozzle_temp": PhysicalBound(100.0, 450.0),
    "injection_pressure": PhysicalBound(5.0, 300.0),
    "peak_pressure": PhysicalBound(5.0, 350.0),
    "hold_pressure": PhysicalBound(0.0, 250.0),
    "injection_time": PhysicalBound(0.1, 30.0),
    "hold_time": PhysicalBound(0.1, 60.0),
    "cooling_time": PhysicalBound(0.5, 180.0),
    "cycle_time": PhysicalBound(2.0, 300.0),
    "part_weight": PhysicalBound(20.0, 500.0),
    "material_moisture": PhysicalBound(0.0, 2.0),
    "ambient_temp": PhysicalBound(-10.0, 65.0),
    "ambient_humidity": PhysicalBound(0.0, 100.0),
}

REQUIRED_SIGNALS = [
    "barrel_temp_z1",
    "barrel_temp_z2",
    "barrel_temp_z3",
    "barrel_temp_z4",
    "barrel_temp_z5",
    "nozzle_temp",
    "injection_pressure",
    "peak_pressure",
    "hold_pressure",
    "injection_time",
    "hold_time",
    "cooling_time",
    "cycle_time",
    "part_weight",
    "material_moisture",
]


class TelemetryValidator:
    """Validates physical range limits and detects dropped, missing, or corrupt sensors."""

    def validate(
        self,
        signals: Dict[str, Optional[float]],
    ) -> Tuple[Dict[str, QualityFlag], bool]:
        """
        Evaluate signal validity against physical plausibility bounds.
        
        Returns:
            Tuple of (quality_flags_dict, is_valid_boolean)
        """
        flags: Dict[str, QualityFlag] = {}
        all_valid = True

        for sig_name in REQUIRED_SIGNALS:
            val = signals.get(sig_name)

            if val is None:
                flags[sig_name] = QualityFlag.MISSING_SIGNAL
                all_valid = False
                continue

            bound = PHYSICAL_BOUNDS.get(sig_name)
            if bound is not None:
                if val < bound.min_val or val > bound.max_val:
                    flags[sig_name] = QualityFlag.OUT_OF_BOUNDS
                    all_valid = False
                    continue

            flags[sig_name] = QualityFlag.VALID

        # Check optional signals
        for sig_name in ("ambient_temp", "ambient_humidity"):
            val = signals.get(sig_name)
            if val is not None:
                bound = PHYSICAL_BOUNDS.get(sig_name)
                if bound and (val < bound.min_val or val > bound.max_val):
                    flags[sig_name] = QualityFlag.OUT_OF_BOUNDS
                else:
                    flags[sig_name] = QualityFlag.VALID

        return flags, all_valid
