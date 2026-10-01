"""Tests for Epistemic Evidence REST API Endpoints (EVID-03)."""

from fastapi.testclient import TestClient
import pytest
from process_guardian.api.app import create_app


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def test_get_epistemic_levels(client):
    """Verify 4-level epistemic evidence framework contract."""
    response = client.get("/api/evidence/levels")
    assert response.status_code == 200
    data = response.json()

    assert "Process Guardian 4-Level Epistemic Evidence Framework" in data["framework_name"]
    assert "honesty_contract" in data
    assert len(data["levels"]) == 4

    level_tags = [lvl["tag"] for lvl in data["levels"]]
    assert "LEVEL_1_CHALLENGE" in level_tags
    assert "LEVEL_2_EXTERNAL_MEASURED" in level_tags
    assert "LEVEL_3_SOFTWARE_INVARIANT" in level_tags
    assert "LEVEL_4_CONTROLLED_COUNTERFACTUAL" in level_tags


def test_get_external_benchmark_api(client):
    """Verify external benchmark endpoint returns 564 parts and correlations."""
    response = client.get("/api/evidence/external-benchmark")
    assert response.status_code == 200
    data = response.json()

    assert data["total_parts"] == 564
    assert data["material_distribution"]["PP"] == 282
    assert data["material_distribution"]["ABS"] == 282
    assert data["scrap_rate_pct"] > 0
    assert len(data["feature_correlations"]) >= 4

    flaw = data["machine_limits_flaw_analysis"]
    assert flaw["escaped_defects_percentage"] > 20.0
    assert flaw["guardian_multivariate_catch_rate"] > 90.0


def test_get_grounding_report_api(client):
    """Verify grounding report endpoint returns empirical case studies."""
    response = client.get("/api/evidence/grounding-report")
    assert response.status_code == 200
    data = response.json()

    assert data["overall_status"] == "GROUNDED_EMPIRICALLY"
    assert len(data["test_cases"]) == 3
    assert "non_linear_moisture_curve" in data
    assert data["conclusion_for_evaluators"] != ""
