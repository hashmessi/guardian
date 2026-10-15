"""Unit and integration tests for Quality (API-03), Interventions (API-04), and Recovery/Containment (API-05) endpoints."""

import pytest
from dataclasses import asdict
from fastapi.testclient import TestClient

from process_guardian.api.app import create_app
from process_guardian.api.dependencies import ServiceContainer, set_service_container
from process_guardian.simulator.scenarios import build_regime_scenario, build_demo_scenario
from process_guardian.core.types import RegimeType
from process_guardian.storage.schemas import StoredRecommendationRecord


@pytest.fixture
def client():
    # Fresh isolated in-memory container for test
    container = ServiceContainer(db_path=":memory:", auto_apply_intervention=False)
    set_service_container(container)
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def test_quality_endpoints(client):
    """Verify GET /api/quality/risk and GET /api/quality/contract."""
    # 1. Quality contract query
    res_contract = client.get("/api/quality/contract?part_id=AUTO-HOUSING-A")
    assert res_contract.status_code == 200
    contract = res_contract.json()
    assert contract["part_id"] == "AUTO-HOUSING-A"
    assert contract["target_weight_g"] == 142.5
    assert contract["weight_min_g"] == 141.0
    assert contract["weight_max_g"] == 144.0
    assert contract["max_sink_mark_mm"] == 0.08
    assert contract["allow_flash"] is False

    # 2. Quality risk query before cycles
    res_risk_pre = client.get("/api/quality/risk?machine_id=IMM-01")
    assert res_risk_pre.status_code == 200
    risk_pre = res_risk_pre.json()
    assert risk_pre["risk_probability"] <= 0.35
    assert risk_pre["risk_state"] == "LOW"


def test_interventions_and_recommendation_flow(client):
    """Verify simulation, recommendation retrieval, and demo intervention application."""
    # Ingest 10 healthy cycles
    sim = build_regime_scenario(RegimeType.HEALTHY, cycles=10, seed=42)
    batch = [asdict(sim.step()) for _ in range(10)]
    client.post("/api/cycles", json={"cycles": batch})

    # 1. Simulate Candidate Actions
    res_sim = client.post("/api/interventions/simulate", json={"machine_id": "IMM-01"})
    assert res_sim.status_code == 200
    sim_data = res_sim.json()
    assert len(sim_data["candidates"]) >= 4
    assert sim_data["recommended_action_id"] in ["A0", "A1", "A2", "A3", "A4"]

    # 2. Recommendation Endpoint
    res_rec = client.get("/api/interventions/recommendation?machine_id=IMM-01")
    assert res_rec.status_code == 200
    rec_data = res_rec.json()
    assert "action" in rec_data
    assert "why" in rec_data
    assert "evidence" in rec_data
    assert "expected_effect" in rec_data
    assert "confidence" in rec_data
    assert "operating_limit" in rec_data
    assert "recovery_check" in rec_data

    # 3. Apply Demo Intervention
    res_apply = client.post(
        "/api/interventions/apply-demo",
        json={"machine_id": "IMM-01", "action_id": "A1", "applied_by": "LEAD_OP_01"},
    )
    assert res_apply.status_code == 200
    apply_data = res_apply.json()
    assert apply_data["status"] == "APPLIED"
    assert apply_data["new_state"] == "RECOVERY_CHECK"
    assert apply_data["action_id"] == "A1"
    # Regression (hostile-review MEDIUM #4): no scenario simulator is active in this test,
    # so zero recovery cycles were stepped -- the message must say so, not claim "3
    # consecutive stabilization cycles verified" regardless of what actually happened.
    assert "3 recovery cycles" not in apply_data["message"]
    assert "not stepped" in apply_data["message"]

    # 4. Intervention History Endpoint
    res_hist = client.get("/api/interventions/history?machine_id=IMM-01")
    assert res_hist.status_code == 200
    hist_data = res_hist.json()
    assert len(hist_data["applications"]) == 1
    assert hist_data["applications"][0]["action_id"] == "A1"
    assert hist_data["applications"][0]["applied_by"] == "LEAD_OP_01"


