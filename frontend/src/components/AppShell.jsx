import React, { useState, useEffect } from 'react';
import './AppShell.css';
import { usePolling, resetDemoSession } from '../hooks/useApi';
import { EvidenceModal } from './EvidenceModal';

export function AppShell({ activeTab, onTabChange, children }) {
  // Pulse dot state for simulation stream indicator
  const [pulseActive, setPulseActive] = useState(true);
  const [isResetting, setIsResetting] = useState(false);
  const [resetStatus, setResetStatus] = useState(null);
  const [showEvidenceModal, setShowEvidenceModal] = useState(false);

  useEffect(() => {
    const interval = setInterval(() => {
      setPulseActive((prev) => !prev);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  // Poll core telemetry streams
  const { data: processData } = usePolling('/api/process/current', 2000);
  const { data: riskData } = usePolling('/api/quality/risk', 2000);
  const { data: driftData } = usePolling('/api/process/drift', 2000);

  // Cycle and machine info
  const cycleNumber = processData?.current_cycle ?? 437;
  const machineId = processData?.machine_id ?? 'HTF-200';
  const moldId = processData?.mold_id ?? 'GMB-48A';
  const partId = processData?.part_id ?? 'Automotive Bracket';
  const recipeId = processData?.recipe_id ?? 'R-12';

  // Signals extraction
  const signals = processData?.signals || {};
  const barrelTemp = signals.barrel_temp_z3 ?? signals.barrel_temperature ?? 238.4;
  const injPressure = signals.injection_pressure ?? 84.2;
  const moisture = signals.material_moisture_pct ?? signals.material_moisture ?? 0.12;

  // Quality Risk extraction
  const qualityRiskPct = processData?.quality_risk_pct ?? 
    (riskData?.risk_percentage ?? (riskData?.risk_probability ? riskData.risk_probability * 100 : 72.0));
  const riskState = riskData?.risk_state ?? (qualityRiskPct >= 50 ? 'HIGH' : qualityRiskPct >= 20 ? 'MEDIUM' : 'LOW');

  // Drift signals check
  const contributing = driftData?.contributing_signals || [];
  const isTempDrifting = contributing.some((s) => s.includes('barrel') || s.includes('temp')) || barrelTemp > 245;
  const isPressureDrifting = contributing.some((s) => s.includes('pressure')) || injPressure > 92;
  const isMoistureDrifting = contributing.some((s) => s.includes('moisture')) || moisture > 0.20;

  const handleResetDemo = async () => {
    setIsResetting(true);
    setResetStatus('Resetting session...');
    try {
      await resetDemoSession(machineId);
      setResetStatus('✓ Baseline reset');
      setTimeout(() => {
        window.location.reload();
      }, 400);
    } catch (err) {
      setResetStatus(`Error: ${err.message}`);
      setIsResetting(false);
    }
  };

  return (
    <div className="app-shell">
      {/* Zone 1: Brand Bar */}
      <header className="app-shell__brand">
        <div className="brand-left">
          <span className="brand-wordmark">PROCESS GUARDIAN</span>
          <span className="brand-subtitle">Injection Process Intelligence</span>
        </div>
        <div className="brand-right">
          <div className="prototype-badge" title="Safety interlock active: simulation & advisory mode only, no PLC write-back">
            <span>PROTOTYPE ADVISORY · NO PLC WRITE-BACK</span>
          </div>
          <div className="simulation-indicator">
            <span className={`pulse-dot ${pulseActive ? 'pulse-dot--active' : ''}`} />
            <span>SIMULATION · 2s STREAM</span>
          </div>
        </div>
      </header>

      {/* Zone 2: Scenario + Dynamic Machine Context + One-Click Reset + Evidence Stack */}
      <div className="app-shell__context">
        <div className="context-left">
          <div className="scenario-badge">
            <span>DEMO · THERMAL DRIFT</span>
          </div>
          <button
            id="demo-reset-btn"
            className="demo-reset-btn"
            onClick={handleResetDemo}
            disabled={isResetting}
            title="Reset scenario to pristine baseline while preserving immutable audit logs"
          >
            {isResetting ? 'RESETTING...' : '↺ RESET DEMO'}
          </button>
          <button
            id="evidence-modal-btn"
            className="evidence-modal-btn"
            onClick={() => setShowEvidenceModal(true)}
            title="Inspect 4-Level Industrial Evidence & Grounding Benchmark (SKZ/Fraunhofer 564 Parts)"
          >
            📊 INDUSTRIAL EVIDENCE [L2]
          </button>
          {resetStatus && <span className="reset-status-msg">{resetStatus}</span>}
        </div>
        <div className="machine-context">
          <span>{machineId}</span> · <span>{moldId}</span> · <span>{partId}</span> · <span>{recipeId}</span> · <span className="cycle-num-highlight num">Cycle #{cycleNumber}</span>
        </div>
      </div>

      {/* Zone 3: PS02 Hero Stats (4 Cards with Epistemic Badges) */}
      <section className="app-shell__hero-stats" aria-label="Process Overview Metrics">
        {/* Card 1: Barrel Temp */}
        <div className="hero-stat-card">
          <div className="hero-stat-card__top">
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span className="hero-stat-card__label">BARREL TEMP</span>
              <span className="epistemic-tag epistemic-tag--l2">L2 MEASURED</span>
            </div>
            <span className={`pill ${isTempDrifting ? 'pill--wine' : 'pill--lagoon'}`}>
              {isTempDrifting ? 'DRIFT' : 'NORMAL'}
            </span>
          </div>
          <div className="hero-stat-card__bottom">
            <span className="hero-stat-card__value num">
              {Number(barrelTemp).toFixed(1)}
              <span className="hero-stat-card__unit">°C</span>
            </span>
            <span className="hero-stat-card__subtext">Target 235.0 °C</span>
          </div>
        </div>

        {/* Card 2: Injection Pressure */}
        <div className="hero-stat-card">
          <div className="hero-stat-card__top">
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span className="hero-stat-card__label">INJ. PRESSURE</span>
              <span className="epistemic-tag epistemic-tag--l2">L2 MEASURED</span>
            </div>
            <span className={`pill ${isPressureDrifting ? 'pill--wine' : 'pill--lagoon'}`}>
              {isPressureDrifting ? 'DRIFT' : 'NORMAL'}
            </span>
          </div>
          <div className="hero-stat-card__bottom">
            <span className="hero-stat-card__value num">
              {Number(injPressure).toFixed(1)}
              <span className="hero-stat-card__unit">MPa</span>
            </span>
            <span className="hero-stat-card__subtext">Target 82.0 MPa</span>
          </div>
        </div>

        {/* Card 3: Material Moisture */}
        <div className="hero-stat-card">
          <div className="hero-stat-card__top">
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span className="hero-stat-card__label">MOISTURE</span>
              <span className="epistemic-tag epistemic-tag--l2">L2 BENCHMARK</span>
            </div>
            <span className={`pill ${isMoistureDrifting ? 'pill--wine' : 'pill--lagoon'}`}>
              {isMoistureDrifting ? 'DEVIATION' : 'NORMAL'}
            </span>
          </div>
          <div className="hero-stat-card__bottom">
            <span className="hero-stat-card__value num">
              {Number(moisture).toFixed(2)}
              <span className="hero-stat-card__unit">%</span>
            </span>
            <span className="hero-stat-card__subtext">Limit &lt; 0.20%</span>
          </div>
        </div>

        {/* Card 4: Quality Risk */}
        <div className="hero-stat-card">
          <div className="hero-stat-card__top">
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span className="hero-stat-card__label">QUALITY RISK</span>
              <span className="epistemic-tag epistemic-tag--l3">L3 CALIBRATED</span>
            </div>
            <span className={`pill ${qualityRiskPct >= 50 ? 'pill--wine' : qualityRiskPct >= 20 ? 'pill--violet' : 'pill--lagoon'}`}>
              {riskState === 'HIGH' ? 'HIGH RISK' : riskState === 'MEDIUM' ? 'ELEVATED' : 'STABLE'}
            </span>
          </div>
          <div className="hero-stat-card__bottom">
            <span className="hero-stat-card__value num" style={{ color: qualityRiskPct >= 50 ? 'var(--color-wine)' : 'var(--color-charcoal)' }}>
              {Number(qualityRiskPct).toFixed(1)}
              <span className="hero-stat-card__unit">%</span>
            </span>
            <span className="hero-stat-card__subtext">Calibrated Prob.</span>
          </div>
        </div>
      </section>

      {/* Main Content Area */}
      <main className="app-shell__content">
        {children}
      </main>

      {/* Evidence & Grounding Modal */}
      <EvidenceModal
        isOpen={showEvidenceModal}
        onClose={() => setShowEvidenceModal(false)}
      />

      {/* Persistent Disclaimer & Safety Footer */}
      <footer className="app-shell__footer">
        <span>PROCESS GUARDIAN MVP · MODELED SIMULATION DATA · ADVISORY INTERVENTION ONLY · NO DIRECT PLC WRITE-BACK</span>
      </footer>
    </div>
  );
}
