import React from 'react';
import './RecommendationCard.css';

export function RecommendationCard({
  recommendation,
  isAbstain = false,
  onApply,
  isApplying = false,
  applied = false,
  applyError = null,
}) {
  // 7 Contract Fields fallback defaults matching calibrated scenario
  const action = recommendation?.action || 'Decrease barrel temp zone 3 by -3.0 °C (A1)';
  const why = recommendation?.why || 'Thermal drift in zone 3 is the leading contributor to projected sink mark quality contract violation.';
  
  // Format evidence whether dict or string
  let evidenceStr = 'EWMA departure confirmed over 14 consecutive cycles with positive z-score excursion +2.8σ.';
  if (recommendation?.evidence) {
    if (typeof recommendation.evidence === 'string') {
      evidenceStr = recommendation.evidence;
    } else if (typeof recommendation.evidence === 'object') {
      evidenceStr = JSON.stringify(recommendation.evidence).replace(/["{}]/g, '').replace(/,/g, ', ');
    }
  }

  const expectedEffect = recommendation?.expected_effect || 'Reduces quality contract risk from 72.4% to 8.2% within 5 stabilization cycles.';
  const confidence = recommendation?.confidence ? `${(recommendation.confidence * 100).toFixed(0)}%` : '96%';
  const operatingLimit = recommendation?.operating_limit || 'Safe zone: 225.0 °C to 245.0 °C. Target 235.0 °C preserves 10.0 °C margin.';
  const recoveryCheck = recommendation?.recovery_check || 'Verify physical thermocouple drop ≥ 2.5 °C and 5 consecutive stable cycles.';

  // Determine button state
  let btnClass = 'apply-btn--active';
  let btnLabel = 'Apply Demo Intervention';
  let btnDisabled = false;

  if (isAbstain) {
    btnClass = 'apply-btn--disabled';
    btnLabel = 'ABSTAIN — Intervention Blocked';
    btnDisabled = true;
  } else if (isApplying) {
    btnClass = 'apply-btn--applying';
    btnLabel = 'Applying Corrective Action...';
    btnDisabled = true;
  } else if (applied) {
    btnClass = 'apply-btn--done';
    btnLabel = '✓ Intervention Applied — Monitoring Recovery';
    btnDisabled = true;
  }

  return (
    <div className="recommendation-card">
      <div className="recommendation-header">
        <span className="label-section" style={{ margin: 0 }}>
          RECOMMENDED MINIMUM-COST ACTION (7-FIELD CONTRACT)
        </span>
        <span className={`pill ${isAbstain ? 'pill--stone' : 'pill--wine'}`}>
          {isAbstain ? 'ABSTAIN MODE' : 'DIRECT RECOMMENDATION'}
        </span>
      </div>

      <div className="recommendation-fields">
        {/* Field 1: Action */}
        <div className="rec-field rec-field--full">
          <span className="rec-field__label">1. Recommended Action</span>
          <span className="rec-field__value" style={{ fontSize: '15px', color: 'var(--color-wine)', fontWeight: 'var(--fw-data)' }}>
            {action}
          </span>
        </div>

        {/* Field 2: Why */}
        <div className="rec-field">
          <span className="rec-field__label">2. Physical Justification (Why)</span>
          <span className="rec-field__value">{why}</span>
        </div>

        {/* Field 3: Evidence */}
        <div className="rec-field">
          <span className="rec-field__label">3. Diagnostic Evidence</span>
          <span className="rec-field__value">{evidenceStr}</span>
        </div>

        {/* Field 4: Expected Effect */}
        <div className="rec-field">
          <span className="rec-field__label">4. Modeled Outcome</span>
          <span className="rec-field__value">{expectedEffect}</span>
        </div>

        {/* Field 5: Model Confidence */}
        <div className="rec-field">
          <span className="rec-field__label">5. Decision Confidence</span>
          <span className="rec-field__value num"><strong>{confidence}</strong> (Calibrated surrogate envelope)</span>
        </div>

        {/* Field 6: Operating Limit */}
        <div className="rec-field">
          <span className="rec-field__label">6. Physical Constraint Boundary</span>
          <span className="rec-field__value">{operatingLimit}</span>
        </div>

        {/* Field 7: Recovery Check */}
        <div className="rec-field">
          <span className="rec-field__label">7. Verification Criteria</span>
          <span className="rec-field__value">{recoveryCheck}</span>
        </div>
      </div>

      {/* THE ONLY MIDNIGHT WINE (#421d24) FILLED BUTTON IN THE UI */}
      <button
        type="button"
        id="btn-apply-intervention"
        className={`apply-btn ${btnClass}`}
        disabled={btnDisabled}
        onClick={onApply}
      >
        {btnLabel}
      </button>

      {applyError && (
        <div className="apply-error" role="alert">
          {applyError}
        </div>
      )}
    </div>
  );
}

export default RecommendationCard;
