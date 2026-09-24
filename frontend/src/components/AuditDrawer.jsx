import React, { useState } from 'react';
import './AuditDrawer.css';

export function AuditDrawer({
  driftData = null,
  riskData = null,
  recommendationData = null,
  recoveryData = null,
  containmentData = null,
}) {
  const [isOpen, setIsOpen] = useState(false);

  const suspectStart = containmentData?.suspect_start_cycle ?? 420;
  const currentCycle = driftData?.current_cycle ?? 441;
  const lastGood = containmentData?.last_known_good_cycle ?? 418;
  const riskPct = riskData?.risk_percentage ?? 95.0;
  const recAction = recommendationData?.action ?? 'Decrease barrel temp zone 3 by -3.0 °C (A1)';

  // 10 Immutable Closed-Loop Evidence Chain Steps (TRST-01)
  const auditEvents = [
    {
      step: 1,
      type: 'SIGNAL CHANGE',
      pillClass: 'pill--violet',
      dotClass: 'audit-event__dot--violet',
      cycle: suspectStart,
      desc: 'Thermocouple Zone 3 departed baseline normal envelope (220.0 °C nominal → 234.5 °C observed).',
    },
    {
      step: 2,
      type: 'DRIFT EVIDENCE',
      pillClass: 'pill--violet',
      dotClass: 'audit-event__dot--violet',
      cycle: suspectStart + 2,
      desc: 'Multi-detector statistical departure confirmed (EWMA +2.8σ, CUSUM accumulation threshold crossed).',
    },
    {
      step: 3,
      type: 'RISK ESTIMATE',
      pillClass: 'pill--wine',
      dotClass: 'audit-event__dot--wine',
      cycle: suspectStart + 4,
      desc: `Calibrated XGBoost classifier projected defect risk escalation to ${riskPct.toFixed(1)}% (96% model confidence).`,
    },
    {
      step: 4,
      type: 'CAUSE EVIDENCE',
      pillClass: 'pill--violet',
      dotClass: 'audit-event__dot--violet',
      cycle: suspectStart + 5,
      desc: 'Physical attribution engine isolated Barrel Temperature Zone 3 as primary root cause (58.1% relative attribution).',
    },
    {
      step: 5,
      type: 'CANDIDATE ACTIONS',
      pillClass: 'pill--mist',
      dotClass: 'audit-event__dot--mist',
      cycle: suspectStart + 6,
      desc: 'Surrogate response surface optimizer evaluated 4 constrained corrective candidates (A1: Temp, A2: Pressure, A3: Cycle Time, A4: Purge).',
    },
    {
      step: 6,
      type: 'SELECTED ACTION',
      pillClass: 'pill--wine',
      dotClass: 'audit-event__dot--wine',
      cycle: suspectStart + 7,
      desc: `Recommended minimum effective intervention: ${recAction} (Cost score 0.15, Disruption 0.10, Feasible).`,
    },
    {
      step: 7,
      type: 'EXPECTED OUTCOME',
      pillClass: 'pill--mist',
      dotClass: 'audit-event__dot--mist',
      cycle: suspectStart + 7,
      desc: 'Predicted defect risk reduction from 95.0% to 41.1% within 3 cooling stabilization cycles.',
    },
    {
      step: 8,
      type: 'OBSERVED OUTCOME',
      pillClass: 'pill--lagoon',
      dotClass: 'audit-event__dot--lagoon',
      cycle: currentCycle - 2,
      desc: 'Physical sensor confirmed thermocouple drop of -2.8 °C. Defect risk declined to 25.3%, stability restored to 71.0%.',
    },
    {
      step: 9,
      type: 'RECOVERY DECISION',
      pillClass: 'pill--lagoon',
      dotClass: 'audit-event__dot--lagoon',
      cycle: currentCycle,
      desc: 'Closed-loop recovery verified across 3 consecutive stable cycles. Production gate released.',
    },
    {
      step: 10,
      type: 'PRODUCTION DISPOSITION',
      pillClass: 'pill--lagoon',
      dotClass: 'audit-event__dot--lagoon',
      cycle: currentCycle,
      desc: `Scrap containment locked: Suspect cycles #${suspectStart} to #${currentCycle} quarantined for CMM inspection. Cycles before #${lastGood} and after #${currentCycle} released.`,
    },
  ];

  const handleExport = (e) => {
    e.stopPropagation();
    const payload = {
      export_timestamp: new Date().toISOString(),
      machine_id: 'IMM-01',
      mold_id: 'MOLD-HOUSING-04',
      part_id: 'PART-AUTO-HOUSING-A',
      scenario: 'THERMAL_DRIFT',
      evidence_chain: auditEvents,
      summary: {
        last_known_good_cycle: lastGood,
        suspect_start_cycle: suspectStart,
        current_cycle: currentCycle,
        quarantined_cycle_count: currentCycle - suspectStart + 1,
        status: 'VERIFIED_RELEASED',
      },
    };

    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `process_guardian_audit_trail_cycle_${currentCycle}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="audit-drawer-container">
      {/* Trigger & Header Bar */}
      <div
        className="audit-drawer__trigger-bar"
        onClick={() => setIsOpen((prev) => !prev)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') setIsOpen((prev) => !prev); }}
      >
        <div className="audit-trigger-left">
          <span className="label-section" style={{ margin: 0 }}>
            CLOSED-LOOP AUDIT TRAIL — IMMUTABLE EVIDENCE CHAIN (TRST-01, TRST-02)
          </span>
          <span className="audit-trigger-subtext">
            10 Decision Events Recorded for Cycle #{currentCycle}
          </span>
        </div>

        <div className="audit-trigger-right">
          <button
            type="button"
            id="btn-export-audit-log"
            className="audit-export-btn"
            onClick={handleExport}
            title="Download audit evidence trail as JSON"
          >
            <span>📥 Export JSON</span>
          </button>

          <button
            type="button"
            id="btn-view-evidence-chain"
            className="audit-drawer__trigger-btn"
            onClick={(e) => {
              e.stopPropagation();
              setIsOpen((prev) => !prev);
            }}
            aria-expanded={isOpen}
          >
            <span>{isOpen ? '▲ Hide Evidence Chain' : '▼ View Evidence Chain (10-Event Audit Trail)'}</span>
          </button>
        </div>
      </div>

      {/* Expandable Timeline Content Tray */}
      <div className={`audit-drawer__tray ${isOpen ? 'audit-drawer__tray--open' : ''}`}>
        <div className="audit-drawer__content">
          <div className="audit-timeline">
            {auditEvents.map((ev) => (
              <div key={ev.step} className="audit-event">
                <span className={`audit-event__dot ${ev.dotClass}`} />
                <div className="audit-event__top">
                  <span className={`pill ${ev.pillClass}`}>{ev.type}</span>
                  <span className="audit-event__step-num num">Step #{ev.step} · Cycle #{ev.cycle}</span>
                </div>
                <div className="audit-event__desc">
                  {ev.desc}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default AuditDrawer;
