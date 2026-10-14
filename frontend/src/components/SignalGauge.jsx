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
  // An absent reading is not a reading at the bottom of the scale. The previous
  // `parseFloat(value) || min` turned a missing barrel temperature into a
  // confident "210.0 °C" sitting at the left edge of the gauge.
  const parsed = typeof value === 'number' ? value : parseFloat(value);
  const hasValue = Number.isFinite(parsed);
  const numVal = hasValue ? parsed : null;
  const hasEnvelope = Number.isFinite(envelopeMin) && Number.isFinite(envelopeMax);

  // Fingerprint envelopes arrive as raw floats. Printing them unrounded put
  // "228.4587 - 231.5273 °C" on the shop-floor gauge; round them the same way
  // the reading above is rounded.
  const decimals = unit === '%' ? 2 : 1;
  const fmt = (n) => (typeof n === 'number' ? n.toFixed(decimals) : n);

  // Calculate percentages along the scale
  const range = max - min || 1;
  const envLeft = hasEnvelope ? Math.max(0, Math.min(100, ((envelopeMin - min) / range) * 100)) : 0;
  const envWidth = hasEnvelope
    ? Math.max(0, Math.min(100 - envLeft, ((envelopeMax - envelopeMin) / range) * 100))
    : 0;
  const markerPos = hasValue ? Math.max(0, Math.min(100, ((numVal - min) / range) * 100)) : 0;

  return (
    <div className="gauge-container">
      <div className="gauge-header">
        <span className="gauge-label">{label}</span>
        <div className="gauge-header-right">
          <span className="gauge-value num">
            {hasValue ? numVal.toFixed(unit === '%' ? 2 : 1) : '—'}
            {hasValue && <span className="gauge-unit">{unit}</span>}
          </span>
          <span className={`pill ${!hasValue ? 'pill--mist' : isDrifting ? 'pill--wine' : 'pill--lagoon'}`}>
            {!hasValue ? 'NO DATA' : isDrifting ? 'DEVIATION' : 'NORMAL'}
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
          title={`Normal Envelope: ${fmt(envelopeMin)} - ${fmt(envelopeMax)} ${unit}`}
        />

        {/* Current State Marker -- omitted entirely when there is no reading */}
        {hasValue && (
          <div
            className={`gauge-marker ${isDrifting ? 'gauge-marker--drift' : 'gauge-marker--normal'}`}
            style={{ left: `${markerPos}%` }}
            title={`Current: ${fmt(numVal)} ${unit}`}
          />
        )}
      </div>

      <div className="gauge-footer">
        <span className="envelope-spec num">{min} {unit}</span>
        <span className="envelope-spec num">
          {hasEnvelope ? `Envelope: ${fmt(envelopeMin)} – ${fmt(envelopeMax)} ${unit}` : 'Envelope: —'}
        </span>
        <span className="envelope-spec num">{max} {unit}</span>
      </div>
    </div>
  );
}

export default SignalGauge;
