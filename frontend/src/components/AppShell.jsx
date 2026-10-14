import React, { useState, useEffect } from 'react';
import './AppShell.css';
import { usePolling, resetDemoSession, selectScenario } from '../hooks/useApi';
import { CoPQModal } from './CoPQModal';
import { ScenarioScorecardModal } from './ScenarioScorecardModal';
import { ValidationSuiteModal } from './ValidationSuiteModal';
import { OperationalCheckpointsModal } from './OperationalCheckpointsModal';

export function AppShell({
  activeTab,
  onTabChange,
  showCoPQModal: propShowCoPQ,
  setShowCoPQModal: propSetShowCoPQ,
  showScorecardModal: propShowScorecard,
  setShowScorecardModal: propSetShowScorecard,
  showValidationSuiteModal: propShowValidationSuite,
  setShowValidationSuiteModal: propSetShowValidationSuite,
  showCheckpointsModal: propShowCheckpoints,
  setShowCheckpointsModal: propSetShowCheckpoints,
  children,
}) {
  // Pulse dot state for simulation stream indicator
  const [pulseActive, setPulseActive] = useState(true);
  const [isResetting, setIsResetting] = useState(false);
  const [resetStatus, setResetStatus] = useState(null);
  const [localShowCoPQModal, setLocalShowCoPQModal] = useState(false);
  
  // Scenario State
  const [localShowScorecardModal, setLocalShowScorecardModal] = useState(false);
  const [localShowValidationSuiteModal, setLocalShowValidationSuiteModal] = useState(false);
  const [localShowCheckpointsModal, setLocalShowCheckpointsModal] = useState(false);
  const [isSwitchingScenario, setIsSwitchingScenario] = useState(false);

  const isCoPQOpen = propShowCoPQ !== undefined ? propShowCoPQ : localShowCoPQModal;
  const setCoPQOpen = propSetShowCoPQ || setLocalShowCoPQModal;

  const isScorecardOpen = propShowScorecard !== undefined ? propShowScorecard : localShowScorecardModal;
  const setScorecardOpen = propSetShowScorecard || setLocalShowScorecardModal;

  const isValidationSuiteOpen = propShowValidationSuite !== undefined ? propShowValidationSuite : localShowValidationSuiteModal;
  const setValidationSuiteOpen = propSetShowValidationSuite || setLocalShowValidationSuiteModal;

  const isCheckpointsOpen = propShowCheckpoints !== undefined ? propShowCheckpoints : localShowCheckpointsModal;
  const setCheckpointsOpen = propSetShowCheckpoints || setLocalShowCheckpointsModal;

  useEffect(() => {
    const interval = setInterval(() => {
      setPulseActive((prev) => !prev);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  // Poll core telemetry and scenario streams
  const { data: processData, failures: processFailures } = usePolling('/api/process/current', 2000);
  const { data: riskData } = usePolling('/api/quality/risk', 2000);
  const { data: driftData } = usePolling('/api/process/drift', 2000);
  const { data: activeScnData } = usePolling('/api/scenarios/active', 2000);
  const { data: scenariosList } = usePolling('/api/scenarios?hero_only=true', 30000);

  // Active scenario details. Default matches the flagship (S06) until a
  // scenario is actually selected.
  const activeScenarioId = activeScnData?.active_scenario_id || 'SCN-06-COMPOUND';
  const activeScenario = activeScnData?.scenario;
  const activeScorecard = activeScnData?.scorecard;

  // Every screen below carries placeholder fallbacks for its numbers. That is
  // survivable while the engine answers, and a fabrication once it stops -- so
  // past three consecutive failed polls (~6s) we refuse to render the screens
  // at all rather than let anyone read an invented figure off them.
  const isOffline = processFailures >= 3;
  const NO_DATA = '--';
  const cycleNumber = processData?.current_cycle ?? NO_DATA;
  const machineId = processData?.machine_id ?? NO_DATA;
  const moldId = processData?.mold_id ?? NO_DATA;
  const partId = processData?.part_id ?? NO_DATA;
  const recipeId = processData?.recipe_id ?? NO_DATA;

  const handleResetDemo = async () => {
    setIsResetting(true);
    setResetStatus('Resetting session...');
    try {
      await resetDemoSession(processData?.machine_id || 'IMM-01');
      setResetStatus('✓ Baseline reset');
      setTimeout(() => {
        window.location.reload();
      }, 400);
    } catch (err) {
      setResetStatus(`Error: ${err.message}`);
      setIsResetting(false);
    }
  };

  const handleScenarioChange = async (newScnId) => {
    if (newScnId === activeScenarioId || isSwitchingScenario) return;
    setIsSwitchingScenario(true);
    setResetStatus(`Loading ${newScnId}...`);
    try {
      await selectScenario(newScnId);
      setResetStatus(`✓ ${newScnId} active`);
      setTimeout(() => {
        setResetStatus(null);
      }, 2500);
    } catch (err) {
      setResetStatus(`Error: ${err.message}`);
    } finally {
      setIsSwitchingScenario(false);
    }
  };

  return (
    <div className="app-shell">
      {/* Zone 1: Brand Bar */}
      <header className="app-shell__brand">
        <div
          className="brand-left"
          onClick={() => onTabChange && onTabChange('scenarios')}
          style={{ cursor: 'pointer' }}
          title="Process Guardian — Return to Scenario Showcase"
        >
          <span className="brand-wordmark">
            <span className="brand-icon-hex" aria-hidden="true">⬡</span> PROCESS GUARDIAN
          </span>
          <span className="brand-subtitle">
            Ragam Polymolds · Plant IMM-01
          </span>
        </div>
        <div className="brand-right">
          <div className="plant-target-badge" title="Ragam Polymolds Automotive Quality Target">
            <span>SCRAP TARGET: ≤2.0% (BASELINE: 6.8%)</span>
          </div>
          <div className="prototype-badge" title="Safety interlock active: simulation & advisory mode only, no PLC write-back">
            <span>ADVISORY ONLY · ZERO PLC WRITE-BACK</span>
          </div>
          <div className="simulation-indicator" aria-live="polite">
            <span
              className={`pulse-dot ${isOffline ? 'pulse-dot--offline' : pulseActive ? 'pulse-dot--active' : ''}`}
            />
            <span>{isOffline ? 'ENGINE OFFLINE' : 'SIMULATED TELEMETRY'}</span>
          </div>
        </div>
      </header>

      {/* Zone 2: Scenario Selector + Reset + Context */}
      <div className="app-shell__context">
        <div className="context-left">
          <div className="scenario-select-wrapper">
            <label htmlFor="scenario-dropdown" className="scenario-select-label">SCENARIO:</label>
            <select
              id="scenario-dropdown"
              className="scenario-select"
              value={activeScenarioId}
              onChange={(e) => handleScenarioChange(e.target.value)}
              disabled={isSwitchingScenario}
              title="Select one of the 2 locked demo scenarios"
            >
              {scenariosList && scenariosList.length > 0 ? (
                scenariosList.map((s) => (
                  <option key={s.scenario_id} value={s.scenario_id}>
                    {s.title}
                  </option>
                ))
              ) : (
                // Offline fallback, kept in sync with the locked hero set
                // (scope_plan.md Sec.4) in case the engine isn't answering yet.
                <>
                  <option value="SCN-06-COMPOUND">Scenario 06 — Compound Multi-Signal Drift</option>
                  <option value="SCN-08-LOW-CONF-ABSTAIN">Scenario 08 — Out-of-Distribution Drift</option>
                </>
              )}
            </select>
          </div>

          <button
            id="demo-reset-btn"
            className="demo-reset-btn"
            onClick={handleResetDemo}
            disabled={isResetting}
            title="Reset scenario to pristine baseline while preserving immutable audit logs"
          >
            {isResetting ? 'RESETTING...' : '↺ RESET'}
          </button>

          {activeTab !== 'scenarios' && onTabChange && (
            <button
              className="demo-reset-btn"
              onClick={() => onTabChange('scenarios')}
              title="Return to 10 Industrial Scenarios Showcase"
              style={{ fontWeight: 500 }}
            >
              ← ALL SCENARIOS
            </button>
          )}

          {resetStatus && <span className="reset-status-msg">{resetStatus}</span>}
        </div>

        <div className="machine-context">
          <span>{machineId}</span> · <span>{moldId}</span> · <span>{partId}</span> · <span>{recipeId}</span> · <span className="cycle-num-highlight num">Cycle #{cycleNumber}</span>
        </div>
      </div>

      {/* Unmissable when the engine is not answering: every number on screen is
          stale or absent, and the operator needs to know that before acting. */}
      {isOffline && (
        <div className="engine-offline-banner" role="alert">
          <strong>ENGINE OFFLINE</strong>
          <span>
            No response from the Process Guardian engine. Readings are not live -- do not act on anything
            shown. Start it with <code>python -m uvicorn process_guardian.api.app:app --port 8000</code>
            {' '}(or run <code>demo.cmd</code>).
          </span>
        </div>
      )}

      {/* Main Content Area */}
      <main className="app-shell__content">
        {isOffline ? (
          <div className="engine-offline-panel">
            <h2>No live data</h2>
            <p>
              The Process Guardian engine has not answered for several seconds, so these screens are not
              being shown. They would otherwise display placeholder numbers, and a placeholder that looks
              like a reading is worse than a blank screen.
            </p>
            <p className="engine-offline-panel__cmd">
              <code>python -m uvicorn process_guardian.api.app:app --port 8000</code>
            </p>
            <p className="engine-offline-panel__hint">
              Or run <code>demo.cmd</code> from the project root, which starts the engine and the UI
              together. This panel clears itself as soon as the engine responds.
            </p>
          </div>
        ) : (
          children
        )}
      </main>

      {/* Decision Economics & Parametric CoPQ Modal (ECON-01, ECON-02) */}
      <CoPQModal
        isOpen={isCoPQOpen}
        onClose={() => setCoPQOpen(false)}
      />


      {/* 7-Pillar Scenario Scorecard Modal */}
      <ScenarioScorecardModal
        isOpen={isScorecardOpen}
        onClose={() => setScorecardOpen(false)}
        scorecard={activeScorecard}
        scenarioTitle={activeScenario?.title}
      />

      {/* Operational Validation Suite Modal */}
      <ValidationSuiteModal
        isOpen={isValidationSuiteOpen}
        onClose={() => setValidationSuiteOpen(false)}
        onSelectScenario={handleScenarioChange}
      />

      {/* Shop-Floor Operational Checkpoints Modal (QCHK-02, P0 human-channel gates) */}
      <OperationalCheckpointsModal
        isOpen={isCheckpointsOpen}
        onClose={() => setCheckpointsOpen(false)}
      />

      {/* Persistent Disclaimer & Safety Footer */}
      <footer className="app-shell__footer">
        <span>RAGAM POLYMOLDS · SHOP-FLOOR PROCESS GUARDIAN · OPERATOR ADVISORY ONLY · NO DIRECT PLC WRITE-BACK</span>
        <span className="app-shell__footer-sub">
          Signal acquisition: Euromap 63/77 on presses that support it; a ~$20 clamp thermocouple + hopper hygrometer retrofit elsewhere — no machine replacement required.
        </span>
      </footer>
    </div>
  );
}

