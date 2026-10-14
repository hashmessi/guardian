"""Integration tests for POST /api/checkpoints/human-channel (P0, scope_plan.md Sec.3)."""

import pytest
from fastapi.testclient import TestClient
from process_guardian.api.app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_spray_confirmation_applies_and_resets_counter(client):
    resp = client.post(
        "/api/checkpoints/human-channel",
        json={"question": "spray_done", "text": "haan spray kar diya", "cycle_index": 437},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["applied"] is True
    assert data["signal"]["choice"] == "yes"
    assert data["mold_release_spray"]["cycles_since_spray"] == 0


def test_spray_confirmation_requires_cycle_index(client):
    resp = client.post(
        "/api/checkpoints/human-channel",
        json={"question": "spray_done", "text": "yes"},
    )
    assert resp.status_code == 422


def test_unclear_spray_text_does_not_apply(client):
    resp = client.post(
        "/api/checkpoints/human-channel",
        json={"question": "spray_done", "text": "the machine sounds fine", "cycle_index": 437},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["applied"] is False
    assert data["signal"]["choice"] == "unknown"


def test_moisture_attestation_is_evidence_only(client):
    resp = client.post(
        "/api/checkpoints/human-channel",
        json={"question": "moisture_signed", "text": "haan sign ho gaya"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["applied"] is False
    assert data["mold_release_spray"] is None
    assert data["signal"]["choice"] == "yes"
    assert data["signal"]["source"] == "deterministic"


def test_recipe_attestation_is_evidence_only(client):
    resp = client.post(
        "/api/checkpoints/human-channel",
        json={"question": "recipe_matches", "text": "yes matches"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["applied"] is False
    assert data["signal"]["choice"] == "yes"
