import React from 'react';
import './RootCauseBar.css';

export function RootCauseBar({
  label,
  percentage,
  rank = 1,
  evidenceText = null,
  zScore = null,
}) {
  const isTop = rank === 1;
  const numPercent = Math.max(0, Math.min(100, Number(percentage) || 0));
  const cleanLabel = (label || 'Signal').replace(/_/g, ' ');

  return (
    <div className={`root-cause-row ${isTop ? 'root-cause-row--top' : ''}`}>
      <div className="root-cause-row__left">
        <span className={`root-cause-row__rank ${isTop ? 'root-cause-row__rank--top' : ''}`}>
          {rank}
        </span>
        <div className="root-cause-row__info">
          <span className="root-cause-row__label">{cleanLabel}</span>
          {isTop && evidenceText && (
            <span className="root-cause-row__evidence">{evidenceText}</span>
          )}
        </div>
      </div>

      <div className="root-cause-row__right">
        <div className="root-cause-row__bar-wrapper">
          <div className="root-cause-row__track">
            <div
              className={`root-cause-row__fill ${isTop ? 'root-cause-row__fill--top' : ''}`}
              style={{ width: `${numPercent}%` }}
            />
          </div>
          <span className={`root-cause-row__percentage num ${isTop ? 'root-cause-row__percentage--top' : ''}`}>
            {numPercent.toFixed(1)}%
          </span>
        </div>
      </div>
    </div>
  );
}

export default RootCauseBar;
