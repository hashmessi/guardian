# Phase 5: Recovery Verifier + Scrap Containment + State Machine — Research & Technical Architecture

## 1. Explicit State Machine Architecture (STMC-01, STMC-02)

### State Enum & Definition:
```python
class ProcessState(str, Enum):
    HEALTHY = "HEALTHY"
    DRIFT_SUSPECTED = "DRIFT_SUSPECTED"
    DRIFT_CONFIRMED = "DRIFT_CONFIRMED"
    QUALITY_RISK_HIGH = "QUALITY_RISK_HIGH"
    DIAGNOSING = "DIAGNOSING"
    INTERVENTION_EVALUATION = "INTERVENTION_EVALUATION"
    ABSTAIN = "ABSTAIN"
    QC_REQUIRED = "QC_REQUIRED"
    RECOMMEND = "RECOMMEND"
    APPLIED = "APPLIED"
    RECOVERY_CHECK = "RECOVERY_CHECK"
    RELEASE = "RELEASE"
    INTERVENTION_MEMORY = "INTERVENTION_MEMORY"
```

### Deterministic State Transitions:
1. `HEALTHY` $\to$ `DRIFT_SUSPECTED`: Drift sentinel single indicator triggered or z-score $> 2.0$.
2. `DRIFT_SUSPECTED` $\to$ `DRIFT_CONFIRMED`: Sentinel persistence gate satisfied ($k \ge 2$).
   - (or $\to$ `HEALTHY`: false alarm cleared, signals return to baseline).
3. `DRIFT_CONFIRMED` $\to$ `QUALITY_RISK_HIGH`: Calibrated defect probability $P_{\text{risk}} > 0.70$.
   - (or $\to$ `QC_REQUIRED`: if $0.35 \le P_{\text{risk}} \le 0.70$).
4. `QUALITY_RISK_HIGH` $\to$ `DIAGNOSING`: Automatic transition upon high risk confirmation.
5. `DIAGNOSING` $\to$ `INTERVENTION_EVALUATION`: Root cause report generated.
6. `INTERVENTION_EVALUATION` $\to$:
   - `RECOMMEND`: Confidence $\ge 0.65$ and at least one feasible action.
   - `QC_REQUIRED`: Confidence medium ($0.50 \le c < 0.65$) or risk borderline.
   - `ABSTAIN`: Confidence $< 0.65$ or all actions infeasible.
7. `RECOMMEND` $\to$ `APPLIED`: Intervention action applied (simulated event or operator confirm).
8. `APPLIED` $\to$ `RECOVERY_CHECK`: Automatic transition immediately after parameter step.
9. `RECOVERY_CHECK` $\to$:
   - `VERIFIED`: Parameter movement confirmed, $N \ge 3$ consecutive stable cycles, Quality Contract compliant.
   - `FAILED`: Parameter did not move, or stability window timeout ($M > 8$ cycles post-action).
10. `VERIFIED` $\to$ `RELEASE`: Production release authorized.
11. `RELEASE` $\to$ `INTERVENTION_MEMORY`: Episode saved to audit memory; returns to `HEALTHY`.
12. `FAILED` $\to$ `DIAGNOSING`: Automatic re-diagnosis with updated telemetry (or escalate).

### Event-Driven Transition Context:
The state machine maintains a mutable `MachineContext` tracking:
- `current_state: ProcessState`
- `active_drift_cycle: Optional[int]`
- `intervention_cycle: Optional[int]`
- `applied_action: Optional[CandidateAction]`
- `recovery_start_cycle: Optional[int]`
- `consecutive_stable_cycles: int`
- `state_history: List[StateTransitionRecord]`

---

## 2. Recovery Verification Protocol (RECV-01..05)

### Verification Pipeline Steps:
1. **Movement Verification (RECV-01)**:
   - Compares the post-intervention parameter value against the value at the intervention cycle.
   - For temperature reduction $\Delta T = -3.0^\circ\text{C}$: requires $T_{\text{post}} \le T_{\text{applied}} - 1.5^\circ\text{C}$.
2. **Dynamic Telemetry & Risk Re-Evaluation (RECV-02)**:
   - Pushes live post-intervention cycles through `TelemetryPipeline`, `DriftSentinel`, and `QualityEngine`.
   - Computes fresh $P_{\text{risk}}$ and drift severity on every cycle.
