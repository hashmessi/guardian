"""Schemas for Quality Risk models and inference outputs."""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class RiskState(str, Enum):
    """Categorical risk classification state (QRSK-04)."""
    LOW = "LOW"           # P < 0.35: Safe baseline operation
    MEDIUM = "MEDIUM"     # 0.35 <= P <= 0.70: Risk watch state / QC sample requested
    HIGH = "HIGH"         # P > 0.70: Active quality contract risk / intervention needed


class OperatorMode(str, Enum):
    """Factory operator guidance mode mapped from risk state and confidence (RCMD-02)."""
    NORMAL_MONITORING = "NORMAL_MONITORING"     # Low risk: maintain operation
    REQUEST_QC_SAMPLE = "REQUEST_QC_SAMPLE"     # Medium risk or low confidence: sample part
    INTERVENE_RECOMMENDED = "INTERVENE_RECOMMENDED" # High risk + high confidence: act
    ABSTAIN_AND_MONITOR = "ABSTAIN_AND_MONITOR" # High risk + low confidence: abstain


class QualityRiskOutput(BaseModel):
    """Comprehensive output of the calibrated quality risk model (QRSK-01..04)."""
    cycle_index: int = Field(..., description="Cycle index evaluated")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")
    
    risk_probability: float = Field(..., ge=0.0, le=1.0, description="Calibrated defect probability P(Defect)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model prediction confidence score")
    risk_state: RiskState = Field(..., description="Categorical risk tier: LOW, MEDIUM, HIGH")
    operator_mode: OperatorMode = Field(..., description="Actionable operator decision mode")
    
    contract_compliant: bool = Field(..., description="True if all Quality Contract tolerances met")
    contract_violations: List[str] = Field(default_factory=list, description="List of specific violated tolerances")
    
    feature_contributions: Dict[str, float] = Field(
        default_factory=dict,
        description="Raw feature attribution values from tree model"
    )
