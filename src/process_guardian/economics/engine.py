"""Parametric Cost of Poor Quality (CoPQ) and Real-Time Decision Value Evaluator (ECON-01, ECON-02)."""

from typing import Optional, List
from process_guardian.economics.models import (
    CoPQParameters,
    CoPQBreakdown,
    DecisionValueBreakdown,
    EconomicActionDecision,
)


class CoPQCalculator:
    """
    Parametric Cost of Poor Quality (CoPQ) engine for injection molding.
    
    Replaces static flat scrap costs with physics-grounded operational cost factors:
    - Material resin shot weight, runner fraction, and regrind recovery
    - Machine hourly burden rate (depreciation, labor, floor space)
    - Active machine electricity consumption and industrial kWh tariffs
    - Secondary containment inspection / sorting labor
    - Downstream OEM assembly line stoppage & warranty penalty exposure
    """

    def __init__(self, default_params: Optional[CoPQParameters] = None):
        self.default_params = default_params or CoPQParameters()

    def calculate_breakdown(self, params: Optional[CoPQParameters] = None) -> CoPQBreakdown:
        p = params or self.default_params

        # 1. Material cost per part with cold runner scrap and regrind recovery credit
        # Net part weight in kg
        part_weight_kg = p.part_weight_grams / 1000.0
        # Gross shot weight including cold runner/sprue
        gross_shot_kg = part_weight_kg * (1.0 + p.runner_scrap_fraction)
        # Net effective material cost taking into account recycled regrind credit
        material_cost = round(
            gross_shot_kg * p.resin_price_per_kg * (1.0 - p.regrind_recovery_credit),
            2,
        )

        # 2. Machine hourly burden allocated per cycle
        # Hourly rate / 3600 seconds * cycle time
        machine_burden = round((p.machine_hourly_rate / 3600.0) * p.cycle_time_seconds, 2)

        # 3. Energy consumption cost per cycle
        # Active kW * (cycle_time / 3600) = kWh per cycle * industrial tariff
        cycle_hours = p.cycle_time_seconds / 3600.0
        kwh_per_cycle = p.machine_power_kw * cycle_hours
        energy_cost = round(kwh_per_cycle * p.electricity_tariff_per_kwh, 2)

        # 4. Secondary sorting / containment inspection labor cost per part
        sorting_cost = round(p.sorting_cost_per_part, 2)

        # 5. Direct scrap CoPQ (scrap at press)
        direct_scrap_copq = round(material_cost + machine_burden + energy_cost + sorting_cost, 2)

        # 6. Total CoPQ including downstream OEM penalty exposure risk
        oem_penalty = round(p.oem_penalty_risk_per_defect, 2)
        total_copq = round(direct_scrap_copq + oem_penalty, 2)

        return CoPQBreakdown(
            material_cost_per_defect=material_cost,
            machine_burden_per_defect=machine_burden,
            energy_cost_per_defect=energy_cost,
            sorting_cost_per_defect=sorting_cost,
            direct_scrap_copq_per_defect=direct_scrap_copq,
            oem_penalty_risk=oem_penalty,
            total_copq_per_defect=total_copq,
            currency="INR (₹)",
        )


