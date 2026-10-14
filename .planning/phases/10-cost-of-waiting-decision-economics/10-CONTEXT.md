# Phase 10: Cost-of-Waiting Decision Economics — Context

**Gathered:** 2026-10-02  
**Status:** Locked for Planning & Execution  
**Target Requirements:** ECON-01, ECON-02

<domain>
## Phase Boundary
Deliver the parametric Cost of Poor Quality (CoPQ) engine and real-time Cost of Waiting vs Cost of Acting decision evaluator for automotive injection molding.
Downstream components require:
1. Parametric CoPQ calculator replacing flat ₹450 with granular physics-and-shop-floor cost components (resin weight, machine burden rate, kWh tariff, secondary sorting, OEM warranty/stoppage risk).
2. Real-time decision evaluator calculating $ExpectedLoss_{wait}$, $Cost_{act}$, and signed $DecisionValue = ExpectedLoss_{wait} - Cost_{act}$.
3. Economic intervention threshold gating: prevents premature line interruption when $DecisionValue \le 0$ (preventing unnecessary scrap from disturbing thermal equilibrium), triggers intervention when $DecisionValue > 0$, while respecting critical safety overrides.
4. REST API endpoints and an industrial UI Hero Card with live parametric tuning.
</domain>

<decisions>
## Implementation Decisions

### 1. Parametric CoPQ Model (ECON-01)
- **D-01:** Granular formula components:
  - **Material cost per part:** `(part_weight_g / 1000) * resin_price_per_kg * (1 + runner_scrap_fraction) * (1 - regrind_recovery_credit)`
  - **Machine burden per cycle:** `(machine_hourly_rate / 3600) * cycle_time_seconds`
  - **Energy cost per cycle:** `machine_power_kw * (cycle_time_seconds / 3600) * electricity_tariff_per_kwh`
  - **Secondary sorting cost:** `sorting_cost_per_part` (mandatory 100% sorting for suspect lot quarantine)
  - **Total direct CoPQ:** sum of material, machine, energy, sorting.
  - **Total CoPQ with OEM risk:** direct CoPQ + `oem_penalty_risk_per_defect`.
- **D-02:** Realistic automotive defaults for Tier-2/Tier-3 molders (Pune/Chennai auto clusters):
  - Resin: PP/ABS blend, ₹195/kg, 220g part weight, 8% runner scrap, 25% regrind credit.
  - Machine: 200T IMM, ₹1,650/hr burden, 24.0s cycle time.
  - Energy: 18.5 kW, ₹9.80/kWh.
  - Sorting: ₹22/part.
  - Resulting baseline direct CoPQ: ~₹80.23/part; full CoPQ with assembly risk: ~₹230.23/part.

### 2. Cost of Waiting vs Cost of Acting Evaluator (ECON-02)
- **D-03:** $Cost_{act}$ formulation:
  - Transition/stabilization penalty: changing temperature or pressure requires $N_{stabilization}$ cycles (default 3 to 5) before thermal equilibrium returns.
  - $Cost_{act} = (N_{stabilization} \times CoPQ_{direct}) + OperatorOverhead$.
- **D-04:** $ExpectedLoss_{wait}$ formulation:
  - Over a lookahead drift horizon $H$ (default 20 cycles):
  - $ExpectedScrap = \sum_{t=1}^H P_{defect}(t) \times CoPQ_{total}$.
  - $ExpectedQuarantineSorting = H \times sorting\_cost\_per\_part$ (because uncontained drift taints the whole lot).
  - $ExpectedLoss_{wait} = ExpectedScrap + ExpectedQuarantineSorting$.
- **D-05:** Signed Decision Value & Gating:
  - $DecisionValue = ExpectedLoss_{wait} - Cost_{act}$.
  - If $DecisionValue > 0$: `INTERVENE_NOW` (positive net avoided loss).
  - If $DecisionValue \le 0$: `MONITOR_AND_WAIT` (disturbing machine costs more than waiting).
  - Overrides: If $P_{risk} \ge 0.75$ or safety envelope breached: `CRITICAL_QUALITY_LOCK` takes precedence. If epistemic confidence < 0.65: `ABSTAIN_UNCERTAINTY` takes precedence.

### 3. API & UI Presentation
- **D-06:** REST endpoints under `/api/economics`:
  - `GET /api/economics/parameters`
  - `POST /api/economics/parameters`
  - `GET /api/economics/copq`
  - `GET /api/economics/decision-value`
- **D-07:** Industrial UI:
  - Hero Card displaying Cost of Waiting, Cost of Acting, and live signed Decision Value.
  - Parametric CoPQ drawer/modal allowing live adjustment of resin price, burden rate, etc. to demonstrate real-time reactivity during pitch.
</decisions>

<canonical_refs>
## Canonical References
- `.planning/REQUIREMENTS.md` §Category 2: Decision Economics (ECON-01, ECON-02)
- `.planning/ROADMAP.md` §Phase 10: Cost-of-Waiting Decision Economics
- `src/process_guardian/intervention/optimizer.py` (Current objective scoring)
- `src/process_guardian/api/routes/demo.py` (Flat ₹450 logic to upgrade)
</canonical_refs>
