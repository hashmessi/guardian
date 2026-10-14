"""Unit tests for PS02 Shop-Floor Operational Checkpoints Engine (QCHK-02)."""

import pytest
from process_guardian.quality.operational_checkpoints import (
    OperationalCheckpointsEvaluator,
    R12_RECIPE_SPECS,
)
from process_guardian.llm.human_channel import BoundedChoice


def test_nominal_all_operational_checkpoints_cleared():
    """Verify nominal machine parameters, dry resin, and recent spray clear all gates."""
    evaluator = OperationalCheckpointsEvaluator()
    evaluator.record_spray(cycle_index=50, operator_id="OP-104")
    evaluator.update_moisture_signoff(moisture_pct=0.08, inspector_id="QC-101")

    nominal_params = {
        "zone_1_temp": 235.0,
        "zone_2_temp": 240.0,
        "zone_3_temp": 245.0,
        "zone_4_temp": 250.0,
        "holding_pressure": 75.0,
        "injection_speed": 45.0,
        "cooling_time": 14.0,
    }

    report = evaluator.evaluate_all(current_cycle=70, active_params=nominal_params)

    assert report.overall_clearance is True
    assert report.clearance_status == "CLEARED"
    assert len(report.blocking_reasons) == 0
    assert report.recipe_verification.status == "PASS"
    assert report.recipe_verification.is_locked is False
    assert report.resin_moisture.status == "PASS"
    assert report.resin_moisture.status_label == "DRYING_SPEC_SATISFIED"
    assert report.mold_release_spray.status == "PASS"
    assert report.mold_release_spray.cycles_since_spray == 20


def test_recipe_lock_triggers_on_parameter_deviation():
    """Verify unauthorized recipe deviation blocks clearance and flags parameter."""
    evaluator = OperationalCheckpointsEvaluator()
    
    # Deviate Zone 1 temp (nominal 235 +/- 5 -> min 230, max 240) and holding pressure (75 +/- 8 -> max 83)
    deviated_params = {
        "zone_1_temp": 243.5,  # Too high (+8.5C from nominal)
        "zone_2_temp": 240.0,
        "zone_3_temp": 245.0,
        "zone_4_temp": 250.0,
        "holding_pressure": 85.0,  # Too high (+10 bar from nominal)
        "injection_speed": 45.0,
        "cooling_time": 14.0,
    }

    report = evaluator.evaluate_all(current_cycle=70, active_params=deviated_params)

    assert report.overall_clearance is False
    assert report.clearance_status == "GATED"
    assert report.recipe_verification.status == "FAIL"
    assert report.recipe_verification.is_locked is True
    assert len(report.recipe_verification.parameter_deviations) == 2
    assert any("Zone 1 Temp" in d for d in report.recipe_verification.parameter_deviations)
    assert any("Holding Pressure" in d for d in report.recipe_verification.parameter_deviations)
    assert any("Recipe Lock R-12 violation" in r for r in report.blocking_reasons)


def test_resin_moisture_gate_blocks_wet_material():
    """Verify moisture > 0.15% triggers BLOCKED_DRYING_REQUIRED."""
    evaluator = OperationalCheckpointsEvaluator()
    evaluator.update_moisture_signoff(moisture_pct=0.22, inspector_id="QC-102")

    nominal_params = {
        "zone_1_temp": 235.0,
        "zone_2_temp": 240.0,
        "zone_3_temp": 245.0,
        "zone_4_temp": 250.0,
        "holding_pressure": 75.0,
        "injection_speed": 45.0,
        "cooling_time": 14.0,
    }

    report = evaluator.evaluate_all(current_cycle=50, active_params=nominal_params)

    assert report.overall_clearance is False
    assert report.resin_moisture.status == "FAIL"
    assert report.resin_moisture.status_label == "BLOCKED_DRYING_REQUIRED"
    assert any("Resin Moisture Gate: 0.22% exceeds 0.15% limit" in r for r in report.blocking_reasons)


