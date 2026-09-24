"""Statistical builder for computing context-specific process fingerprints."""

from datetime import datetime, timezone
from typing import List, Dict, Optional
import numpy as np

from process_guardian.adapter.schemas import NormalizedCycleRecord, EnrichedContext
from process_guardian.fingerprint.models import (
    SignalStats,
    OperatingEnvelope,
    ProcessFingerprint,
)

FEATURE_SIGNALS = [
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


class FingerprintBuilder:
    """
    Fits empirical baseline distributions, operating envelopes, and regularized
    covariance matrices from healthy reference cycle records.
    """

    def __init__(self, feature_signals: Optional[List[str]] = None):
        self.feature_signals = feature_signals or list(FEATURE_SIGNALS)

    def fit(
        self,
        records: List[NormalizedCycleRecord],
        ridge_epsilon: float = 1e-4,
    ) -> ProcessFingerprint:
        """
        Fit a process fingerprint from healthy baseline cycles.
        
        Requires at least 15 valid cycle records.
        """
        if len(records) < 15:
            raise ValueError(f"Fingerprint fitting requires >= 15 cycles, got {len(records)}")

        # Extract context from first record
        ctx = records[0].context
        context_key = f"{ctx.machine_id}:{ctx.mold_id}:{ctx.part_id}:{ctx.recipe_id}:{ctx.recipe_version}"

        signal_stats: Dict[str, SignalStats] = {}
        operating_envelopes: Dict[str, OperatingEnvelope] = {}

        # 1. Univariate distributions
        for sig in self.feature_signals:
            vals = np.array([getattr(r, sig) for r in records], dtype=float)
            mean_val = float(np.mean(vals))
            std_val = float(np.std(vals, ddof=1))
            # Protect against zero variance in synthetic or constant signals
            std_val = max(1e-4, std_val)

            min_val = float(np.min(vals))
            max_val = float(np.max(vals))
            p01 = float(np.percentile(vals, 1))
            p99 = float(np.percentile(vals, 99))
            p25 = float(np.percentile(vals, 25))
            p75 = float(np.percentile(vals, 75))
            iqr = float(p75 - p25)

            signal_stats[sig] = SignalStats(
                mean=round(mean_val, 4),
                std=round(std_val, 4),
                min_val=round(min_val, 4),
                max_val=round(max_val, 4),
                p01=round(p01, 4),
                p99=round(p99, 4),
                iqr=round(iqr, 4),
            )

            operating_envelopes[sig] = OperatingEnvelope(
                lower_limit=round(mean_val - 3.0 * std_val, 4),
                upper_limit=round(mean_val + 3.0 * std_val, 4),
                warning_lower=round(mean_val - 2.0 * std_val, 4),
                warning_upper=round(mean_val + 2.0 * std_val, 4),
            )

        # 2. Multivariate structure (Mean vector & Regularized Inverse Covariance)
        p = len(self.feature_signals)
        X = np.zeros((len(records), p), dtype=float)
        for i, r in enumerate(records):
            for j, sig in enumerate(self.feature_signals):
                X[i, j] = getattr(r, sig)

        mean_vector = [signal_stats[sig].mean for sig in self.feature_signals]

        # Sample covariance matrix
        cov = np.cov(X, rowvar=False)
        if cov.ndim == 0:
            cov = np.array([[cov]])

        # Ridge regularization to guarantee invertibility (lambda * I)
        cov_reg = cov + (ridge_epsilon * np.eye(p))
        inv_cov = np.linalg.pinv(cov_reg)

        inv_cov_list = [[round(float(inv_cov[i, j]), 6) for j in range(p)] for i in range(p)]

        fingerprint_id = f"FP-{ctx.machine_id}-{ctx.recipe_id}-{int(datetime.now(timezone.utc).timestamp())}"

        return ProcessFingerprint(
            fingerprint_id=fingerprint_id,
            context_key=context_key,
            context=ctx,
            sample_count=len(records),
            created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            signal_stats=signal_stats,
            operating_envelopes=operating_envelopes,
            feature_names=list(self.feature_signals),
            mean_vector=mean_vector,
            inv_cov_matrix=inv_cov_list,
        )
