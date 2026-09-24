"""Sliding window trend analysis and rate-of-change estimation."""

from collections import deque
from typing import Dict, List, Optional
import numpy as np


class SlidingTrendDetector:
    """Computes rolling least-squares linear slope over a sliding window of cycles."""

    def __init__(self, window_size: int = 15):
        self.window_size = window_size
        self.windows: Dict[str, deque] = {}

    def reset(self) -> None:
        """Clear all sliding history."""
        self.windows.clear()

    def update(self, signal_values: Dict[str, float]) -> Dict[str, float]:
        """
        Append signal values and compute current linear slope (unit/cycle).
        
        Returns:
            Dict mapping signal_name -> slope_per_cycle
        """
        slopes: Dict[str, float] = {}

        for sig, val in signal_values.items():
            if sig not in self.windows:
                self.windows[sig] = deque(maxlen=self.window_size)
            self.windows[sig].append(val)

            w = self.windows[sig]
            if len(w) < 4:
                slopes[sig] = 0.0
                continue

            # Linear regression: slope = Cov(t, x) / Var(t)
            t = np.arange(len(w), dtype=float)
            x = np.array(w, dtype=float)
            t_mean = np.mean(t)
            x_mean = np.mean(x)

            denom = np.sum((t - t_mean) ** 2)
            if denom < 1e-8:
                slopes[sig] = 0.0
            else:
                nom = np.sum((t - t_mean) * (x - x_mean))
                slopes[sig] = float(nom / denom)

        return slopes

    def get_trend_stats(self, sig: str) -> tuple[float, float]:
        """
        Return (slope, r_squared) for a signal over the sliding window.
        """
        if sig not in self.windows or len(self.windows[sig]) < 4:
            return 0.0, 0.0

        w = self.windows[sig]
        t = np.arange(len(w), dtype=float)
        x = np.array(w, dtype=float)
        t_mean = np.mean(t)
        x_mean = np.mean(x)

        denom = np.sum((t - t_mean) ** 2)
        if denom < 1e-8:
            return 0.0, 0.0

        slope = float(np.sum((t - t_mean) * (x - x_mean)) / denom)
        intercept = float(x_mean - slope * t_mean)
        pred = slope * t + intercept

        ss_tot = np.sum((x - x_mean) ** 2)
        ss_res = np.sum((x - pred) ** 2)
        r2 = float(1.0 - (ss_res / ss_tot)) if ss_tot > 1e-8 else 0.0
        return slope, max(0.0, min(1.0, r2))
