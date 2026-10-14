"""
Phase 8: Safety Invariants & Hardening Audit (SAFE-01 .. SAFE-04, DEMO-03)
========================================================================
Comprehensive automated audit verifying that Process Guardian strictly satisfies
all safety interlocks, envelope boundaries, mandatory ABSTAIN policies, and epistemic
honesty requirements.
"""

import re
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from process_guardian.api.app import app
from process_guardian.intervention.schemas import ActionType, CandidateAction
from process_guardian.intervention.candidates import ConstraintChecker
from process_guardian.intervention.recommendation import RecommendationEngine, BANNED_DOGMATIC_WORDS
from process_guardian.fingerprint.builder import FingerprintBuilder
from process_guardian.adapter.pipeline import TelemetryPipeline
from process_guardian.simulator.engine import InjectionMoldingSimulator
from process_guardian.simulator.regimes import RegimeType
from process_guardian.quality.schemas import QualityRiskOutput, RiskState, OperatorMode
from process_guardian.validation.scenarios import validate_scenario_9_unseen_drift


# ---------------------------------------------------------------------------
# SAFE-01: Read-Only Machine Integration / Zero Automatic PLC Write-Back
# ---------------------------------------------------------------------------

def test_safe_01_codebase_zero_plc_writeback_hooks():
    """Verify via static code analysis that no PLC write-back sockets, Modbus write

    calls, or snap7 / OPC-UA write clients exist in the codebase.
    """
    src_dir = Path(__file__).resolve().parent.parent / "src" / "process_guardian"
    assert src_dir.exists(), f"Source directory {src_dir} must exist"

    # Forbidden network/hardware write patterns that would violate read-only constraint
    forbidden_patterns = [
        re.compile(r"pymodbus.*write", re.IGNORECASE),
        re.compile(r"snap7.*db_write", re.IGNORECASE),
        re.compile(r"socket\.sendall", re.IGNORECASE),
        re.compile(r"socket\.sendto", re.IGNORECASE),
        re.compile(r"opcua.*set_value", re.IGNORECASE),
        re.compile(r"write_register", re.IGNORECASE),
        re.compile(r"write_coil", re.IGNORECASE),
        re.compile(r"plc_write", re.IGNORECASE),
    ]

    violations = []
    for py_file in src_dir.rglob("*.py"):
        code = py_file.read_text(encoding="utf-8", errors="ignore")
        for pattern in forbidden_patterns:
            matches = pattern.findall(code)
            if matches:
                violations.append((py_file.name, matches))

    assert len(violations) == 0, f"Found forbidden PLC write-back hooks: {violations}"


