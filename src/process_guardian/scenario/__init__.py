"""Scenario Engine & Operational Validation Suite for Process Guardian.

Provides deterministic data-driven scenario definitions, execution through the
unified Guardian decision pipeline, dual-run counterfactual replay (Guardian OFF vs ON),
and automated operational scorecards.
"""

from process_guardian.scenario.models import (
    DisturbanceSpec,
    OperationalOverrideSpec,
    ExpectedOutcome,
    NarrativeMilestone,
    ScenarioDefinition,
    ScenarioReplayCycle,
    ScenarioScorecard,
    ScenarioRunSummary,
)
from process_guardian.scenario.registry import ScenarioRegistry, get_scenario_registry
from process_guardian.scenario.runner import ScenarioRunner
from process_guardian.scenario.scorecard import ScenarioScorecardEvaluator
from process_guardian.scenario.suite import OperationalValidationSuiteRunner

__all__ = [
    "DisturbanceSpec",
    "OperationalOverrideSpec",
    "ExpectedOutcome",
    "NarrativeMilestone",
    "ScenarioDefinition",
    "ScenarioReplayCycle",
    "ScenarioScorecard",
    "ScenarioRunSummary",
    "ScenarioRegistry",
    "get_scenario_registry",
    "ScenarioRunner",
    "ScenarioScorecardEvaluator",
    "OperationalValidationSuiteRunner",
]
