import React, { useState } from 'react';
import './AuditDrawer.css';
import { usePolling } from '../hooks/useApi';

const STATE_TONE = {
  HEALTHY: 'pill--lagoon',
  DRIFT_SUSPECTED: 'pill--violet',
  DRIFT_CONFIRMED: 'pill--violet',
  QUALITY_RISK_HIGH: 'pill--wine',
  DIAGNOSING: 'pill--violet',
  INTERVENTION_EVALUATION: 'pill--violet',
  ABSTAIN: 'pill--stone',
  QC_REQUIRED: 'pill--wine',
  RECOMMEND: 'pill--wine',
  APPLIED: 'pill--wine',
  RECOVERY_CHECK: 'pill--violet',
  RELEASE: 'pill--lagoon',
  INTERVENTION_MEMORY: 'pill--mist',
};

/**
 * The decision trail, read back from the engine.
 *
 * Every row below is a state transition the state machine actually executed,
 * with the cycle it happened on and the reason it recorded at the time. This
 * component previously rendered a hand-written ten-step narrative with invented
 * readings (and credited a classifier the project does not use) -- which is the
 * one thing an audit trail must never do.
 */
export function AuditDrawer() {
  const [isOpen, setIsOpen] = useState(false);
  const { data, error } = usePolling('/api/process/audit-trail?limit=40', 3000);

  const entries = data?.entries ?? [];
  const total = data?.total ?? 0;

  const handleExport = () => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `process_guardian_audit_trail_${data.machine_id}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="audit-drawer-container">
      <div
        className="audit-drawer__trigger-bar"
        onClick={() => setIsOpen((prev) => !prev)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') setIsOpen((prev) => !prev); }}
        aria-expanded={isOpen}
      >
        <div className="audit-trigger-left">
          <span className="label-section" style={{ margin: 0 }}>Decision trail</span>
          <span className="audit-trigger-subtext">
            {error
              ? 'Engine not answering'
              : `${total} state transition${total === 1 ? '' : 's'} recorded`}
          </span>
        </div>

        <div className="audit-trigger-right">
          <button
            type="button"
            id="btn-export-audit-log"
            className="audit-export-btn"
            onClick={(e) => { e.stopPropagation(); handleExport(); }}
            disabled={entries.length === 0}
            title="Download the recorded transitions as JSON"
          >
            <span>Export JSON ↓</span>
          </button>

          <button
            type="button"
            id="btn-view-evidence-chain"
            className="audit-drawer__trigger-btn"
            onClick={(e) => { e.stopPropagation(); setIsOpen((prev) => !prev); }}
            aria-expanded={isOpen}
          >
            <span>{isOpen ? '▲ Hide' : '▼ View'}</span>
          </button>
        </div>
      </div>

      <div className={`audit-drawer__tray ${isOpen ? 'audit-drawer__tray--open' : ''}`}>
        <div className="audit-drawer__content">
          {entries.length === 0 ? (
            <p className="audit-empty">
              Nothing recorded yet. Transitions appear here as the engine makes them.
            </p>
          ) : (
            <div className="audit-timeline">
              {entries.map((ev) => (
                <div key={`${ev.step}-${ev.cycle_index}`} className="audit-event">
                  <span className="audit-event__dot audit-event__dot--violet" />
                  <div className="audit-event__top">
                    <span className={`pill ${STATE_TONE[ev.to_state] ?? 'pill--mist'}`}>{ev.to_state}</span>
                    <span className="audit-event__step-num num">
                      #{ev.step} · Cycle {ev.cycle_index} · {ev.from_state} → {ev.to_state}
                    </span>
                  </div>
                  <div className="audit-event__desc">{ev.reason}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default AuditDrawer;