class CostOfWaitingEvaluator:
    """
    Real-time Cost of Waiting vs Cost of Acting decision evaluator (ECON-02).
    
    Formula:
        Decision Value = ExpectedLoss_wait - Cost_act
    
    Operational Invariants:
    - If Decision Value <= threshold: Hold machine! Premature adjustment causes more scrap
      than waiting because adjusting machine disturbs thermal equilibrium.
    - If Decision Value > threshold: Intervene immediately! Waiting allows scrap runaway.
    - Safety override: Critical quality risk (P_risk >= 0.75) mandates immediate intervention.
    - Epistemic override: Model confidence < 0.65 forces ABSTAIN_UNCERTAINTY.
    """

    def __init__(
        self,
        copq_calculator: Optional[CoPQCalculator] = None,
        default_economic_threshold: float = 0.0,
        default_horizon_cycles: int = 20,
        default_stabilization_cycles: int = 3,
        default_operator_overhead: float = 45.0,
        baseline_risk_rate: float = 0.03,
        suspect_quarantine_risk_threshold: float = 0.20,
    ):
        self.copq_calculator = copq_calculator or CoPQCalculator()
        self.default_economic_threshold = default_economic_threshold
        self.default_horizon_cycles = default_horizon_cycles
        self.default_stabilization_cycles = default_stabilization_cycles
        self.default_operator_overhead = default_operator_overhead
        self.baseline_risk_rate = baseline_risk_rate
        self.suspect_quarantine_risk_threshold = suspect_quarantine_risk_threshold

    def evaluate(
        self,
        current_cycle: int,
        current_risk_probability: float,
        confidence: float = 1.0,
        horizon_cycles: Optional[int] = None,
        stabilization_cycles: Optional[int] = None,
        copq_params: Optional[CoPQParameters] = None,
        economic_threshold: Optional[float] = None,
        drift_growth_rate: float = 0.03,
        is_drift_confirmed: bool = False,
        is_critical_safety_override: bool = False,
    ) -> DecisionValueBreakdown:
        """
        Evaluate Cost of Waiting vs Cost of Acting for the current cycle.
        """
        h_cycles = horizon_cycles if horizon_cycles is not None else self.default_horizon_cycles
        s_cycles = stabilization_cycles if stabilization_cycles is not None else self.default_stabilization_cycles
        threshold = economic_threshold if economic_threshold is not None else self.default_economic_threshold

        breakdown = self.copq_calculator.calculate_breakdown(copq_params)
        copq_unit = breakdown.total_copq_per_defect
        direct_copq = breakdown.direct_scrap_copq_per_defect
        sorting_unit = breakdown.sorting_cost_per_defect

        # 1. Project drift risk over lookahead horizon H
        # Calculate excess risk over golden baseline (3%) due to drift
        projected_risks: List[float] = []
        excess_risks: List[float] = []
        suspect_cycles_count = 0

        for t in range(1, h_cycles + 1):
            projected_p = min(0.98, max(0.01, current_risk_probability + (drift_growth_rate * t)))
            projected_risks.append(projected_p)
            
            # Excess defect risk attributed to progressive drift beyond golden baseline
            excess_p = max(0.0, projected_p - self.baseline_risk_rate)
            excess_risks.append(excess_p)

            # Cycle qualifies for quarantine sorting if drift is confirmed or defect risk is elevated
            if is_drift_confirmed or projected_p >= self.suspect_quarantine_risk_threshold:
                suspect_cycles_count += 1

        expected_scrap_cycles = round(sum(excess_risks), 2)
        expected_scrap_cost = round(expected_scrap_cycles * copq_unit, 2)

        # Uncontained drift causes suspect cycles to require 100% containment sorting
        expected_quarantine_sorting_cycles = suspect_cycles_count
        expected_sorting_cost = round(expected_quarantine_sorting_cycles * sorting_unit, 2)

        # Total Expected Loss if Waiting
        expected_loss_waiting = round(expected_scrap_cost + expected_sorting_cost, 2)

        # 2. Calculate Cost of Acting
        # Machine adjustment requires stabilization cycles before thermal equilibrium returns
        stabilization_scrap_cost = round(s_cycles * direct_copq, 2)
        operator_overhead = round(self.default_operator_overhead, 2)
        cost_acting = round(stabilization_scrap_cost + operator_overhead, 2)

        # 3. Signed Decision Value
        decision_value = round(expected_loss_waiting - cost_acting, 2)

        # 4. Epistemic and Safety Decision Gating
        if confidence < 0.65:
            decision = EconomicActionDecision.ABSTAIN_UNCERTAINTY
            justification = (
                f"Model epistemic confidence ({confidence * 100:.1f}%) is below 65% safety gate. "
                "Abstaining from intervention to avoid uncalibrated parameter disturbance."
            )
            avoided_loss = 0.0
        elif is_critical_safety_override or current_risk_probability >= 0.75:
            decision = EconomicActionDecision.CRITICAL_QUALITY_LOCK
            justification = (
                f"Quality contract violation imminent ({current_risk_probability * 100:.1f}% risk). "
                f"Mandatory intervention override triggered (Decision Value: ₹{decision_value:+.2f})."
            )
            avoided_loss = max(0.0, decision_value)
        elif decision_value > threshold:
            decision = EconomicActionDecision.INTERVENE_NOW
            justification = (
                f"Expected loss of waiting (₹{expected_loss_waiting:.2f}) exceeds intervention cost "
                f"(₹{cost_acting:.2f}) by ₹{decision_value:.2f}. Corrective adjustment is economically justified."
            )
            avoided_loss = decision_value
        else:
            decision = EconomicActionDecision.MONITOR_AND_WAIT
            if decision_value > 0:
                justification = (
                    f"Decision Value (₹{decision_value:+.2f}) is positive but below the ₹{threshold:.2f} "
                    f"economic threshold. Maintain monitoring until the margin clears the threshold."
                )
            else:
                justification = (
                    f"Cost of intervention (₹{cost_acting:.2f} for {s_cycles} stabilization cycles) exceeds "
                    f"projected waiting loss (₹{expected_loss_waiting:.2f}). Disturbing machine now would cause "
                    f"unnecessary scrap. Maintain monitoring."
                )
            avoided_loss = 0.0

        return DecisionValueBreakdown(
            current_cycle=current_cycle,
            current_risk_probability=current_risk_probability,
            copq_per_defect=copq_unit,
            expected_drift_horizon_cycles=h_cycles,
            expected_scrap_cycles_if_waiting=expected_scrap_cycles,
            expected_quarantine_sorting_cycles=expected_quarantine_sorting_cycles,
            expected_scrap_cost=expected_scrap_cost,
            expected_sorting_cost=expected_sorting_cost,
            expected_loss_waiting=expected_loss_waiting,
            stabilization_cycles=s_cycles,
            stabilization_scrap_cost=stabilization_scrap_cost,
            operator_tuning_overhead=operator_overhead,
            cost_acting=cost_acting,
            decision_value=decision_value,
            economic_threshold=threshold,
            actionable_recommendation=decision,
            avoided_loss_if_acting=avoided_loss,
            justification=justification,
            epistemic_level="Level 3: Software Invariant",
        )
