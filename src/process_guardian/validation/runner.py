"""Validation Suite Execution Runner & Machine-Readable Report Generator."""

import time
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional

from process_guardian.validation.scenarios import (
    SCENARIO_CATALOG,
    ValidationScenario,
    ScenarioValidationResult,
)


@dataclass
class ValidationReport:
    """Comprehensive validation suite execution report."""
    timestamp: str
    total_scenarios: int
    passed_count: int
    failed_count: int
    pass_rate: float
    total_duration_sec: float
    all_passed: bool
    results: List[Dict[str, Any]]

    def to_json(self, indent: int = 2) -> str:
        """Serialize report to formatted JSON string."""
        return json.dumps(asdict(self), indent=indent)

    def save_json(self, file_path: str) -> None:
        """Write JSON report to disk."""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self.to_json())


class ScenarioValidationRunner:
    """Executes validation scenarios and collects behavioral scorecards."""

    def __init__(self, scenarios: Optional[List[ValidationScenario]] = None):
        self.scenarios = scenarios or SCENARIO_CATALOG

    def run_scenario(self, scenario_id_or_name: Any) -> ScenarioValidationResult:
        """Run a single scenario by its integer ID or string name."""
        scenario = next(
            (s for s in self.scenarios if s.scenario_id == scenario_id_or_name or s.name == scenario_id_or_name),
            None,
        )
        if scenario is None:
            raise ValueError(f"Unknown scenario identifier: {scenario_id_or_name}")
        return scenario.build_and_execute()

    def run_all(self, on_scenario_start: Optional[Any] = None, on_scenario_complete: Optional[Any] = None) -> ValidationReport:
        """
        Execute all registered validation scenarios sequentially and compile summary report.
        """
        start_time = time.time()
        results: List[ScenarioValidationResult] = []

        for s in self.scenarios:
            if on_scenario_start:
                on_scenario_start(s)
            res = s.build_and_execute()
            results.append(res)
            if on_scenario_complete:
                on_scenario_complete(s, res)

        duration = round(time.time() - start_time, 2)
        passed_cnt = sum(1 for r in results if r.passed)
        failed_cnt = len(results) - passed_cnt
        pass_rate = round((passed_cnt / len(results)) * 100.0, 1) if results else 0.0

        return ValidationReport(
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            total_scenarios=len(results),
            passed_count=passed_cnt,
            failed_count=failed_cnt,
            pass_rate=pass_rate,
            total_duration_sec=duration,
            all_passed=(failed_cnt == 0),
            results=[asdict(r) for r in results],
        )
