"""Tests for Decision Economics and Parametric CoPQ REST API Endpoints (ECON-01, ECON-02)."""

import pytest
from fastapi.testclient import TestClient

from process_guardian.api.app import create_app
from process_guardian.api.dependencies import ServiceContainer, get_service_container


@pytest.fixture
def client_with_container():
    """Create test client with clean in-memory container."""
    container = ServiceContainer(db_path=":memory:", machine_id="IMM-01")
    app = create_app()
    app.dependency_overrides[get_service_container] = lambda: container
    with TestClient(app) as client:
        yield client, container
    app.dependency_overrides.clear()


def test_get_copq_parameters_api(client_with_container):
    """Verify GET /api/economics/parameters returns standard automotive defaults."""
    client, _ = client_with_container
    resp = client.get("/api/economics/parameters")
    assert resp.status_code == 200
    data = resp.json()

    assert data["resin_price_per_kg"] == 195.0
    assert data["part_weight_grams"] == 220.0
    assert data["machine_hourly_rate"] == 1650.0
    assert data["cycle_time_seconds"] == 24.0
    assert data["electricity_tariff_per_kwh"] == 9.80
    assert data["sorting_cost_per_part"] == 22.0
    assert data["oem_penalty_risk_per_defect"] == 150.0


def test_get_copq_breakdown_api(client_with_container):
    """Verify GET /api/economics/copq returns itemized and total cost amounts."""
    client, _ = client_with_container
    resp = client.get("/api/economics/copq")
    assert resp.status_code == 200
    data = resp.json()

    assert data["material_cost_per_defect"] > 0.0
    assert data["machine_burden_per_defect"] > 0.0
    assert data["energy_cost_per_defect"] > 0.0
    assert data["sorting_cost_per_defect"] == 22.0
    assert data["direct_scrap_copq_per_defect"] > 0.0
    assert data["oem_penalty_risk"] == 150.0
    assert data["total_copq_per_defect"] == round(
        data["direct_scrap_copq_per_defect"] + data["oem_penalty_risk"], 2
    )
    assert data["currency"] == "INR (₹)"


def test_update_copq_parameters_api(client_with_container):
    """Verify POST /api/economics/parameters updates inputs and recalculates breakdown immediately."""
    client, _ = client_with_container

    update_payload = {
        "resin_type": "PBT-GF20 Automotive Grade",
        "resin_price_per_kg": 320.0,
        "part_weight_grams": 180.0,
        "runner_scrap_fraction": 0.05,
        "regrind_recovery_credit": 0.15,
        "machine_hourly_rate": 2100.0,
        "cycle_time_seconds": 22.0,
        "machine_power_kw": 22.0,
        "electricity_tariff_per_kwh": 10.20,
        "sorting_cost_per_part": 28.0,
        "oem_penalty_risk_per_defect": 200.0,
    }

    resp = client.post("/api/economics/parameters", json=update_payload)
    assert resp.status_code == 200
    res_data = resp.json()

    assert res_data["message"] == "CoPQ parameters successfully updated and verified."
    assert res_data["parameters"]["resin_price_per_kg"] == 320.0
    assert res_data["parameters"]["machine_hourly_rate"] == 2100.0

    # Ensure subsequent GET reflects the change
    get_resp = client.get("/api/economics/copq")
    assert get_resp.status_code == 200
    assert get_resp.json()["sorting_cost_per_defect"] == 28.0


def test_update_copq_parameters_propagates_to_scenario_runner(client_with_container):
    """Regression (hostile-review LOW #10): scenario_runner holds its own copq_params and
    copq_calculator (constructed once at container init) plus a per-scenario-id result
    cache. Updating economics parameters via POST must update the runner's copy and clear
    its cache too, or scenario scorecards/validation-suite INR figures silently keep using
    the stale price after the update."""
    client, container = client_with_container

    original_resin_price = container.scenario_runner.copq_params.resin_price_per_kg
    assert original_resin_price != 320.0

    # Prime the scenario cache so staleness would be observable if the fix were missing.
    from process_guardian.scenario.registry import get_scenario_registry
    scn = get_scenario_registry().get("SCN-01-THERMAL")
    container.scenario_runner.run_scenario(scn, use_cache=True)
    assert "SCN-01-THERMAL" in container.scenario_runner._cache

    update_payload = {
        "resin_type": "PBT-GF20 Automotive Grade",
        "resin_price_per_kg": 320.0,
        "part_weight_grams": 180.0,
        "runner_scrap_fraction": 0.05,
        "regrind_recovery_credit": 0.15,
        "machine_hourly_rate": 2100.0,
        "cycle_time_seconds": 22.0,
        "machine_power_kw": 22.0,
        "electricity_tariff_per_kwh": 10.20,
        "sorting_cost_per_part": 28.0,
        "oem_penalty_risk_per_defect": 200.0,
    }
    resp = client.post("/api/economics/parameters", json=update_payload)
    assert resp.status_code == 200

    assert container.scenario_runner.copq_params.resin_price_per_kg == 320.0
    assert container.scenario_runner.copq_calculator.default_params.resin_price_per_kg == 320.0
    assert "SCN-01-THERMAL" not in container.scenario_runner._cache, (
        "stale cached scorecard must be invalidated after a price update"
    )


def test_get_decision_value_api_hold_and_intervene(client_with_container):
    """Verify GET /api/economics/decision-value evaluates Cost of Waiting vs Cost of Acting."""
    client, _ = client_with_container

    # Case A: Low risk (5%) -> should recommend MONITOR_AND_WAIT
    resp_low = client.get("/api/economics/decision-value?risk_probability=0.05&confidence=0.95")
    assert resp_low.status_code == 200
    data_low = resp_low.json()

    assert data_low["decision_value"] < 0.0
    assert data_low["actionable_recommendation"] == "MONITOR_AND_WAIT"
    assert data_low["avoided_loss_if_acting"] == 0.0
    assert "Disturbing machine now would cause unnecessary scrap" in data_low["justification"]

    # Case B: High risk (55%) -> should recommend INTERVENE_NOW
    resp_high = client.get("/api/economics/decision-value?risk_probability=0.55&confidence=0.92")
    assert resp_high.status_code == 200
    data_high = resp_high.json()

    assert data_high["decision_value"] > 0.0
    assert data_high["actionable_recommendation"] == "INTERVENE_NOW"
    assert data_high["avoided_loss_if_acting"] == data_high["decision_value"]
    assert "Corrective adjustment is economically justified" in data_high["justification"]

    # Case C: Low confidence (< 0.65) -> should ABSTAIN_UNCERTAINTY
    resp_abstain = client.get("/api/economics/decision-value?risk_probability=0.55&confidence=0.50")
    assert resp_abstain.status_code == 200
    data_abstain = resp_abstain.json()

    assert data_abstain["actionable_recommendation"] == "ABSTAIN_UNCERTAINTY"
    assert "below 65% safety gate" in data_abstain["justification"]


def test_demo_economic_impact_includes_copq_breakdown(client_with_container):
    """Verify GET /api/demo/economic-impact includes the granular parametric CoPQ breakdown."""
    client, _ = client_with_container

    resp = client.get("/api/demo/economic-impact?part_cost=450.0")
    assert resp.status_code == 200
    data = resp.json()

    assert "copq_breakdown" in data
    assert data["copq_breakdown"] is not None
    assert data["copq_breakdown"]["material_cost_per_defect"] > 0.0
    assert data["copq_breakdown"]["machine_burden_per_defect"] > 0.0
    assert data["copq_breakdown"]["sorting_cost_per_defect"] == 22.0
