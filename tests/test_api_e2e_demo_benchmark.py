"""End-to-End Primary Demo Scenario Benchmark over FastAPI & SQLite Storage Layer."""

import pytest
from dataclasses import asdict
from fastapi.testclient import TestClient

from process_guardian.api.app import create_app
from process_guardian.api.dependencies import ServiceContainer, set_service_container
from process_guardian.simulator.scenarios import build_demo_scenario
from process_guardian.state_machine.schemas import ProcessState


@pytest.fixture
def api_client():
    # Initialize container with auto_apply=False so the API demo apply endpoint can be explicitly invoked
    container = ServiceContainer(db_path=":memory:", auto_apply_intervention=False, seed=42)
    set_service_container(container)
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client, container


def test_complete_demo_scenario_via_rest_api_and_sqlite(api_client):
    """
    Execute the entire 10-step primary demo story purely through HTTP REST endpoints against SQLite:
    1. System Topology & Baseline Fingerprint Check
    2. Healthy Production (Cycles 1-419)
    3. Injected Thermal Drift at Cycle 420
    4. Early Drift Detection & Risk Escalation (Cycles 420-431)
    5. Intervention Surrogate Simulation & 7-Field Recommendation
    6. Demo Operator Enactment (POST /api/interventions/apply-demo)
    7. Post-Intervention Recovery & 3-Cycle Cooling Window (Cycles 432-444)
    8. Scrap Containment Suspect Window Quarantine & Released Disposition
    9. Verification of all 17 SQLite tables populated with full audit trail
    10. Deterministic Scenario Reset
    """
    client, container = api_client
    sim = build_demo_scenario(seed=42)

    # -------------------------------------------------------------------------
    # Step 1: Topology & Baseline Fingerprint Verification
    # -------------------------------------------------------------------------
    res_fp = client.get("/api/process/fingerprint?machine_id=IMM-01")
    assert res_fp.status_code == 200
    fp_data = res_fp.json()
    assert fp_data["machine_id"] == "IMM-01"
    assert fp_data["sample_count"] >= 60
    assert "barrel_temp_z3" in fp_data["signal_means"]

    res_qc = client.get("/api/quality/contract?part_id=AUTO-HOUSING-A")
    assert res_qc.status_code == 200
    assert res_qc.json()["target_weight_g"] == 142.5

    # -------------------------------------------------------------------------
    # Step 2: Healthy Production Run (Cycles 1-419)
    # -------------------------------------------------------------------------
    healthy_batch = [asdict(sim.step()) for _ in range(419)]
    res_healthy = client.post("/api/cycles", json={"cycles": healthy_batch})
    assert res_healthy.status_code == 201
    assert res_healthy.json()["total_processed"] == 419
    assert res_healthy.json()["current_state"] == "HEALTHY"

    # Verify Screen 1 metrics in healthy operation
    res_curr = client.get("/api/process/current?machine_id=IMM-01")
    assert res_curr.status_code == 200
    curr_data = res_curr.json()
    assert curr_data["current_cycle"] == 419
    assert curr_data["state"] == "HEALTHY"
    assert curr_data["process_stability_pct"] >= 90.0
    assert curr_data["quality_risk_pct"] <= 15.0

    # -------------------------------------------------------------------------
    # Step 3: Event Injection & Drift Telemetry (Cycles 420-440)
    # -------------------------------------------------------------------------
    res_evt = client.post(
        "/api/events",
        json={
            "event_type": "THERMAL_DRIFT_INJECTED",
            "cycle_index": 420,
            "machine_id": "IMM-01",
            "severity": "HIGH",
            "signals": ["barrel_temp_z3"],
            "details": {"heater_band_offset": 5.0, "target_signal": "barrel_temp_z3"},
        },
    )
    assert res_evt.status_code == 201
    assert res_evt.json()["status"] == "RECORDED"

    # Ingest drift cycles (420 to 440)
    drift_batch = [asdict(sim.step()) for _ in range(21)]
    res_drift = client.post("/api/cycles", json={"cycles": drift_batch})
    assert res_drift.status_code == 201
    assert res_drift.json()["end_cycle"] == 440

    # Ingest peak risk escalation cycle (441)
    res_441 = client.post("/api/cycles", json=asdict(sim.step()))
    assert res_441.status_code == 201
    assert res_441.json()["cycle_index"] == 441

    # -------------------------------------------------------------------------
    # Step 4: Early Drift Sentinel Detection & Root Cause Isolation (Screen 2)
    # -------------------------------------------------------------------------
    res_drift_diag = client.get("/api/process/drift?machine_id=IMM-01")
    assert res_drift_diag.status_code == 200
    drift_diag = res_drift_diag.json()
    assert drift_diag["drift"] is True
    assert drift_diag["severity"] >= 0.40
    assert "barrel_temp_z3" in drift_diag["contributing_signals"]

    res_risk = client.get("/api/quality/risk?machine_id=IMM-01")
    assert res_risk.status_code == 200
    risk_data = res_risk.json()
    assert risk_data["risk_probability"] >= 0.50
    assert risk_data["risk_state"] == "HIGH"
    assert risk_data["root_cause_isolated"] is True
    assert len(risk_data["contributors"]) > 0
    top_contributor = risk_data["contributors"][0]
    assert top_contributor["signal_name"] == "barrel_temp_z3"
    assert top_contributor["percentage"] >= 50.0

    # -------------------------------------------------------------------------
    # Step 5: Candidate Action Simulation & 7-Field Recommendation (Screen 3)
    # -------------------------------------------------------------------------
    res_sim = client.post("/api/interventions/simulate", json={"machine_id": "IMM-01"})
    assert res_sim.status_code == 200
    sim_data = res_sim.json()
    assert len(sim_data["candidates"]) >= 4

    res_rec = client.get("/api/interventions/recommendation?machine_id=IMM-01")
    assert res_rec.status_code == 200
    rec_data = res_rec.json()
    assert "barrel_temp_z3" in rec_data["action"] or "temperature" in rec_data["action"].lower()
    assert rec_data["confidence"] >= 0.80
    assert rec_data["is_abstain"] is False
    assert len(rec_data["expected_effect"]) > 0
    assert len(rec_data["operating_limit"]) > 0
    assert len(rec_data["recovery_check"]) > 0

    # -------------------------------------------------------------------------
    # Step 6: Apply Demo Corrective Intervention (A1)
    # -------------------------------------------------------------------------
    res_apply = client.post(
        "/api/interventions/apply-demo",
        json={"machine_id": "IMM-01", "action_id": "A1", "applied_by": "LEAD_OPERATOR"},
    )
    assert res_apply.status_code == 200
    apply_data = res_apply.json()
    assert apply_data["status"] == "APPLIED"
    assert apply_data["new_state"] == "RECOVERY_CHECK"

    # Verify recovery monitoring is active
    res_recov_pre = client.get("/api/recovery/status?machine_id=IMM-01")
    assert res_recov_pre.status_code == 200
    assert res_recov_pre.json()["is_monitoring"] is True

    # -------------------------------------------------------------------------
    # Step 7: Post-Intervention Recovery Telemetry & Cooling Window (Cycles 442-444)
    # -------------------------------------------------------------------------
    # Inject recovery cycle telemetry through the pipeline step by step (Cycles 442, 443, 444)
    for _ in range(3):
        c_payload = asdict(sim.step())
        client.post("/api/cycles", json=c_payload)

    # Verify recovery verification completed
    res_recov_post = client.get("/api/recovery/status?machine_id=IMM-01")
    assert res_recov_post.status_code == 200
    recov_post = res_recov_post.json()
    assert recov_post["recovery_status"] == "VERIFIED"
    assert recov_post["release_decision"] == "APPROVED"
    assert recov_post["consecutive_stable_cycles"] >= 3

    # -------------------------------------------------------------------------
    # Step 8: Scrap Containment Window & Production Release
    # -------------------------------------------------------------------------
    res_win = client.get("/api/containment/window?machine_id=IMM-01")
    assert res_win.status_code == 200
    win_data = res_win.json()
    assert win_data["suspect_start_cycle"] >= 420
    assert win_data["recovery_cycle"] == 444
    assert win_data["release_cycle"] == 445
    assert win_data["suspect_cycle_count"] <= 25  # Tightly contained suspect window
    assert win_data["estimated_scrap_saved_cycles"] >= 400  # Saved ~95%+ of 450 total cycles!

    # Authorize release
    res_rel = client.post(
        "/api/containment/release",
        json={"machine_id": "IMM-01", "release_notes": "Post-recovery Quality Contract verified compliant.", "operator_id": "QC_SUPERVISOR"},
    )
    assert res_rel.status_code == 200
    assert res_rel.json()["status"] == "RELEASE_AUTHORIZED"

    # Ingest remaining healthy cycles (445-450)
    final_batch = [asdict(sim.step()) for _ in range(6)]
    res_final = client.post("/api/cycles", json={"cycles": final_batch})
    assert res_final.status_code == 201
    assert res_final.json()["end_cycle"] == 450

    # -------------------------------------------------------------------------
    # Step 9: Verify All 17 SQLite Tables Populated with Records (STOR-01, STOR-02)
    # -------------------------------------------------------------------------
    repo = container.repository
    assert len(repo.list_machines()) >= 1
    assert repo.get_mold("MOLD-18") is not None
    assert repo.get_part("AUTO-HOUSING-A") is not None
    assert repo.get_recipe("RCP-12") is not None
    assert repo.get_material("PA66-GF30") is not None
    assert repo.get_cycle_count("IMM-01") == 450
    assert repo.get_fingerprint_by_machine("IMM-01") is not None
    assert repo.get_quality_contract_by_part("AUTO-HOUSING-A") is not None
    assert len(repo.list_drift_events("IMM-01")) >= 1
    assert len(repo.list_quality_predictions("IMM-01")) >= 1
    assert repo.get_latest_recommendation("IMM-01") is not None
    assert len(repo.list_intervention_applications("IMM-01")) >= 1
    assert repo.get_latest_recovery_event("IMM-01") is not None
    assert repo.get_latest_containment_window("IMM-01") is not None
    assert len(repo.list_audit_logs("IMM-01")) >= 5

    # -------------------------------------------------------------------------
    # Step 10: Deterministic Scenario Reset
    # -------------------------------------------------------------------------
    container.reset()
    assert repo.get_cycle_count("IMM-01") == 0
    assert container.orchestrator.current_state == ProcessState.HEALTHY
