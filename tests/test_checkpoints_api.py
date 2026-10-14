"""API tests for Operational Poka-Yoke checkpoints and the Containment Boundary (QCHK-02, CNTN-05)."""

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


def _ingest_cycle(client: TestClient, cycle_index: int) -> None:
    """Push one in-envelope telemetry cycle so endpoints have real data to report on."""
    payload = {
        "cycle_index": cycle_index,
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


def test_operational_checkpoints_require_real_telemetry():
    """With no processed cycle, the checkpoint report 404s rather than inventing setpoints.

    Regression guard: this endpoint used to fall back to a hardcoded cycle 437 and a
    fixed set of placeholder zone temperatures, so it reported confident gate status
    for a machine that had produced no data at all.
    """
    client = TestClient(app)
    response = client.get("/api/checkpoints/operational")
    assert response.status_code == 404


def test_operational_checkpoints_get():
    """Verify GET /api/checkpoints/operational returns unified 3-gate evaluation."""
    client = TestClient(app)
    _ingest_cycle(client, cycle_index=1)

    response = client.get("/api/checkpoints/operational")
    assert response.status_code == 200
    data = response.json()
    assert "recipe_verification" in data
    assert "resin_moisture" in data
    assert "mold_release_spray" in data
    assert "overall_clearance" in data
    assert "clearance_status" in data


def test_mold_spray_and_moisture_endpoints():
    """Verify POST /api/checkpoints/spray and POST /api/checkpoints/moisture update state."""
    client = TestClient(app)

    # Apply spray at cycle 105
    spray_resp = client.post(
        "/api/checkpoints/spray",
        json={"cycle_index": 105, "operator_id": "OP-301"},
    )
    assert spray_resp.status_code == 200
    spray_data = spray_resp.json()
    assert spray_data["last_spray_cycle"] == 105
    assert spray_data["cycles_since_spray"] == 0
    assert spray_data["last_operator_id"] == "OP-301"

    # Update moisture to 0.11%
    moisture_resp = client.post(
        "/api/checkpoints/moisture",
        json={"moisture_pct": 0.11, "inspector_id": "QC-202", "batch_id": "BATCH-109"},
    )
    assert moisture_resp.status_code == 200
    moisture_data = moisture_resp.json()
    assert moisture_data["moisture_pct"] == 0.11
    assert moisture_data["status"] == "PASS"
    assert moisture_data["status_label"] == "DRYING_SPEC_SATISFIED"


def test_containment_boundary_endpoint_milestones():
    """Verify GET /api/containment/boundary returns the 6 observed cycle milestones.

    There is deliberately no physical-measurement milestone: the engine cannot
    witness a caliper reading, so it does not report one.
    """
    client = TestClient(app)
    response = client.get("/api/containment/boundary")
    assert response.status_code == 200
    data = response.json()
    assert "milestones" in data
    m = data["milestones"]
    assert set(m.keys()) == {
        "last_verified_good",
        "drift_start",
        "suspect_lot_start",
        "action_applied",
        "stabilized",
        "lot_release",
    }
    assert "containment_window" in data
