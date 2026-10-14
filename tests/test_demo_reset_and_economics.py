"""Unit & Integration Tests for Deterministic Isolated Demo Reset & Economic Impact (DEMO-01, DEMO-02)."""

import pytest
from fastapi.testclient import TestClient
from process_guardian.api.app import create_app
from process_guardian.api.dependencies import ServiceContainer, set_service_container
from process_guardian.storage.schemas import StoredAuditLogRecord


@pytest.fixture
def client_with_clean_container():
    """Create a TestClient with a fresh in-memory service container."""
    container = ServiceContainer(db_path=":memory:", auto_apply_intervention=False)
    set_service_container(container)
    app = create_app()
    return TestClient(app), container


def test_demo_reset_preserves_historical_audit_records(client_with_clean_container):
    """Verify that demo reset clears active telemetry while strictly preserving audit history (DEMO-02)."""
    client, container = client_with_clean_container

    # 1. Seed some initial audit log entries
    container.repository.log_audit_event(
        StoredAuditLogRecord(
            event_id="audit_event_1",
            cycle_index=15,
            machine_id="IMM-01",
            timestamp="2026-09-24T10:00:00Z",
            event_type="PARAMETER_DRIFT_ALERT",
            severity="WARNING",
            description="Historical drift alert from run 1",
            details_json={"param": "barrel_temp_z3"},
        )
    )
    container.repository.log_audit_event(
        StoredAuditLogRecord(
            event_id="audit_event_2",
            cycle_index=20,
            machine_id="IMM-01",
            timestamp="2026-09-24T10:05:00Z",
            event_type="RECOMMENDATION_ISSUED",
            severity="INFO",
            description="Historical intervention recommendation from run 1",
            details_json={"action_id": "A1"},
        )
    )

    prior_audit_logs = container.repository.list_audit_logs("IMM-01")
    assert len(prior_audit_logs) >= 2

    # 2. Trigger demo reset via REST API
    response = client.post("/api/demo/reset", json={"machine_id": "IMM-01", "seed_baseline": True, "baseline_cycles": 60})
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "RESET_COMPLETE"
    assert "run_" in data["run_id"]
    assert data["state"] == "HEALTHY"
    assert data["seeded_cycles"] == 60
    assert data["audit_records_preserved"] >= 3  # 2 prior + 1 DEMO_SESSION_RESET

    # 3. Verify prior audit records remain intact and queryable
    post_reset_audit_logs = container.repository.list_audit_logs("IMM-01")
    event_ids = [r.event_id for r in post_reset_audit_logs]
    assert "audit_event_1" in event_ids
    assert "audit_event_2" in event_ids

    # Verify a DEMO_SESSION_RESET record was inserted
    reset_records = [r for r in post_reset_audit_logs if r.event_type == "DEMO_SESSION_RESET"]
    assert len(reset_records) >= 1
    assert reset_records[0].details_json["run_id"] == data["run_id"]

    # 4. Verify /api/demo/runs lists this reset event
    runs_res = client.get("/api/demo/runs")
    assert runs_res.status_code == 200
    runs_data = runs_res.json()
    assert len(runs_data) >= 1
    assert runs_data[0]["details"]["run_id"] == data["run_id"]


