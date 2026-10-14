"""Integration tests for Scenario Engine REST API endpoints."""

import pytest
from fastapi.testclient import TestClient
from process_guardian.api.app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_list_scenarios_endpoint(client):
    """Test GET /api/scenarios returns all 9 scenarios."""
    resp = client.get("/api/scenarios")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 9
    ids = [s["scenario_id"] for s in data]
    assert "SCN-01-THERMAL" in ids
    assert "SCN-06-COMPOUND" in ids
    assert "SCN-FLIP-HUMAN-CHANNEL" in ids


def test_list_hero_scenarios_filter(client):
    """GET /api/scenarios?hero_only=true returns only the locked demo-worthy set.

    Per scope_plan.md Sec.4: live demo keeps S06 (closed-loop + SPC contradiction),
    SCN-FLIP-HUMAN-CHANNEL (the sensor-blind gap filled), and S08 (ABSTAIN / trust
    gate). The other 8 scenarios stay in the registry for the automated validation
    suite but are not surfaced as hero/live scenarios.
    """
    resp = client.get("/api/scenarios?hero_only=true")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    assert all(s["is_hero"] is True for s in data)
    ids = {s["scenario_id"] for s in data}
    assert ids == {"SCN-06-COMPOUND", "SCN-FLIP-HUMAN-CHANNEL", "SCN-08-LOW-CONF-ABSTAIN"}


def test_get_single_scenario_endpoint(client):
    """Test GET /api/scenarios/{id} returns narrative and details."""
    resp = client.get("/api/scenarios/SCN-01-THERMAL")
    assert resp.status_code == 200
    data = resp.json()
    assert data["scenario_id"] == "SCN-01-THERMAL"
    assert len(data["narrative"]) >= 4
    assert data["expected_outcome"]["dominant_signal"] == "barrel_temp_z3"


def test_get_unknown_scenario_returns_404(client):
    """Test GET /api/scenarios/INVALID returns 404."""
    resp = client.get("/api/scenarios/INVALID_SCENARIO_ID")
    assert resp.status_code == 404


def test_select_scenario_endpoint(client):
    """Test POST /api/scenarios/{id}/select sets active scenario."""
    resp = client.post("/api/scenarios/SCN-02-PRESSURE/select")
    assert resp.status_code == 200
    data = resp.json()
    assert data["scenario"]["scenario_id"] == "SCN-02-PRESSURE"
    assert data["scorecard"]["scenario_id"] == "SCN-02-PRESSURE"
    assert len(data["stream"]) > 0

    # Verify active scenario endpoint reflects this
    active_resp = client.get("/api/scenarios/active")
    assert active_resp.status_code == 200
    assert active_resp.json()["active_scenario_id"] == "SCN-02-PRESSURE"


def test_validation_suite_endpoint(client):
    """Test GET /api/scenarios/validation-suite returns comprehensive report."""
    resp = client.get("/api/scenarios/validation-suite")
    assert resp.status_code == 200
    data = resp.json()
    assert data["metrics"]["total_scenarios_evaluated"] == 9
    assert len(data["scorecards"]) == 9
    assert data["metrics"]["completion_rate_pct"] == 100.0


def test_select_unknown_scenario_returns_404(client):
    """A genuinely missing scenario id is still a 404."""
    resp = client.post("/api/scenarios/NO_SUCH_SCENARIO/select")
    assert resp.status_code == 404
    assert "not found in registry" in resp.json()["detail"]


def test_replay_failure_is_not_reported_as_a_missing_scenario(client, monkeypatch):
    """A ValueError from inside the replay must not masquerade as 'scenario not found'.

    Regression guard: both failures used to return 404 "not found in registry",
    which points anyone debugging a broken replay at the registry instead of at
    the real exception.
    """
    from process_guardian.api.dependencies import get_service_container

    container = get_service_container()
    assert container.scenario_registry.get("SCN-01-THERMAL") is not None

    def boom(_scenario_id):
        raise ValueError("surrogate model produced a non-finite value")

    monkeypatch.setattr(container, "select_scenario", boom)

    resp = client.post("/api/scenarios/SCN-01-THERMAL/select")
    assert resp.status_code == 500
    detail = resp.json()["detail"]
    assert "failed during replay" in detail
    assert "non-finite" in detail  # the real cause survives to the caller
