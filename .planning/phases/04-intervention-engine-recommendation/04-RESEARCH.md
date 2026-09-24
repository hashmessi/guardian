# Phase 4: Intervention Engine + Recommendation — Research & Technical Architecture

## 1. Candidate Action Set & Constraints (INTV-01, INTV-02)
Injection molding machines cannot tolerate arbitrary parameter jumps. In Indian Tier-2/Tier-3 automotive supplier environments:
- **Heater bands**: Zone 3 adjustment cannot exceed $\pm 3.0^\circ\text{C}$ in a single step due to thermal inertia.
- **Hydraulics/Servos**: Holding pressure cannot step more than $\pm 8.0\text{ bar}$ per cycle.
- **Cycle Timing**: Cooling time cannot be reduced below minimum required HDT solidification time ($10.0\text{ s}$).
- **Material Inspection**: Involves operator checking resin dryer dew point or hopper moisture; high operational disruption ($D=0.85$, $C=0.60$).

### Action Catalog:
| ID | Action Code | Target Parameter | Typical Delta Range | Max Step | Cost Weight $\lambda$ | Disruption $\mu$ |
|---|---|---|---|---|---|---|
| $A_0$ | `DO_NOTHING` | None | $0$ | $0$ | 0.00 | 0.00 |
| $A_1$ | `TEMP_ADJUST` | `barrel_temp_z3` | $[-5.0, +5.0]^\circ\text{C}$ | $3.0^\circ\text{C}$ | 0.15 | 0.10 |
| $A_2$ | `PRESSURE_ADJUST` | `hold_pressure` | $[-10.0, +10.0]\text{ bar}$ | $6.0\text{ bar}$ | 0.10 | 0.05 |
| $A_3$ | `CYCLE_TIME_ADJUST` | `cooling_time` | $[-2.0, +4.0]\text{ s}$ | $2.0\text{ s}$ | 0.25 | 0.30 |
| $A_4$ | `MATERIAL_INSPECT_PURGE` | `material_moisture` | Purge / dry hopper | N/A | 0.60 | 0.75 |

### Feasibility Constraints:
For each candidate $A_i$:
1. $x_{\min}^{\text{safety}} \le x' \le x_{\max}^{\text{safety}}$ (Physical equipment safety bounds)
2. $x_{\min}^{\text{recipe}} \le x' \le x_{\max}^{\text{recipe}}$ (Approved part recipe tolerance)
3. $x_{\min}^{\text{envelope}} \le x' \le x_{\max}^{\text{envelope}}$ (Baseline fingerprint $\mu \pm 3\sigma$)
4. $|\Delta| \le \Delta_{\max}^{\text{step}}$ (Max single-step adjustment)
5. Non-conflicting direction: The adjustment must oppose the observed drift (e.g. if temperature drifted positive, adjustment delta must be negative).

## 2. Surrogate Response Surface Model (INTV-03)
Given the current normalized record $\mathbf{x}_t$, a candidate adjustment $\Delta_j$ produces an estimated post-intervention state $\mathbf{x}'$:
- Forward kinematics:
  $$x_j' = x_{t, j} + \Delta_j$$
- Coupled physics adjustments:
  If $A_1$ (temperature reduced by $3.0^\circ\text{C}$):
  - $\Delta T_{\text{eff}} = 0.50 \Delta T_{\text{z3}} = -1.5^\circ\text{C}$
  - Viscosity increases by $+0.018$
  - Peak pressure increases by $+2.4\text{ bar}$
  - Flash risk drops to 0.0
- Post-intervention Quality Risk Prediction:
  $$\hat{P}_{\text{risk}}(A_i) = \text{QualityRiskModel.predict}(\mathbf{x}')$$

## 3. Cost-Disruption Optimization (INTV-04, INTV-05)
The objective function minimizes risk plus weighted economic and disruption penalties:
$$J(A_i) = \hat{P}_{\text{risk}}(A_i) + 0.25 \cdot C(A_i) + 0.20 \cdot D(A_i)$$
The candidate with lowest $J$ among feasible actions is selected:
$$A^* = \arg\min_{A_i \in \mathcal{A}_{\text{feasible}}} J(A_i)$$

## 4. Seven-Field Structured Recommendation Contract (RCMD-01..03)
Every generated recommendation must strictly fulfill:
1. `ACTION`: Exact parameter and magnitude (e.g., `"ADJUST barrel_temp_z3 BY -3.0°C"`)
2. `WHY`: Root-cause justification linking to drift detection and defect risk
3. `EVIDENCE`: Quantitative baseline deviations and trend metrics
4. `EXPECTED_EFFECT`: Estimated post-intervention quality risk drop (e.g., `"Reduces defect risk from 85% to 8%"`)
5. `CONFIDENCE`: Probabilistic confidence score in $[0.0, 1.0]$
6. `OPERATING_LIMIT`: Verification that target remains within envelope/recipe bounds
7. `RECOVERY_CHECK`: Exact post-action verification criteria (e.g., `"Verify zone 3 drops below 231.5°C within 3 cycles"`)

### ABSTAIN Policy (RCMD-03):
If model confidence $< 0.65$ or if all candidate actions are infeasible, the engine refuses automated adjustment recommendations and outputs `ABSTAIN_AND_MONITOR` (or `REQUEST_QC_SAMPLE`).
