# Phase 5: Recovery Verifier + Scrap Containment + State Machine — Context

## Objective
Build the **Post-Intervention Recovery Verifier** (`RECV-01..05`), **Scrap Containment Engine** (`CNTN-01..04`), and the explicit **System State Machine** (`STMC-01..02`) that governs the complete intervention lifecycle (Phase 5). This completes Process Guardian's core value proposition: **the closed operational decision loop: detect drift → diagnose cause → evaluate constrained interventions → recommend minimum-cost action → verify recovery → contain affected production**.

## Target Requirements
- **RECV-01**: After intervention, system confirms parameter movement in expected direction.
- **RECV-02**: System re-evaluates drift and recomputes quality risk post-intervention from live telemetry.
- **RECV-03**: System checks stability window (not immediate release — verifies $N \ge 3$ consecutive stable cycles).
- **RECV-04**: System verifies Quality Contract conditions before releasing production.
- **RECV-05**: System produces structured recovery status output: risk before/after, stability before/after, parameter movement, recovery status (VERIFIED/FAILED), and release decision.
- **CNTN-01**: System identifies last-known-good cycle before drift started.
- **CNTN-02**: System identifies suspect window (potentially affected cycles between drift detection and recovery).
- **CNTN-03**: System identifies intervention cycle, recovery cycle, and release cycle.
- **CNTN-04**: System answers "which production should we inspect, quarantine, or release?" with clear batch dispositions.
- **STMC-01**: System implements explicit state machine:
  `HEALTHY → DRIFT_SUSPECTED → DRIFT_CONFIRMED → QUALITY_RISK_HIGH → DIAGNOSING → INTERVENTION_EVALUATION → (ABSTAIN | QC_REQUIRED | RECOMMEND) → APPLIED → RECOVERY_CHECK → (FAILED → REASSESS | VERIFIED → RELEASE) → INTERVENTION_MEMORY`.
- **STMC-02**: State machine exists explicitly in code, not hidden inside UI logic.

## Mathematical & Operational Formulation

### 1. Explicit State Machine (STMC-01, STMC-02)
13 discrete operational states with deterministic transition guards:
1. `HEALTHY`: Baseline operation ($\text{severity} < 0.20$, $P_{\text{risk}} < 0.35$).
2. `DRIFT_SUSPECTED`: Single drift detector flag triggered (EWMA/CUSUM/z-score).
3. `DRIFT_CONFIRMED`: Multi-method persistence gate satisfied ($k \ge 2$ consecutive cycles).
4. `QUALITY_RISK_HIGH`: Calibrated defect probability $P_{\text{risk}} > 0.70$.
5. `DIAGNOSING`: Root-cause attribution engine running.
6. `INTERVENTION_EVALUATION`: Candidate action simulation and constraint optimization running.
7. `ABSTAIN`: Low confidence ($< 0.65$) or all actions infeasible.
8. `QC_REQUIRED`: Medium risk ($0.35 \le P_{\text{risk}} \le 0.70$), requesting physical QC sample.
9. `RECOMMEND`: High confidence ($\ge 0.65$), feasible minimum effective action ready.
10. `APPLIED`: Corrective intervention enacted on the line.
11. `RECOVERY_CHECK`: Post-intervention monitoring of parameter movement and stability window.
12. `RELEASE`: Recovery verified and Quality Contract confirmed; normal production release.
13. `INTERVENTION_MEMORY`: Episode archived for continuous learning and audit trail.

### 2. Recovery Verification Protocol (RECV-01..05)
Post-intervention verification is never instant; it requires:
1. **Parameter Movement Direction**:
   $$\Delta x_{\text{observed}} = x_{\text{curr}} - x_{\text{intervention}}$$
   Sign and magnitude must match candidate intent: $\text{sign}(\Delta x_{\text{observed}}) = \text{sign}(\Delta_{\text{action}})$ with $|\Delta x_{\text{observed}}| \ge 0.5 |\Delta_{\text{action}}|$.
2. **Dynamic Recalculation**:
   - Drift Sentinel re-evaluates EWMA/CUSUM on new cycles.
   - Quality Risk Model recomputes $P_{\text{risk}}$.
3. **Stability Window**:
   $$W_{\text{stable}} = [c_{\text{start}}, c_{\text{start}} + N - 1]$$
   Requires $N \ge 3$ consecutive cycles with $P_{\text{risk}} < 0.35$, all key signals within fingerprint envelope $[\mu - 3\sigma, \mu + 3\sigma]$, and drift severity $< 0.30$.
4. **Quality Contract Gate**:
   Physical part tolerances ($141.0 \le W \le 144.0$ g, sink mark $\le 0.08$ mm, flash = False) must be 100% compliant.
5. **Outcome**:
   - `VERIFIED`: Stability window met $\to$ `RELEASE APPROVED`.
   - `FAILED`: Parameter did not move, or stability window timeout ($M > 8$ cycles) $\to$ `REASSESS / QUARANTINE`.

### 3. Scrap Containment & Disposition Protocol (CNTN-01..04)
Partition production run into 3 disjoint sets:
1. `last_known_good`: $c_{\text{lkg}} = c_{\text{drift\_start}} - 1$.
2. `suspect_window`: $[c_{\text{drift\_start}}, c_{\text{recovery}}]$.
   - Cycles within this window are assigned `Disposition: QUARANTINE_INSPECT` (flagged for 100% manual or CMM inspection).
3. `release_cycle`: $c_{\text{release}} = c_{\text{recovery}} + 1$.
   - Subsequent production is assigned `Disposition: RELEASE_APPROVED`.
