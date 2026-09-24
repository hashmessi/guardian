"""Two-sided tabular CUSUM (Cumulative Sum) detector for gradual persistent drift."""

from typing import Dict, Tuple
from process_guardian.fingerprint.models import ProcessFingerprint


class CUSUMDetector:
    """
    Two-sided tabular CUSUM statistical quality control detector.
    
    Tracks cumulative upward and downward deviations in standardized units.
    """

    def __init__(
        self,
        fingerprint: ProcessFingerprint,
        K: float = 0.5,
        H: float = 4.5,
    ):
        self.fingerprint = fingerprint
        self.K = K  # Slack allowance (in sigma units)
        self.H = H  # Decision threshold (in sigma units)

        self.s_pos: Dict[str, float] = {sig: 0.0 for sig in fingerprint.signal_stats}
        self.s_neg: Dict[str, float] = {sig: 0.0 for sig in fingerprint.signal_stats}

    def reset(self) -> None:
        """Reset CUSUM cumulative sums to zero."""
        for sig in self.fingerprint.signal_stats:
            self.s_pos[sig] = 0.0
            self.s_neg[sig] = 0.0

    def update(self, signal_values: Dict[str, float]) -> Dict[str, Tuple[float, float, bool]]:
        """
        Update positive and negative CUSUM accumulators.
        
        Returns:
            Dict mapping signal_name -> (s_pos, s_neg, is_breached)
        """
        results: Dict[str, Tuple[float, float, bool]] = {}

        for sig, val in signal_values.items():
            if sig not in self.fingerprint.signal_stats:
                continue

            stat = self.fingerprint.signal_stats[sig]
            mu = stat.mean
            sigma = stat.std

            # Standardized z-score
            z = (val - mu) / sigma

            # Accumulate positive (upward drift) and negative (downward drift)
            s_p = max(0.0, self.s_pos.get(sig, 0.0) + z - self.K)
            s_n = max(0.0, self.s_neg.get(sig, 0.0) - z - self.K)

            self.s_pos[sig] = s_p
            self.s_neg[sig] = s_n

            breached = (s_p > self.H) or (s_n > self.H)
            results[sig] = (s_p, s_n, breached)

        return results
