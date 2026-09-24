import React from 'react';
import './LiveProcess.css';
import { usePolling } from '../hooks/useApi';
import { SignalGauge } from '../components/SignalGauge';
import { ProcessStateTimeline } from '../components/ProcessStateTimeline';

export function LiveProcess() {
  const { data: processData } = usePolling('/api/process/current', 2000);
  const { data: driftData } = usePolling('/api/process/drift', 2000);
  const { data: contractData } = usePolling('/api/quality/contract', 5000);
  const { data: riskData } = usePolling('/api/quality/risk', 2000);

  const signals = processData?.signals || {};
  const currentState = processData?.state || 'HEALTHY';

  // Signal extraction with fallback to scenario baselines
  const barrelTemp = signals.barrel_temp_z3 ?? signals.barrel_temperature ?? 238.4;
  const injPressure = signals.injection_pressure ?? 84.2;
  const moisture = signals.material_moisture_pct ?? signals.material_moisture ?? 0.12;
  const cycleTime = signals.cycle_time ?? 27.6;
  const partWeight = signals.part_weight_g ?? 244.8;

  // Contributing signals from multi-detector sentinel
  const contributing = driftData?.contributing_signals || [];
  const isTempDrifting = contributing.some((s) => s.includes('barrel') || s.includes('temp')) || barrelTemp > 245;
  const isPressureDrifting = contributing.some((s) => s.includes('pressure')) || injPressure > 92;
  const isMoistureDrifting = contributing.some((s) => s.includes('moisture')) || moisture > 0.20;
  const isCycleTimeDrifting = contributing.some((s) => s.includes('cycle_time')) || cycleTime > 30.0;

  // Quality Contract spec targets
  const targetWeight = contractData?.target_weight_g ?? 245.0;
  const weightTol = contractData?.weight_tolerance_g ?? 3.0;
  const weightMin = contractData?.weight_min_g ?? (targetWeight - weightTol);
  const weightMax = contractData?.weight_max_g ?? (targetWeight + weightTol);
  const isWeightOk = partWeight >= weightMin && partWeight <= weightMax;

  const stabilityPct = processData?.process_stability_pct ?? 96.0;
  const qualityRiskPct = processData?.quality_risk_pct ?? (riskData?.risk_percentage ?? 72.0);

  return (
    <div id="panel-live" role="tabpanel" aria-labelledby="tab-live" className="live-process">
      {/* Left Column (8fr): Process Signals & State Pipeline */}
      <div className="live-process__left">
        <div>
          <span className="label-section">PROCESS SIGNALS &amp; OPERATING ENVELOPES</span>
          
          {/* Signal 1: Barrel Temperature */}
          <SignalGauge
            label="Barrel Temperature (Zone 3)"
            value={barrelTemp}
            unit="°C"
            min={220}
            max={260}
            envelopeMin={228}
            envelopeMax={245}
            isDrifting={isTempDrifting}
          />

          {/* Signal 2: Injection Pressure */}
          <SignalGauge
            label="Peak Injection Pressure"
            value={injPressure}
            unit="MPa"
            min={60}
            max={110}
            envelopeMin={78}
            envelopeMax={92}
            isDrifting={isPressureDrifting}
          />

          {/* Signal 3: Material Moisture */}
          <SignalGauge
            label="Material Moisture Content"
            value={moisture}
            unit="%"
            min={0.0}
            max={0.5}
            envelopeMin={0.05}
            envelopeMax={0.20}
            isDrifting={isMoistureDrifting}
          />

          {/* Signal 4: Cycle Time */}
          <SignalGauge
            label="Mold Cycle Duration"
            value={cycleTime}
            unit="s"
            min={20}
            max={35}
            envelopeMin={24}
            envelopeMax={30}
            isDrifting={isCycleTimeDrifting}
          />
        </div>

        <div>
          <span className="label-section">DECISION PIPELINE TIMELINE</span>
          <ProcessStateTimeline currentState={currentState} />
        </div>
      </div>

      {/* Right Column (4fr): Quality Contract & System State */}
      <div className="live-process__right">
        {/* Quality Contract Card */}
        <div className="contract-card">
          <div className="contract-header">
            <span className="label-section" style={{ margin: 0 }}>QUALITY CONTRACT SPEC</span>
            <span className="pill pill--mist num">{contractData?.contract_code ?? 'QC-AUTO-01'}</span>
          </div>

          <table className="quality-contract-table">
            <thead>
              <tr>
                <th>Parameter</th>
                <th>Target Spec</th>
                <th>Current</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Part Weight</td>
                <td className="num">{targetWeight.toFixed(1)} ± {weightTol.toFixed(1)}g</td>
                <td className="num">{partWeight.toFixed(1)}g</td>
                <td>
                  <span className={`pill ${isWeightOk ? 'pill--lagoon' : 'pill--wine'}`}>
                    {isWeightOk ? 'PASS' : 'OUT'}
                  </span>
                </td>
              </tr>
              <tr>
                <td>Max Sink Mark</td>
                <td className="num">&lt; 0.15 mm</td>
                <td className="num">0.08 mm</td>
                <td><span className="pill pill--lagoon">PASS</span></td>
              </tr>
              <tr>
                <td>Flash Allowance</td>
                <td>None</td>
                <td>0.00</td>
                <td><span className="pill pill--lagoon">PASS</span></td>
              </tr>
              <tr>
                <td>Cycle Time</td>
                <td className="num">26.5 ± 2.5s</td>
                <td className="num">{cycleTime.toFixed(1)}s</td>
                <td>
                  <span className={`pill ${!isCycleTimeDrifting ? 'pill--lagoon' : 'pill--violet'}`}>
                    {!isCycleTimeDrifting ? 'PASS' : 'WARN'}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* System State Card */}
        <div className="system-card">
          <span className="label-section">SYSTEM GOVERNANCE STATE</span>
          <div className="system-status-badge">
            <span className="system-status-state">{currentState}</span>
            <span className={`pill ${currentState === 'HEALTHY' ? 'pill--lagoon' : 'pill--wine'}`}>
              {currentState === 'HEALTHY' ? 'STABLE' : 'ACTION REQUIRED'}
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginTop: '16px' }}>
            <div className="card" style={{ padding: '12px', backgroundColor: 'var(--color-parchment)' }}>
              <span style={{ fontSize: '11px', color: 'var(--color-stone)', textTransform: 'uppercase', display: 'block' }}>Stability</span>
              <span className="num" style={{ fontSize: '20px', fontWeight: 'var(--fw-data)', color: 'var(--color-lagoon)' }}>
                {stabilityPct.toFixed(1)}%
              </span>
            </div>
            <div className="card" style={{ padding: '12px', backgroundColor: 'var(--color-parchment)' }}>
              <span style={{ fontSize: '11px', color: 'var(--color-stone)', textTransform: 'uppercase', display: 'block' }}>Drift Risk</span>
              <span className="num" style={{ fontSize: '20px', fontWeight: 'var(--fw-data)', color: qualityRiskPct >= 50 ? 'var(--color-wine)' : 'var(--color-charcoal)' }}>
                {qualityRiskPct.toFixed(1)}%
              </span>
            </div>
          </div>
        </div>

        {/* Operational Context Card */}
        <div className="context-card">
          <span className="label-section">OPERATIONAL CONTEXT</span>
          <div className="context-grid">
            <div className="context-item">
              <span className="context-item__label">Machine</span>
              <span className="context-item__value">{processData?.machine_id ?? 'HTF-200'}</span>
            </div>
            <div className="context-item">
              <span className="context-item__label">Mold Tooling</span>
              <span className="context-item__value">{processData?.mold_id ?? 'GMB-48A'}</span>
            </div>
            <div className="context-item">
              <span className="context-item__label">Component</span>
              <span className="context-item__value">{processData?.part_id ?? 'Automotive Bracket'}</span>
            </div>
            <div className="context-item">
              <span className="context-item__label">Active Recipe</span>
              <span className="context-item__value">{processData?.recipe_id ?? 'R-12'}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LiveProcess;
