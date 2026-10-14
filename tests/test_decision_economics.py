"""Tests for Cost of Waiting vs Cost of Acting Decision Evaluator (ECON-02)."""

import pytest
from process_guardian.economics.models import (
    CoPQParameters,
    EconomicActionDecision,
    DecisionValueBreakdown,
)
from process_guardian.economics.engine import (
    CoPQCalculator,
    CostOfWaitingEvaluator,
)


def test_decision_economics_hold_on_low_risk_prevents_premature_action():
    """Verify that when drift is mild/low, decision value is negative and engine advises MONITOR_AND_WAIT."""
    evaluator = CostOfWaitingEvaluator()
    
    # Healthy / early subtle deviation: 8% defect risk
    res = evaluator.evaluate(
        current_cycle=105,
        current_risk_probability=0.08,
        confidence=0.95,
        horizon_cycles=10,
        stabilization_cycles=3,
        drift_growth_rate=0.01,
    )

    assert isinstance(res, DecisionValueBreakdown)
    # Acting cost: 3 stabilization cycles (~₹206.88) + ₹45 overhead = ~₹251.88
    # Waiting cost over 10 cycles with small risk is much lower
    assert res.decision_value < 0.0
    assert res.actionable_recommendation == EconomicActionDecision.MONITOR_AND_WAIT
    assert res.avoided_loss_if_acting == 0.0
    assert "Disturbing machine now would cause unnecessary scrap" in res.justification


def test_decision_economics_intervene_on_escalated_drift():
    """Verify that when drift escalates, decision value flips positive and advises INTERVENE_NOW."""
    evaluator = CostOfWaitingEvaluator()

    # Confirmed thermal drift: 48% current risk, projecting upward
    res = evaluator.evaluate(
        current_cycle=435,
        current_risk_probability=0.48,
        confidence=0.92,
        horizon_cycles=20,
        stabilization_cycles=3,
        drift_growth_rate=0.03,
    )

    assert res.decision_value > 0.0
    assert res.actionable_recommendation == EconomicActionDecision.INTERVENE_NOW
    assert res.avoided_loss_if_acting == res.decision_value
    assert "Corrective adjustment is economically justified" in res.justification
    # Check itemized breakdown consistency
    assert res.expected_loss_waiting == round(res.expected_scrap_cost + res.expected_sorting_cost, 2)
    assert res.cost_acting == round(res.stabilization_scrap_cost + res.operator_tuning_overhead, 2)


def test_decision_economics_critical_quality_lock_override():
    """Verify that severe quality risk (>= 75%) forces CRITICAL_QUALITY_LOCK regardless of threshold."""
    evaluator = CostOfWaitingEvaluator()

    res = evaluator.evaluate(
        current_cycle=440,
        current_risk_probability=0.82,
        confidence=0.90,
        horizon_cycles=2,  # artificially short horizon
        stabilization_cycles=5,
    )

    assert res.actionable_recommendation == EconomicActionDecision.CRITICAL_QUALITY_LOCK
    assert "Quality contract violation imminent" in res.justification


def test_decision_economics_abstain_on_low_confidence():
    """Verify SAFE-03 invariant: epistemic confidence < 0.65 forces ABSTAIN_UNCERTAINTY."""
    evaluator = CostOfWaitingEvaluator()

    res = evaluator.evaluate(
        current_cycle=442,
        current_risk_probability=0.60,
        confidence=0.52,  # below 0.65 threshold
    )

    assert res.actionable_recommendation == EconomicActionDecision.ABSTAIN_UNCERTAINTY
    assert res.avoided_loss_if_acting == 0.0
    assert "below 65% safety gate" in res.justification


def test_decision_economics_custom_economic_threshold():
    """Verify custom economic safety margin threshold shifting intervention point."""
    evaluator = CostOfWaitingEvaluator()

    # Suppose decision value is +₹35, but management requires >= ₹100 net margin before stopping line
    res_default = evaluator.evaluate(
        current_cycle=200,
        current_risk_probability=0.20,
        confidence=0.90,
        horizon_cycles=15,
        stabilization_cycles=3,
        drift_growth_rate=0.015,
        economic_threshold=0.0,
    )

    res_strict = evaluator.evaluate(
        current_cycle=200,
        current_risk_probability=0.20,
        confidence=0.90,
        horizon_cycles=15,
        stabilization_cycles=3,
        drift_growth_rate=0.015,
        economic_threshold=2000.0,  # very high threshold
    )

    assert res_strict.actionable_recommendation == EconomicActionDecision.MONITOR_AND_WAIT
