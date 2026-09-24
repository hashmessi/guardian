"""Drift Sentinel multi-method statistical fusion engine."""

from typing import Dict, List, Optional
import numpy as np

from process_guardian.adapter.schemas import NormalizedCycleRecord
from process_guardian.fingerprint.models import ProcessFingerprint
from process_guardian.sentinel.schemas import (
    SignalDriftDetail,
    DriftMetrics,
    DriftOutput,
)
from process_guardian.sentinel.ewma import EWMADetector
from process_guardian.sentinel.cusum import CUSUMDetector
from process_guardian.sentinel.multivariate import MultivariateDetector
from process_guardian.sentinel.trend import SlidingTrendDetector


class DriftSentinel:
    """
    Multi-method statistical drift detection engine.
    
    Combines EWMA, tabular CUSUM, rolling linear trends, and regularized Mahalanobis distance
    with persistence gating (>= 2 consecutive cycles) to provide early warning of process-state
    deterioration while eliminating false alarms from sensor noise (DRFT-01..04).
    """

    def __init__(
        self,
        fingerprint: ProcessFingerprint,
        min_warmup_cycles: int = 5,
        persistence_required: int = 2,
    ):
        self.fingerprint = fingerprint
        self.min_warmup_cycles = min_warmup_cycles
        self.persistence_required = persistence_required

        # Child statistical detectors
        self.ewma = EWMADetector(fingerprint, lambda_param=0.15, L=2.8)
        self.cusum = CUSUMDetector(fingerprint, K=0.5, H=4.5)
        self.multivariate = MultivariateDetector(fingerprint, confidence_level=0.995)
        self.trend = SlidingTrendDetector(window_size=15)

        # Operational state
        self.cycle_count: int = 0
        self.consecutive_drift_count: int = 0
        self._recent_records: List[Dict[str, float]] = []

    def reset(self) -> None:
        """Reset internal history and counters."""
        self.cycle_count = 0
        self.consecutive_drift_count = 0
        self._recent_records.clear()
        self.ewma.reset()
        self.cusum.reset()
        self.trend.reset()

    def evaluate(self, record: NormalizedCycleRecord) -> DriftOutput:
        """
        Evaluate a single normalized cycle record against the process fingerprint baseline.
        """
        self.cycle_count += 1

        # 1. Extract signals present in fingerprint
        signals: Dict[str, float] = {
            sig: getattr(record, sig) for sig in self.fingerprint.feature_names
        }

        # Keep recent sliding window for rolling stats
        self._recent_records.append(signals)
        if len(self._recent_records) > 20:
            self._recent_records.pop(0)

        # 2. Update statistical detectors
        ewma_results = self.ewma.update(signals)
        cusum_results = self.cusum.update(signals)
        self.trend.update(signals)
        d_m, multi_breach = self.multivariate.compute_distance(signals)

        # 3. Analyze each signal
        details: Dict[str, SignalDriftDetail] = {}
        drifting_signals: List[str] = []
        z_scores: Dict[str, float] = {}

        ewma_breached_any = False
        cusum_breached_any = False
        has_true_signal_drift = False

        for sig in self.fingerprint.feature_names:
            val = signals[sig]
            stat = self.fingerprint.signal_stats[sig]
            z = (val - stat.mean) / stat.std
            z_scores[sig] = z

            ewma_val, ewma_br = ewma_results.get(sig, (stat.mean, False))
            s_pos, s_neg, cusum_br = cusum_results.get(sig, (0.0, 0.0, False))
            slope_val, r2_val = self.trend.get_trend_stats(sig)

            if ewma_br:
                ewma_breached_any = True
            if cusum_br:
                cusum_breached_any = True

            # Rolling stats over recent window
            recent_vals = [r[sig] for r in self._recent_records]
            n = len(recent_vals)
            rolling_mean = float(np.mean(recent_vals))
            z_mean = (rolling_mean - stat.mean) / stat.std
            s = float(np.std(recent_vals, ddof=1)) if n > 1 else stat.std
            if s < 1e-4:
                s = 1e-4

            # Student's t-test of sample mean shift relative to observed sample standard error
            t_mean = abs(rolling_mean - stat.mean) / (s / np.sqrt(n)) if n > 1 else 0.0

            # Linear trend slope t-statistic
            if n >= 4:
                t_arr = np.arange(n, dtype=float)
                v_arr = np.array(recent_vals, dtype=float)
                pred = slope_val * t_arr + (rolling_mean - slope_val * np.mean(t_arr))
                rmse = float(np.sqrt(np.mean((v_arr - pred) ** 2)))
                denom_t = float(np.sqrt(np.sum((t_arr - np.mean(t_arr)) ** 2)))
                se_slope = (rmse / denom_t) if denom_t > 1e-6 else 1e-6
                t_slope = abs(slope_val) / se_slope if se_slope > 1e-6 else 0.0
            else:
                t_slope = 0.0

            # Multi-method true drift determination:
            # Requires persistent mean shift or verified trend, preventing white sensor jitter false alarms
            is_sig_drifting = False
            if n >= 5:
                # 1) Statistically significant mean shift relative to sample noise
                c_mean_shift = (t_mean >= 3.0) and (abs(z_mean) >= 1.8) and (ewma_br or cusum_br or abs(z) >= 2.0)
                # 2) Statistically significant linear slope
                c_linear_trend = (t_slope >= 2.8) and (abs(z_mean) >= 1.2)
                # 3) Large persistent single-point offset confirmed by distribution shift
                c_offset_shift = (abs(z) >= 3.5) and (abs(z_mean) >= 1.4)

                if c_mean_shift or c_linear_trend or c_offset_shift:
                    is_sig_drifting = True
                    has_true_signal_drift = True

            if is_sig_drifting or abs(z) >= 2.0:
                drifting_signals.append(sig)

            details[sig] = SignalDriftDetail(
                signal_name=sig,
                current_value=round(val, 2),
                baseline_mean=stat.mean,
                baseline_std=stat.std,
                z_score=round(z, 2),
                ewma_value=round(ewma_val, 2),
                ewma_breached=ewma_br,
                cusum_pos=round(s_pos, 2),
                cusum_neg=round(s_neg, 2),
                cusum_breached=cusum_br,
                slope_per_cycle=round(slope_val, 4),
                is_drifting=is_sig_drifting,
            )

        max_abs_z = max(abs(z) for z in z_scores.values()) if z_scores else 0.0

        # 4. Instantaneous drift determination
        instant_drift = has_true_signal_drift

        # 5. Persistence gate (strict consecutive streak)
        if instant_drift:
            self.consecutive_drift_count += 1
        else:
            self.consecutive_drift_count = 0

        confirmed_drift = (
            (self.consecutive_drift_count >= self.persistence_required)
            and (self.cycle_count >= self.min_warmup_cycles)
        )

        # 6. Severity score in [0.0, 1.0]
        z_component = min(1.0, max_abs_z / 4.0)
        multi_component = min(1.0, d_m / (self.multivariate.threshold * 1.3))
        raw_severity = (0.50 * z_component) + (0.50 * multi_component)

        if confirmed_drift:
            severity = round(max(0.40, min(1.0, 0.40 + 0.60 * raw_severity)), 2)
        else:
            severity = round(min(0.30, raw_severity * 0.30), 2)

        # 7. Contributing signal ranking
        ranked_signals = sorted(
            drifting_signals,
            key=lambda s: abs(z_scores[s]),
            reverse=True,
        )

        # 8. Lead cycle estimation
        lead_cycles: Optional[int] = None
        if confirmed_drift and ranked_signals:
            top_sig = ranked_signals[0]
            slope_val, _ = self.trend.get_trend_stats(top_sig)
            curr_val = signals[top_sig]
            env = self.fingerprint.operating_envelopes[top_sig]

            if slope_val > 0.01:
                dist = env.upper_limit - curr_val
                if dist <= 0:
                    lead_cycles = 1
                else:
                    lead_cycles = max(1, int(round(dist / slope_val)))
            elif slope_val < -0.01:
                dist = curr_val - env.lower_limit
                if dist <= 0:
                    lead_cycles = 1
                else:
                    lead_cycles = max(1, int(round(dist / abs(slope_val))))
            else:
                lead_cycles = 5

        # 9. Structured output
        metrics = DriftMetrics(
            ewma_breached=ewma_breached_any,
            cusum_breached=cusum_breached_any,
            multivariate_distance=round(d_m, 2),
            multivariate_threshold=round(self.multivariate.threshold, 2),
            multivariate_breached=multi_breach,
            max_z_score=round(max_abs_z, 2),
            consecutive_drift_count=self.consecutive_drift_count,
        )

        return DriftOutput(
            cycle_index=record.cycle_index,
            timestamp=record.timestamp,
            drift=confirmed_drift,
            severity=severity,
            lead_cycles=lead_cycles,
            signals=ranked_signals,
            details=details,
            metrics=metrics,
        )
