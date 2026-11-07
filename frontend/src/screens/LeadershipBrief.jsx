import React, { useState, useEffect } from 'react';
import './LeadershipBrief.css';
import { fetchLeadershipBrief, generateLeadershipBrief } from '../hooks/useApi';

export function LeadershipBrief({ activeScenarioId = 'SCN-06-COMPOUND', onNavigateBack }) {
  const [selectedScenarioId, setSelectedScenarioId] = useState(activeScenarioId);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const [error, setError] = useState(null);

  const demoScenarios = [
    { id: 'SCN-06-COMPOUND', num: '1', label: 'Scenario 1: Compound Drift' },
    { id: 'SCN-FLIP-HUMAN-CHANNEL', num: '2', label: 'Scenario 2: Human-Channel Risk' },
    { id: 'SCN-08-LOW-CONF-ABSTAIN', num: '3', label: 'Scenario 3: Out-of-Distribution Drift' },
  ];

  const loadBrief = async (scenarioId, forceFresh = false) => {
    if (forceFresh) {
      setRegenerating(true);
    } else {
      setLoading(true);
    }
    setError(null);
    try {
      const data = forceFresh
        ? await generateLeadershipBrief(scenarioId, true)
        : await fetchLeadershipBrief(scenarioId);
      setReport(data);
    } catch (err) {
      setError(err.message || 'Failed to load Leadership Incident Brief');
    } finally {
      setLoading(false);
      setRegenerating(false);
    }
  };

  useEffect(() => {
    loadBrief(selectedScenarioId, false);
  }, [selectedScenarioId]);

  const handleScenarioSwitch = (newId) => {
    if (newId === selectedScenarioId) return;
    setSelectedScenarioId(newId);
  };

  const handleRegenerate = () => {
    loadBrief(selectedScenarioId, true);
  };

  const getPillClass = (finalState) => {
    switch (finalState) {
      case 'VERIFIED_RECOVERY':
        return 'pill--lagoon';
      case 'QC_HOLD':
        return 'pill--violet';
      case 'ESCALATION_REQUIRED':
        return 'pill--wine';
      default:
        return 'pill--mist';
    }
  };

  const getNextActionClass = (finalState) => {
    switch (finalState) {
      case 'VERIFIED_RECOVERY':
        return 'next-action-card--recovery';
      case 'QC_HOLD':
        return 'next-action-card--qchold';
      case 'ESCALATION_REQUIRED':
        return 'next-action-card--escalate';
      default:
        return '';
    }
  };

  return (
    <div className="leadership-brief-canvas" role="region" aria-label="Leadership Incident Brief">
      {/* Top Bar: Navigation & Scenario Switcher */}
      <div className="brief-nav-bar">
        <div className="brief-nav-left">
          {onNavigateBack && (
            <button
              type="button"
              className="brief-back-btn"
              onClick={onNavigateBack}
              aria-label="Back to Decision Journey"
            >
              ← Back to Replay
            </button>
          )}
          <div className="brief-title-group">
            <span className="label-section" style={{ margin: 0 }}>Executive Operations Report</span>
            <h1 className="brief-main-title">Leadership Incident Brief</h1>
          </div>
        </div>

        {/* 3-Scenario Switcher for fast judging inspection */}
        <div className="brief-scenario-switcher" role="tablist" aria-label="Scenario Selection">
          {demoScenarios.map((s) => {
            const isSel = s.id === selectedScenarioId;
            return (
              <button
                key={s.id}
                type="button"
                role="tab"
                aria-selected={isSel}
                className={`brief-scenario-tab ${isSel ? 'brief-scenario-tab--active' : ''}`}
                onClick={() => handleScenarioSwitch(s.id)}
              >
                <span className="brief-tab-num">{s.num}</span>
                <span className="brief-tab-text">{s.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {loading && (
        <div className="brief-loading-state">
          <div className="brief-spinner" />
          <span>Generating validated leadership brief...</span>
        </div>
      )}

      {error && !loading && (
        <div className="brief-error-state card">
          <h3>Could not load leadership brief</h3>
          <p>{error}</p>
          <button type="button" className="btn-secondary" onClick={() => loadBrief(selectedScenarioId, false)}>
            Retry
          </button>
        </div>
      )}

      {report && !loading && (
        <div className="brief-content-wrapper">
          {/* SECTION 1: OUTCOME BANNER */}
          <div className="brief-outcome-banner card">
            <div className="banner-top-row">
              <div className="banner-meta">
                <span className="banner-category">{report.category}</span>
                <span className="banner-context">• Machine IMM-01 • Recipe RCP-12 • {report.display_title}</span>
              </div>
              <div className="banner-status-cluster">
                <span className={`pill ${getPillClass(report.final_state)}`}>
                  {report.final_state_label}
                </span>
                <button
                  type="button"
                  className="brief-refresh-ai-btn"
                  onClick={handleRegenerate}
                  disabled={regenerating}
                  title="Request structured summary from Gemini 3.8 Flash"
                >
                  {regenerating ? 'Analyzing...' : '✦ Gemini Summary'}
                </button>
              </div>
            </div>

            <div className="banner-headline-row">
              <h2 className="banner-headline editorial-title">“{report.headline}”</h2>
            </div>

            <div className="banner-bottom-row">
              <div className="banner-provenance">
                {report.leadership_takeaway.source === 'gemini-3.8-flash' ? (
                  <span className="provenance-tag provenance-tag--ai">
                    ✦ Executive Summary by Gemini 3.8 Flash (Structured Output)
                  </span>
                ) : (
                  <span className="provenance-tag provenance-tag--engine">
                    🔒 Ground-Truth Deterministic Summary (Validated Engine)
                  </span>
                )}
              </div>
              <div className="banner-disclaimer-pill">
                <span>Deterministic Decision Invariant SAFE-01 / SAFE-02 Enforced</span>
              </div>
            </div>
          </div>

          {/* SECTION 2: FOUR-STEP VISUAL STORY */}
          <div className="brief-story-section">
            <div className="section-header-row">
              <span className="label-section">Closed-Loop Incident Progression</span>
              <span className="section-subtext">Four-step operational lifecycle from early signal to verified state</span>
            </div>

            <div className="story-stepper-grid">
              {report.story_steps.map((step) => (
                <div key={step.step_num} className="story-step-card card">
                  <div className="story-step-header">
                    <div className="story-step-number">{step.step_num}</div>
                    <span className={`story-step-status-tag story-step-status-tag--${step.status.toLowerCase()}`}>
                      {step.status}
                    </span>
                  </div>
                  <h4 className="story-step-title">{step.title}</h4>
                  <div className="story-step-subtitle">{step.subtitle}</div>
                  <p className="story-step-detail">{step.detail}</p>
                </div>
              ))}
            </div>
          </div>

          {/* SECTION 3 & 4: TWO-COLUMN DECISION EVIDENCE & BUSINESS IMPACT */}
          <div className="brief-two-col-grid">
            {/* COLUMN LEFT: DECISION EVIDENCE */}
            <div className="brief-col card">
              <div className="card-section-title">
                <span className="label-section">Technical Decision Evidence</span>
                <h3>Triggered Signals & Root-Cause Attribution</h3>
              </div>

              {/* Physical Signals */}
              <div className="evidence-signals-group">
                <div className="subhead-label">Physical Telemetry & Ingestion Gates</div>
                <div className="signals-table">
                  {report.decision_evidence.triggered_signals.map((sig, idx) => (
                    <div key={idx} className="signal-row">
                      <div className="signal-row__left">
                        <span className="signal-name">{sig.label}</span>
                        <span className="signal-dev">{sig.deviation}</span>
                      </div>
                      <div className="signal-row__right">
                        <span className="signal-val num">
                          {typeof sig.value === 'number' ? sig.value : sig.value} {sig.unit !== 'text' && sig.unit !== 'score' ? sig.unit : ''}
                        </span>
                        <span className={`signal-status-pill signal-status-pill--${sig.status.toLowerCase()}`}>
                          {sig.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Root Cause Share */}
              <div className="evidence-rc-group">
                <div className="subhead-label">Rule-Based Root-Cause Contribution</div>
                <div className="rc-bars-wrapper">
                  {report.decision_evidence.root_cause_shares.map((rc, idx) => (
                    <div key={idx} className="rc-bar-item">
                      <div className="rc-bar-label-row">
                        <span>{rc.label}</span>
                        <span className="num font-semibold">{rc.percentage}%</span>
                      </div>
                      <div className="rc-bar-track">
                        <div
                          className="rc-bar-fill"
                          style={{ width: `${Math.min(100, rc.percentage)}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Action Traceability */}
              <div className="evidence-trace-group">
                <div className="subhead-label">Decision Traceability</div>
                <div className="trace-table">
                  <div className="trace-row">
                    <span className="trace-k">Recommended:</span>
                    <span className="trace-v">{report.decision_evidence.recommended_action}</span>
                  </div>
                  <div className="trace-row">
                    <span className="trace-k">Selected Action:</span>
                    <span className="trace-v">{report.decision_evidence.selected_action}</span>
                  </div>
                  <div className="trace-row">
                    <span className="trace-k">Quality Disposition:</span>
                    <span className="trace-v">{report.decision_evidence.quality_disposition}</span>
                  </div>
                  <div className="trace-row">
                    <span className="trace-k">Safety Invariant:</span>
                    <span className="trace-v font-mono">{report.decision_evidence.safety_justification}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* COLUMN RIGHT: BUSINESS IMPACT & BEFORE/AFTER */}
            <div className="brief-col card">
              <div className="card-section-title">
                <span className="label-section">Verified Operational & Financial Impact</span>
                <h3>Modeled Production Consequences</h3>
              </div>

              {/* 5 Impact Tiles */}
              <div className="impact-kpi-grid">
                <div className="impact-tile">
                  <span className="impact-tile__label">Detection Lead Time</span>
                  <div className="impact-tile__val num">
                    {report.business_impact.detection_lead_time_cycles}
                    <span className="impact-tile__unit">cycles</span>
                  </div>
                  <span className="impact-tile__sub">{report.business_impact.lead_time_description}</span>
                </div>

                <div className="impact-tile">
                  <span className="impact-tile__label">Suspect Parts Contained</span>
                  <div className="impact-tile__val num">
                    {report.business_impact.suspect_parts_contained}
                    <span className="impact-tile__unit">parts</span>
                  </div>
                  <span className="impact-tile__sub">
                    {report.business_impact.baseline_suspect_parts > 0
                      ? `${report.business_impact.suspect_reduction_pct}% smaller quarantine vs status quo (${report.business_impact.baseline_suspect_parts} parts)`
                      : 'Physical quarantine isolation'}
                  </span>
                </div>

                <div className="impact-tile">
                  <span className="impact-tile__label">Modeled Scrap Avoided</span>
                  <div className="impact-tile__val num text-lagoon">
                    {report.business_impact.modeled_scrap_avoided}
                    <span className="impact-tile__unit">parts</span>
                  </div>
                  <span className="impact-tile__sub">
                    {report.business_impact.modeled_scrap_avoided > 0
                      ? `Collapsed from ${report.business_impact.baseline_scrap_parts} parts to ${report.business_impact.actual_scrap_parts}`
                      : 'No speculative scrap savings claimed'}
                  </span>
                </div>

                <div className="impact-tile impact-tile--financial">
                  <span className="impact-tile__label">Modeled Cost Avoided</span>
                  <div className="impact-tile__val num text-savings">
                    {report.business_impact.modeled_cost_avoided_inr > 0 ? (
                      `₹${Math.round(report.business_impact.modeled_cost_avoided_inr).toLocaleString('en-IN')}`
                    ) : (
                      '₹0'
                    )}
                  </div>
                  <span className="impact-tile__sub">
                    {report.business_impact.modeled_cost_avoided_inr > 0
                      ? 'Net savings in direct scrap & sorting costs'
                      : 'Zero invented savings — risk avoided via containment'}
                  </span>
                </div>

                <div className="impact-tile impact-tile--wide">
                  <span className="impact-tile__label">Recovery Time / Operational Improvement</span>
                  <div className="impact-tile__text">
                    {report.business_impact.production_improvement}
                  </div>
                </div>
              </div>

              {/* Mandatory Financial Disclaimer Banner */}
              <div className="financial-disclaimer-banner">
                <span className="disclaimer-icon">⚠️</span>
                <span>{report.business_impact.disclaimer}</span>
              </div>

              {/* Before / After Divergence Canvas */}
              {report.divergence_points && report.divergence_points.length > 0 && (
                <div className="divergence-canvas-wrapper">
                  <div className="subhead-label">Trajectory Divergence — Status Quo vs Process Guardian</div>
                  <div className="divergence-comparison-bars">
                    <div className="comparison-bar-row">
                      <span className="comparison-label">Status Quo (Wide SPC)</span>
                      <div className="bar-track">
                        <div
                          className="bar-fill bar-fill--off"
                          style={{
                            width: `${Math.min(100, Math.max(10, (report.business_impact.baseline_scrap_parts / Math.max(1, report.business_impact.baseline_scrap_parts)) * 100))}%`
                          }}
                        />
                      </div>
                      <span className="comparison-val num font-semibold text-wine">
                        {report.business_impact.baseline_scrap_parts} scrap parts
                      </span>
                    </div>

                    <div className="comparison-bar-row">
                      <span className="comparison-label">Process Guardian</span>
                      <div className="bar-track">
                        <div
                          className="bar-fill bar-fill--on"
                          style={{
                            width: `${Math.min(100, Math.max(3, (report.business_impact.actual_scrap_parts / Math.max(1, report.business_impact.baseline_scrap_parts)) * 100))}%`
                          }}
                        />
                      </div>
                      <span className="comparison-val num font-semibold text-lagoon">
                        {report.business_impact.actual_scrap_parts} scrap parts
                      </span>
                    </div>
                  </div>
                  <div className="divergence-caption">
                    Divergence cycle: Intervention applied before defect threshold. Status quo ran to failure.
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* SECTION 5: LEADERSHIP TAKEAWAY (AI / ENGINE) */}
          <div className="brief-takeaway-card card">
            <div className="takeaway-header">
              <span className="label-section" style={{ margin: 0 }}>Executive Briefing Takeaway</span>
              <div className="takeaway-pill">
                {report.leadership_takeaway.source === 'gemini-3.8-flash' ? (
                  <span>✦ Gemini 3.8 Flash</span>
                ) : (
                  <span>🔒 Ground-Truth Verification</span>
                )}
              </div>
            </div>

            <div className="takeaway-body">
              <p className="takeaway-exec-summary">
                {report.leadership_takeaway.executive_summary}
              </p>
              <div className="takeaway-details-grid">
                <div className="takeaway-detail-box">
                  <span className="takeaway-detail-box__title">Decision Rationale</span>
                  <p>{report.leadership_takeaway.decision_rationale}</p>
                </div>
                <div className="takeaway-detail-box">
                  <span className="takeaway-detail-box__title">Impact Statement</span>
                  <p>{report.leadership_takeaway.impact_statement}</p>
                </div>
              </div>
            </div>
          </div>

          {/* SECTION 6: NEXT ACTION INDUSTRIAL DIRECTIVE */}
          <div className={`next-action-card card ${getNextActionClass(report.final_state)}`}>
            <div className="next-action-left">
              <span className="next-action-pill">MANDATED NEXT ACTION</span>
              <h3 className="next-action-title">{report.next_action}</h3>
              <p className="next-action-desc">{report.next_action_detail}</p>
            </div>
            <div className="next-action-right">
              <span className="next-action-badge">
                {report.final_state === 'VERIFIED_RECOVERY' && '✓ APPROVED FOR RELEASE'}
                {report.final_state === 'QC_HOLD' && '✋ MANDATORY LAB SIGN-OFF'}
                {report.final_state === 'ESCALATION_REQUIRED' && '⚡ MAINTENANCE ESCALATION'}
              </span>
            </div>
          </div>

          {/* SECTION 7: IMMUTABLE AUDIT TRAIL */}
          <div className="brief-audit-card card">
            <div className="audit-header">
              <div>
                <span className="label-section" style={{ margin: 0 }}>Traceability & Compliance</span>
                <h4>Immutable Audit Trail Snapshot</h4>
              </div>
              <span className="pill pill--stone font-mono">CRYPTOGRAPHIC RECORD</span>
            </div>

            <div className="audit-table-wrapper">
              <table className="audit-table">
                <thead>
                  <tr>
                    <th>Cycle</th>
                    <th>Timestamp</th>
                    <th>Actor / Authority</th>
                    <th>Operational Event</th>
                    <th>Integrity Hash</th>
                  </tr>
                </thead>
                <tbody>
                  {report.audit_trail.map((item, idx) => (
                    <tr key={idx}>
                      <td className="num font-semibold">{item.cycle}</td>
                      <td className="num font-mono">{item.timestamp}</td>
                      <td>
                        <span className="audit-actor-pill">{item.actor}</span>
                      </td>
                      <td className="audit-event-cell">{item.event}</td>
                      <td className="num font-mono audit-hash">{item.hash_digest}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default LeadershipBrief;

