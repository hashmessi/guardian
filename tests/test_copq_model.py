"""Tests for Parametric Cost of Poor Quality (CoPQ) Engine (ECON-01)."""

import pytest
from pydantic import ValidationError
from process_guardian.economics.models import CoPQParameters, CoPQBreakdown
from process_guardian.economics.engine import CoPQCalculator


def test_copq_default_parameters_calculation():
    """Verify default automotive injection molding CoPQ breakdown matches expected physics and accounting math."""
    calculator = CoPQCalculator()
    breakdown = calculator.calculate_breakdown()

    assert isinstance(breakdown, CoPQBreakdown)
    # Check components exist and are positive
    assert breakdown.material_cost_per_defect > 0.0
    assert breakdown.machine_burden_per_defect > 0.0
    assert breakdown.energy_cost_per_defect > 0.0
    assert breakdown.sorting_cost_per_defect == 22.0
    assert breakdown.oem_penalty_risk == 150.0

    # Verify direct scrap CoPQ is exact sum of components
    expected_direct = round(
        breakdown.material_cost_per_defect
        + breakdown.machine_burden_per_defect
        + breakdown.energy_cost_per_defect
        + breakdown.sorting_cost_per_defect,
        2,
    )
    assert breakdown.direct_scrap_copq_per_defect == expected_direct

    # Verify total CoPQ is direct + OEM penalty
    expected_total = round(expected_direct + breakdown.oem_penalty_risk, 2)
    assert breakdown.total_copq_per_defect == expected_total
    assert breakdown.currency == "INR (₹)"


def test_copq_parameter_overrides_pa66():
    """Verify calculation with engineering polymer PA66-GF30 (higher resin cost, higher machine tonnage)."""
    calculator = CoPQCalculator()
    pa66_params = CoPQParameters(
        resin_type="PA66-GF30 Glass-Filled Polyamide",
        resin_price_per_kg=380.0,
        part_weight_grams=350.0,
        runner_scrap_fraction=0.12,
        regrind_recovery_credit=0.10,  # lower regrind allowance on glass-filled
        machine_hourly_rate=2400.0,
        cycle_time_seconds=32.0,
        machine_power_kw=28.0,
        electricity_tariff_per_kwh=10.50,
        sorting_cost_per_part=35.0,
        oem_penalty_risk_per_defect=250.0,
    )

    breakdown = calculator.calculate_breakdown(pa66_params)

    # Material: 0.350 * 1.12 = 0.392 kg * 380 * 0.90 = 134.064 -> 134.06
    assert breakdown.material_cost_per_defect == 134.06
    # Machine burden: (2400 / 3600) * 32 = 21.33
    assert breakdown.machine_burden_per_defect == 21.33
    # Energy: 28 * (32 / 3600) * 10.5 = 2.6133 -> 2.61
    assert breakdown.energy_cost_per_defect == 2.61
    # Sorting: 35.0
    assert breakdown.sorting_cost_per_defect == 35.0
    # Direct: 134.06 + 21.33 + 2.61 + 35.0 = 193.00
    assert breakdown.direct_scrap_copq_per_defect == 193.00
    # Total: 193.00 + 250.0 = 443.00
    assert breakdown.total_copq_per_defect == 443.00


def test_copq_zero_sorting_and_recovery():
    """Verify edge case with zero sorting labor and zero regrind recovery credit."""
    calculator = CoPQCalculator()
    params = CoPQParameters(
        resin_price_per_kg=150.0,
        part_weight_grams=100.0,
        runner_scrap_fraction=0.0,
        regrind_recovery_credit=0.0,
        machine_hourly_rate=1200.0,
        cycle_time_seconds=18.0,
        machine_power_kw=12.0,
        electricity_tariff_per_kwh=9.0,
        sorting_cost_per_part=0.0,
        oem_penalty_risk_per_defect=0.0,
    )

    breakdown = calculator.calculate_breakdown(params)
    assert breakdown.material_cost_per_defect == 15.00
    assert breakdown.machine_burden_per_defect == 6.00
    assert breakdown.energy_cost_per_defect == 0.54
    assert breakdown.sorting_cost_per_defect == 0.0
    assert breakdown.direct_scrap_copq_per_defect == 21.54
    assert breakdown.total_copq_per_defect == 21.54


def test_copq_validation_bounds():
    """Verify Pydantic enforces bounds on negative or implausible inputs."""
    with pytest.raises(ValidationError):
        CoPQParameters(resin_price_per_kg=-50.0)

    with pytest.raises(ValidationError):
        CoPQParameters(part_weight_grams=0.0)

    with pytest.raises(ValidationError):
        CoPQParameters(runner_scrap_fraction=1.5)  # must be <= 1.0
