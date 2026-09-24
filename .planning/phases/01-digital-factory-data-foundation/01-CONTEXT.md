# Phase 1: Digital Factory + Data Foundation - Context

**Gathered:** 2026-09-24
**Status:** Ready for planning
**Source:** PRD Express Path & Brutal Product Engine Specification

<domain>
## Phase Boundary

Build the deterministic cycle-level injection molding simulator with event injection and the data adapter layer that normalizes telemetry for all downstream engines.
Phase 1 delivers the data foundation (SIM-01..05, DADP-01..03). It does NOT build drift detectors (Phase 2), quality risk ML models (Phase 3), or intervention optimizers (Phase 4).

</domain>

<decisions>
## Implementation Decisions

### 1. Telemetry & Simulation Fidelity
- **D-01:** Cycle-level granularity is the primary telemetry contract. Each cycle generates a comprehensive summary record containing:
  - Temperatures: `barrel_temp_z1`, `barrel_temp_z2`, `barrel_temp_z3`, `barrel_temp_z4`, `barrel_temp_z5`, `nozzle_temp` (°C)
  - Pressures: `injection_pressure`, `peak_pressure`, `hold_pressure` (bar)
  - Timings: `injection_time`, `hold_time`, `cooling_time`, `cycle_time` (seconds)
  - Material & Environment: `material_moisture` (%), `ambient_temp` (°C), `ambient_humidity` (%)
  - Quality Ground Truth: `part_weight` (grams), `sink_mark_depth` (mm), `flash_observed` (bool), `defect_flag` (bool)
- **D-02:** Purely deterministic replay via seeded pseudo-random number generator (NumPy RNG with default seed 42). Two runs with the same seed and injection profile must produce bitwise identical sequence records.

### 2. Regimes & Drift Physics
- **D-03:** Support 9 explicit regimes:
  1. `healthy`: Stationary process centered on recipe targets with Gaussian white noise (~0.5% CV).
  2. `thermal_drift`: Linear/exponential drift in zone-3 heater temperature (+0.15°C to +0.3°C/cycle).
  3. `pressure_drift`: Gradual loss of hydraulic/screw pressure (-0.25 bar/cycle) simulating valve wear.
  4. `moisture_drift`: Hopper moisture increase (from 0.02% to 0.15%), altering plastic viscosity.
  5. `cycle_instability`: Cooling water flow fluctuations causing erratic cycle time variations.
  6. `combined_drift`: Simultaneous thermal + moisture drift (multi-factor degradation).
  7. `sensor_noise`: High-frequency sensor jitter/spikes on thermocouple or pressure transducer without true underlying melt shift (tests false positive avoidance).
  8. `recovery`: Controlled parameter adjustment back into nominal operating envelope.
  9. `unseen_drift`: Oscillatory PID hunting pattern to test anomaly generalization.
- **D-04:** Causal relationship formulation:
  - Moisture spike → decreases polymer melt viscosity → drops injection peak pressure resistance → changes cushion/hold behavior → alters part shrinkage and reduces part weight.
  - Barrel temperature rise → lowers melt viscosity → lower peak pressure, higher flash risk → part weight increase if hold pressure constant.
  - Cycle time instability → cooling time variance → thermal contraction variance → dimensional and weight variance.

### 3. Event Injection API
- **D-05:** Explicit programmatic API:
  `inject_event(event_type: str, start_cycle: int, severity: float = 1.0, duration: Optional[int] = None, params: Optional[dict] = None)`
- **D-06:** Support both pre-scheduled injections (for repeatable test/demo scenarios like `inject_event("thermal_drift", cycle=420)`) and dynamic real-time injections during simulator execution.
- **D-07:** Deterministic scenario runner with one-click reset: `simulator.reset()` returns the simulator to cycle 0 with pristine initial conditions.

### 4. Data Adapter & Ingestion Pipeline
- **D-08:** Pydantic v2 data models for rigorous schema enforcement and validation.
- **D-09:** Unit normalization:
  - Temperatures normalized to Celsius (°C)
  - Pressures normalized to bar (automatic conversion if input is MPa or psi)
  - Times normalized to seconds (s)
  - Weights normalized to grams (g)
  - Moisture normalized to percentage (%)
- **D-10:** Strict monotonic cycle sequencing and ISO 8601 UTC timestamp generation (`timestamp` as datetime/string).
- **D-11:** Range bounds validation and sensor quality flagging:
  - If a signal exceeds physical plausibility bounds (e.g., barrel temp < 50°C or > 450°C), flag as `OUT_OF_BOUNDS`.
  - If a required signal is None or missing, flag as `MISSING_SIGNAL` and attach quality flag without crashing the pipeline.
- **D-12:** Context enrichment: Every cycle record must be tagged with production context:
  - `machine_id` (e.g., "IMM-01")
  - `mold_id` (e.g., "MOLD-HOUSING-04")
  - `part_id` (e.g., "PART-AUTO-HOUSING-A")
  - `recipe_id` and `recipe_version` (e.g., "RECIPE-PP-V2.1")
  - `material_batch` (e.g., "BATCH-20260924-A")
  - `operator_id` (e.g., "OP-102")

### Principal Engineer's Discretion
- Exact mathematical coefficients for the causal surrogate formulas (calibrated to realistic polypropylene automotive housing values).
- Internal class hierarchy and modular directory structure under `src/process_guardian/`.
- File naming conventions and fixture designs for unit tests.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents and implementers MUST read these before planning or implementing.**

### Architecture & Requirements
- `.planning/REQUIREMENTS.md` § Simulator (SIM-01..SIM-05) & Data Adapter (DADP-01..DADP-03)
- `.planning/PRODUCT_SPECIFICATION.md` § F1 (Digital Factory Simulator), § F2 (Data Adapter), § 13 (Data Requirements)
- `Process_Guardian_ARCHITECTURE_BUILD_PLAN.md` § Phase 1 Specifications & Mathematical Regimes

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None (Greenfield project starting Phase 1).

### Established Patterns
- Python 3.12 modern type hinting (`typing`, `dataclasses`, `pydantic`).
- Clean separation between simulation physics, event scheduling, and data normalization.

### Integration Points
- Simulator output feeds directly into the Data Adapter pipeline.
- Data Adapter output will feed Phase 2 Fingerprint & Drift Sentinel engines.

</code_context>

<specifics>
## Specific Ideas

- In the demo scenario:
  - Cycles 1 to 419: Nominal healthy baseline.
  - Cycle 420: `inject_event("thermal_drift", cycle=420, severity=0.8)`.
  - Cycles 420 to 441: Thermal drift develops, pressure drops, part weight drifts.
  - Cycle 442: Simulated operator intervention applied (barrel temp adjusted down by -3°C).
  - Cycles 443 to 446: Process stabilizes back toward nominal.
  - Cycle 447+: Verified recovery and production release.

</specifics>

<deferred>
## Deferred Ideas

- None — All items fall strictly within Phase 1 requirements.
- Process Fingerprint and EWMA/CUSUM drift calculation are explicitly Phase 2.
- XGBoost/LightGBM quality risk modeling is Phase 3.

</deferred>

---

*Phase: 01-digital-factory-data-foundation*
*Context gathered: 2026-09-24 via PRD Express Path*
