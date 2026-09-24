# Phase 4: Intervention Engine + Recommendation — Context

## Objective
Build the **Constrained Intervention Engine** and **Action Recommendation System** (Phase 4). When process drift and high quality risk are confirmed, Process Guardian evaluates at least 5 candidate operational actions (A0-A4), tests them against strict safety/envelope/recipe boundaries, estimates post-intervention quality risk using a surrogate response surface model, optimizes total operational cost $J = P_{\text{risk}} + \lambda C_{\text{cost}} + \mu D_{\text{disrupt}}$, and formats an actionable 7-field recommendation with an explicit, mandatory **ABSTAIN** safety gate when confidence is low.

## Target Requirements
- **INTV-01**: System evaluates at least 4 candidate actions (A0: continue monitoring, A1: temperature adjustment, A2: pressure adjustment, A3: cycle/process adjustment, A4: material inspection/check).
- **INTV-02**: Every candidate action is checked against operating envelope, recipe limits, max permitted parameter delta, machine safety bounds, intervention policy.
- **INTV-03**: System uses surrogate model (learned response surface / constrained regression) to estimate post-intervention quality risk for each candidate.
- **INTV-04**: System optimizes minimize(predicted_quality_risk + λ×intervention_cost + μ×process_disruption) subject to machine/recipe/envelope constraints.
- **INTV-05**: System outputs comparison table (Do nothing → X% risk, Pressure → Y% risk, Temperature → Z% risk, etc.) with recommended action.
- **RCMD-01**: Every recommendation contains: ACTION, WHY, EVIDENCE, EXPECTED EFFECT, CONFIDENCE, OPERATING LIMIT, RECOVERY CHECK.
- **RCMD-02**: System supports 3 operator modes — HIGH CONFIDENCE → recommend action; MEDIUM → request additional QC sample; LOW → ABSTAIN + monitor.
- **RCMD-03**: ABSTAIN is a product feature — system must refuse to act when confidence is low.

## Mathematical Formulation
1. **Candidate Actions**:
   - $A_0$ (`DO_NOTHING` / `MONITOR`): $\Delta = 0$, Cost = 0, Disruption = 0.
   - $A_1$ (`TEMP_ADJUST`): $\Delta T_{\text{z3}} \in [-5.0, +5.0]^\circ\text{C}$, small thermal cost, low disruption.
   - $A_2$ (`PRESSURE_ADJUST`): $\Delta P_{\text{hold}} \in [-10.0, +10.0]\text{ bar}$, low cost, immediate response.
   - $A_3$ (`CYCLE_TIME_ADJUST`): $\Delta t_{\text{cool}} \in [-3.0, +5.0]\text{ s}$, moderate production throughput impact.
   - $A_4$ (`MATERIAL_INSPECTION` / `PURGE`): High cost (line pause), high disruption, essential when moisture/resin degraded.
2. **Constraint Verification**:
   - For proposed parameter $x' = x_t + \Delta$:
     - Machine safety bounds: $x_{\min}^{\text{safety}} \le x' \le x_{\max}^{\text{safety}}$
     - Recipe limits: $x_{\min}^{\text{recipe}} \le x' \le x_{\max}^{\text{recipe}}$
     - Fingerprint Operating Envelope: $\mu - 3\sigma \le x' \le \mu + 3\sigma$
     - Maximum permitted single adjustment step: $|\Delta| \le \Delta_{\max}^{\text{step}}$ (e.g. max $\pm 3.0^\circ\text{C}$ per step)
3. **Surrogate Model**:
   - Predicts post-action state $\mathbf{x}'$ via coupled polymer physics response functions and calculates expected post-action risk $\hat{P}_{\text{risk}}(A_i)$ using the calibrated quality model.
4. **Objective Function**:
   $$J(A_i) = \hat{P}_{\text{risk}}(A_i) + \lambda \cdot C(A_i) + \mu \cdot D(A_i)$$
   subject to $\text{feasible}(A_i) = \text{True}$.
   Optimal recommendation $A^* = \arg\min_{A_i \in \mathcal{A}_{\text{feasible}}} J(A_i)$.
5. **Epistemic ABSTAIN Gate**:
   - If confidence $< 0.65$ or all candidates infeasible, system forces `ABSTAIN_AND_MONITOR` (or `REQUEST_QC_SAMPLE`).
