"""Operational Validation Suite Batch Runner.

Executes every registered validation scenario in sequence or on-demand, aggregating
measured evidence across detection, intervention safety, containment and recovery.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from process_guardian.scenario.models import ScenarioScorecard, ScenarioRunSummary
from process_guardian.scenario.registry import get_scenario_registry, ScenarioRegistry
from process_guardian.scenario.runner import ScenarioRunner


class OperationalSuiteMetrics(BaseModel):
    """Aggregated reliability metrics, every one of them measured.

    No field carries a default: an optimistic default (100% pass, 0% false
    interventions, a 3.2-cycle latency nobody timed) is indistinguishable from a
    real result once it reaches a slide, so the report cannot be built without
    computing each number.
    """
    total_scenarios_evaluated: int
    total_scenarios_passed: int
    completion_rate_pct: float
    correct_detection_rate_pct: float
    false_intervention_rate_pct: float
    recovery_verification_rate_pct: float
    containment_correctness_pct: float
    mean_decision_latency_cycles: Optional[float]
    total_avoided_scrap_parts: int
    total_avoided_loss_inr: float


class OperationalValidationSuiteReport(BaseModel):
    """Comprehensive validation report for industrial evaluators."""
    title: str = "PS02 Operational Validation Suite"
    summary: str
    metrics: OperationalSuiteMetrics
    scorecards: List[ScenarioScorecard] = Field(default_factory=list)
    timestamp: str = ""
    disclaimer: str = (
        "CONTROLLED SIMULATION · ALL METRICS DERIVED FROM DETERMINISTIC PVT POLYMER PHYSICS TRAJECTORIES. "
        "REPRESENTS PROTOTYPE VALIDATION EVIDENCE UNDER CONTROLLED CONDITIONS; CALIBRATION AGAINST HISTORICAL "
        "FACTORY DATA REQUIRED FOR OEM PLANT DEPLOYMENT."
    )


class OperationalValidationSuiteRunner:
    """Executes the complete 11-scenario suite and generates the operational scorecard."""

    def __init__(
        self,
        registry: Optional[ScenarioRegistry] = None,
        runner: Optional[ScenarioRunner] = None,
    ):
        self.registry = registry or get_scenario_registry()
        self.runner = runner or ScenarioRunner()

    def run_all(self, use_cache: bool = True) -> OperationalValidationSuiteReport:
        """Run every registered scenario and compile measured aggregate metrics."""
        from datetime import datetime, timezone
        now_iso = datetime.now(timezone.utc).isoformat()

        scenarios = self.registry.list_validation_scenarios()
        scorecards: List[ScenarioScorecard] = []
        total_avoided_scrap = 0
        total_avoided_loss = 0.0
        passed_count = 0
        correct_detections = 0
        false_interventions = 0
        recovery_successes = 0
        containment_successes = 0
        monitor_scenarios = 0
        latencies: List[float] = []

        for scn in scenarios:
            res: ScenarioRunSummary = self.runner.run_scenario(scn, use_cache=use_cache)
            card = res.scorecard
            scorecards.append(card)

            if card.overall_passed:
                passed_count += 1
            if card.detection.passed:
                correct_detections += 1
            # A false intervention is the engine acting on a scenario where the
            # correct answer was to leave the machine alone.
            if scn.expected_outcome.action_class == "monitor":
                monitor_scenarios += 1
                if not card.intervention.passed:
                    false_interventions += 1
            if card.recovery.passed:
                recovery_successes += 1
            if card.containment.passed:
                containment_successes += 1

            latency = card.detection.metrics.get("detection_latency_cycles")
            if isinstance(latency, (int, float)):
                latencies.append(float(latency))

            total_avoided_scrap += res.counterfactual.guardian_off.scrap_parts_count - res.counterfactual.guardian_on.scrap_parts_count
            total_avoided_loss += res.counterfactual.net_avoided_loss

        total_n = max(1, len(scenarios))
        metrics = OperationalSuiteMetrics(
            total_scenarios_evaluated=len(scenarios),
            total_scenarios_passed=passed_count,
            completion_rate_pct=round((passed_count / total_n) * 100.0, 1),
            correct_detection_rate_pct=round((correct_detections / total_n) * 100.0, 1),
            false_intervention_rate_pct=round((false_interventions / max(1, monitor_scenarios)) * 100.0, 1),
            recovery_verification_rate_pct=round((recovery_successes / total_n) * 100.0, 1),
            containment_correctness_pct=round((containment_successes / total_n) * 100.0, 1),
            mean_decision_latency_cycles=round(sum(latencies) / len(latencies), 1) if latencies else None,
            total_avoided_scrap_parts=max(0, total_avoided_scrap),
            total_avoided_loss_inr=round(total_avoided_loss, 2),
        )

        return OperationalValidationSuiteReport(
            title="PS02 Operational Validation Suite",
            summary=f"{passed_count} / {len(scenarios)} Scenarios Completed",
            metrics=metrics,
            scorecards=scorecards,
            timestamp=now_iso,
        )
