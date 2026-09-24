# Phase 1: Digital Factory + Data Foundation - Research

**Researched:** 2026-09-24
**Domain:** Deterministic Cycle-Level Industrial Simulation & Telemetry Normalization
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Cycle-level granularity is the primary telemetry contract: temperatures (z1-z5, nozzle), pressures (injection, peak, hold), timings (injection, hold, cooling, cycle), material & environment (moisture, ambient temp/humidity), and quality ground truth (part weight, sink mark, flash, defect flag).
- **D-02:** Purely deterministic replay via seeded pseudo-random number generator (NumPy RNG with default seed 42). Two runs with the same seed and injection profile produce bitwise identical sequence records.
- **D-03:** Support 9 explicit regimes: healthy, thermal_drift, pressure_drift, moisture_drift, cycle_instability, combined_drift, sensor_noise, recovery, unseen_drift.
- **D-04:** Causal relationship formulation: moisture ↑ → melt viscosity ↓ → injection peak pressure drops → hold/cushion shift → part weight drop/variance; thermal drift → viscosity ↓ → pressure drop; cycle instability → cooling variation → part weight/shrinkage variance.
- **D-05:** Explicit programmatic API: `inject_event(event_type: str, start_cycle: int, severity: float = 1.0, duration: Optional[int] = None, params: Optional[dict] = None)`.
- **D-06:** Support both pre-scheduled injections (for repeatable test/demo scenarios like `inject_event("thermal_drift", cycle=420)`) and dynamic real-time injections.
- **D-07:** Deterministic scenario runner with one-click reset: `simulator.reset()` returns the simulator to cycle 0 with pristine initial conditions.
- **D-08:** Pydantic v2 data models for rigorous schema enforcement and validation.
- **D-09:** Unit normalization: Temperatures to °C, pressures to bar, times to seconds, weights to grams, moisture to %.
- **D-10:** Strict monotonic cycle sequencing and ISO 8601 UTC timestamp generation.
- **D-11:** Range bounds validation and sensor quality flagging: Out-of-bounds flagged as `OUT_OF_BOUNDS`, missing signals flagged as `MISSING_SIGNAL` with `quality_flags`.
- **D-12:** Context enrichment: Every cycle record tagged with machine_id, mold_id, part_id, recipe_id, recipe_version, material_batch, operator_id.

### Principal Engineer's Discretion
- Mathematical coefficients for causal surrogate formulas calibrated to realistic automotive PP (polypropylene) housing specs.
- Directory and package layout under `src/process_guardian/`.
- Test harness structure and test fixtures under `tests/`.

### Deferred Ideas (OUT OF SCOPE)
- Drift detection engines (Phase 2).
- XGBoost/LightGBM ML models (Phase 3).
- Intervention optimization and surrogate actions (Phase 4).
- Database persistence & FastAPI endpoints (Phase 6).

</user_constraints>

<research_summary>
## Summary

Phase 1 establishes the mathematical bedrock and ingestion pipeline for Process Guardian. The objective is to build a high-performance, deterministic cycle-level injection molding simulator capable of simulating realistic factory dynamics and a data adapter that ingests, validates, normalizes, and enriches telemetry into strongly-typed domain records.

Industry-standard approaches in discrete manufacturing simulation rely on state-space equations with coupled causal terms rather than heavyweight continuous finite element analysis (FEA). For high-volume automotive injection molding (specifically polypropylene exterior/interior housing), the dominant physical relationships linking raw material moisture, barrel heating, and hydraulic pressure to part weight and dimensional shrinkage are well-characterized by empirical pvT (pressure-volume-temperature) relationships.

The primary recommendation is to implement the simulator as a stateful, seedable Python generator with an active event queue, coupled with a multi-stage Pydantic v2 validation and enrichment pipeline that guarantees type safety and failure tolerance without crashing on corrupt sensor packets.
</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `python` | 3.12+ | Core runtime | Modern type annotations, performance optimizations |
| `numpy` | 1.26+ | Deterministic RNG & vectorized math | `numpy.random.default_rng(seed)` guarantees bitwise reproducible pseudo-random streams across platforms |
| `pydantic` | 2.10+ | Schema validation & serialization | High-performance Rust-backed validation, explicit field constraints, custom validators |
| `pytest` | 8.0+ | Test framework | Standard Python testing with fixtures, parameterization, and assertion introspection |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `dataclasses` | stdlib | Lightweight data carriers | Internal simulator physics state representation |
| `datetime` | stdlib | ISO 8601 timestamping | Monotonic cycle timestamp creation |
| `json` / `csv` | stdlib | Serialization & dataset export | Exporting generated telemetry streams for offline inspection and model training |

