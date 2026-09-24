import React from 'react';
import './RootCauseBar.css';

export function RootCauseBar({
  label,
  percentage,
  rank = 1,
  evidenceText = null,
}) {
  const isTop = rank === 1;
  const numPercent = Math.max(0, Math.min(100, Number(percentage) || 0));

  // Format label replacing underscores
  const cleanLabel = (label || 'Signal').replace(/_/g, ' ');

  return (
    <div className="root-cause-bar">
      <div className="root-cause-bar__header">
        <div className="root-cause-bar__label-group">
          <span className={`root-cause-bar__rank ${isTop ? 'root-cause-bar__rank--top' : ''}`}>
            {rank}
          </span>
          <span className="root-cause-bar__label">{cleanLabel}</span>
        </div>
        <span className={`root-cause-bar__percentage num ${isTop ? 'root-cause-bar__percentage--top' : ''}`}>
          {numPercent.toFixed(1)}%
        </span>
      </div>

      <div className="root-cause-bar__track">
        <div
          className={`root-cause-bar__fill ${isTop ? 'root-cause-bar__fill--top' : 'root-cause-bar__fill--secondary'}`}
          style={{ width: `${numPercent}%` }}
        />
      </div>

      {evidenceText && (
        <div className="root-cause-bar__evidence">
          <strong>Evidence:</strong> {evidenceText}
        </div>
      )}
    </div>
  );
}

export default RootCauseBar;
