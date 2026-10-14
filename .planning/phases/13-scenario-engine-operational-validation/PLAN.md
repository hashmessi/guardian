# Phase 13: Scenario Engine & Operational Validation Suite

## Goal
Upgrade Process Guardian from a single injected-drift demo into a deterministic, scenario-driven industrial validation system running through the identical closed-loop Guardian decision pipeline.

## Implementation Specifications
Derived from `architecture.md` (lines 1-776):
- Scenario definitions must be data-driven, not hardcoded code branches.
- Every scenario must run through the same Guardian decision pipeline: Digital Factory → Data Adapter → Fingerprint → Drift → Risk → Diagnosis → Intervention → Recovery → Containment → QC → Release.
- Deterministic seeds, reproducible trajectories, and counterfactual baseline (Guardian OFF vs Guardian ON) comparison.
- 10 Industrial Scenarios:
  1. Thermal drift (Hero scenario)
  2. Injection pressure drift
  3. Material moisture excursion (Material gate)
  4. Recipe / setting drift (Clerical error / configuration mismatch)
  5. Mold-release spray checkpoint (Operational maintenance interval)
  6. Compound / multi-signal drift (Boss scenario)
  7. Normal variation (False-positive robustness)
  8. Low confidence / abstain (Safety gate)
  9. Failed intervention (Safety hold / escalation)
  10. Successful recovery + release (Complete closed-loop lifecycle)

---

## Concise Phase Execution Plans

### Phase 13.1: Deterministic Scenario Registry & Disturbance Injection Framework
- **Models**: `DisturbanceSpec`, `OperationalOverrideSpec`, `ScenarioDefinition`, `ScenarioRunResult`, `ScenarioScorecard`.
- **Registry**: 10 deterministic scenario definitions with calibrated parameters, seeds, and lifecycle milestones.
- **Injector & Runner**: Dynamic simulation disturbance driver and cycle orchestrator executing through `ClosedLoopOrchestrator`.

### Phase 13.2: Counterfactual Dual Replay & Operational Scorecard Engine
- **Counterfactual Engine**: Exact same seed and disturbance trajectory executed under Guardian OFF (status quo uncontained drift) vs Guardian ON (closed-loop intervention).
- **Scorecard Evaluator**: Asserts detection, root-cause diagnosis, constrained action, recovery verification, suspect containment, and QC release gate.
- **Validation Suite**: Batch runner executing all 10 scenarios and aggregating industrial reliability metrics.
- **API Endpoints**: `/api/scenarios`, `/api/scenarios/{id}`, `/api/scenarios/{id}/select`, `/api/scenarios/{id}/run`, `/api/scenarios/validation-suite`.

### Phase 13.3: Frontend Scenario Selector, Evidence Scorecard & Validation Suite
- **UI Components**:
  - Scenario Selector in header allowing instant switching between hero scenarios.
  - Scenario Timeline Bar displaying healthy, drift, intervention, recovery, and QC intervals.
  - Scenario Result Scorecard Modal displaying the 7-pillar verification checklist.
  - 10-Scenario Operational Validation Suite Modal displaying 10/10 verified status and aggregate metrics.
- **Verification**:
  - All existing 144 unit/integration tests must pass.
  - New comprehensive test suite for scenario engine, counterfactuals, and API routes.
  - Browser verification of UI controls, scenario playback, and scorecards.
