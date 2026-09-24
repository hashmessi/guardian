# Phase 2: Process Fingerprint + Drift Sentinel - Research

**Researched:** 2026-09-24
**Domain:** Statistical Process Control, Non-Stationary Drift Detection & Multivariate Anomaly Detection
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Context-Specific Baselines: Fingerprints identified by unique context key `machine_id:mold_id:part_id:recipe_id:recipe_version`.
- **D-02:** No Global Thresholds: Each production context learns its own normal ($\mu$, $\sigma$, percentiles, covariance $\Sigma$).
- **D-03:** Operating Envelope: Derived empirically from $k$-sigma bounds ($\mu \pm 3\sigma$) and percentiles of baseline cycles.
- **D-04:** Storage & Retrieval: `FingerprintStore` with in-memory caching and JSON serialization.
- **D-05:** Multi-Method Statistical Fusion: EWMA ($\lambda=0.15$), CUSUM ($K=0.5\sigma, H=4.5\sigma$), rolling slope (window=15), and multivariate Mahalanobis distance ($D_M$).
- **D-06:** Persistence Requirement: Alert triggers only when drift conditions persist for $\ge 2$ consecutive cycles.
- **D-07:** Structured Output Contract: `{drift: bool, severity: float, lead_cycles: int, signals: List[str], metrics: dict}`.
- **D-08:** Severity Scoring: Calibrated continuous score in $[0.0, 1.0]$.
- **D-09:** Lead Time Estimation: Calculates remaining lead cycles before operating limit breach using slope extrapolation.
- **D-10:** Sensor Noise Rejection: High-frequency zero-mean sensor jitter (`SENSOR_NOISE` regime) must NOT trigger drift alarms.
- **D-11:** Minimum Sample Gate: Minimum 10 cycles warm-up before activating alerts.

### Principal Engineer's Discretion
- Matrix regularization: add ridge $\epsilon I$ ($\epsilon = 10^{-4}$) to covariance matrix before inversion to prevent numerical instability from collinear sensors (e.g. z4 and z5 temperatures).
- Signal attribution ranking formula using standardized absolute z-scores $|(x_i - \mu_i)/\sigma_i|$.

</user_constraints>

<research_summary>
## Summary

Standard Statistical Process Control (SPC) in manufacturing relies on control charts (Shewhart, EWMA, CUSUM) to separate common cause variability (inherent process noise) from special cause variability (drift, tool wear, material inconsistency). For high-precision injection molding, single-parameter Shewhart charts fail because gradual drifts (such as heater degradation or progressive check-ring wear) move in tiny increments that do not cross $\pm 3\sigma$ Shewhart limits until many defective cycles have already been stamped out.

EWMA and CUSUM accumulate historical deviations, making them 3× to 5× faster at detecting subtle shifts of magnitude 0.5 to 1.5 standard deviations. Coupled with multivariate Mahalanobis distance, which accounts for correlations across temperatures, pressures, and timings, the system detects multidimensional state drift long before any individual sensor breaches traditional alarm thresholds.
</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `numpy` | 1.26+ | Linear algebra & vector math | Covariance computation (`np.cov`), matrix inversion (`np.linalg.pinv`), vectorized z-scores |
| `scipy` | 1.13+ | Statistical distributions | Chi-squared distribution (`scipy.stats.chi2`) for calibrated Mahalanobis p-values and critical values |
| `pydantic` | 2.10+ | Schema validation & serialization | Strongly typed schemas for `ProcessFingerprint`, `DriftOutput`, `SignalMetrics` |
| `pytest` | 8.0+ | Test framework | Deterministic verification of detection lead time and false-positive rejection |

</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Recommended Project Structure
```
src/process_guardian/
├── fingerprint/
│   ├── __init__.py
│   ├── models.py       # Pydantic schemas: SignalStats, OperatingEnvelope, ProcessFingerprint
│   ├── builder.py      # FingerprintBuilder (computes stats, covariance, envelope from baseline cycles)
│   └── store.py        # FingerprintStore (in-memory + JSON persistence)
└── sentinel/
    ├── __init__.py
    ├── ewma.py         # Exponentially Weighted Moving Average detector
    ├── cusum.py        # Cumulative Sum (upper and lower) detector
    ├── multivariate.py # Mahalanobis distance detector with ridge regularization
    ├── trend.py        # Sliding window least-squares slope & variance ratio
    ├── detector.py     # DriftSentinel multi-method fusion engine
    └── schemas.py      # DriftOutput, DriftMetrics, DriftSeverity schemas
```

