# Phase 03 Plan 02: Calibrated Quality Risk Predictor Summary

## Overview
Implemented the **Calibrated Quality Risk Model** using gradient boosted trees with Platt scaling probability calibration to output well-calibrated defect risk probabilities $P(\text{Defect}) \in [0.0, 1.0]$, confidence scoring, categorical risk states, and operator guidance modes (QRSK-01, QRSK-04).

## Key Deliverables Completed
1. **Schemas (`src/process_guardian/quality/schemas.py`)**:
   - `RiskState`: `LOW` ($P < 0.35$), `MEDIUM` ($0.35 \le P \le 0.70$), `HIGH` ($P > 0.70$).
   - `OperatorMode`: `NORMAL_MONITORING`, `REQUEST_QC_SAMPLE`, `INTERVENE_RECOMMENDED`, `ABSTAIN_AND_MONITOR`.
   - `QualityRiskOutput`: Calibrated probability, confidence score, risk tier, operator mode, contract violations, and feature contributions.
2. **Quality Risk Model (`src/process_guardian/quality/model.py`)**:
   - `QualityRiskModel`: Gradient boosting classifier calibrated via `CalibratedClassifierCV(method='sigmoid', cv=3)`.
   - Pre-trained on multi-regime simulation history (healthy baseline, thermal runaway, pressure loss, moisture ingress, sensor noise).
   - Confidence scoring derived from prediction decisiveness ($|P - 0.5|$) and feature manifold density penalties.
   - Enforces `ABSTAIN_AND_MONITOR` when confidence is below actionable threshold ($< 0.65$) under high risk (RCMD-03).
3. **Unit Verification (`tests/test_quality_risk.py`)**:
   - 2/2 tests green:
     - `test_calibrated_risk_probabilities`
     - `test_risk_state_classification_and_escalation`
