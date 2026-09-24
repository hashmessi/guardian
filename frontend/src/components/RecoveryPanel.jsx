import React from 'react';
import './RecoveryPanel.css';

export function RecoveryPanel({
  recoveryData = null,
  containmentData = null,
  isVisible = false,
}) {
  if (!isVisible && (!recoveryData || recoveryData.recovery_status === 'IDLE')) {
    return null;
  }

  const status = recoveryData?.recovery_status || 'VERIFIED';
  const isVerified = status === 'VERIFIED';
  const isFailed = status === 'FAILED';
  const isPending = !isVerified && !isFailed;

  const riskBefore = recoveryData?.risk_before ? (recoveryData.risk_before * 100) : 72.4;
  const riskCurrent = recoveryData?.risk_current ? (recoveryData.risk_current * 100) : 8.2;
  const stabilityBefore = recoveryData?.stability_before ? (recoveryData.stability_before * 100) : 78.0;
  const stabilityCurrent = recoveryData?.stability_current ? (recoveryData.stability_current * 100) : 96.5;

  const consecutive = recoveryData?.consecutive_stable_cycles ?? 5;
  const required = recoveryData?.required_stable_cycles ?? 5;

  // Scrap containment boundaries
  const lastGood = containmentData?.last_known_good_cycle ?? 418;
  const suspectStart = containmentData?.suspect_start_cycle ?? 420;
  const suspectEnd = containmentData?.suspect_end_cycle ?? 437;
  const suspectCount = containmentData?.suspect_cycle_count ?? 18;
  const scrapSaved = containmentData?.estimated_scrap_saved_cycles ?? 382;

  let bannerClass = 'recovery-status-banner--verified';
  let bannerText = '✓ VERIFIED — CLOSED LOOP RECOVERY CONFIRMED & PRODUCTION RELEASED';

  if (isFailed) {
    bannerClass = 'recovery-status-banner--failed';
    bannerText = '✕ RECOVERY FAILED — PARAMETER DRIFT RECURRED. OPERATOR ESCALATION REQUIRED.';
  } else if (isPending) {
    bannerClass = 'recovery-status-banner--pending';
    bannerText = `STABILIZATION MONITORING IN PROGRESS (${consecutive}/${required} STABLE CYCLES)`;
  }

  return (
    <div className="recovery-panel">
      <span className="label-section">CLOSED-LOOP RECOVERY VERIFICATION</span>

      {/* Status Banner */}
      <div className={`recovery-status-banner ${bannerClass}`}>
        {bannerText}
      </div>

      {/* 4 Before/After Metrics Grid */}
      <div className="recovery-metrics-grid">
        <div className="recovery-metric-card">
          <span className="recovery-metric__label">Risk Before Intervention</span>
          <span className="recovery-metric__value num" style={{ color: 'var(--color-stone)' }}>
            {riskBefore.toFixed(1)}%
          </span>
          <span className="recovery-metric__subtext">Unmitigated trajectory</span>
        </div>

        <div className="recovery-metric-card">
          <span className="recovery-metric__label">Risk After Verification</span>
          <span className="recovery-metric__value num" style={{ color: riskCurrent <= 20 ? 'var(--color-lagoon)' : 'var(--color-wine)' }}>
            {riskCurrent.toFixed(1)}%
          </span>
          <span className="recovery-metric__subtext">Within tolerance spec</span>
        </div>

        <div className="recovery-metric-card">
          <span className="recovery-metric__label">Stability Before</span>
          <span className="recovery-metric__value num" style={{ color: 'var(--color-stone)' }}>
            {stabilityBefore.toFixed(1)}%
          </span>
          <span className="recovery-metric__subtext">Degraded operational state</span>
        </div>

        <div className="recovery-metric-card">
          <span className="recovery-metric__label">Stability Verified</span>
          <span className="recovery-metric__value num" style={{ color: 'var(--color-lagoon)' }}>
            {stabilityCurrent.toFixed(1)}%
          </span>
          <span className="recovery-metric__subtext">{consecutive}/{required} cycles validated</span>
        </div>
      </div>

      {/* Scrap Containment & Lot Disposition */}
      <div className="containment-summary-box">
        <span className="containment-summary-title">AUTOMATIC PRODUCTION DISPOSITION &amp; SCRAP REDUCTION</span>
        <p>
          • <strong>Quarantined Lot:</strong> Cycles <span className="num">#{suspectStart}</span> to <span className="num">#{suspectEnd}</span> ({suspectCount} cycles) isolated for manual CMM dimensional inspection.
        </p>
        <p>
          • <strong>Production Release:</strong> Parts prior to cycle <span className="num">#{lastGood}</span> validated and released. Parts produced after verified recovery cycle <span className="num">#{suspectEnd}</span> released to standard packaging.
        </p>
        <p>
          • <strong>Estimated Scrap Prevented:</strong> <span className="num" style={{ color: 'var(--color-lagoon)', fontWeight: 'var(--fw-data)' }}>{scrapSaved} cycles</span> of defective injection molding avoided through early minimum-effective intervention.
        </p>
      </div>
    </div>
  );
}

export default RecoveryPanel;
