"""Temporal and physical interaction feature engineering pipeline (QRSK-02)."""

from collections import deque
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

from process_guardian.adapter.schemas import NormalizedCycleRecord
from process_guardian.fingerprint.models import ProcessFingerprint


class TemporalFeatureExtractor:
    """
    Stateful sliding-window feature extractor for cycle-level injection molding telemetry.
    
    Generates rich temporal representations including:
    - Raw normalized process parameters
    - Standardized deviations from baseline fingerprint (delta, z-score)
    - Short (W=5) and medium (W=15) rolling moments (mean, std, spread)
    - Sliding linear slopes and trends
    - Lag-1, Lag-2 observations and first differences (acceleration/velocity)
    - Polymer pvT physical interaction ratios (effective melt temp, pressure transfer, cooling fraction)
    """

    CORE_SIGNALS = [
        "barrel_temp_z1", "barrel_temp_z2", "barrel_temp_z3", "barrel_temp_z4", "barrel_temp_z5",
        "nozzle_temp", "injection_pressure", "peak_pressure", "hold_pressure",
        "injection_time", "hold_time", "cooling_time", "cycle_time",
        "part_weight", "material_moisture",
    ]

    def __init__(self, fingerprint: ProcessFingerprint, max_window: int = 20):
        self.fingerprint = fingerprint
        self.max_window = max_window
        self.signal_history: Dict[str, deque] = {
            sig: deque(maxlen=max_window) for sig in self.CORE_SIGNALS
        }
        self.cycle_count: int = 0
        self._feature_names: Optional[List[str]] = None

    def reset(self) -> None:
        """Clear rolling history."""
        self.cycle_count = 0
        for q in self.signal_history.values():
            q.clear()

    def get_feature_names(self) -> List[str]:
        """Return deterministic ordered list of feature column names."""
        if self._feature_names is not None:
            return self._feature_names

        names: List[str] = []
        # Per-signal temporal features
        for sig in self.CORE_SIGNALS:
            names.extend([
                f"{sig}_raw",
                f"{sig}_delta_fp",
                f"{sig}_z_fp",
                f"{sig}_mean_w5",
                f"{sig}_std_w5",
                f"{sig}_mean_w15",
                f"{sig}_std_w15",
                f"{sig}_slope_w15",
                f"{sig}_lag1",
                f"{sig}_step_diff",
            ])

        # Coupled physical interaction features
        names.extend([
            "effective_melt_temp",
            "thermal_gradient_z3_z1",
            "thermal_gradient_nozzle_z5",
            "pressure_transfer_ratio",
            "packing_ratio",
            "cooling_time_fraction",
            "ambient_heat_index",
            "moisture_viscosity_proxy",
        ])

        self._feature_names = names
        return names

    def extract_features(self, record: NormalizedCycleRecord) -> Tuple[Dict[str, float], np.ndarray]:
        """
        Extract features from a new incoming cycle record.
        
        Returns:
            Tuple of (named_feature_dict, ordered_numpy_feature_vector)
        """
        self.cycle_count += 1
        features: Dict[str, float] = {}

        # 1. Update history and compute per-signal features
        for sig in self.CORE_SIGNALS:
            val = float(getattr(record, sig, 0.0))
            self.signal_history[sig].append(val)
            hist = list(self.signal_history[sig])

            stat = self.fingerprint.signal_stats.get(sig)
            base_mean = stat.mean if stat else val
            base_std = stat.std if stat and stat.std > 1e-4 else 1.0

            # Raw, delta, z-score
            delta_fp = val - base_mean
            z_fp = delta_fp / base_std
            features[f"{sig}_raw"] = round(val, 4)
            features[f"{sig}_delta_fp"] = round(delta_fp, 4)
            features[f"{sig}_z_fp"] = round(z_fp, 4)

            # Short window W=5
            w5 = hist[-5:]
            features[f"{sig}_mean_w5"] = round(float(np.mean(w5)), 4)
            features[f"{sig}_std_w5"] = round(float(np.std(w5, ddof=1)) if len(w5) > 1 else base_std, 4)

            # Medium window W=15
            w15 = hist[-15:]
            features[f"{sig}_mean_w15"] = round(float(np.mean(w15)), 4)
            features[f"{sig}_std_w15"] = round(float(np.std(w15, ddof=1)) if len(w15) > 1 else base_std, 4)

            # Slope over W=15
            if len(w15) >= 4:
                t_arr = np.arange(len(w15), dtype=float)
                v_arr = np.array(w15, dtype=float)
                denom = np.sum((t_arr - np.mean(t_arr)) ** 2)
                slope = float(np.sum((t_arr - np.mean(t_arr)) * (v_arr - np.mean(v_arr))) / denom) if denom > 1e-8 else 0.0
            else:
                slope = 0.0
            features[f"{sig}_slope_w15"] = round(slope, 5)

            # Lag1 and Step difference
            lag1 = hist[-2] if len(hist) >= 2 else val
            step_diff = val - lag1
            features[f"{sig}_lag1"] = round(lag1, 4)
            features[f"{sig}_step_diff"] = round(step_diff, 4)

        # 2. Compute polymer physics interaction features
        z3 = float(getattr(record, "barrel_temp_z3", 230.0))
        z4 = float(getattr(record, "barrel_temp_z4", 235.0))
        z1 = float(getattr(record, "barrel_temp_z1", 210.0))
        z5 = float(getattr(record, "barrel_temp_z5", 235.0))
        nozzle = float(getattr(record, "nozzle_temp", 240.0))

        p_inj = float(getattr(record, "injection_pressure", 110.0))
        p_peak = float(getattr(record, "peak_pressure", 135.0))
        p_hold = float(getattr(record, "hold_pressure", 65.0))

        t_cool = float(getattr(record, "cooling_time", 14.0))
        t_cycle = float(getattr(record, "cycle_time", 28.5))

        moisture = float(getattr(record, "material_moisture", 0.02))
        amb_t = float(getattr(record, "ambient_temp", 28.0))
        amb_h = float(getattr(record, "ambient_humidity", 65.0))

        eff_melt_temp = 0.50 * z3 + 0.30 * z4 + 0.20 * nozzle
        features["effective_melt_temp"] = round(eff_melt_temp, 4)
        features["thermal_gradient_z3_z1"] = round(z3 - z1, 4)
        features["thermal_gradient_nozzle_z5"] = round(nozzle - z5, 4)

        features["pressure_transfer_ratio"] = round(p_peak / max(1.0, p_inj), 4)
        features["packing_ratio"] = round(p_hold / max(1.0, p_peak), 4)
        features["cooling_time_fraction"] = round(t_cool / max(1.0, t_cycle), 4)

        features["ambient_heat_index"] = round(amb_t + 0.05 * amb_h, 4)
        features["moisture_viscosity_proxy"] = round(moisture * (eff_melt_temp / 230.0), 5)

        # 3. Assemble vector
        ordered_names = self.get_feature_names()
        vector = np.array([features[name] for name in ordered_names], dtype=np.float32)

        return features, vector