3. **Stability Window Evaluation (RECV-03)**:
   - Window size $N = 3$ consecutive cycles.
   - A cycle is considered stable if:
     - $P_{\text{risk}} < 0.35$ (low risk tier)
     - Targeted parameter is within fingerprint operating envelope $[\mu - 3\sigma, \mu + 3\sigma]$
     - Ground-truth defect flags are false
   - If a cycle fails stability before $N$ consecutive cycles are reached, counter resets to 0.
   - If timeout $M = 8$ cycles is reached without $N=3$ consecutive stable cycles, recovery is marked `FAILED`.
4. **Quality Contract Gate (RECV-04)**:
   - Evaluates `QualityContract.evaluate(record)`.
   - Part weight, cavity pressure, and sink mark depth must all be compliant before authorizing production release.
5. **Structured Recovery Status (RECV-05)**:
   - Emits structured report:
     - `risk_before` vs `risk_after`
     - `stability_before` vs `stability_after`
     - `parameter_movement_verified: bool`
     - `stability_window_cycles: int` ($N/3$)
     - `contract_compliant: bool`
     - `recovery_status: RecoveryStatus` (`VERIFIED`, `IN_PROGRESS`, `FAILED`)
     - `release_decision: ReleaseDecision` (`APPROVED`, `PENDING_VERIFICATION`, `REJECTED_QUARANTINE`)

---

## 3. Scrap Containment & Batch Disposition Engine (CNTN-01..04)

### Milestone Cycles:
- $c_{\text{lkg}}$ (`last_known_good`): The cycle immediately preceding the first confirmed drift alert ($c_{\text{drift}} - 1$).
- $c_{\text{drift}}$ (`drift_start`): First cycle drift sentinel confirmed persistent drift.
- $c_{\text{intervention}}$ (`intervention_cycle`): The cycle the corrective parameter shift was applied.
- $c_{\text{recovery}}$ (`recovery_cycle`): The cycle that completed the $N$-cycle stability window.
- $c_{\text{release}}$ (`release_cycle`): The cycle production was officially released ($c_{\text{recovery}} + 1$).

### Suspect Window & Disposition (CNTN-02, CNTN-04):
- **Suspect Window**: $[c_{\text{drift}}, c_{\text{recovery}}]$.
  Every cycle produced during this interval is tagged with `Disposition: QUARANTINE_INSPECT`.
  - Computes `suspect_part_count = (c_recovery - c_drift + 1) * parts_per_cycle`.
  - Categorizes scrap risk: high probability defective cycles vs marginal cycles.
- **Pre-Drift Window**: $[1, c_{\text{lkg}}]$.
  Tagged with `Disposition: RELEASED_PRE_DRIFT`.
- **Post-Recovery Window**: $[c_{\text{release}}, \dots]$.
  Tagged with `Disposition: RELEASED_POST_RECOVERY`.

---

## 4. End-to-End Demo Scenario Integration

In `build_demo_scenario(seed=42)`:
- Cycles 1 - 419: Healthy baseline $\to$ State: `HEALTHY`.
- Cycle 420: Thermal drift injected $\to$ Cycle 420-421: `DRIFT_SUSPECTED` $\to$ `DRIFT_CONFIRMED`.
- Cycle 430-440: Risk escalates $\to$ `QUALITY_RISK_HIGH` $\to$ `DIAGNOSING`.
- Cycle 441: `INTERVENTION_EVALUATION` $\to$ `RECOMMEND` (Action A1: Zone 3 $-3.0^\circ\text{C}$).
- Cycle 442: Action applied in simulator $\to$ State: `APPLIED` $\to$ `RECOVERY_CHECK`.
- Cycles 443 - 445: Temperature cools down, cavity pressure recovers, risk drops $\to$ Stability window ($1/3 \to 2/3 \to 3/3$).
- Cycle 446: Recovery complete $\to$ State: `VERIFIED` $\to$ `RELEASE`.
- Containment Window:
  - Last known good: 419
  - Suspect window: 420 to 445 (26 cycles quarantined for inspection)
  - Released: 446+
