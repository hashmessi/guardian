"""Calibrated Quality Risk Model using gradient boosted trees and probability calibration (QRSK-01..04)."""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV

from process_guardian.adapter.schemas import NormalizedCycleRecord
from process_guardian.fingerprint.models import ProcessFingerprint
from process_guardian.quality.contract import QualityContract
from process_guardian.quality.features import TemporalFeatureExtractor
from process_guardian.quality.schemas import QualityRiskOutput, RiskState, OperatorMode


class QualityRiskModel:
    """
    Predicts calibrated probability of Quality Contract violation per cycle.
    
    Combines tree-based non-linear feature interaction modeling with isotonic/sigmoid
    calibration to output mathematically calibrated risk probabilities (QRSK-01) and
    maps them into operational risk states and operator guidance modes (QRSK-04).
    """

    def __init__(self, fingerprint: ProcessFingerprint):
        self.fingerprint = fingerprint
        self.feature_extractor = TemporalFeatureExtractor(fingerprint)
        self.feature_names = self.feature_extractor.get_feature_names()
        
        self.base_model = GradientBoostingClassifier(
            n_estimators=60,
            learning_rate=0.08,
            max_depth=3,
            random_state=42,
        )
        self.calibrated_model: Optional[CalibratedClassifierCV] = None
        self.is_trained: bool = False
        self._train_default_baseline()

    def _train_default_baseline(self) -> None:
        """
        Train and calibrate on synthetic multi-regime factory baseline data.
        
        Ensures the model is immediately usable and fully deterministic out-of-the-box.
        """
        from process_guardian.simulator.engine import InjectionMoldingSimulator
        from process_guardian.simulator.regimes import RegimeType
        from process_guardian.adapter.pipeline import TelemetryPipeline

        pipeline = TelemetryPipeline()
        extractor = TemporalFeatureExtractor(self.fingerprint)

        X_train_list = []
        y_train_list = []

        # Generate representative dataset from diverse regimes
        regimes_to_sample = [
            (RegimeType.HEALTHY, 80),
            (RegimeType.SENSOR_NOISE, 40),
            (RegimeType.THERMAL_DRIFT, 40),
            (RegimeType.PRESSURE_DRIFT, 40),
            (RegimeType.MOISTURE_DRIFT, 40),
        ]

        for regime, n_cycles in regimes_to_sample:
            sim = InjectionMoldingSimulator(seed=100 + len(X_train_list), base_regime=regime)
            extractor.reset()
            for _ in range(n_cycles):
                raw = sim.step()
                rec = pipeline.process(raw)
                _, vec = extractor.extract_features(rec)
                X_train_list.append(vec)
                y_train_list.append(1 if rec.defect_flag else 0)

        X = np.array(X_train_list, dtype=np.float32)
        y = np.array(y_train_list, dtype=np.int32)

        # Fit calibrated classifier directly with 3-fold cross-validation
        self.calibrated_model = CalibratedClassifierCV(estimator=self.base_model, method="sigmoid", cv=3)
        self.calibrated_model.fit(X, y)
        self.base_model.fit(X, y)
        self.is_trained = True

    def predict(
        self,
        record: NormalizedCycleRecord,
        contract: Optional[QualityContract] = None,
    ) -> QualityRiskOutput:
        """
        Predict calibrated quality risk and operator mode for an incoming cycle.
        """
        contract = contract or QualityContract()
        feat_dict, vec = self.feature_extractor.extract_features(record)
        contract_res = contract.evaluate(record)

        # 1. Calibrated probability estimation
        if self.calibrated_model is not None:
            proba = float(self.calibrated_model.predict_proba(vec.reshape(1, -1))[0, 1])
        else:
            proba = float(self.base_model.predict_proba(vec.reshape(1, -1))[0, 1])

        # If direct quality contract defects exist on the physical part, fuse contract indicator
        if not contract_res.is_compliant:
            proba = max(proba, contract_res.defect_risk_indicator)

        # Clamp calibrated probability
        calibrated_risk = round(max(0.01, min(0.99, proba)), 3)

        # 2. Confidence estimation
        # Higher confidence when probability is decisive (near 0 or near 1) and features are within normal range
        decisiveness = 1.0 - 2.0 * abs(0.50 - calibrated_risk)  # 0 at extremes, 1 at 0.5
        max_z = max(abs(feat_dict.get(f"{sig}_z_fp", 0.0)) for sig in TemporalFeatureExtractor.CORE_SIGNALS)
        outlier_penalty = min(0.30, max(0.0, (max_z - 6.0) * 0.05))
        confidence = round(max(0.50, min(0.98, 0.95 - 0.35 * decisiveness - outlier_penalty)), 2)

        # 3. Risk state mapping (QRSK-04)
        if calibrated_risk < 0.35:
            risk_state = RiskState.LOW
        elif calibrated_risk <= 0.70:
            risk_state = RiskState.MEDIUM
        else:
            risk_state = RiskState.HIGH

        # 4. Operator mode mapping (RCMD-02, RCMD-03)
        if risk_state == RiskState.LOW:
            operator_mode = OperatorMode.NORMAL_MONITORING
        elif risk_state == RiskState.MEDIUM:
            operator_mode = OperatorMode.REQUEST_QC_SAMPLE
        else:
            # High risk
            if confidence >= 0.65:
                operator_mode = OperatorMode.INTERVENE_RECOMMENDED
            else:
                # ABSTAIN when confidence is low (RCMD-03)
                operator_mode = OperatorMode.ABSTAIN_AND_MONITOR

        # 5. Feature attribution
        importances = getattr(self.base_model, "feature_importances_", np.zeros(len(self.feature_names)))
        feature_contributions = {}
        for name, imp, val in zip(self.feature_names, importances, vec):
            if imp > 0.01:
                feature_contributions[name] = round(float(imp), 4)

        return QualityRiskOutput(
            cycle_index=record.cycle_index,
            timestamp=record.timestamp,
            risk_probability=calibrated_risk,
            confidence=confidence,
            risk_state=risk_state,
            operator_mode=operator_mode,
            contract_compliant=contract_res.is_compliant,
            contract_violations=contract_res.violations,
            feature_contributions=feature_contributions,
        )
