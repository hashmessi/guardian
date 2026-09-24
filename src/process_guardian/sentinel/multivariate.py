"""Multivariate Mahalanobis distance detector for coupled cross-signal drift."""

import math
from typing import Tuple, List, Dict
import numpy as np
from scipy.stats import chi2

from process_guardian.fingerprint.models import ProcessFingerprint


class MultivariateDetector:
    """
    Multivariate statistical process control using regularized Mahalanobis distance.
    
    Identifies multidimensional process shifts where several correlated parameters
    drift simultaneously even if no individual sensor breaches Shewhart limits.
    """

    def __init__(self, fingerprint: ProcessFingerprint, confidence_level: float = 0.99):
        self.fingerprint = fingerprint
        self.feature_names = fingerprint.feature_names
        self.p = len(self.feature_names)
        self.mean_vector = np.array(fingerprint.mean_vector, dtype=float)
        self.inv_cov = np.array(fingerprint.inv_cov_matrix, dtype=float)

        # Critical threshold: D_M^2 follows Chi-Square distribution with p degrees of freedom
        chi2_crit = float(chi2.ppf(confidence_level, df=self.p))
        self.threshold = math.sqrt(chi2_crit)

    def compute_distance(self, signal_values: Dict[str, float]) -> Tuple[float, bool]:
        """
        Calculate Mahalanobis distance D_M from fingerprint baseline.
        
        Returns:
            Tuple of (distance, is_breached)
        """
        x = np.array([signal_values.get(sig, self.mean_vector[i]) for i, sig in enumerate(self.feature_names)], dtype=float)
        diff = x - self.mean_vector

        # D_M^2 = diff^T * inv_cov * diff
        d2 = float(diff @ self.inv_cov @ diff)
        d_m = math.sqrt(max(0.0, d2))

        return d_m, (d_m > self.threshold)
