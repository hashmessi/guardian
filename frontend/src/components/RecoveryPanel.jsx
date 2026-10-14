import React from 'react';
import './RecoveryPanel.css';

const pct = (v) => (v != null ? `${(v * 100).toFixed(1)}%` : '—');

export function RecoveryPanel({
  recoveryData = null,
  isVisible = false,
}) {
  if (!isVisible && (!recoveryData || recoveryData.recovery_status === 'IDLE')) {
    return null;
  }

  // No fabricated default: before any recovery data arrives this is PENDING, not VERIFIED.
  const status = recoveryData?.recovery_status ?? 'PENDING';
  const isFailed = status === 'FAILED';
  const isVerified = status === 'VERIFIED';

  const consecutive = recoveryData?.consecutive_stable_cycles;
  const required = recoveryData?.required_stable_cycles;
  const cycleProgress = consecutive != null && required != null ? `${consecutive}/${required}` : '—';

  let bannerClass = 'recovery-status-banner--pending';
  let bannerText = `Stabilization monitoring — ${cycleProgress} consecutive stable cycles`;

  if (isFailed) {
    bannerClass = 'recovery-status-banner--failed';
    bannerText = 'Recovery failed — parameter drift recurred. Operator escalation required.';
  } else if (isVerified) {
    bannerClass = 'recovery-status-banner--verified';
    bannerText = `Recovery verified — ${cycleProgress} consecutive stable cycles within envelope`;
  }

  return (
    <div className="recovery-panel">
      <span className="label-section">Recovery verification</span>

      <div className={`recovery-status-banner ${bannerClass}`}>
        <span>{bannerText}</span>
      </div>

      <div className="recovery-metrics-grid">
        <div className="recovery-metric-card">
          <span className="recovery-metric__label">Defect risk before</span>
          <span className="recovery-metric__value num" style={{ color: 'var(--color-stone)' }}>
            {pct(recoveryData?.risk_before)}
          </span>
          <span className="recovery-metric__subtext">At intervention</span>
        </div>

        <div className="recovery-metric-card">
          <span className="recovery-metric__label">Defect risk now</span>
          <span className="recovery-metric__value num" style={{ color: isVerified ? 'var(--color-lagoon)' : 'var(--color-stone)' }}>
            {pct(recoveryData?.risk_current)}
          </span>
          <span className="recovery-metric__subtext">{cycleProgress} stable cycles</span>
        </div>
      </div>
    </div>
  );
}

export default RecoveryPanel;
