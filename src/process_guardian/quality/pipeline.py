"""Unified Quality Engine orchestrating feature extraction, risk modeling, and root cause attribution."""

from typing import Optional, Tuple
from process_guardian.adapter.schemas import NormalizedCycleRecord
from process_guardian.fingerprint.models import ProcessFingerprint
from process_guardian.sentinel.schemas import DriftOutput
from process_guardian.quality.contract import QualityContract
from process_guardian.quality.model import QualityRiskModel
from process_guardian.quality.schemas import QualityRiskOutput
from process_guardian.root_cause.analyzer import RootCauseAnalyzer
from process_guardian.root_cause.schemas import RootCauseReport


class QualityEngine:
    """
    Unified end-to-end quality risk assessment and root-cause evidence engine.
    
    Orchestrates temporal feature extraction, calibrated tree risk prediction,
    contract tolerance evaluation, and 100%-normalized contributor attribution.
    """

    def __init__(
        self,
        fingerprint: ProcessFingerprint,
        contract: Optional[QualityContract] = None,
    ):
        self.fingerprint = fingerprint
        self.contract = contract or QualityContract()
        self.risk_model = QualityRiskModel(fingerprint=fingerprint)
        self.root_cause_analyzer = RootCauseAnalyzer()

    def evaluate_cycle(
        self,
        record: NormalizedCycleRecord,
        drift_output: Optional[DriftOutput] = None,
    ) -> Tuple[QualityRiskOutput, RootCauseReport]:
        """
        Evaluate an incoming cycle record end-to-end.
        
        Returns:
            Tuple of (QualityRiskOutput, RootCauseReport)
        """
        # 1. Predict calibrated risk and operator mode
        risk_output = self.risk_model.predict(record=record, contract=self.contract)

        # 2. Attribute root cause contributors
        root_cause_report = self.root_cause_analyzer.analyze(
            record=record,
            fingerprint=self.fingerprint,
            drift_output=drift_output,
            risk_output=risk_output,
        )

        return risk_output, root_cause_report