def test_economic_impact_avoided_scrap_calculation(client_with_clean_container):
    """Verify Modeled Avoided Scrap Value formula, configurable cost, and clear assumptions (DEMO-01, Step 10)."""
    client, container = client_with_clean_container

    # 1. Query initial healthy baseline economic impact
    res = client.get("/api/demo/economic-impact?part_cost=450.0")
    assert res.status_code == 200
    data = res.json()

    assert data["part_cost"] == 450.0
    assert data["currency"] == "INR"
    assert data["currency_symbol"] == "₹"
    assert data["assumptions_label"] == "Modeled Avoided Scrap Value"
    assert "SIMULATION · PROTOTYPE RESULTS ONLY" in data["disclaimer"]
    assert data["is_prototype"] is True
    assert "Assumes ₹450.00/part defect cost" in data["assumptions_detail"]

    # 2. Simulate drift and containment window
    container.orchestrator.containment_engine.record_drift_detection(cycle_index=420)
    container.orchestrator.containment_engine.record_intervention(cycle_index=442)
    container.orchestrator.containment_engine.record_recovery_verified(recovery_cycle=444, release_cycle=445)

    # Populate 450 cycle records in orchestrator
    container.orchestrator.cycle_records = [None] * 450

    res_drift = client.get("/api/demo/economic-impact?part_cost=450.0")
    assert res_drift.status_code == 200
    data_drift = res_drift.json()

    # Quarantined window: cycles 420 to 444 = 25 cycles (or suspect count)
    # Avoided defective cycles = the quarantined/suspect cycles themselves -- the
    # parts Guardian withheld from shipping, not the other 425 cycles in the run
    # that have nothing to do with this drift event.
    assert data_drift["quarantined_suspect_cycles"] == 25
    assert data_drift["avoided_defective_cycles"] == 25
    assert data_drift["modeled_avoided_scrap_value"] == 25 * 450.0  # 11,250.0

    # 3. Test with configurable part cost parameter (e.g. ₹550)
    res_custom = client.get("/api/demo/economic-impact?part_cost=550.0")
    assert res_custom.status_code == 200
    data_custom = res_custom.json()
    assert data_custom["part_cost"] == 550.0
    assert data_custom["modeled_avoided_scrap_value"] == 25 * 550.0
    assert "Assumes ₹550.00/part defect cost" in data_custom["assumptions_detail"]


def test_reset_clears_stale_scenario_simulator(client_with_clean_container):
    """Regression (hostile-review MEDIUM #5): selecting a scenario leaves container.active_sim
    and active_scenario_summary set. A subsequent demo reset must clear both, or the stale
    simulator keeps stepping from its own cycle count on the next apply-demo call -- advancing
    the machine far past the freshly-seeded baseline cycles instead of acting on them."""
    client, container = client_with_clean_container

    # 1. Select a scenario -- this sets active_sim and active_scenario_summary.
    res_select = client.post("/api/scenarios/SCN-01-THERMAL/select")
    assert res_select.status_code == 200
    assert container.active_sim is not None
    assert container.active_scenario_summary is not None

    # 2. Reset to a short baseline -- must clear the stale scenario state, not just the DB.
    res_reset = client.post("/api/demo/reset", json={"machine_id": "IMM-01", "seed_baseline": True, "baseline_cycles": 5})
    assert res_reset.status_code == 200
    assert container.active_sim is None, "reset must clear the stale scenario simulator"
    assert container.active_scenario_summary is None, "reset must clear the stale scenario summary"

    # 3. Apply-demo must act on the freshly-seeded baseline, not resume the old scenario
    # simulator mid-run (which would jump the cycle index far past the 5 seeded cycles).
    res_apply = client.post("/api/interventions/apply-demo", json={"machine_id": "IMM-01", "action_id": "A1"})
    assert res_apply.status_code == 200
    apply_cycle = res_apply.json()["cycle_index"]
    assert apply_cycle <= 10, (
        f"apply-demo cycle_index={apply_cycle} indicates the stale scenario simulator "
        f"(not the freshly-reset 5-cycle baseline) drove the response"
    )


def test_reset_rejects_invalid_baseline_cycles(client_with_clean_container):
    """Regression (hostile-review MEDIUM #6): negative/zero/oversized baseline_cycles must be
    rejected by request validation, not silently accepted (e.g. a negative value previously
    seeded 0 cycles and returned 200 as if the request were honored)."""
    client, container = client_with_clean_container

    res_negative = client.post("/api/demo/reset", json={"machine_id": "IMM-01", "baseline_cycles": -5})
    assert res_negative.status_code == 422

    res_zero = client.post("/api/demo/reset", json={"machine_id": "IMM-01", "baseline_cycles": 0})
    assert res_zero.status_code == 422

    res_huge = client.post("/api/demo/reset", json={"machine_id": "IMM-01", "baseline_cycles": 100000})
    assert res_huge.status_code == 422


def test_reset_rejects_unknown_machine_id(client_with_clean_container):
    """Regression (hostile-review MEDIUM #6): a reset request for a machine_id the container
    doesn't serve must be rejected, not silently run against the real machine while echoing
    the caller's unrelated machine_id back in the response."""
    client, container = client_with_clean_container

    res = client.post("/api/demo/reset", json={"machine_id": "IMM-99", "baseline_cycles": 10})
    assert res.status_code == 400
