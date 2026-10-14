"""API integration tests for Controlled Counterfactual Replay Canvas (CRPL-01, CRPL-02)."""

import pytest
from fastapi.testclient import TestClient

from process_guardian.api.app import app
from process_guardian.api.dependencies import ServiceContainer, set_service_container


@pytest.fixture(autouse=True)
def setup_test_container():
    """Create fresh isolated service container for each test."""
    container = ServiceContainer(db_path=":memory:", auto_apply_intervention=False)
    set_service_container(container)
    yield container


def test_get_counterfactual_compare_endpoint():
    """Verify GET /api/counterfactual/compare returns dual streams, delta KPIs, and >75% suspect lot reduction."""
    client = TestClient(app)
    response = client.get("/api/counterfactual/compare?total_cycles=156")
    assert response.status_code == 200
    data = response.json()

    # Structure checks
    assert "guardian_off" in data
    assert "guardian_on" in data
    assert "suspect_lot_reduction_pct" in data
    assert "scrap_reduction_pct" in data
    assert "net_avoided_loss" in data
    assert "timeline_divergence_cycle" in data
    assert "epistemic_level" in data
    assert data["epistemic_level"] == "LEVEL_4_CONTROLLED_COUNTERFACTUAL"

    # KPI values
    assert data["suspect_lot_reduction_pct"] >= 75.0
    assert data["scrap_reduction_pct"] >= 85.0
    assert data["net_avoided_loss"] > 10000.0
    assert data["timeline_divergence_cycle"] == 85

    # Stream checks
    off_stream = data["guardian_off"]["stream"]
    on_stream = data["guardian_on"]["stream"]
    assert len(off_stream) == 156
    assert len(on_stream) == 156

    # Compare cycle 70 (pre-drift)
    assert off_stream[69]["barrel_temp"] == on_stream[69]["barrel_temp"]

    # Compare cycle 110 (post-divergence)
    assert off_stream[109]["barrel_temp"] > 250.0
    assert on_stream[109]["barrel_temp"] < 237.0
    assert off_stream[109]["is_quarantine"] is True
    assert on_stream[109]["is_quarantine"] is False


def test_post_counterfactual_replay_endpoint():
    """Verify POST /api/counterfactual/replay accepts custom horizon and parameters."""
    client = TestClient(app)
    payload = {
        "total_cycles": 120,
        "drift_start_cycle": 72,
        "intervention_cycle": 85,
    }
    response = client.post("/api/counterfactual/replay", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["guardian_off"]["total_cycles"] == 120
    assert data["guardian_on"]["total_cycles"] == 120
    assert len(data["guardian_off"]["stream"]) == 120
    assert data["net_avoided_loss"] > 0.0
