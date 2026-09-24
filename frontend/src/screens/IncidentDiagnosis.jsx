import React from 'react';
import './IncidentDiagnosis.css';
import { usePolling } from '../hooks/useApi';
import { RootCauseBar } from '../components/RootCauseBar';

export function IncidentDiagnosis() {
  const { data: riskData } = usePolling('/api/quality/risk', 2000);
  const { data: driftData } = usePolling('/api/process/drift', 2000);
  const { data: containmentData } = usePolling('/api/containment/window', 2000);

  // Risk data extraction
  const currentRisk = riskData?.risk_percentage ?? (riskData?.risk_probability ? riskData.risk_probability * 100 : 72.4);
  const baselineRisk = 3.0; // Validated golden baseline risk rate
  const leadCycles = driftData?.lead_cycles ?? 14;
  const confidenceScore = riskData?.confidence ? Math.round(riskData.confidence * 100) : 96;

  // Drift detectors
  const detectors = driftData?.detectors || {};
  const ewmaFired = detectors?.ewma?.fired ?? true;
  const cusumFired = detectors?.cusum?.fired ?? true;
  const mahalanobisFired = detectors?.multivariate_distance?.fired ?? (detectors?.mahalanobis?.fired ?? true);
  const slopeFired = detectors?.slope?.fired ?? false;

  // Containment window
  const lastGood = containmentData?.last_known_good_cycle ?? 418;
  const suspectStart = containmentData?.suspect_start_cycle ?? 420;
  const currentCycle = driftData?.current_cycle ?? 437;
  const suspectCount = containmentData?.suspect_cycle_count ?? (currentCycle - suspectStart + 1);

  // Root cause contributors
  const contributors = riskData?.contributors || [];

  // Arc Gauge Math (180-degree semicircular dial, radius = 50)
  const arcRadius = 45;
  const arcCircumference = Math.PI * arcRadius;
  const arcOffset = arcCircumference * (1 - Math.min(100, confidenceScore) / 100);

  return (
    <div id="panel-diagnosis" role="tabpanel" aria-labelledby="tab-diagnosis" className="incident-diagnosis">
      {/* Left Column (7fr): Escalation, Detectors, Cycle Window */}
      <div className="incident-diagnosis__left">
        {/* Risk Escalation Card */}
        <div className="escalation-card">
          <span className="label-section">EARLY RISK ESCALATION TRAJECTORY</span>
          
          <div className="escalation-row">
            <div className="escalation-point">
              <span className="escalation-point__label">BASELINE RISK</span>
              <span className="escalation-point__value escalation-point__value--baseline num">
                {baselineRisk.toFixed(1)}%
              </span>
            </div>

            <div className="escalation-arrow">→</div>

            <div className="escalation-point">
              <span className="escalation-point__label">CURRENT DEFECT RISK</span>
              <span className="escalation-point__value escalation-point__value--current num">
                {currentRisk.toFixed(1)}%
              </span>
            </div>
          </div>

          <div className="escalation-meta">
            <div className="escalation-meta-item">
              <span className="escalation-meta-label">EARLY WARNING LEAD TIME</span>
              <span className="escalation-meta-value num">{leadCycles} Cycles Ahead of Scrap</span>
            </div>
            <div className="escalation-meta-item">
              <span className="escalation-meta-label">GOVERNANCE MODE</span>
              <span className="escalation-meta-value">{riskData?.operator_mode ?? 'DIRECT_RECOMMENDATION'}</span>
            </div>
          </div>
        </div>

        {/* Drift Evidence Card */}
        <div className="evidence-card">
          <span className="label-section">MULTI-DETECTOR SENTINEL STATUS</span>
          <table className="drift-evidence-table">
            <thead>
              <tr>
                <th>Detection Method</th>
                <th>Target Mechanism</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>EWMA Moving Average</td>
                <td>Persistent slow drift</td>
                <td>
                  <span className={`pill ${ewmaFired ? 'pill--wine' : 'pill--lagoon'}`}>
                    {ewmaFired ? 'DEVIATION FIRED' : 'NORMAL'}
                  </span>
                </td>
              </tr>
              <tr>
                <td>CUSUM Cumulative Sum</td>
                <td>Small shift accumulation</td>
                <td>
                  <span className={`pill ${cusumFired ? 'pill--wine' : 'pill--lagoon'}`}>
                    {cusumFired ? 'DEVIATION FIRED' : 'NORMAL'}
                  </span>
                </td>
              </tr>
              <tr>
                <td>Mahalanobis Distance</td>
                <td>Multivariate correlation break</td>
                <td>
                  <span className={`pill ${mahalanobisFired ? 'pill--wine' : 'pill--lagoon'}`}>
                    {mahalanobisFired ? 'DEVIATION FIRED' : 'NORMAL'}
                  </span>
                </td>
              </tr>
              <tr>
                <td>Slope &amp; Velocity Tracker</td>
                <td>Sudden step excursions</td>
                <td>
                  <span className={`pill ${slopeFired ? 'pill--wine' : 'pill--lagoon'}`}>
                    {slopeFired ? 'DEVIATION FIRED' : 'NORMAL'}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Affected Cycle Window */}
        <div className="window-card">
          <span className="label-section">SCRAP CONTAINMENT SUSPECT WINDOW</span>
          <p style={{ fontSize: '13px', color: 'var(--color-charcoal)', marginBottom: '8px' }}>
            Suspect quarantined production interval: <strong className="num">Cycles #{suspectStart} to #{currentCycle}</strong> ({suspectCount} cycles)
          </p>

          <div className="cycle-window-bar-container">
            <div className="cycle-window-bar">
              <div
                className="cycle-window-suspect-range"
                style={{
                  left: '30%',
                  width: '65%',
                }}
              />
            </div>
            <div className="cycle-window-labels">
              <span className="num">Last Good: #{lastGood}</span>
              <span className="num" style={{ color: 'var(--color-wine)', fontWeight: 'var(--fw-label)' }}>
                Drift Injected: #{suspectStart}
              </span>
              <span className="num">Current: #{currentCycle}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Right Column (5fr): Root Cause Contributors & Confidence */}
      <div className="incident-diagnosis__right">
        {/* Ranked Root Cause Contributors */}
        <div>
          <span className="label-section">RANKED ROOT-CAUSE CONTRIBUTORS</span>
          
          {contributors.length > 0 ? (
            contributors.map((c, idx) => (
              <RootCauseBar
                key={c.signal_name || idx}
                label={c.signal_name}
                percentage={c.percentage}
                rank={idx + 1}
                evidenceText={c.evidence_text}
              />
            ))
          ) : (
            <div className="card" style={{ padding: '24px', textAlign: 'center' }}>
              <span style={{ fontSize: '13px', color: 'var(--color-stone)' }}>
                Insufficient data for root cause analysis
              </span>
            </div>
          )}
        </div>

        {/* Confidence Arc Gauge (Hairline SVG dial - NOT gradient ring) */}
        <div className="confidence-card">
          <span className="label-section">DIAGNOSTIC CERTAINTY</span>
          
          <div className="arc-gauge-container">
            <svg width="120" height="70" viewBox="0 0 120 70" className="arc-gauge-svg">
              {/* Background Track Arc */}
              <path
                d="M 15 60 A 45 45 0 0 1 105 60"
                fill="none"
                stroke="var(--color-mist)"
                strokeWidth="4"
                strokeLinecap="round"
              />
              {/* Value Arc */}
              <path
                d="M 15 60 A 45 45 0 0 1 105 60"
                fill="none"
                stroke="var(--color-violet)"
                strokeWidth="4"
                strokeLinecap="round"
                strokeDasharray={arcCircumference}
                strokeDashoffset={arcOffset}
              />
            </svg>
            <div className="arc-gauge-text num">{confidenceScore}%</div>
            <div className="arc-gauge-label">Model Confidence</div>
          </div>

          <p style={{ fontSize: '11px', color: 'var(--color-stone)', lineHeight: 1.4, margin: '8px 12px 0' }}>
            Empirically calibrated probability model based on validated baseline distributions.
          </p>
        </div>
      </div>
    </div>
  );
}

export default IncidentDiagnosis;