def test_safe_01_intervention_is_read_only_and_advisory():
    """Verify that applying an intervention only updates simulation/audit records

    and operates purely as an advisory state change without hardware network writes.
    """
    client = TestClient(app)
    # Seed baseline and apply demo action
    client.post("/api/demo/reset", json={"machine_id": "IMM-01", "seed_baseline": True, "baseline_cycles": 20})
    
    resp = client.post("/api/interventions/apply-demo", json={
        "machine_id": "IMM-01",
        "action_id": "A1",
        "applied_by": "DEMO_OPERATOR"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "APPLIED"
    assert data["action_id"] == "A1"
    # No scenario simulator was selected in this test, so no recovery cycles were
    # stepped -- the message must say so (hostile-review MEDIUM #4: it previously
    # claimed "3 consecutive stabilization cycles verified" unconditionally).
    assert "A1 applied" in data["message"]
    assert "not stepped" in data["message"]

    # Verify intervention history recorded application immutably with operator attribution
    hist_resp = client.get("/api/interventions/history?machine_id=IMM-01")
    assert hist_resp.status_code == 200
    hist_data = hist_resp.json()
    assert len(hist_data["applications"]) >= 1
    assert hist_data["applications"][-1]["applied_by"] == "DEMO_OPERATOR"
    assert hist_data["applications"][-1]["action_id"] == "A1"

    # Verify audit log recorded event immutably
    from process_guardian.api.dependencies import get_service_container
    container = get_service_container()
    audit_logs = container.repository.list_audit_logs(machine_id="IMM-01", limit=20)
    assert any("DEMO_OPERATOR" in log.description for log in audit_logs)



# ---------------------------------------------------------------------------
# SAFE-02: Strict Boundary Limits & 5-Layer Operating Envelope
# ---------------------------------------------------------------------------

def test_safe_02_strict_operating_limits_rejection():
    """Verify that candidate adjustments exceeding machine limits or envelope

    bounds are strictly marked non-feasible with explicit violation reasons.
    """
    pipeline = TelemetryPipeline()
    sim = InjectionMoldingSimulator(seed=42, base_regime=RegimeType.HEALTHY)
    records = [pipeline.process(sim.step()) for _ in range(60)]
    builder = FingerprintBuilder()
    fp = builder.fit(records)
    current_record = records[-1]
    checker = ConstraintChecker()

    # 1. Candidate exceeding machine safety max limit (e.g. delta +50°C pushing barrel temp > 285°C)
    dangerous_candidate = CandidateAction(
        action_id="A_DANGEROUS",
        action_type=ActionType.TEMP_ADJUST,
        name="Dangerous Overheat",
        target_signal="barrel_temp_z3",
        delta_value=50.0,
        unit="°C",
    )
    val = checker.check_constraints(dangerous_candidate, current_record, fp)
    assert not val.is_feasible, "Dangerous action must not be feasible"
    assert not val.safety_ok, "Machine safety limit must fail"
    assert any("Safety Limit" in v for v in val.violations)

    # 2. Candidate exceeding recipe limits
    recipe_violating_candidate = CandidateAction(
        action_id="A_OVERPRESSURE",
        action_type=ActionType.PRESSURE_ADJUST,
        name="Excessive Pressure",
        target_signal="hold_pressure",
        delta_value=40.0,
        unit="MPa",
    )
    val2 = checker.check_constraints(recipe_violating_candidate, current_record, fp)
    assert not val2.is_feasible
    assert not val2.recipe_ok
    assert any("Recipe Limit" in v for v in val2.violations)


# ---------------------------------------------------------------------------
# SAFE-03: Mandatory ABSTAIN Policy on Low Confidence or Unseen Drift
# ---------------------------------------------------------------------------

def test_safe_03_mandatory_abstain_on_low_confidence():
    """Verify that when epistemic confidence is low (< 0.65) or drift is out-of-envelope,

    the recommendation contract mandates ABSTAIN_AND_MONITOR without forcing action.
    """
    from process_guardian.quality.model import QualityRiskModel
    from process_guardian.intervention.surrogate import InterventionSurrogateModel
    from process_guardian.intervention.optimizer import InterventionOptimizer

    pipeline = TelemetryPipeline()
    sim = InjectionMoldingSimulator(seed=42, base_regime=RegimeType.HEALTHY)
    records = [pipeline.process(sim.step()) for _ in range(60)]
    builder = FingerprintBuilder()
    fp = builder.fit(records)
    drift_record = records[-1]

    risk_model = QualityRiskModel(fingerprint=fp)
    surrogate = InterventionSurrogateModel(quality_risk_model=risk_model)
    optimizer = InterventionOptimizer(surrogate_model=surrogate)
    recommender = RecommendationEngine(min_confidence_threshold=0.65)

    low_conf_out = QualityRiskOutput(
        cycle_index=10,
        timestamp=drift_record.timestamp,
        risk_probability=0.92,
        confidence=0.52,  # Low epistemic confidence below 0.65
        risk_state=RiskState.HIGH,
        operator_mode=OperatorMode.ABSTAIN_AND_MONITOR,
        contract_compliant=False,
    )

    table = optimizer.evaluate_candidates(record=drift_record, fingerprint=fp)
    rec = recommender.generate_recommendation(
        record=drift_record,
        fingerprint=fp,
        comparison_table=table,
        risk_output=low_conf_out,
    )

    assert rec.is_abstain is True
    assert rec.operator_mode == "ABSTAIN_AND_MONITOR"
    assert rec.action == "ABSTAIN_AND_MONITOR"
    assert rec.abstain_reason is not None
    assert "Low epistemic confidence" in rec.abstain_reason


def test_safe_03_scenario_9_unseen_drift_abstains():
    """Verify Scenario 9 from the 10-scenario validation suite: severe unseen drift

    triggers the mandatory ABSTAIN gate in practice.
    """
    result = validate_scenario_9_unseen_drift()
    assert result.passed is True
    assert result.metrics["abstain_triggered"] is True
    assert result.metrics["unvalidated_action_prevented"] is True


# ---------------------------------------------------------------------------
# SAFE-04 & DEMO-03: Simulation Only & Epistemic Honesty Labels
# ---------------------------------------------------------------------------

def test_safe_04_and_demo_03_honest_epistemic_disclaimers():
    """Verify that all economic and operational endpoints clearly label metrics

    as modeled/prototype values, state clear assumptions, and use non-dogmatic language.
    """
    client = TestClient(app)
    
    # 1. Verify Economic Impact endpoint has strict modeled label and assumptions
    resp = client.get("/api/demo/economic-impact?part_cost=450.0&machine_id=IMM-01")
    assert resp.status_code == 200
    econ = resp.json()
    assert econ["assumptions_label"] == "Modeled Avoided Scrap Value"
    assert econ["disclaimer"] == "SIMULATION · PROTOTYPE RESULTS ONLY"
    assert econ["is_prototype"] is True
    assert econ["part_cost"] == 450.0

    # 2. Verify Recommendation endpoint uses calibrated and evidence-based framing
    rec_resp = client.get("/api/interventions/recommendation?machine_id=IMM-01")
    assert rec_resp.status_code == 200
    rec = rec_resp.json()
    assert "confidence" in rec

    # 3. Verify banned dogmatic words are never used in recommendations
    for word in BANNED_DOGMATIC_WORDS:
        assert word not in rec.get("why", "").lower()
        assert word not in rec.get("action", "").lower()