def test_apply_demo_rejects_unknown_action_id(client):
    """Regression (hostile-review HIGH/MEDIUM): posting an action_id that isn't one
    of the evaluated candidates used to be silently accepted -- either substituting
    the engine's own pick (if a recommendation was pending) or fabricating a candidate
    with the unknown id (if not) -- and reporting 200 APPLIED either way, with an
    audit record for an action nobody actually offered."""
    sim = build_regime_scenario(RegimeType.THERMAL_DRIFT, cycles=40, seed=123)
    batch = [asdict(sim.step()) for _ in range(40)]
    client.post("/api/cycles", json={"cycles": batch})

    res_rec = client.get("/api/interventions/recommendation?machine_id=IMM-01")
    assert res_rec.status_code == 200
    valid_ids = {c["action_id"] for c in res_rec.json()["candidate_comparison"]}
    assert valid_ids, "fixture must reach a real pending recommendation with candidates"
    assert "NOT_REAL" not in valid_ids

    res_bad = client.post(
        "/api/interventions/apply-demo",
        json={"machine_id": "IMM-01", "action_id": "NOT_REAL", "applied_by": "QA"},
    )
    assert res_bad.status_code == 404
    assert "NOT_REAL" in res_bad.json()["detail"]

    # No audit trail of an action that was never actually offered or applied.
    res_hist = client.get("/api/interventions/history?machine_id=IMM-01")
    assert res_hist.json()["applications"] == []

    # A valid id from the same table still applies cleanly.
    res_ok = client.post(
        "/api/interventions/apply-demo",
        json={"machine_id": "IMM-01", "action_id": next(iter(valid_ids)), "applied_by": "QA"},
    )
    assert res_ok.status_code == 200


def test_recovery_and_containment_endpoints(client):
    """Verify recovery verification tracking, containment window inspection, and batch release."""
    # Ingest 10 healthy cycles
    sim = build_regime_scenario(RegimeType.HEALTHY, cycles=10, seed=42)
    batch = [asdict(sim.step()) for _ in range(10)]
    client.post("/api/cycles", json={"cycles": batch})

    # Apply an intervention to start recovery tracking
    client.post("/api/interventions/apply-demo", json={"machine_id": "IMM-01", "action_id": "A1"})

    # 1. Recovery Status
    res_recov = client.get("/api/recovery/status?machine_id=IMM-01")
    assert res_recov.status_code == 200
    recov_data = res_recov.json()
    assert recov_data["is_monitoring"] is True
    assert recov_data["required_stable_cycles"] == 3

    # 2. Containment Window
    res_win = client.get("/api/containment/window?machine_id=IMM-01")
    assert res_win.status_code == 200
    win_data = res_win.json()
    assert win_data["machine_id"] == "IMM-01"
    assert win_data["suspect_cycle_count"] >= 0

    # 3. Authorize Production Release
    res_rel = client.post(
        "/api/containment/release",
        json={"machine_id": "IMM-01", "release_notes": "Dimensional QC passed 100%", "operator_id": "QC_MGR"},
    )
    assert res_rel.status_code == 200
    rel_data = res_rel.json()
    assert rel_data["status"] == "RELEASE_AUTHORIZED"
    assert "QC_MGR" in rel_data["message"]


def test_stored_recommendation_has_no_fabricated_economics(client):
    """Regression (hostile-review MEDIUM #8): StoredRecommendationRecord does not persist
    the risk value that produced it, so GET /recommendation for a *replayed* (non-live)
    recommendation must not fabricate a decision_value_breakdown from a hardcoded
    current_risk_probability=0.48 -- it must report no breakdown instead."""
    client_obj = client
    # No live pending_recommendation on the orchestrator -- forces the stored_rec branch.
    container = ServiceContainer(db_path=":memory:", auto_apply_intervention=False)
    set_service_container(container)
    from fastapi.testclient import TestClient
    from process_guardian.api.app import create_app
    app = create_app()
    with TestClient(app) as c:
        rec = StoredRecommendationRecord(
            recommendation_id="rec_stored_001",
            event_id="evt_stored_001",
            cycle_index=431,
            machine_id="IMM-01",
            action_id="A1",
            action_text="Decrease barrel temperature zone 3 by -4.0 deg C",
            why_text="Barrel temperature zone 3 elevated above fingerprint baseline.",
            evidence_json={"primary_signal": "barrel_temp_z3"},
            expected_effect="Reduces melt temperature, lowers flash risk.",
            confidence=0.93,
            operating_limit="Within safe limits [260.0, 300.0] deg C.",
            recovery_check="Confirm zone 3 temp within 3 cycles.",
            is_abstain=False,
            operator_mode="DIRECT_RECOMMENDATION",
        )
        container.repository.insert_recommendation(rec, [])
        assert container.orchestrator.pending_recommendation is None

        res = c.get("/api/interventions/recommendation?machine_id=IMM-01")
        assert res.status_code == 200
        data = res.json()
        assert data["recommendation_id"] == "rec_stored_001"
        assert data["decision_value_breakdown"] is None, (
            "a stored recommendation has no real risk value on record -- the breakdown "
            "must be None, not computed from a fabricated current_risk_probability"
        )
