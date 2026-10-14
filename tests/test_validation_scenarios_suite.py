"""Automated Pytest Suite for the 10-Scenario Validation Suite (DEMO-01, P1).

Asserts deterministic, correct behavioral responses for:
1. Healthy baseline (zero false alarms)
2. Thermal drift (complete closed decision loop)
3. Pressure drift (pressure-specific detection & attribution)
4. Moisture drift (hygroscopic moisture detection)
5. Sensor noise (noise robustness & filter stability)
6. Combined drift (multivariate detection & multi-signal attribution)
7. Sustained recovery (3-cycle cooling window verification)
8. Missing signal (sensor dropout resilience & graceful degradation)
9. Unseen drift (mandatory ABSTAIN safety gate under model uncertainty)
10. Sudden step shift (fast CUSUM detection & immediate scrap containment)
"""

import pytest
from process_guardian.validation.scenarios import (
    validate_scenario_1_healthy_baseline,
    validate_scenario_2_thermal_drift,
    validate_scenario_3_pressure_drift,
    validate_scenario_4_moisture_drift,
    validate_scenario_5_sensor_noise,
    validate_scenario_6_combined_drift,
    validate_scenario_7_sustained_recovery,
    validate_scenario_8_missing_signal,
    validate_scenario_9_unseen_drift,
    validate_scenario_10_sudden_step_shift,
)


def test_scenario_1_healthy_baseline():
    result = validate_scenario_1_healthy_baseline()
    assert result.passed is True, f"Scenario 1 Failed: {result.failure_reasons}"
    assert result.metrics["drift_alerts"] == 0
    assert result.metrics["interventions"] == 0


def test_scenario_2_thermal_drift():
    result = validate_scenario_2_thermal_drift()
    assert result.passed is True, f"Scenario 2 Failed: {result.failure_reasons}"
    assert result.metrics["lead_time_cycles"] >= 5
    assert result.metrics["release_cycle"] == 444


def test_scenario_3_pressure_drift():
    result = validate_scenario_3_pressure_drift()
    assert result.passed is True, f"Scenario 3 Failed: {result.failure_reasons}"
    assert result.metrics["drift_detected"] is True
    assert result.metrics["pressure_attributed"] is True


def test_scenario_4_moisture_drift():
    result = validate_scenario_4_moisture_drift()
    assert result.passed is True, f"Scenario 4 Failed: {result.failure_reasons}"
    assert result.metrics["moisture_drift_detected"] is True
    assert result.metrics["moisture_attributed"] is True


def test_scenario_5_sensor_noise():
    result = validate_scenario_5_sensor_noise()
    assert result.passed is True, f"Scenario 5 Failed: {result.failure_reasons}"
    assert result.metrics["false_interventions"] == 0


def test_scenario_6_combined_drift():
    result = validate_scenario_6_combined_drift()
    assert result.passed is True, f"Scenario 6 Failed: {result.failure_reasons}"
    assert result.metrics["multivariate_drift_detected"] is True
    assert result.metrics["temp_and_moisture_ranked"] is True


def test_scenario_7_sustained_recovery():
    result = validate_scenario_7_sustained_recovery()
    assert result.passed is True, f"Scenario 7 Failed: {result.failure_reasons}"
    assert result.metrics["release_verified"] is True


def test_scenario_8_missing_signal():
    result = validate_scenario_8_missing_signal()
    assert result.passed is True, f"Scenario 8 Failed: {result.failure_reasons}"
    assert result.metrics["missing_flags_logged"] >= 8
    assert result.metrics["crashes"] == 0


def test_scenario_9_unseen_drift():
    result = validate_scenario_9_unseen_drift()
    assert result.passed is True, f"Scenario 9 Failed: {result.failure_reasons}"
    assert result.metrics["abstain_triggered"] is True
    assert result.metrics["unvalidated_action_prevented"] is True


def test_scenario_10_sudden_step_shift():
    result = validate_scenario_10_sudden_step_shift()
    assert result.passed is True, f"Scenario 10 Failed: {result.failure_reasons}"
    assert result.metrics["fast_alert_cycle"] <= 37
    assert result.metrics["quarantine_activated"] is True
