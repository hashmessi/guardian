import React, { useState } from 'react';
import './OperationalCheckpointsModal.css';
import { usePolling, submitHumanChannelText, recordMoldSpray } from '../hooks/useApi';

/**
 * Bounded shop-floor text confirmation for one checkpoint gate (P0, scope_plan.md
 * Sec.3). Any language the deterministic/Laya parser recognizes -- "yes", "haan
 * spray kar diya", "not done" -- resolves to a typed, sourced, confidence-scored
 * signal, never a silent guess.
 */
function HumanChannelAttestation({ question, cycleIndex, placeholder, onApplied }) {
  const [text, setText] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!text.trim() || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = await submitHumanChannelText(question, text.trim(), cycleIndex);
      setResult(res);
      setText('');
      if (res.applied && onApplied) onApplied();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="hc-form" onSubmit={handleSubmit}>
      <label className="hc-form__label" htmlFor={`hc-input-${question}`}>
        Shop-floor confirmation, any language
      </label>
      <div className="hc-form__row">
        <input
          id={`hc-input-${question}`}
          type="text"
          className="hc-form__input"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={placeholder}
          disabled={submitting}
        />
        <button type="submit" className="hc-form__submit" disabled={submitting || !text.trim()}>
          {submitting ? '…' : 'Confirm'}
        </button>
      </div>
      {result && (
        <span className={`hc-form__result hc-form__result--${result.signal.choice}`}>
          {result.signal.choice === 'unknown'
            ? 'UNCLEAR — NO CHANGE MADE'
            : `${result.signal.choice.toUpperCase()} · ${Math.round(result.signal.confidence * 100)}% CONFIDENCE · ${result.signal.source === 'laya' ? 'LAYA' : 'RULE-BASED'}${result.applied ? '' : ' · EVIDENCE ONLY'}`}
        </span>
      )}
      {error && <span className="hc-form__error">{error}</span>}
    </form>
  );
}

