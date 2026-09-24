import React from 'react';
import './SignalGauge.css';

export function SignalGauge({
  label,
  value,
  unit,
  min,
  max,
  envelopeMin,
  envelopeMax,
  isDrifting = false,
}) {
  const numVal = typeof value === 'number' ? value : parseFloat(value) || min;

  // Calculate percentages along the scale
  const range = max - min || 1;
  const envLeft = Math.max(0, Math.min(100, ((envelopeMin - min) / range) * 100));
  const envWidth = Math.max(0, Math.min(100 - envLeft, ((envelopeMax - envelopeMin) / range) * 100));
  const markerPos = Math.max(0, Math.min(100, ((numVal - min) / range) * 100));

  return (
    <div className="gauge-container">
      <div className="gauge-header">
        <span className="gauge-label">{label}</span>
        <div className="gauge-header-right">
          <span className="gauge-value num">
            {numVal.toFixed(unit === '%' ? 2 : 1)}
            <span className="gauge-unit">{unit}</span>
          </span>
          <span className={`pill ${isDrifting ? 'pill--wine' : 'pill--lagoon'}`}>
            {isDrifting ? 'DEVIATION' : 'NORMAL'}
          </span>
        </div>
      </div>

      <div className="gauge-track">
        {/* Shaded Normal Operating Envelope */}
        <div
          className="gauge-envelope"
          style={{
            left: `${envLeft}%`,
            width: `${envWidth}%`,
          }}
          title={`Normal Envelope: ${envelopeMin} - ${envelopeMax} ${unit}`}
        />

        {/* Current State Marker */}
        <div
          className={`gauge-marker ${isDrifting ? 'gauge-marker--drift' : 'gauge-marker--normal'}`}
          style={{ left: `${markerPos}%` }}
          title={`Current: ${numVal} ${unit}`}
        />
      </div>

      <div className="gauge-footer">
        <span className="envelope-spec num">{min} {unit}</span>
        <span className="envelope-spec num">
          Envelope: {envelopeMin} – {envelopeMax} {unit}
        </span>
        <span className="envelope-spec num">{max} {unit}</span>
      </div>
    </div>
  );
}

export default SignalGauge;
