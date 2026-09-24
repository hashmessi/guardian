# Phase 2: Process Fingerprint + Drift Sentinel - Context

**Gathered:** 2026-09-24
**Status:** Ready for planning
**Source:** PRD Express Path & Brutal Product Engine Specification

<domain>
## Phase Boundary

Build the context-specific process baseline engine (Process Fingerprint) and the multi-method drift detection engine (Drift Sentinel) that identifies process-state shifts before quality contract violations.
Phase 2 consumes normalized cycle records from Phase 1 (`NormalizedCycleRecord`) and outputs structured drift assessments (`DriftAlert`, `DriftSummary`).
Phase 2 does NOT build machine learning quality risk models (Phase 3) or intervention optimizers (Phase 4).

</domain>

<decisions>
## Implementation Decisions

### 1. Process Fingerprint Architecture
- **D-01:** Context-Specific Baselines: Fingerprints are identified by a unique context key composed of `machine_id:mold_id:part_id:recipe_id:recipe_version`.
- **D-02:** No Global Thresholds: Each production context calculates its own baseline statistics from healthy historical cycles (mean $\mu$, std $\sigma$, median, IQR, covariance matrix $\Sigma$, and inverse covariance $\Sigma^{-1}$).
- **D-03:** Operating Envelope: Derived empirically from $k$-sigma bounds ($\mu \pm 3\sigma$) and 1st/99th percentiles of baseline cycles, not hardcoded constants.
- **D-04:** Storage & Retrieval: `FingerprintStore` interface with in-memory cache and JSON persistence (`save()`, `get()`, `list()`).

### 2. Drift Sentinel Multi-Method Detection
- **D-05:** Multi-Method Statistical Fusion: Drift detection combines 4 complementary algorithms:
  1. **EWMA (Exponentially Weighted Moving Average):** $\lambda = 0.15, L = 2.8$ for detecting small persistent mean shifts.
  2. **CUSUM (Cumulative Sum Control Chart):** Slack $K = 0.5\sigma$, decision threshold $H = 4.5\sigma$ for gradual parameter creep.
  3. **Rolling Trend / Slope:** Least-squares linear slope over sliding window of 15 cycles.
  4. **Multivariate Distance:** Mahalanobis distance $D_M = \sqrt{(x - \mu)^T \Sigma^{-1} (x - \mu)}$ across key correlated process signals.
- **D-06:** Persistence Requirement: An alert triggers only when statistical deviations persist for $\ge 2$ consecutive cycles (prevents single-cycle noise spikes from causing false alarms).
- **D-07:** Structured Output Contract:
  ```json
  {
    "drift": true,
    "severity": 0.78,
    "lead_cycles": 11,
    "signals": ["barrel_temp_z3", "injection_pressure", "cycle_time"],
    "metrics": {
      "ewma_drift": true,
      "cusum_drift": true,
      "multivariate_distance": 4.82,
      "worst_z_score": 3.4
    }
  }
  ```
- **D-08:** Severity Scoring: Calibrated continuous score in $[0.0, 1.0]$ based on normalized multivariate distance and standardized z-scores.
- **D-09:** Lead Time Estimation: Calculates remaining lead cycles before the fastest-drifting parameter reaches operating envelope limits using slope extrapolation: $cycles_{lead} = \frac{\text{envelope\_limit} - x_t}{slope}$.

### 3. False Alarm & Noise Rejection
- **D-10:** Rejection of Sensor Noise: High-frequency zero-mean sensor jitter (`SENSOR_NOISE` regime) must NOT trigger drift alarms. EWMA and CUSUM filters naturally smooth zero-mean noise.
- **D-11:** Minimum Sample Gate: Drift detection requires a minimum of 10 cycles of warm-up before activating alerts, with confidence marked accordingly.

### Principal Engineer's Discretion
- Matrix inversion regularization ($\Sigma + \epsilon I$) to handle collinear sensor signals.
- Internal signal ranking heuristic for attributing contributing signals.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents and implementers MUST read these before planning or implementing.**

### Architecture & Requirements
- `.planning/REQUIREMENTS.md` § Process Fingerprint (FPRN-01..FPRN-03) & Drift Detection (DRFT-01..DRFT-04)
- `.planning/PRODUCT_SPECIFICATION.md` § F2 (Process Fingerprint Engine) & § F3 (Drift Sentinel)
- `Process_Guardian_ARCHITECTURE_BUILD_PLAN.md` § Statistical Process Control & Drift Formulation

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/process_guardian/adapter/schemas.py`: `NormalizedCycleRecord`, `EnrichedContext`
- `src/process_guardian/simulator/engine.py`: `InjectionMoldingSimulator` for generating baseline and drifted streams
- `src/process_guardian/simulator/scenarios.py`: `build_demo_scenario` for benchmark testing

### Established Patterns
- Pydantic v2 schemas and models
- NumPy statistical computations
- Pytest testing framework

</code_context>

<specifics>
## Specific Ideas

- In the demo scenario:
  - Drift starts at cycle 420 (thermal drift on z3).
  - Drift Sentinel must flag drift by cycle 428-430 ($\ge 8$ cycles lead time before defect at cycle 438-440).
  - Contributing signal ranking must highlight `barrel_temp_z3` as #1 and `injection_pressure` as #2.

</specifics>

<deferred>
## Deferred Ideas

- None — All items fall strictly within Phase 2 requirements.
- Supervised ML risk modeling with XGBoost is Phase 3.

</deferred>

---

*Phase: 02-process-fingerprint-drift-sentinel*
*Context gathered: 2026-09-24 via PRD Express Path*
