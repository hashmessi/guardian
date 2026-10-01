"""Tests for Automated Grounding Benchmark Report Engine (EVID-02)."""

import json
from pathlib import Path
import pytest
from process_guardian.evidence.grounding_report import (
    GroundingBenchmarkEngine,
    GroundingReport,
    GroundingTestCaseResult,
)


def test_grounding_report_generation():
    """Verify report generates with all required empirical test cases."""
    report = GroundingBenchmarkEngine.generate_report()
    assert isinstance(report, GroundingReport)
    assert report.overall_status == "GROUNDED_EMPIRICALLY"
    assert len(report.test_cases) == 3
    assert len(report.key_findings) >= 4

    case_ids = [tc.case_id for tc in report.test_cases]
    assert "IND-CASE-2026-01" in case_ids
    assert "IND-CASE-2026-02" in case_ids
    assert "IND-CASE-2025-01" in case_ids


def test_grounding_report_in_limits_case():
    """Verify Case 1 reflects the 2026 study showing conventional SPC escape."""
    report = GroundingBenchmarkEngine.generate_report()
    case_1 = next(tc for tc in report.test_cases if tc.case_id == "IND-CASE-2026-01")
    assert case_1.conventional_defect_escape_rate_pct == 100.0
    assert case_1.process_guardian_lead_time_cycles > 5.0
    assert case_1.scrap_reduction_pct > 75.0
    assert case_1.is_conclusive is True


def test_grounding_report_moisture_non_linearity():
    """Verify non-linear moisture scrap curve exhibits the critical threshold."""
    report = GroundingBenchmarkEngine.generate_report()
    curve = report.non_linear_moisture_curve
    assert "0.10% (Optimal)" in curve
    assert "0.22%" in curve
    # 0.10% scrap should be low (~2.8%)
    assert curve["0.10% (Optimal)"] < 5.0
    # 0.22% scrap should jump > 20%
    assert curve["0.22%"] > 20.0


def test_grounding_report_disk_serialization(tmp_path):
    """Verify writing report to disk produces valid, parseable JSON."""
    test_file = tmp_path / "grounding_benchmark_report.json"
    written_path = GroundingBenchmarkEngine.write_report_to_disk(test_file)
    assert written_path.exists()

    with open(written_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["report_id"] == "GBR-2026-V11"
    assert len(data["test_cases"]) == 3
    assert "conclusion_for_evaluators" in data