### Statistical Formulation

#### 1. EWMA
For signal $i$ at cycle $t$:
$$z_{i,t} = \lambda x_{i,t} + (1 - \lambda) z_{i, t-1}, \quad z_{i,0} = \mu_i$$
Control limits:
$$UCL_{i,t} = \mu_i + L \sigma_i \sqrt{\frac{\lambda}{2 - \lambda} \left[1 - (1 - \lambda)^{2t}\right]}$$
$$LCL_{i,t} = \mu_i - L \sigma_i \sqrt{\frac{\lambda}{2 - \lambda} \left[1 - (1 - \lambda)^{2t}\right]}$$
With $\lambda = 0.15$ and $L = 2.8$, EWMA detects $1.0\sigma$ shifts within 4-7 cycles while maintaining false alarm rates $< 0.2\%$.

#### 2. Tabular CUSUM
Standardized score $y_{i,t} = \frac{x_{i,t} - \mu_i}{\sigma_i}$:
$$C_{i,t}^+ = \max(0, C_{i,t-1}^+ + y_{i,t} - K)$$
$$C_{i,t}^- = \max(0, C_{i,t-1}^- - y_{i,t} - K)$$
With reference value $K = 0.5$ and decision interval $H = 4.5$, CUSUM flags drift when $\max(C^+, C^-) > H$.

#### 3. Regularized Mahalanobis Distance
Given $p$-dimensional feature vector $\mathbf{x}_t$, mean vector $\boldsymbol{\mu}$, and sample covariance $\mathbf{\Sigma}$:
$$\mathbf{\Sigma}_{reg} = \mathbf{\Sigma} + \epsilon \mathbf{I}, \quad \epsilon = 10^{-4}$$
$$D_M(\mathbf{x}_t) = \sqrt{(\mathbf{x}_t - \boldsymbol{\mu})^T \mathbf{\Sigma}_{reg}^{-1} (\mathbf{x}_t - \boldsymbol{\mu})}$$
Under healthy conditions, $D_M^2 \sim \chi^2(p)$. A multivariate drift is flagged when $D_M > \sqrt{\chi^2_{0.99}(p)}$.

</architecture_patterns>

<validation_architecture>
## Validation Architecture

Nyquist test plan for Phase 2:
- `tests/test_fingerprint.py`:
  - Validates fingerprint fitting from healthy records: computes accurate means, standard deviations, and non-singular covariance matrices.
  - Validates context separation: Machine A with Recipe X produces distinct fingerprint from Machine B with Recipe Y.
  - Validates storage and retrieval: saving to store and retrieving by context yields identical models.
- `tests/test_drift_sentinel.py`:
  - Validates EWMA and CUSUM single-variable tracking.
  - Validates Mahalanobis multivariate distance calculation.
  - Validates persistence gate: single transient spike does not trigger drift; persistent drift for $\ge 2$ cycles triggers alert.
  - Validates signal contribution ranking: identifies drifting signals in correct order of deviation.
- `tests/test_drift_benchmark.py`:
  - Validates false-positive rejection:
    - 200 cycles of healthy baseline (`HEALTHY` regime) produces 0 false drift alerts.
    - 200 cycles of high sensor noise (`SENSOR_NOISE` regime) produces 0 false drift alerts.
  - Validates early warning lead time:
    - Primary demo scenario (drift injected at cycle 420): Drift Sentinel triggers alert between cycle 426 and 431.
    - Quality defect occurs at cycle 439.
    - Guaranteed lead time $\ge 8$ cycles ($\ge 5$ cycles required by PS02 spec).

</validation_architecture>

---

*Phase: 02-process-fingerprint-drift-sentinel*
*Research completed: 2026-09-24*
*Ready for planning: yes*
