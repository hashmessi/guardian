"""Tests for Process Guardian Leadership Incident Brief.

Validates deterministic calculations, Gemini client structured output,
anti-hallucination number verification, safe fallback, zero invented savings for
Scenario 3, and API endpoint integration.
"""

import pytest
from fastapi.testclient import TestClient

from process_guardian.api.app import app
from process_guardian.scenario.registry import get_scenario_registry
from process_guardian.scenario.runner import ScenarioRunner
from process_guardian.leadership.engine import LeadershipReportBuilder
from process_guardian.leadership.gemini_client import (
    GeminiLeadershipClient,
    DETERMINISTIC_TEMPLATES,
)
from process_guardian.leadership.models import (
    LeadershipFactPacket,
    LeadershipTakeaway,
)


@pytest.fixture(scope="module")
def scenario_runner():
    return ScenarioRunner()


@pytest.fixture(scope="module")
def registry():
    return get_scenario_registry()


@pytest.fixture(scope="module")
def report_builder():
    return LeadershipReportBuilder()


@pytest.fixture(scope="module")
def test_client():
    return TestClient(app)


# =============================================================================
# 1. Deterministic Calculation & Invariant Tests for the 3 Scenarios
# =============================================================================

def test_scenario_1_compound_brief(scenario_runner, registry, report_builder):
    """Scenario 1: Compound Multi-Signal Drift -> Verified Recovery."""
    scn = registry.get("SCN-06-COMPOUND")
    summary = scenario_runner.run_scenario(scn, use_cache=True)
    report = report_builder.build_report(summary)

    # Outcome & Final State
    assert report.scenario_id == "SCN-06-COMPOUND"
    assert report.final_state == "VERIFIED_RECOVERY"
    assert report.final_state_label == "Verified Recovery"
    assert "early" in report.headline.lower() or "contained" in report.headline.lower()

    # Story Steps
    assert len(report.story_steps) == 4
    assert report.story_steps[0].title == "Drift Detected Early"
    assert report.story_steps[3].title == "Verified Recovery & Containment"

    # Business Impact Numbers
    impact = report.business_impact
    assert impact.detection_lead_time_cycles == 12
    assert impact.suspect_parts_contained == 12
    assert impact.baseline_suspect_parts == 301
    assert impact.suspect_reduction_pct == 96.0
    assert impact.modeled_scrap_avoided == 281
    assert impact.modeled_cost_avoided_inr == pytest.approx(37485.76, rel=1e-2)
    assert impact.recovery_time_cycles == 5
    assert impact.disclaimer == "Modeled controlled-scenario estimate — not plant-validated savings."

    # Next Action
    assert report.next_action == "Release Production"


def test_scenario_2_human_channel_brief(scenario_runner, registry, report_builder):
    """Scenario 2: Human-Channel Material Risk -> QC Hold."""
    scn = registry.get("SCN-FLIP-HUMAN-CHANNEL")
    summary = scenario_runner.run_scenario(scn, use_cache=True)
    report = report_builder.build_report(summary)

    # Outcome & Final State
    assert report.scenario_id == "SCN-FLIP-HUMAN-CHANNEL"
    assert report.final_state == "QC_HOLD"
    assert report.final_state_label == "QC Hold"

    # Story Steps
    assert len(report.story_steps) == 4
    assert "Human-Channel" in report.story_steps[0].title

    # Business Impact (Zero invented savings, customer risk prevented)
    impact = report.business_impact
    assert impact.suspect_parts_contained == 151
    assert impact.modeled_scrap_avoided == 0
    assert impact.modeled_cost_avoided_inr == 0.0
    assert impact.is_savings_invented is False

    # Next Action
    assert report.next_action == "Require QC Inspection"


def test_scenario_3_low_conf_abstain_brief(scenario_runner, registry, report_builder):
    """Scenario 3: Out-of-Distribution Drift -> Escalation Required.

    Strict invariant: DO NOT INVENT SAVINGS.
    """
    scn = registry.get("SCN-08-LOW-CONF-ABSTAIN")
    summary = scenario_runner.run_scenario(scn, use_cache=True)
    report = report_builder.build_report(summary)

    # Outcome & Final State
    assert report.scenario_id == "SCN-08-LOW-CONF-ABSTAIN"
    assert report.final_state == "ESCALATION_REQUIRED"
    assert report.final_state_label == "Escalation Required"

    # Business Impact (Strictly zero invented savings)
    impact = report.business_impact
    assert impact.suspect_parts_contained == 250
    assert impact.modeled_scrap_avoided == 0
    assert impact.modeled_cost_avoided_inr == 0.0
    assert impact.is_savings_invented is False

    # Next Action
    assert report.next_action == "Escalate to Maintenance"


# =============================================================================
# 2. Gemini Client & Anti-Hallucination Number Validator Tests
# =============================================================================

