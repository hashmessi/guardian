"""Exponentially Weighted Moving Average (EWMA) detector for small persistent mean shifts."""

import math
from typing import Dict, Tuple, Optional
from process_guardian.fingerprint.models import ProcessFingerprint


class EWMADetector:
    """
    EWMA statistical control chart detector.
    
    Accumulates past observations to rapidly detect mean shifts of 0.5 to 1.5 sigma.
    """

    def __init__(
        self,
        fingerprint: ProcessFingerprint,
        lambda_param: float = 0.15,
        L: float = 2.8,
    ):
        self.fingerprint = fingerprint
        self.lambda_param = lambda_param
        self.L = L

        # Tracked states per signal: {sig: current_z}
        self.z_values: Dict[str, float] = {
            sig: stat.mean for sig, stat in fingerprint.signal_stats.items()
        }
        self.t: int = 0

    def reset(self) -> None:
        """Reset EWMA state to baseline means."""
        self.t = 0
        self.z_values = {
            sig: stat.mean for sig, stat in self.fingerprint.signal_stats.items()
        }

    def update(self, signal_values: Dict[str, float]) -> Dict[str, Tuple[float, bool]]:
        """
        Update EWMA values and evaluate against dynamic control limits.
        
        Returns:
            Dict mapping signal_name -> (ewma_value, is_breached)
        """
        self.t += 1
        results: Dict[str, Tuple[float, bool]] = {}

        # Finite-horizon variance factor
        # sqrt( (lambda / (2 - lambda)) * (1 - (1 - lambda)^(2*t)) )
        var_factor = math.sqrt(
            (self.lambda_param / (2.0 - self.lambda_param))
            * (1.0 - math.pow(1.0 - self.lambda_param, 2 * self.t))
        )

        for sig, val in signal_values.items():
            if sig not in self.fingerprint.signal_stats:
                continue

            stat = self.fingerprint.signal_stats[sig]
            mu = stat.mean
            sigma = stat.std

            # Update EWMA
            prev_z = self.z_values.get(sig, mu)
            curr_z = (self.lambda_param * val) + ((1.0 - self.lambda_param) * prev_z)
            self.z_values[sig] = curr_z

            # Dynamic limits
            ucl = mu + (self.L * sigma * var_factor)
            lcl = mu - (self.L * sigma * var_factor)

            breached = (curr_z > ucl) or (curr_z < lcl)
            results[sig] = (curr_z, breached)

        return results
