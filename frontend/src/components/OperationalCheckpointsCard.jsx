import React from 'react';
import './OperationalCheckpointsCard.css';
import { usePolling } from '../hooks/useApi';

const GATES = [
  { key: 'recipe_verification', num: 1, label: 'Recipe Lock' },
  { key: 'resin_moisture', num: 2, label: 'Moisture' },
  { key: 'mold_release_spray', num: 3, label: 'Spray' },
];

/**
 * Compact, high-visibility trigger for the 3 PS02 shop-floor checkpoints
 * (QCHK-02). The full gate detail and human-channel confirmation forms live in
 * OperationalCheckpointsModal -- this bar exists so the gate state is always
 * visible without crowding the Act & Verify screen (user feedback: the old
 * 3-column inline card was congested and easy to miss).
 */
export function OperationalCheckpointsCard({ onOpenModal }) {
  const { data: report } = usePolling('/api/checkpoints/operational', 3000);

  // No data is not a pass. Defaulting these to true/PASS meant a safety gate
  // announced "clearance granted" while loading, while offline, and on a 404.
  const hasReport = report != null;
  const overallClearance = report?.overall_clearance === true;

  return (
    <button type="button" className="op-trigger-bar" onClick={onOpenModal} id="operational-checkpoints-card">
      <div className="op-trigger-left">
        <span className="label-section" style={{ margin: 0 }}>SHOP-FLOOR OPERATIONAL CHECKPOINTS</span>
        <span className="pill pill--mist">POKA-YOKE GATES</span>
      </div>

      <div className="op-trigger-chips">
        {GATES.map((gate) => {
          const status = report?.[gate.key]?.status;
          const isPass = status === 'PASS';
          const isWarn = status === 'WARNING';
          const mark = !hasReport ? '–' : isPass ? '✓' : isWarn ? '⚠' : '✕';
          return (
            <span
              key={gate.key}
              className={`op-bar-chip ${!hasReport ? 'op-bar-chip--unknown' : isPass ? 'op-bar-chip--pass' : isWarn ? 'op-bar-chip--warn' : 'op-bar-chip--fail'}`}
            >
              G{gate.num} {gate.label} {mark}
            </span>
          );
        })}
      </div>

      <div className={`op-clearance-pill ${overallClearance ? 'op-clearance-pill--cleared' : 'op-clearance-pill--gated'}`}>
        {!hasReport ? 'GATE STATUS UNKNOWN' : overallClearance ? '✓ CLEARANCE GRANTED' : '🔒 LINE GATED'}
      </div>

      <span className="op-trigger-cta">VIEW &amp; CONFIRM GATES →</span>
    </button>
  );
}