</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Recommended Project Structure
```
c:\Users\Hashvanth\Hack4purpose\
├── src/
│   └── process_guardian/
│       ├── __init__.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── types.py          # Enums, shared domain types
│       │   └── constants.py      # Baseline nominals, unit constants
│       ├── simulator/
│       │   ├── __init__.py
│       │   ├── engine.py         # InjectionMoldingSimulator stateful runner
│       │   ├── regimes.py        # 9 baseline regime definitions & generators
│       │   ├── physics.py        # Causal coupling functions (moisture, thermal, pressure)
│       │   ├── events.py         # Event queue, scheduled & dynamic injection API
│       │   └── scenarios.py      # Standard 10-step demo scenario & regime test suites
│       └── adapter/
│           ├── __init__.py
│           ├── schemas.py        # Pydantic models for raw and normalized payloads
│           ├── normalizer.py     # Unit conversions and timestamping
│           ├── validator.py      # Physical bounds checking & quality flagging
│           ├── enricher.py       # Context injection (machine, mold, recipe, batch)
│           └── pipeline.py       # TelemetryPipeline end-to-end ingest function
└── tests/
    ├── __init__.py
    ├── conftest.py               # Shared fixtures (simulator instances, seed fixtures)
    ├── test_simulator_core.py    # Tests for SIM-01, SIM-02, SIM-05
    ├── test_event_injection.py   # Tests for SIM-03, SIM-04
    ├── test_data_adapter.py      # Tests for DADP-01, DADP-02, DADP-03
    └── test_digital_factory_e2e.py # Complete Phase 1 integration verification
```

### Pattern 1: Pure Seeded Generator with Step Execution
**What:** The simulator encapsulates state inside an `InjectionMoldingSimulator` class initialized with a base seed.
**When to use:** All cycle generation.
**Example:**
```python
class InjectionMoldingSimulator:
    def __init__(self, seed: int = 42, context: Optional[MachineContext] = None):
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.current_cycle = 0
        self.context = context or DEFAULT_CONTEXT
        self.event_queue: List[ScheduledEvent] = []
        self.state = SimulatorState()

    def reset(self, new_seed: Optional[int] = None) -> None:
        if new_seed is not None:
            self.seed = new_seed
        self.rng = np.random.default_rng(self.seed)
        self.current_cycle = 0
        self.state = SimulatorState()
        self.event_queue.clear()

    def step(self) -> RawCycleTelemetry:
        self.current_cycle += 1
        # Apply active events, evaluate physics dynamics, sample process noise
        ...
```

### Pattern 2: Defensive Pipeline Ingestion
**What:** Incoming raw telemetry is parsed, validated against physical bounds, normalized into standard units, and enriched with machine context without throwing uncaught exceptions.
**When to use:** Telemetry adapter layer.
**Example:**
```python
class TelemetryPipeline:
    def __init__(self, context: MachineContext):
        self.context = context

    def process_cycle(self, raw_data: dict) -> NormalizedCycleRecord:
        # 1. Parse raw data into RawTelemetryPayload (tolerant parsing)
        # 2. Validate range bounds and collect quality flags
        # 3. Normalize units (e.g. psi -> bar, °F -> °C)
        # 4. Attach monotonic sequence and ISO timestamp
        # 5. Enrich with machine, mold, part, recipe metadata
        # 6. Return validated NormalizedCycleRecord
```

### Anti-Patterns to Avoid
- **Global Random State:** Never use `random.random()` or unseeded `np.random`. Always use `np.random.default_rng(seed)` bound to the class instance.
- **Unchecked Physical Realism:** Don't simulate variables independently. When zone-3 temperature rises by 5°C, melt viscosity must drop, peak injection pressure must decrease, and part weight must react.
- **Hard-coded Threshold Discard:** Never drop malformed packets silently. Tag them with `SignalQualityFlags` so downstream models know a sensor dropped.

</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Seeded RNG | Custom LCG or standard `random` | `numpy.random.default_rng` | NumPy's PCG64 generator guarantees cross-platform reproducibility and vectorized statistical samplers |
| Schema & Range Validation | Manual `if x < min: raise ValueError` | Pydantic v2 `BaseModel` + `Field(ge=..., le=...)` | High performance, clear error messages, automatic coercion, JSON serialization |
| ISO 8601 Timestamps | Custom string formatting | `datetime.now(timezone.utc).isoformat()` | Handles timezones, leap seconds, strict standard compliance |