export function OperationalCheckpointsModal({ isOpen, onClose }) {
  const { data: report, refresh } = usePolling('/api/checkpoints/operational', 3000);
  const [spraying, setSpraying] = useState(false);

  if (!isOpen) return null;

  // A safety gate with no data behind it must say so. These used to default to a
  // full set of passing values (inspector QC-101, moisture 0.08%, spray at C-400),
  // so the modal announced "all 3 gates cleared" while loading and when offline.
  if (!report) {
    return (
      <div className="op-modal-overlay" role="dialog" aria-modal="true">
        <div className="op-modal">
          <div className="op-modal__bar">
            <span>Shop-floor operational checkpoints</span>
            <button type="button" className="op-modal__close" onClick={onClose} aria-label="Close">×</button>
          </div>
          <p className="op-modal__empty">
            Gate status unavailable — the engine has not reported a processed cycle yet.
            Do not treat this as clearance.
          </p>
        </div>
      </div>
    );
  }

  const recipe = report.recipe_verification;
  const moisture = report.resin_moisture;
  const spray = report.mold_release_spray;
  const overallClearance = report.overall_clearance === true;
  const sprayProgressPct = Math.min(100, Math.round((spray.cycles_since_spray / spray.scheduled_interval_cycles) * 100));

  const handleApplySpray = async () => {
    setSpraying(true);
    try {
      await recordMoldSpray(spray.current_cycle);
    } catch (err) {
      console.error('Failed to record mold spray:', err);
    } finally {
      setSpraying(false);
    }
  };

  return (
    <div className="ockp-backdrop" onClick={onClose}>
      <div className="ockp-modal" onClick={(e) => e.stopPropagation()} role="dialog" aria-modal="true" aria-labelledby="ockp-heading">
        <div className="ockp-header">
          <div className="ockp-header__title-group">
            <span id="ockp-heading" className="ockp-header__title">SHOP-FLOOR OPERATIONAL CHECKPOINTS</span>
            <span className="pill pill--mist">POKA-YOKE GATES</span>
          </div>
          <button type="button" className="ockp-close" onClick={onClose} aria-label="Close">✕</button>
        </div>

        <div className={`ockp-clearance-banner ${overallClearance ? 'ockp-clearance-banner--cleared' : 'ockp-clearance-banner--gated'}`}>
          {overallClearance ? '✓ ALL 3 GATES CLEARED — LINE CAN PROCEED' : '🔒 LINE GATED — ACTION REQUIRED BEFORE RELEASE'}
        </div>

        <div className="ockp-body">
          {/* Gate 1: Recipe Verification Lock */}
          <section className={`ockp-gate ${recipe.is_locked ? 'ockp-gate--alert' : 'ockp-gate--pass'}`}>
            <header className="ockp-gate__header">
              <span className="ockp-gate__num">GATE 1</span>
              <h3 className="ockp-gate__title">Recipe Verification Lock</h3>
              <span className={`ockp-status-pill ${recipe.status === 'PASS' ? 'ockp-status-pill--pass' : 'ockp-status-pill--fail'}`}>
                {recipe.status === 'PASS' ? 'UNLOCKED' : 'LOCKED'}
              </span>
            </header>

            <div className="ockp-metric-strip">
              <div className="ockp-metric">
                <span className="ockp-metric__label">Target Recipe</span>
                <span className="ockp-metric__value num">{recipe.recipe_id}</span>
              </div>
              <div className="ockp-metric">
                <span className="ockp-metric__label">Parameters In Spec</span>
                <span className="ockp-metric__value num">
                  {recipe.parameter_deviations?.length === 0 ? '7 / 7' : `${recipe.parameter_deviations?.length} deviation(s)`}
                </span>
              </div>
            </div>

            {recipe.parameter_deviations?.length > 0 ? (
              <div className="ockp-deviation-list">
                {recipe.parameter_deviations.map((d, i) => (
                  <div key={i} className="ockp-deviation">⚠ {d}</div>
                ))}
              </div>
            ) : (
              <p className="ockp-nominal-text">
                Zone Temps (235–250°C), Holding P (75 bar), Injection (45mm/s), Cooling (14s) verified.
              </p>
            )}

            <HumanChannelAttestation
              question="recipe_matches"
              placeholder="Setpoint matches recipe R-12? (e.g. 'yes matches')"
            />

            <footer className="ockp-gate__footer">
              {recipe.is_locked ? 'Unauthorized override prevents cycle start' : 'Parameter limits locked to signed recipe'}
            </footer>
          </section>

          {/* Gate 2: Resin Moisture Batch Sign-off */}
          <section className={`ockp-gate ${moisture.status === 'FAIL' ? 'ockp-gate--alert' : 'ockp-gate--pass'}`}>
            <header className="ockp-gate__header">
              <span className="ockp-gate__num">GATE 2</span>
              <h3 className="ockp-gate__title">Resin Moisture Sign-Off</h3>
              <span className={`ockp-status-pill ${moisture.status === 'PASS' ? 'ockp-status-pill--pass' : 'ockp-status-pill--fail'}`}>
                {moisture.status}
              </span>
            </header>

            <div className="ockp-metric-strip">
              <div className="ockp-metric">
                <span className="ockp-metric__label">Batch ID</span>
                <span className="ockp-metric__value num">{moisture.batch_id}</span>
              </div>
              <div className="ockp-metric">
                <span className="ockp-metric__label">Hopper Moisture</span>
                <span
                  className="ockp-metric__value num"
                  style={{ color: moisture.moisture_pct > 0.15 ? 'var(--color-wine)' : 'var(--color-lagoon)' }}
                >
                  {moisture.moisture_pct.toFixed(2)}% <span className="ockp-metric__sub">(max 0.15%)</span>
                </span>
              </div>
              <div className="ockp-metric">
                <span className="ockp-metric__label">Inspector Sign-Off</span>
                <span className="ockp-metric__value num">{moisture.inspector_id}</span>
              </div>
            </div>

            <p className="ockp-nominal-text">
              Grounded in Fraunhofer/SKZ non-linear moisture threshold for PA66 hydrolytic degradation.
            </p>

            <HumanChannelAttestation
              question="moisture_signed"
              placeholder="Resin lot dried & signed? (e.g. 'haan sign ho gaya')"
            />

            <footer className="ockp-gate__footer">
              {moisture.status === 'PASS' ? 'Moisture drying spec certified' : 'BLOCKED: Hopper drying required'}
            </footer>
          </section>

          {/* Gate 3: Mold-Release Spray Interval */}
          <section className={`ockp-gate ${spray.status === 'FAIL' ? 'ockp-gate--alert' : spray.status === 'WARNING' ? 'ockp-gate--warn' : 'ockp-gate--pass'}`}>
            <header className="ockp-gate__header">
              <span className="ockp-gate__num">GATE 3</span>
              <h3 className="ockp-gate__title">Mold Spray Interval</h3>
              <span className={`ockp-status-pill ${spray.status === 'PASS' ? 'ockp-status-pill--pass' : 'ockp-status-pill--fail'}`}>
                {spray.status_label || spray.status}
              </span>
            </header>

            <div className="ockp-metric-strip">
              <div className="ockp-metric">
                <span className="ockp-metric__label">Cycles Since Spray</span>
                <span className="ockp-metric__value num">{spray.cycles_since_spray} / {spray.scheduled_interval_cycles}</span>
              </div>
              <div className="ockp-metric">
                <span className="ockp-metric__label">Last Spray</span>
                <span className="ockp-metric__value num">C-{spray.last_spray_cycle} ({spray.last_operator_id || 'OP-SYS'})</span>
              </div>
              <div className="ockp-metric">
                <span className="ockp-metric__label">Overdue Limit</span>
                <span className="ockp-metric__value num">{spray.overdue_limit_cycles}c</span>
              </div>
            </div>

            <div className="ockp-progress-track">
              <div
                className={`ockp-progress-fill ${spray.cycles_since_spray > 50 ? 'ockp-progress-fill--warn' : ''}`}
                style={{ width: `${sprayProgressPct}%` }}
              />
            </div>

            <button type="button" className="ockp-primary-btn" onClick={handleApplySpray} disabled={spraying}>
              {spraying ? 'RECORDING SPRAY…' : 'APPLY MOLD SPRAY NOW'}
            </button>

            <HumanChannelAttestation
              question="spray_done"
              cycleIndex={spray.current_cycle}
              placeholder="Or confirm by text, any language (e.g. 'spray kar diya')"
              onApplied={refresh}
            />

            <footer className="ockp-gate__footer">
              Scheduled every 50 cycles to avoid surface drag blemishes
            </footer>
          </section>
        </div>
      </div>
    </div>
  );
}

export default OperationalCheckpointsModal;