def test_mold_spray_interval_stages():
    """Verify spray interval triggers PASS, WARNING, and FAIL stages."""
    evaluator = OperationalCheckpointsEvaluator()
    evaluator.record_spray(cycle_index=100, operator_id="OP-201")

    # Within 50 cycles: PASS
    s1 = evaluator.evaluate_mold_spray(current_cycle=140)
    assert s1.status == "PASS"
    assert s1.status_label == "SPRAY_SCHEDULE_NORMAL"
    assert s1.cycles_since_spray == 40

    # Between 51 and 60 cycles: WARNING (due soon)
    s2 = evaluator.evaluate_mold_spray(current_cycle=155)
    assert s2.status == "WARNING"
    assert s2.status_label == "SPRAY_DUE_SOON"
    assert s2.cycles_since_spray == 55

    # Greater than 60 cycles: FAIL (overdue)
    s3 = evaluator.evaluate_mold_spray(current_cycle=165)
    assert s3.status == "FAIL"
    assert s3.status_label == "SPRAY_OVERDUE_APPLY_NOW"
    assert s3.cycles_since_spray == 65

    # Spraying resets cycle counter
    evaluator.record_spray(cycle_index=165, operator_id="OP-202")
    s4 = evaluator.evaluate_mold_spray(current_cycle=166)
    assert s4.status == "PASS"
    assert s4.cycles_since_spray == 1
    assert s4.last_operator_id == "OP-202"


def test_spray_confirmed_via_text_records_the_same_as_structured_endpoint():
    """P0 (scope_plan.md Sec.3): a bounded multilingual confirmation drives the same
    checkpoint as the structured /checkpoints/spray form."""
    evaluator = OperationalCheckpointsEvaluator()
    evaluator.record_spray(cycle_index=100, operator_id="OP-201")
    assert evaluator.evaluate_mold_spray(current_cycle=165).status == "FAIL"

    status, signal = evaluator.record_spray_from_text("haan spray kar diya", cycle_index=165)

    assert signal.choice == BoundedChoice.YES
    assert status.status == "PASS"
    assert status.cycles_since_spray == 0
    assert status.last_operator_id == "HUMAN-CHANNEL"


def test_spray_text_confirmation_with_low_confidence_does_not_mutate_state():
    """SAFE-03: an unclear signal must not silently reset the spray counter."""
    evaluator = OperationalCheckpointsEvaluator()
    evaluator.record_spray(cycle_index=100, operator_id="OP-201")

    status, signal = evaluator.record_spray_from_text("the machine sounds fine", cycle_index=165)

    assert signal.choice == BoundedChoice.UNKNOWN
    assert status.status == "FAIL"
    assert status.last_operator_id == "OP-201"


def test_spray_text_confirmation_negative_does_not_mutate_state():
    evaluator = OperationalCheckpointsEvaluator()
    evaluator.record_spray(cycle_index=100, operator_id="OP-201")

    status, signal = evaluator.record_spray_from_text("nahi, abhi nahi kiya", cycle_index=165)

    assert signal.choice == BoundedChoice.NO
    assert status.status == "FAIL"
    assert status.last_operator_id == "OP-201"


def test_moisture_attestation_from_text_never_overrides_the_measured_reading():
    """Corroborating evidence only -- evaluate_moisture() stays the authority
    (scope_plan.md Sec.6 rule 1)."""
    evaluator = OperationalCheckpointsEvaluator()
    evaluator.update_moisture_signoff(moisture_pct=0.22, inspector_id="QC-102")

    signal = evaluator.attest_moisture_signoff_from_text("haan, QC ne sign kar diya")

    assert signal.choice == BoundedChoice.YES
    # The sensor reading is still what decides -- an operator's "yes" cannot clear a
    # moisture gate the sensor says is failing.
    assert evaluator.evaluate_moisture().status == "FAIL"


def test_recipe_attestation_from_text_never_overrides_the_measured_parameters():
    evaluator = OperationalCheckpointsEvaluator()
    deviated_params = {"zone_1_temp": 243.5, "zone_2_temp": 240.0, "zone_3_temp": 245.0,
                        "zone_4_temp": 250.0, "holding_pressure": 85.0, "injection_speed": 45.0,
                        "cooling_time": 14.0}

    signal = evaluator.attest_recipe_setpoint_from_text("yes matches")

    assert signal.choice == BoundedChoice.YES
    assert evaluator.evaluate_recipe(deviated_params).status == "FAIL"
