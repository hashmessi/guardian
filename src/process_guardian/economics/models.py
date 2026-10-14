"""Pydantic schemas and domain models for Process Guardian Decision Economics and Parametric CoPQ (ECON-01, ECON-02)."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class EconomicActionDecision(str, Enum):
    """Actionable recommendation resulting from economic evaluation."""
    INTERVENE_NOW = "INTERVENE_NOW"
    MONITOR_AND_WAIT = "MONITOR_AND_WAIT"
    CRITICAL_QUALITY_LOCK = "CRITICAL_QUALITY_LOCK"
    ABSTAIN_UNCERTAINTY = "ABSTAIN_UNCERTAINTY"


class CoPQParameters(BaseModel):
    """
    Parametric inputs for Cost of Poor Quality (CoPQ) calculation.
    
    Defaults reflect calibrated Tier-2/Tier-3 automotive injection molding plants
    in Indian automotive clusters (Pune, Chennai, NCR) producing structural components.
    """
    resin_type: str = Field(default="PP / ABS Automotive Grade", description="Polymer material specification")
    resin_price_per_kg: float = Field(default=195.0, ge=10.0, le=2000.0, description="Raw resin cost in INR/kg")
    part_weight_grams: float = Field(default=220.0, ge=1.0, le=10000.0, description="Net molded part shot weight in grams")
    runner_scrap_fraction: float = Field(default=0.08, ge=0.0, le=1.0, description="Cold runner/sprue scrap weight fraction (0.08 = 8%)")
    regrind_recovery_credit: float = Field(default=0.25, ge=0.0, le=1.0, description="Recycled regrind value credit (0.25 = 25% material recovery)")
    machine_hourly_rate: float = Field(default=1650.0, ge=100.0, le=20000.0, description="Machine burden rate in INR/hr (depreciation, labor, floor space)")
    cycle_time_seconds: float = Field(default=24.0, ge=1.0, le=600.0, description="Nominal cycle time in seconds")
    machine_power_kw: float = Field(default=18.5, ge=1.0, le=200.0, description="Average active machine power consumption in kW")
    electricity_tariff_per_kwh: float = Field(default=9.80, ge=1.0, le=50.0, description="Industrial electricity tariff in INR/kWh")
    sorting_cost_per_part: float = Field(default=22.0, ge=0.0, le=500.0, description="Secondary inspection / sorting labor cost per suspect part in INR")
    oem_penalty_risk_per_defect: float = Field(default=150.0, ge=0.0, le=5000.0, description="OEM warranty / assembly line stoppage risk penalty per defect in INR")


class CoPQBreakdown(BaseModel):
    """Itemized breakdown of Cost of Poor Quality per defective part."""
    material_cost_per_defect: float = Field(..., description="Direct resin and runner scrap cost in INR")
    machine_burden_per_defect: float = Field(..., description="Wasted machine hour burden cost in INR")
    energy_cost_per_defect: float = Field(..., description="Wasted energy electricity cost in INR")
    sorting_cost_per_defect: float = Field(..., description="Secondary containment sorting cost in INR")
    direct_scrap_copq_per_defect: float = Field(..., description="Direct manufacturing scrap cost (material + machine + energy + sorting)")
    oem_penalty_risk: float = Field(..., description="Downstream warranty and assembly penalty exposure risk")
    total_copq_per_defect: float = Field(..., description="Total comprehensive CoPQ per defective part in INR")
    currency: str = Field(default="INR (₹)", description="Currency designation")


class DecisionValueBreakdown(BaseModel):
    """
    Real-time economic evaluation comparing Cost of Waiting vs Cost of Acting.
    
    Decision Value = ExpectedLoss_wait - Cost_act
    If Decision Value > threshold: INTERVENE_NOW (cost of waiting exceeds disruption cost).
    If Decision Value <= threshold: MONITOR_AND_WAIT (disturbing machine costs more than waiting).
    """
    current_cycle: int = Field(..., description="Current operational cycle index")
    current_risk_probability: float = Field(..., description="Model-predicted probability of producing defective part [0, 1]")
    copq_per_defect: float = Field(..., description="Applicable unit CoPQ in INR")
    expected_drift_horizon_cycles: int = Field(default=20, description="Lookahead horizon in cycles if left uncorrected")
    expected_scrap_cycles_if_waiting: float = Field(..., description="Cumulative expected defective parts produced over horizon")
    expected_quarantine_sorting_cycles: int = Field(..., description="Total cycles entering suspect lot quarantine requiring 100% sorting")
    expected_scrap_cost: float = Field(..., description="Expected scrap loss over horizon in INR")
    expected_sorting_cost: float = Field(..., description="Expected secondary containment sorting cost over horizon in INR")
    expected_loss_waiting: float = Field(..., description="Total expected economic loss if waiting (scrap + sorting) in INR")
    stabilization_cycles: int = Field(default=3, description="Cycles required for thermal/pressure stabilization post-intervention")
    stabilization_scrap_cost: float = Field(..., description="Direct cost of stabilization scrap cycles in INR")
    operator_tuning_overhead: float = Field(default=45.0, description="Operator overhead / line disruption cost in INR")
    cost_acting: float = Field(..., description="Total cost of taking corrective intervention right now in INR")
    decision_value: float = Field(..., description="Net signed decision value = ExpectedLoss_wait - Cost_act in INR")
    economic_threshold: float = Field(default=0.0, description="Economic intervention threshold in INR (default >= 0)")
    actionable_recommendation: EconomicActionDecision = Field(..., description="Actionable operational recommendation")
    avoided_loss_if_acting: float = Field(..., description="Modeled net financial savings if intervening now in INR")
    justification: str = Field(..., description="Auditable epistemic justification for the decision")
    epistemic_level: str = Field(default="Level 3: Software Invariant", description="Epistemic evidence level")