def test_gemini_fallback_on_network_error():
    """Client immediately falls back to deterministic template when API is unreachable."""
    client = GeminiLeadershipClient(api_key="dummy_invalid_key")
    packet = LeadershipFactPacket(
        scenario_id="SCN-06-COMPOUND",
        scenario_title="Scenario 06 — Compound Multi-Signal Drift",
        final_state="VERIFIED_RECOVERY",
        outcome_theme="Verified Recovery",
        dominant_signal="barrel_temp_z3",
        triggered_signals=["Barrel Temp Zone 3", "Injection Pressure"],
        detection_lead_time_cycles=12,
        recommendation="A1: Adjust barrel_temp_z3 by -3.0°C",
        operator_action="Candidate A1 Applied",
        suspect_parts_contained=12,
        modeled_scrap_avoided=281,
        modeled_cost_avoided_inr=37485.76,
        recovery_time_cycles=5,
        next_action_directive="Release production to standard cycle time",
    )

    takeaway = client.generate_takeaway(packet, force_fresh=True)
    assert takeaway is not None
    assert takeaway.source == "deterministic_template"
    assert "Loss was prevented through early detection" in takeaway.executive_summary
    assert "12 parts" in takeaway.executive_summary


def test_anti_hallucination_sanitizer_scenario_3():
    """Validates that any accidental claim of savings in Scenario 3 is wiped out."""
    client = GeminiLeadershipClient(api_key="dummy_invalid_key")
    packet = LeadershipFactPacket(
        scenario_id="SCN-08-LOW-CONF-ABSTAIN",
        scenario_title="Scenario 08 — Low Confidence",
        final_state="ESCALATION_REQUIRED",
        outcome_theme="Escalation Required",
        dominant_signal=None,
        triggered_signals=["Anomaly Variance"],
        detection_lead_time_cycles=1,
        recommendation="MANDATORY ABSTAIN",
        operator_action="HUMAN ESCALATION",
        suspect_parts_contained=250,
        modeled_scrap_avoided=0,
        modeled_cost_avoided_inr=0.0,
        recovery_time_cycles=0,
        next_action_directive="Escalate to tooling maintenance",
    )

    # Hallucinated takeaway claiming ₹50,000 saved
    hallucinated = LeadershipTakeaway(
        headline="Fabricated report",
        executive_summary="We saved money",
        decision_rationale="Tampered settings",
        impact_statement="Saved ₹50,000 in scrap avoided!",
        next_action="Continue",
        source="gemini-3.8-flash",
        model_version="gemini-3.8-flash",
        timestamp="2026-11-06T00:00:00Z",
    )

    sanitized = client._validate_and_sanitize_numbers(hallucinated, packet)
    assert "₹50,000" not in sanitized.impact_statement
    assert "0 parts (no invented savings)" in sanitized.impact_statement


def test_gemini_client_caching():
    """Client caches generated takeaway per scenario ID."""
    client = GeminiLeadershipClient(api_key="dummy_invalid_key")
    packet = LeadershipFactPacket(
        scenario_id="SCN-06-COMPOUND",
        scenario_title="Scenario 06",
        final_state="VERIFIED_RECOVERY",
        outcome_theme="Verified Recovery",
        dominant_signal="barrel_temp_z3",
        triggered_signals=["barrel_temp_z3"],
        detection_lead_time_cycles=12,
        recommendation="A1",
        operator_action="A1",
        suspect_parts_contained=12,
        modeled_scrap_avoided=281,
        modeled_cost_avoided_inr=37485.76,
        recovery_time_cycles=5,
        next_action_directive="Release production",
    )

    t1 = client.generate_takeaway(packet, force_fresh=True)
    t2 = client.generate_takeaway(packet, force_fresh=False)
    assert t1 is t2


# =============================================================================
# 3. API Endpoints Integration Tests
# =============================================================================

def test_api_get_active_leadership_brief(test_client):
    """GET /api/leadership/brief returns valid report for active scenario."""
    # First select scenario 1
    resp_sel = test_client.post("/api/scenarios/SCN-06-COMPOUND/select")
    assert resp_sel.status_code == 200

    resp = test_client.get("/api/leadership/brief")
    assert resp.status_code == 200
    data = resp.json()
    assert data["scenario_id"] == "SCN-06-COMPOUND"
    assert data["final_state"] == "VERIFIED_RECOVERY"
    assert data["business_impact"]["suspect_parts_contained"] == 12
    assert data["business_impact"]["modeled_scrap_avoided"] == 281
    assert "disclaimer" in data["business_impact"]


def test_api_get_specific_scenario_briefs(test_client):
    """GET /api/leadership/brief/{id} returns valid reports for all 3 scenarios."""
    for sid, expected_state in [
        ("SCN-06-COMPOUND", "VERIFIED_RECOVERY"),
        ("SCN-FLIP-HUMAN-CHANNEL", "QC_HOLD"),
        ("SCN-08-LOW-CONF-ABSTAIN", "ESCALATION_REQUIRED"),
    ]:
        resp = test_client.get(f"/api/leadership/brief/{sid}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["scenario_id"] == sid
        assert data["final_state"] == expected_state
        assert len(data["story_steps"]) == 4
        assert len(data["decision_evidence"]["triggered_signals"]) > 0
        assert data["leadership_takeaway"]["executive_summary"] is not None


def test_api_unknown_scenario_returns_404(test_client):
    """Unknown scenario returns 404."""
    resp = test_client.get("/api/leadership/brief/SCN-UNKNOWN-999")
    assert resp.status_code == 404