</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Seed Drift Across Scenario Resets
**What goes wrong:** Calling `reset()` doesn't restore the exact same sequence if intermediate method calls modified unmanaged RNG state.
**Why it happens:** Re-using generator state or having secondary unseeded calls to `random`.
**How to avoid:** Reset explicitly re-instantiates `self.rng = np.random.default_rng(self.seed)` and clears all mutable state.
**Warning signs:** Running cycle 1-50 twice produces different 50th cycle values.

### Pitfall 2: Disconnected Failure Dynamics
**What goes wrong:** Temperature drifts upwards, but pressure and part quality remain nominal.
**Why it happens:** Variables are modeled in silos.
**How to avoid:** Implement explicit coupling equations in `physics.py` where temperature and moisture act as inputs to the pressure and weight transfer functions.

### Pitfall 3: Crashing on Missing or Corrupt Signals
**What goes wrong:** An unexpected `None` or out-of-range sensor value throws a 500 error in the ingestion pipeline.
**Why it happens:** Strict schemas without fallback / partial validation.
**How to avoid:** Define optional fields with default fallbacks and store errors in a dedicated `quality_flags` dictionary on the record.

</common_pitfalls>

<code_examples>
## Code Examples

### Baseline Automotive PP Parameters
```python
# Polypropylene Automotive Housing Nominal Parameters:
NOMINAL_PARAMETERS = {
    "barrel_temp_z1": 210.0,   # Feed zone (°C)
    "barrel_temp_z2": 220.0,   # Compression zone (°C)
    "barrel_temp_z3": 230.0,   # Metering zone (°C)
    "barrel_temp_z4": 235.0,   # Transition zone (°C)
    "barrel_temp_z5": 235.0,   # Front zone (°C)
    "nozzle_temp": 240.0,      # Nozzle (°C)
    "injection_pressure": 110.0, # Main injection (bar)
    "peak_pressure": 135.0,    # Peak cavity transfer (bar)
    "hold_pressure": 65.0,     # Holding packing pressure (bar)
    "injection_time": 2.4,     # Fill time (s)
    "hold_time": 6.5,          # Packing time (s)
    "cooling_time": 14.0,      # In-mold cooling time (s)
    "cycle_time": 28.5,        # Total cycle time (s)
    "part_weight": 142.5,      # Nominal part weight (g)
    "material_moisture": 0.02, # Material moisture content (%)
    "ambient_temp": 28.0,      # Shopfloor temp (°C)
    "ambient_humidity": 55.0,  # Shopfloor humidity (%)
}
```

### Causal Coupled Equations
```python
# Temperature influence on peak pressure and part weight:
# ΔT_z3 = current_T_z3 - nominal_T_z3
# Δviscosity ~ -0.015 * ΔT_z3
# Δpeak_pressure = nominal_peak_pressure * (1.0 + Δviscosity)
# Δpart_weight = nominal_weight * (1.0 + 0.0012 * ΔT_z3 - 0.0008 * Δpeak_pressure)
```

</code_examples>

<validation_architecture>
## Validation Architecture

The test suite enforces Nyquist feedback sampling across all Phase 1 deliverables:
- `tests/test_simulator_core.py`:
  - Validates nominal values for all 18 telemetry signals against industrial PP targets.
  - Validates all 9 regimes run without error and demonstrate expected statistical signatures.
  - Validates deterministic repeatability: two runs with `seed=42` produce bitwise identical records over 100 cycles.
  - Validates `simulator.reset()` returns the system to pristine state.
- `tests/test_event_injection.py`:
  - Validates `inject_event("thermal_drift", cycle=420)` triggers at cycle 420 and initiates gradual temperature increase.
  - Validates causal coupling: moisture spike at cycle 50 directly causes drop in injection peak pressure and part weight variance.
  - Validates dynamic mid-run injections.
- `tests/test_data_adapter.py`:
  - Validates unit normalization: inputs in psi are converted to bar (1 bar = 14.5038 psi), MPa to bar (1 MPa = 10 bar).
  - Validates out-of-bounds detection: flags temperatures > 450°C as `OUT_OF_BOUNDS`.
  - Validates missing signal tolerance: `None` for optional fields flags `MISSING_SIGNAL` without raising unhandled exceptions.
  - Validates metadata enrichment: machine ID, mold ID, part ID, recipe ID, and batch are attached to every record.
- `tests/test_digital_factory_e2e.py`:
  - Runs the full 500-cycle demo progression: Healthy (1-419) → Drift (420-441) → Intervention (442) → Recovery (443-446) → Release (447+).
  - Verifies that raw simulator output flows seamlessly through the Data Adapter into fully validated, normalized, enriched records ready for Phase 2.

</validation_architecture>

---

*Phase: 01-digital-factory-data-foundation*
*Research completed: 2026-09-24*
*Ready for planning: yes*
