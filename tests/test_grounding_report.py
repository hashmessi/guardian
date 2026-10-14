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
    """Verify report generates with all required test cases."""
    report = GroundingBenchmarkEngine.generate_report()
    assert isinstance(report, GroundingReport)
    assert report.overall_status == "PARTIALLY_GROUNDED"
    assert len(report.test_cases) == 3
    assert len(report.key_findings) >= 4

    case_ids = [tc.case_id for tc in report.test_cases]
    assert "EVID-REPLICA-01" in case_ids
    assert "MODEL-MOISTURE-01" in case_ids
    assert "OWN-REPLAY-01" in case_ids


def test_every_case_declares_its_evidence_class():
    """Honesty guard: no case may be published without saying what kind of evidence it is."""
    report = GroundingBenchmarkEngine.generate_report()
    allowed = {"PUBLISHED_DATASET", "COMPUTED_ON_REPLICA", "MODELLED_ASSUMPTION", "OWN_SIMULATION"}

    for case in report.test_cases:
        assert case.source_type in allowed, f"{case.case_id} has unclassified evidence"
        # Only outside-anchored evidence may carry a citation, and it must be a real DOI.
        if case.source_type == "COMPUTED_ON_REPLICA":
            assert case.citation and "10.23728/b2share" in case.citation
        if case.source_type in {"MODELLED_ASSUMPTION", "OWN_SIMULATION"}:
            assert case.citation is None, f"{case.case_id} cites a source for its own model"


def test_no_case_invents_an_industry_study():
    """Regression guard for the uncitable '2026 study' references this report used to carry."""
    report = GroundingBenchmarkEngine.generate_report()
    text = " ".join(
        f"{c.empirical_reference} {c.evidence_summary} {c.conventional_spc_behavior}"
        for c in report.test_cases
    ).lower()

    for invented in ("2026 automotive component", "2026 resin drying", "2025 tier-1"):
        assert invented not in text


def test_grounding_report_in_limits_case():
    """Case 1 must report the computed univariate escape, not a frozen figure."""
    report = GroundingBenchmarkEngine.generate_report()
    case_1 = next(tc for tc in report.test_cases if tc.case_id == "EVID-REPLICA-01")
    assert case_1.conventional_defect_escape_rate_pct > 25.0
    assert case_1.source_type == "COMPUTED_ON_REPLICA"
    assert case_1.is_conclusive is True
    # Modelled benefit figures must not be smuggled into a detection comparison.
    assert case_1.scrap_reduction_pct == 0.0


def test_grounding_report_moisture_non_linearity():
    """Verify the modelled moisture penalty curve keeps its gate/knee labels distinct."""
    report = GroundingBenchmarkEngine.generate_report()
    curve = report.non_linear_moisture_curve
    assert "0.10%" in curve
    assert "0.22%" in curve
    assert "0.15% (process gate)" in curve
    assert "0.18% (modelled knee)" in curve
    # Low moisture stays low; the knee accelerates.
    assert curve["0.10%"] < 5.0
    assert curve["0.22%"] > 20.0
    assert curve["0.18% (modelled knee)"] > curve["0.15% (process gate)"]


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
