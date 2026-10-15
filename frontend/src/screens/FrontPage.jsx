import React, { useState } from 'react';
import './FrontPage.css';
import { selectScenario } from '../hooks/useApi';
import { DetectionComparison } from '../components/DetectionComparison';

export function FrontPage({
  onSelectScenario,
  onOpenScorecard,
  onOpenCoPQModal,
  onNavigateToLive,
}) {
  const [loadingScenarioId, setLoadingScenarioId] = useState(null);
  const [runError, setRunError] = useState(null);

  // Locked demo scope (scope_plan.md Sec.4): three scenarios, each a distinct
  // proof. S06 proves the closed loop + the SPC-says-fine/Guardian-acts
  // contradiction; SCN-FLIP-HUMAN-CHANNEL proves the sensor-blind gap filled
  // (scope_plan.md Sec.3: "the one demo that wins"); S08 proves the ABSTAIN
  // trust gate. The other 8 registry scenarios still run in the automated
  // validation suite (cited, not shown).
  const scenarios = [
    {
      id: 'SCN-06-COMPOUND',
      code: 'S06',
      title: 'Scenario 06 — Compound Multi-Signal Drift',
      category: 'COMPOUND (BOSS)',
      categoryType: 'compound',
      isHero: true,
      cycles: 500,
      seed: 506,
      description:
        'Coupled Zone 3 thermal drift (+0.22°C/cycle) and hydraulic valve wear (-0.28 bar/cycle) simultaneously degrade cavity fill and pack dynamics.',
      detect:
        'Coupled Zone 3 thermal drift (+0.22°C) + injection pressure loss (-0.28 bar); Hotelling T² triggers early.',
      diagnose:
        'Multivariate interaction analysis ranks thermal (58%) and hydraulic pressure (34%) as coupled drivers.',
      actVerify:
        'Evaluates combined candidates; selects minimum-cost coordinated action; 5-cycle stability window confirmed; suspect lot collapsed by 78%.',
      transition: 'COUPLED FAILURE → COORDINATED RECOVERY',
      statusClass: 'status-compound',
    },
    {
      id: 'SCN-FLIP-HUMAN-CHANNEL',
      code: 'S-FLIP',
      title: 'Scenario FLIP — Human-Channel Material Risk',
      category: 'MATERIAL (SENSOR-BLIND)',
      categoryType: 'material',
      isHero: true,
      cycles: 300,
      seed: 913,
      description:
        'Zero sensor-level disturbance anywhere in this replay — every barrel, pressure and timing signal stays fully in-envelope. An operator shift note in a local language ("new resin lot, dryer was down, moisture not verified") is the only evidence of risk.',
      detect:
        'No drift on any sensor the entire run; the operator note is the only signal, parsed through the same bounded multilingual channel as the P0 checkpoint gates.',
      diagnose:
        'Root-cause attribution ranks the human-channel evidence above all sensor noise for the whole hold — the sensor-blind gap no gauge-only system can see.',
      actVerify:
        'No machine-side action exists for an unverified resin lot; the engine holds production at QC_REQUIRED pending a physical moisture check instead of guessing.',
      transition: 'CONTINUE → MATERIAL VERIFICATION REQUIRED',
      statusClass: 'status-material',
    },
    {
      id: 'SCN-08-LOW-CONF-ABSTAIN',
      code: 'S08',
      title: 'Scenario 08 — Out-of-Distribution Drift',
      category: 'SAFETY GATE',
      categoryType: 'safety',
      isHero: true,
      cycles: 350,
      seed: 708,
      description:
        'High-variance uncalibrated drift pattern falls outside surrogate response surface, depressing model epistemic confidence below 0.65.',
      detect:
        'Unseen drift pattern with high epistemic variance (epistemic confidence < 0.65).',
      diagnose:
        'Model flags out-of-distribution anomaly without sufficient historical calibration.',
      actVerify:
        'SAFE-03 mandatory ABSTAIN enforced; refuses speculative intervention; triggers supervisor physical inspection hold.',
      transition: 'HIGH UNCERTAINTY → SAFE ABSTAIN GATE',
      statusClass: 'status-abstain',
    },
  ];

  const handleRunScenario = async (scenarioId) => {
    setLoadingScenarioId(scenarioId);
    setRunError(null);
    try {
      await selectScenario(scenarioId);
      if (onSelectScenario) {
        onSelectScenario(scenarioId);
      }
      if (onNavigateToLive) {
        onNavigateToLive('detect');
      }
    } catch (err) {
      // Silent failure here used to look like a dead button mid-demo.
      setRunError(
        `Could not start ${scenarioId}. The engine is not answering on its API port. (${err.message})`
      );
    } finally {
      setLoadingScenarioId(null);
    }
  };

  return (
    <div className="front-page-container">
      {/* Hero Section */}
      <section className="fp-hero">
        <div className="fp-hero__badge">
          Demo plant &middot; Tier-2 automotive molder &middot; Scrap target &le;2.0% (PS02 baseline 6.8%)
        </div>
        <h1 className="fp-hero__title">
          It catches the drift your machine&rsquo;s own limits pass as normal.
        </h1>
        <p className="fp-hero__subtitle">
          Process Guardian watches shop-floor telemetry for the multi-signal drift that stays inside every
          individual tolerance band, names the variable responsible, prices waiting against acting, and
          recommends the one smallest setting change &mdash; then verifies recovery with a physical sample
          before the lot is released. It never writes to the machine; the operator decides.
        </p>

        {/* Flagship Demo Box (Scenario 06 - Compound Drift) */}
        <div className="flagship-demo-card">
          <div className="flagship-demo-content">
            <div className="flagship-badges">
              <span className="badge-flagship">FLAGSHIP DEMO</span>
              <span className="badge-scenario">SCENARIO S06</span>
              <span className="badge-spec">500 CYCLES · SEED #506</span>
            </div>
            <h2 className="flagship-title">
              Compound Multi-Signal Drift (Coupled Thermal & Hydraulic Degradation)
            </h2>
            <p className="flagship-description">
              Coupled barrel Zone 3 thermal drift (+0.22°C/cycle) + hydraulic valve wear (-0.28 bar/cycle) threatens cavity pack. Single-variable factory alarms miss multivariate covariance until physical scrap occurs. Process Guardian detects early, isolates dominant contributors, applies minimum-cost intervention, and verifies recovery.
            </p>
          </div>
          <div className="flagship-action">
            <button
              className="btn-run-flagship"
              onClick={() => handleRunScenario('SCN-06-COMPOUND')}
              disabled={loadingScenarioId === 'SCN-06-COMPOUND'}
              aria-busy={loadingScenarioId === 'SCN-06-COMPOUND'}
            >
              {loadingScenarioId === 'SCN-06-COMPOUND' ? 'Starting the line…' : 'Run the flagship scenario'}
            </button>
            <span className="flagship-action__hint">Opens the live line at the drift</span>
          </div>
        </div>

        {runError && (
          <p className="fp-run-error" role="alert">
            {runError}
          </p>
        )}
      </section>

      {/* Why not just the machine's own alarms? Answered before the catalogue. */}
      <DetectionComparison />

      {/* Scenarios Section — locked to the three demo-worthy proofs (scope_plan.md Sec.4).
          No filter/toggle: there is nothing left to hide behind one. */}
      <section className="fp-scenarios-section">
        <div className="scenarios-filter-bar">
          <div className="scenarios-heading">
            <h2 className="scenarios-heading__title">Production failure trajectories</h2>
            <p className="scenarios-heading__sub">
              Each one replays through the same engine. Pick any; the loop does not change.
            </p>
          </div>
        </div>

        {/* Scenario grid */}
        <div className="scenarios-grid">
          {scenarios.map((s) => (
            <div key={s.id} className="scenario-card">
              {/* Card Header */}
              <div className="scenario-card__header">
                <div className="header-badges">
                  <span className="code-badge">{s.code}</span>
                  <span className={`cat-badge cat-badge--${s.categoryType}`}>{s.category}</span>
                </div>
                <div className="meta-info">
                  {s.cycles} CYCLES · SEED #{s.seed}
                </div>
              </div>

              {/* Title & Description */}
              <h3 className="scenario-card__title">{s.title}</h3>
              <p className="scenario-card__desc">{s.description}</p>

              {/* THE 3-STAGE CLOSED-LOOP CONTRACT */}
              {/* ● DETECT ───── DIAGNOSE ───── ACT & VERIFY */}
              <div className="closed-loop-box">
                <div className="closed-loop-rail">
                  <div className="rail-step">
                    <span className="dot dot--detect">●</span>
                    <span className="step-tag">DETECT</span>
                  </div>
                  <div className="rail-line" />
                  <div className="rail-step">
                    <span className="dot dot--diagnose">●</span>
                    <span className="step-tag">DIAGNOSE</span>
                  </div>
                  <div className="rail-line" />
                  <div className="rail-step">
                    <span className="dot dot--act">●</span>
                    <span className="step-tag">ACT & VERIFY</span>
                  </div>
                </div>

                {/* Collapsed by default: ten cards of three paragraphs each left
                    nothing scannable. The rail above still shows the loop. */}
                <details className="closed-loop-details">
                  <summary>What the engine does, stage by stage</summary>
                  <div className="closed-loop-content">
                    <div className="stage-row">
                      <span className="stage-label stage-label--detect">DETECT:</span>
                      <span className="stage-text">{s.detect}</span>
                    </div>
                    <div className="stage-row">
                      <span className="stage-label stage-label--diagnose">DIAGNOSE:</span>
                      <span className="stage-text">{s.diagnose}</span>
                    </div>
                    <div className="stage-row">
                      <span className="stage-label stage-label--act">ACT & VERIFY:</span>
                      <span className="stage-text">{s.actVerify}</span>
                    </div>
                  </div>
                </details>
              </div>

              {/* Card Footer */}
              <div className="scenario-card__footer">
                <span className={`transition-pill ${s.statusClass}`}>
                  {s.transition}
                </span>

                <div className="footer-actions">
                  <button
                    className="btn-card-scorecard"
                    onClick={() => {
                      if (onOpenScorecard) {
                        selectScenario(s.id)
                          .then(() => onOpenScorecard())
                          .catch((err) => setRunError(`Could not load the scorecard. (${err.message})`));
                      }
                    }}
                    title="Per-pillar evidence for this scenario"
                  >
                    Evidence
                  </button>

                  <button
                    className="btn-card-run"
                    onClick={() => handleRunScenario(s.id)}
                    disabled={loadingScenarioId === s.id}
                    aria-busy={loadingScenarioId === s.id}
                  >
                    {loadingScenarioId === s.id ? 'Starting…' : 'Run scenario'}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
