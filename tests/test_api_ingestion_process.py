"""Unit and integration tests for Ingestion (API-01) and Process State (API-02) endpoints."""

import pytest
from fastapi.testclient import TestClient

from process_guardian.api.app import create_app
from process_guardian.api.dependencies import ServiceContainer, set_service_container
from process_guardian.simulator.scenarios import build_regime_scenario
from process_guardian.core.types import RegimeType


@pytest.fixture
def client():
    # Fresh isolated in-memory container for test
    container = ServiceContainer(db_path=":memory:", auto_apply_intervention=False)
    set_service_container(container)
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def test_health_check_endpoint(client):
    """Verify system health check endpoint."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "HEALTHY"
    assert data["machine_id"] == "IMM-01"
    assert data["state"] == "HEALTHY"


def test_single_cycle_ingestion(client):
    """Verify ingesting a single healthy telemetry cycle via POST /api/cycles."""
    payload = {
        "cycle_index": 1,
        "machine_id": "IMM-01",
        "mold_id": "MOLD-18",
        "part_id": "AUTO-HOUSING-A",
        "recipe_id": "RCP-12",
        "telemetry": {
            "barrel_temp_z1": 275.0,
            "barrel_temp_z2": 280.0,
            "barrel_temp_z3": 285.0,
            "barrel_temp_z4": 285.0,
            "nozzle_temp": 285.0,
            "mold_temp": 80.0,
            "injection_pressure": 120.0,
            "holding_pressure": 85.0,
            "back_pressure": 10.0,
            "injection_speed": 45.0,
            "screw_rpm": 60.0,
            "cushion_position": 5.0,
            "dosing_time": 3.5,
            "injection_time": 2.1,
            "cooling_time": 12.0,
            "cycle_time": 30.0,
            "ambient_temp": 25.0,
            "ambient_humidity": 45.0,
            "material_moisture_pct": 0.12,
            "part_weight_g": 142.5,
        },
    }

    res = client.post("/api/cycles", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["cycle_index"] == 1
    assert data["machine_id"] == "IMM-01"
    assert data["state"] == "HEALTHY"
    assert data["drift_detected"] is False
    assert data["quality_risk_pct"] < 35.0
    assert data["disposition"] == "RELEASED_PRE_DRIFT"
    assert data["is_suspect"] is False


from dataclasses import asdict

def test_batch_cycle_ingestion(client):
    """Verify ingesting a batch of cycles via POST /api/cycles."""
    sim = build_regime_scenario(RegimeType.HEALTHY, cycles=15, seed=99)
    batch = [asdict(sim.step()) for _ in range(15)]

    res = client.post("/api/cycles", json={"cycles": batch})
    assert res.status_code == 201
    data = res.json()
    assert data["total_processed"] == 15
    assert data["start_cycle"] == 1
    assert data["end_cycle"] == 15
    assert data["current_state"] == "HEALTHY"
    assert data["suspect_cycle_count"] == 0


def test_event_ingestion(client):
    """Verify ingesting external/operator event via POST /api/events."""
    event_payload = {
        "event_type": "THERMAL_DRIFT_INJECTED",
        "cycle_index": 420,
        "machine_id": "IMM-01",
        "severity": "HIGH",
        "signals": ["barrel_temp_z3"],
        "details": {"heater_fault": True, "target_delta": 4.5},
    }

    res = client.post("/api/events", json=event_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "RECORDED"
    assert data["cycle_index"] == 420
    assert data["event_id"].startswith("evt_")


def test_checkpoint_creation(client):
    """Verify creating a state checkpoint via POST /api/checkpoints."""
    chk_payload = {
        "checkpoint_name": "demo_baseline_snap",
        "machine_id": "IMM-01",
        "metadata": {"operator": "admin", "phase": 6},
    }

    res = client.post("/api/checkpoints", json=chk_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["checkpoint_name"] == "demo_baseline_snap"
    assert data["state"] == "HEALTHY"
    assert data["machine_id"] == "IMM-01"


def test_process_current_endpoint(client):
    """Verify GET /api/process/current returns live machine state and signals."""
    # Ingest a cycle first
    payload = {
        "cycle_index": 100,
        "machine_id": "IMM-01",
        "telemetry": {
            "barrel_temp_z1": 275.0,
            "barrel_temp_z2": 280.0,
            "barrel_temp_z3": 285.5,
            "barrel_temp_z4": 285.0,
            "nozzle_temp": 285.0,
            "mold_temp": 80.0,
            "injection_pressure": 120.0,
            "holding_pressure": 85.0,
            "back_pressure": 10.0,
            "injection_speed": 45.0,
            "screw_rpm": 60.0,
            "cushion_position": 5.0,
            "dosing_time": 3.5,
            "injection_time": 2.1,
            "cooling_time": 12.0,
            "cycle_time": 30.0,
            "ambient_temp": 25.0,
            "ambient_humidity": 45.0,
            "material_moisture_pct": 0.12,
            "part_weight_g": 142.5,
        },
    }
    client.post("/api/cycles", json=payload)

    res = client.get("/api/process/current?machine_id=IMM-01")
    assert res.status_code == 200
    data = res.json()
    assert data["machine_id"] == "IMM-01"
    assert data["current_cycle"] == 100
    assert data["state"] == "HEALTHY"
    assert data["process_stability_pct"] >= 90.0
    assert "barrel_temp_z3" in data["signals"]
    assert pytest.approx(data["signals"]["barrel_temp_z3"], rel=1e-3) == 285.5


def test_process_fingerprint_endpoint(client):
    """Verify GET /api/process/fingerprint returns baseline means and envelopes."""
    res = client.get("/api/process/fingerprint?machine_id=IMM-01")
    assert res.status_code == 200
    data = res.json()
    assert data["machine_id"] == "IMM-01"
    assert data["sample_count"] >= 60
    assert "barrel_temp_z3" in data["signal_means"]
    assert "barrel_temp_z3" in data["signal_envelopes"]
    assert "lower" in data["signal_envelopes"]["barrel_temp_z3"]
    assert "upper" in data["signal_envelopes"]["barrel_temp_z3"]


def test_process_drift_endpoint(client):
    """Verify GET /api/process/drift returns drift sentinel diagnostics."""
    res = client.get("/api/process/drift?machine_id=IMM-01")
    assert res.status_code == 200
    data = res.json()
    assert data["machine_id"] == "IMM-01"
    assert data["drift"] is False
    assert data["severity"] == 0.0
