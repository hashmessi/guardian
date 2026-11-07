import React from 'react';
import './RecommendationCard.css';

export function RecommendationCard({
  recommendation,
  isAbstain = false,
  isReady = false,
  onApply,
  isApplying = false,
  applied = false,
  applyError = null,
  netBenefit = null,
  costWait = null,
  costAct = null,
}) {
  const inr = (v) =>
    v == null ? '—' : `${v < 0 ? '-' : '+'}₹${Math.abs(v).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
  const rawAction = recommendation?.action || '';
  
  const formatActionTitle = (raw) => {
    if (!raw) return 'EVALUATING CONSTRAINED INTERVENTIONS...';
    return raw
      .replace(/barrel_temp_z3/gi, 'Zone 3 Temperature')
      .replace(/barrel_temp_z1/gi, 'Zone 1 Temperature')
      .replace(/barrel_temp_z2/gi, 'Zone 2 Temperature')
      .replace(/injection_pressure/gi, 'Injection Pressure')
      .replace(/hold_pressure/gi, 'Holding Pressure')
      .replace(/material_moisture/gi, 'Resin Moisture')
      .replace(/cooling_time/gi, 'Cooling Time')
      .toUpperCase();
  };

  const dominantAction = !isReady
    ? 'ASSESSING LIVE EVIDENCE'
    : isAbstain
    ? (recommendation?.abstain_reason ? `ABSTAIN — ${recommendation.abstain_reason.toUpperCase()}` : 'ABSTAIN — OPERATOR VERIFICATION REQUIRED')
    : formatActionTitle(rawAction);

  const why = !isReady
    ? 'No action is available until Process Guardian selects a verified candidate.'
    : recommendation?.why || 'Physical parameter deviation requires correction to restore quality contract safety margin.';
  const operatingLimit = !isReady
    ? 'Waiting for the current process state and operating limits.'
    : recommendation?.operating_limit || 'Parameter adjustment verified within calibrated safe operating envelope.';
  const expectedEffect = !isReady
    ? 'The action remains locked until the evidence is complete.'
    : recommendation?.expected_effect || 'Reduces projected defect risk and returns process parameters toward nominal baseline.';

  // Button state
  let btnClass = 'apply-btn--active';
  let btnLabel = 'CONFIRM OPERATOR ACTION';
  let btnDisabled = false;

  if (!isReady) {
    btnClass = 'apply-btn--disabled';
    btnLabel = 'WAITING FOR A VERIFIED RECOMMENDATION';
    btnDisabled = true;
  } else if (isAbstain) {
    btnClass = 'apply-btn--disabled';
    btnLabel = 'ABSTAIN — INTERVENTION BLOCKED BY SAFETY POLICY';
    btnDisabled = true;
  } else if (isApplying) {
    btnClass = 'apply-btn--applying';
    btnLabel = 'RECORDING ACTION…';
    btnDisabled = true;
  } else if (applied) {
    btnClass = 'apply-btn--done';
    btnLabel = 'ACTION RECORDED — CHECKING RECOVERY';
    btnDisabled = true;
  }

  return (
    <div className="recommendation-card">
      <div className="recommendation-header">
        <span className="label-section" style={{ margin: 0 }}>
          RECOMMENDED CORRECTIVE ACTION
        </span>
        <span className={`pill ${isAbstain ? 'pill--stone' : 'pill--wine'}`}>
          {isAbstain ? 'SAFETY ABSTAIN' : 'MINIMUM-EFFECTIVE SELECTION'}
        </span>
      </div>

      {/* Lock 10 & 11: Dominant Action Callout */}
      <div className="dominant-action-callout">
        <div className="dominant-action-title">{dominantAction}</div>
        <div className="dominant-action-subtext">
          {isAbstain
            ? 'Intervention locked by Process Guardian safety policy · Manual inspection required'
            : 'Advisory recommendation · Non-invasive supervisory guidance · Operator enters setpoint on machine PLC'}
        </div>
      </div>

      {/* 3 Physical & Operational Support Attributes + Reconciled Economics */}
      <div className="rec-attributes-grid">
        <div className="rec-attr-card">
          <span className="rec-attr-label">Why this action</span>
          <span className="rec-attr-value">{why}</span>
        </div>

        <div className="rec-attr-card">
          <span className="rec-attr-label">Safe operating limit</span>
          <span className="rec-attr-value">{operatingLimit}</span>
        </div>

        <div className="rec-attr-card">
          <span className="rec-attr-label">Expected modeled effect</span>
          <span className="rec-attr-value">{expectedEffect}</span>
        </div>

        {/* Lock 14: Dominant Economic Number */}
        <div className="rec-attr-card rec-attr-card--econ">
          <div className="rec-attr-label">
            <span>{netBenefit != null && netBenefit < 0 ? 'COST OF ACTING NOW' : 'NET BENEFIT OF ACTING'}</span>
            <span className="econ-modeled-pill">MODELED</span>
          </div>
          <div className="rec-econ-headline num">{inr(netBenefit)}</div>
          <div className="rec-econ-detail">
            {costWait != null && costAct != null
              ? `₹${costWait.toFixed(0)} projected scrap exposure vs ₹${costAct.toFixed(0)} to intervene`
              : 'Waiting for the engine to price this decision'}
          </div>
        </div>
      </div>

      {/* Dominant Action Button */}
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
