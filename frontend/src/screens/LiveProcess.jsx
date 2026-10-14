import React from 'react';
import './LiveProcess.css';
import { usePolling } from '../hooks/useApi';
import { SignalGauge } from '../components/SignalGauge';
import { ProcessStateTimeline } from '../components/ProcessStateTimeline';

export function LiveProcess({ onProceed }) {
  const { data: processData } = usePolling('/api/process/current', 2000);
  const { data: driftData } = usePolling('/api/process/drift', 2000);
  const { data: contractData } = usePolling('/api/quality/contract', 5000);
  const { data: riskData } = usePolling('/api/quality/risk', 2000);
  const { data: fpData } = usePolling('/api/process/fingerprint', 5000);

  // Until the engine answers there is nothing to show. Rendering placeholder
  // readings under a "PRODUCTION SAFE" banner is the worst possible failure mode
  // for this screen: it looks exactly like a healthy line.
  if (!processData) {
    return (
      <div id="panel-detect" role="tabpanel" aria-labelledby="tab-detect" className="live-process">
        <div className="process-state-banner">
          <div className="process-state-banner__left">
            <div className="process-state-banner__title-row">
              <span className="process-state-banner__title">Waiting for the line…</span>
            </div>
            <div className="process-state-banner__subtext">
              No processed cycle yet. Pick a scenario on the front page to start the run.
            </div>
          </div>
        </div>
      </div>
    );
  }

  const signals = processData.signals || {};
  const currentState = processData.state;

  const barrelTemp = signals.barrel_temp_z3 ?? signals.barrel_temperature;
  const injPressure = signals.injection_pressure;
  const moisture = signals.material_moisture_pct ?? signals.material_moisture;
  const cycleTime = signals.cycle_time;
  const partWeight = signals.part_weight_g;

  // Envelopes from baseline fingerprint
  const envZ3 = fpData?.signal_envelopes?.barrel_temp_z3 || { lower: 228, upper: 236 };
  const envInj = fpData?.signal_envelopes?.injection_pressure || { lower: 98, upper: 122 };
  const envMoist = fpData?.signal_envelopes?.material_moisture || { lower: 0.01, upper: 0.15 };
  const envCycle = fpData?.signal_envelopes?.cycle_time || { lower: 25, upper: 31 };

  // Contributing signals from multi-detector sentinel
  const contributing = driftData?.contributing_signals || [];
  const isDriftActive = (driftData?.drift === true) || (currentState !== 'HEALTHY');

  const isTempDrifting = contributing.some((s) => s.includes('barrel') || s.includes('temp')) || barrelTemp > envZ3.upper || barrelTemp < envZ3.lower;
  const isPressureDrifting = contributing.some((s) => s.includes('pressure')) || injPressure > envInj.upper || injPressure < envInj.lower;
  const isMoistureDrifting = contributing.some((s) => s.includes('moisture')) || moisture > envMoist.upper;
  const isCycleTimeDrifting = contributing.some((s) => s.includes('cycle_time')) || cycleTime > envCycle.upper;

  // Dynamic banner message based on actual active drift signals
  let driftMessage = 'Process drift detected by multivariate Sentinel. Quality contract at risk if uncorrected.';
  if (contributing.length > 0) {
    const primaryName = contributing[0].replace(/_/g, ' ').toUpperCase();
    const lead = driftData?.lead_cycles;
    driftMessage = lead != null
      ? `Statistical process drift detected on ${primaryName}. Projected quality contract violation in ~${lead} cycles if uncorrected.`
      : `Statistical process drift detected on ${primaryName}.`;
  }

  // Quality Contract spec targets
  const targetWeight = contractData?.target_weight_g ?? null;
  const weightTol = contractData?.weight_tolerance_g ?? null;
  const weightMin = contractData?.weight_min_g ?? (targetWeight - weightTol);
  const weightMax = contractData?.weight_max_g ?? (targetWeight + weightTol);
  const isWeightOk = partWeight != null && weightMin != null && weightMax != null
    && partWeight >= weightMin && partWeight <= weightMax;

  const qualityRiskPct =
    processData.quality_risk_pct ??
    riskData?.risk_percentage ??
    (riskData?.risk_probability != null ? riskData.risk_probability * 100 : null);

  return (
    <div id="panel-detect" role="tabpanel" aria-labelledby="tab-detect" className="live-process">
      {/* P0-01: Full-Width Process State Banner */}
      <div className={`process-state-banner ${isDriftActive ? 'process-state-banner--alarm' : 'process-state-banner--healthy'}`}>
        <div className="process-state-banner__left">
          <div className="process-state-banner__title-row">
            <span className="process-state-banner__title">
              {isDriftActive ? '⚠ PROCESS DRIFT DETECTED — QUALITY CONTRACT AT RISK' : '✓ PROCESS STABLE — PRODUCTION SAFE'}
            </span>
            <span className={`pill ${isDriftActive ? 'pill--wine' : 'pill--lagoon'}`}>
              {isDriftActive ? `QUALITY RISK: ${qualityRiskPct != null ? qualityRiskPct.toFixed(1) + '%' : '—'}` : 'NORMAL TOLERANCE'}
            </span>
          </div>
          <div className="process-state-banner__subtext">
            {isDriftActive
              ? driftMessage
              : `All process signals operating within calibrated safe boundaries. Machine state: ${currentState}.`}
          </div>
        </div>
        {isDriftActive && onProceed && (
          <button
            type="button"
            className="process-state-banner__btn"
            onClick={onProceed}
            title="Advance to Stage 2: Diagnose Root Cause & Suspect Production"
          >
            INSPECT CAUSE &amp; RISK →
          </button>
        )}
      </div>

      {/* Primary Pipeline Progress */}
      <div className="card" style={{ padding: '16px 20px', backgroundColor: 'var(--color-white)', border: 'var(--border-card)', borderRadius: 'var(--r-card)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <span className="label-section" style={{ margin: 0 }}>DECISION PIPELINE PROGRESS</span>
          <span style={{ fontSize: '12px', color: 'var(--color-stone)' }}>
            State: <strong style={{ color: 'var(--color-charcoal)' }}>{currentState}</strong> · Risk: <strong style={{ color: isDriftActive ? 'var(--color-wine)' : 'var(--color-lagoon)' }}>{qualityRiskPct != null ? `${qualityRiskPct.toFixed(1)}%` : '—'}</strong>
          </span>
        </div>
        <ProcessStateTimeline currentState={currentState} />
      </div>

      {/* Core Process Signals (PS02 Parameters) */}
      <div className="card" style={{ padding: '20px 24px', backgroundColor: 'var(--color-white)', border: 'var(--border-card)', borderRadius: 'var(--r-card)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <span className="label-section" style={{ margin: 0 }}>Primary process telemetry</span>
          <span style={{ fontSize: '11px', color: 'var(--color-stone)' }}>Simulated telemetry · 2 s refresh</span>
        </div>

        <div className="signals-grid">
          {/* Signal 1: Barrel Temperature */}
          <SignalGauge
            label="Barrel Temperature (Zone 3)"
            value={barrelTemp}
            unit="°C"
            min={210}
            max={260}
            envelopeMin={envZ3.lower}
            envelopeMax={envZ3.upper}
            isDrifting={isTempDrifting}
          />

          {/* Signal 2: Injection Pressure */}
          <SignalGauge
            label="Injection Pressure"
            value={injPressure}
            unit="bar"
            min={70}
            max={140}
            envelopeMin={envInj.lower}
            envelopeMax={envInj.upper}
            isDrifting={isPressureDrifting}
          />

          {/* Signal 3: Material Moisture */}
          <SignalGauge
            label="Material Moisture Content"
            value={moisture}
            unit="%"
            min={0.0}
            max={0.4}
            envelopeMin={envMoist.lower}
            envelopeMax={envMoist.upper}
            isDrifting={isMoistureDrifting}
          />

          {/* Signal 4: Mold Cycle Duration (Secondary) */}
          <SignalGauge
            label="Mold Cycle Duration (Secondary)"
            value={cycleTime}
            unit="s"
            min={20}
            max={35}
            envelopeMin={envCycle.lower}
            envelopeMax={envCycle.upper}
            isDrifting={isCycleTimeDrifting}
          />
        </div>
      </div>

      {/* Secondary Quality Contract View (UIredesign §3) */}
      <details className="contract-expander">
        <summary className="contract-expander__summary">
          Quality Contract Specifications &amp; Offline Inspection Boundaries →
        </summary>
        <div className="contract-card" style={{ marginTop: '12px' }}>
          <div className="contract-header">
            <span className="label-section" style={{ margin: 0 }}>PART QUALITY CONTRACT SPECIFICATIONS</span>
            <span className="pill pill--mist num">Target Specification</span>
          </div>

          <table className="quality-contract-table">
            <thead>
              <tr>
                <th>Quality Characteristic</th>
                <th>Target Specification</th>
                <th>Validation Method</th>
                <th>Contract Status</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Part Weight</td>
                <td className="num">
                  {targetWeight != null && weightTol != null ? `${targetWeight.toFixed(1)} ± ${weightTol.toFixed(1)}g` : '—'}
                </td>
                <td>Offline CTQ Scale (Mandatory Release Gate)</td>
                <td>
                  <span className={`pill ${isWeightOk ? 'pill--lagoon' : 'pill--wine'}`}>
                    {isWeightOk ? 'IN SPEC' : 'SUSPECT'}
                  </span>
                </td>
              </tr>
              <tr>
                <td>Cycle Duration</td>
                <td className="num">26.5 ± 2.5s</td>
                <td>In-Line Press PLC Timestamp</td>
                <td>
                  <span className={`pill ${!isCycleTimeDrifting ? 'pill--lagoon' : 'pill--violet'}`}>
                    {!isCycleTimeDrifting ? 'IN SPEC' : 'ELEVATED'}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>

          <div style={{ marginTop: '12px', padding: '10px 12px', backgroundColor: 'var(--color-parchment)', borderRadius: '6px', fontSize: '11px', color: 'var(--color-stone)', lineHeight: 1.4 }}>
            * Calibrated automotive quality contract for plastic bracket. Part weight verification is performed during post-recovery physical QC before lot release.
          </div>
        </div>
      </details>
    </div>
  );
}

export default LiveProcess;

