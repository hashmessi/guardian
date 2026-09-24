# Phase 3: Quality Risk + Root-Cause Evidence — Context

## Objective
Build the **Calibrated Quality Risk Predictor** and **Root-Cause Evidence Engine** for Process Guardian (Phase 3). This connects early drift detection from Phase 2 into quantified Quality Contract violation probabilities and actionable, honestly phrased contributor evidence for factory engineers and operators.

## Target Requirements
- **QRSK-01**: System produces calibrated quality risk probability (0-1) with confidence score using XGBoost/LightGBM.
- **QRSK-02**: System uses temporal feature engineering (current value, rolling mean/std, trend/slope, delta from fingerprint, lag features, interaction features, process-phase features, material moisture, machine context).
- **QRSK-03**: System evaluates risk against a defined Quality Contract (part-specific targets and tolerances).
- **QRSK-04**: System classifies risk state (LOW / MEDIUM / HIGH) with corresponding operator modes.
- **ROOT-01**: System provides ranked likely contributors with percentage contribution (e.g., Temperature 68%, Pressure 21%, Cycle 8%, Other 3%) summing to 100%.
- **ROOT-02**: System provides supporting evidence for each contributor (variance changes, distribution shifts, similar past events).
- **ROOT-03**: System uses honest language: "likely contributor", "evidence", "modeled effect", "confidence" — never "guaranteed cause" or "proven causal effect".

## System Boundary & Data Flow
1. **Inputs**:
   - `NormalizedCycleRecord` from `TelemetryPipeline` (Phase 1).
   - `ProcessFingerprint` from `FingerprintStore` (Phase 2).
   - `DriftOutput` from `DriftSentinel` (Phase 2).
2. **Transformations**:
   - `FeatureExtractor`: Transforms streaming cycle records + fingerprint into a rich 45+ dimension tabular feature vector.
   - `QualityRiskModel`: Calibrated classifier (Gradient Boosting / Platt scaled) predicting $P(\text{Defect} \mid \mathbf{x}_t)$.
   - `QualityContractEvaluator`: Compares predicted and current process parameters against engineering tolerances.
   - `RootCauseAnalyzer`: Tree SHAP / gradient feature attribution + empirical distribution divergence breakdown normalized to 100%.
3. **Outputs**:
   - `QualityRiskOutput`: Risk score $[0.0, 1.0]$, confidence score $[0.0, 1.0]$, risk state (`LOW`, `MEDIUM`, `HIGH`), contract status details.
   - `RootCauseReport`: Ranked contributor list with percentage contributions, evidence snippets, and honest epistemics.
