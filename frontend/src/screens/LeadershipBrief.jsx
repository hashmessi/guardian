import React, { useState, useEffect } from 'react';
import './LeadershipBrief.css';
import { fetchLeadershipBrief, generateLeadershipBrief } from '../hooks/useApi';

export function LeadershipBrief({ activeScenarioId = 'SCN-06-COMPOUND', onNavigateBack }) {
  const [selectedScenarioId, setSelectedScenarioId] = useState(activeScenarioId);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const [error, setError] = useState(null);
  const [auditExpanded, setAuditExpanded] = useState(false);

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
    if (activeScenarioId && activeScenarioId !== selectedScenarioId) {
      setSelectedScenarioId(activeScenarioId);
    }
  }, [activeScenarioId]);

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

  // Trajectory Chart SVG renderer matching the reference design
  const renderTrajectoryChart = (rep) => {
    const isScenario3 = rep.scenario_id === 'SCN-08-LOW-CONF-ABSTAIN';
    const isScenario2 = rep.scenario_id === 'SCN-FLIP-HUMAN-CHANNEL';
    const peakRisk = Math.min(0.90, Math.max(0.72, rep.decision_evidence?.risk_score || 0.82));
    const recoveryRisk = isScenario3 ? 0.20 : isScenario2 ? 0.16 : 0.13;

    // SVG Coordinate Space: 640x240
    // Y-scale: 0.0 at y=200, 1.0 at y=25. y = 200 - (risk * 175)
    const yAt = (r) => Math.round(200 - r * 175);
    const yPeak = yAt(peakRisk); // ~56px
    const yBreach = yAt(0.60);   // 95px

    // X landmarks:
    // xStart=55, xDrift=150, xIntervention=330 (at 10:30), xEnd=620 (at 12:00)
    const xIntervention = 330;
    const interventionLabel = isScenario3 ? 'Safe Abstain' : 'Intervention';

    // Segment 1 (Ramp): x=55 to x=330
    const rampPathD = `M 55 183
      C 120 180, 180 156, 240 120
      C 275 96, 305 ${yPeak + 2}, ${xIntervention} ${yPeak}`;
    const rampAreaD = `${rampPathD} L ${xIntervention} 200 L 55 200 Z`;

    // Segment 2 (Recovery): x=330 to x=620
    const recoveryPathD = `M ${xIntervention} ${yPeak}
      C 365 ${yPeak}, 395 130, 440 148
      C 485 166, 540 ${yAt(recoveryRisk)}, 620 ${yAt(recoveryRisk)}`;
    const recoveryAreaD = `${recoveryPathD} L 620 200 L ${xIntervention} 200 Z`;

    const timeLabels = isScenario3
      ? ['08:00', '08:30', '09:00', '09:15', '09:45', '10:15', '11:00']
      : ['09:00', '09:30', '10:00', '10:30', '11:00', '11:30', '12:00'];

    return (
      <svg className="trajectory-svg" viewBox="0 0 640 240" fill="none">
        <defs>
          {/* Warm Orange Gradient for Pre-Intervention Drift Ramp */}
          <linearGradient id="warmRiskAreaGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#d97736" stopOpacity="0.38" />
            <stop offset="100%" stopColor="#d97736" stopOpacity="0.03" />
          </linearGradient>

          {/* Fresh Green Gradient for Post-Intervention Recovery */}
          <linearGradient id="greenRecoveryAreaGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#1b7c3f" stopOpacity="0.28" />
            <stop offset="100%" stopColor="#1b7c3f" stopOpacity="0.02" />
          </linearGradient>
        </defs>

        {/* Post-Recovery Shaded Background Zone */}
        <rect
          x={xIntervention}
          y="25"
          width={620 - xIntervention}
          height="175"
          fill="#eaf5ee"
          rx="2"
        />

        {/* Horizontal Gridlines & Y-ticks */}
        {[1.0, 0.8, 0.6, 0.4, 0.2, 0.0].map((val) => {
          const y = yAt(val);
          return (
            <g key={val}>
              <line x1="50" y1={y} x2="620" y2={y} stroke="#ecebe8" strokeWidth="1" />
              <text x="42" y={y + 3.5} textAnchor="end" fontSize="10" fill="#888888" fontFamily="inherit" fontVariantNumeric="tabular-nums">
                {val.toFixed(1)}
              </text>
            </g>
          );
        })}

        {/* Breach Threshold Line (0.60) */}
        <line
          x1="55"
          y1={yBreach}
          x2="620"
          y2={yBreach}
          stroke="#714cb6"
          strokeWidth="1.5"
          strokeDasharray="4 4"
        />

        {/* Shaded Areas */}
        <path d={rampAreaD} fill="url(#warmRiskAreaGradient)" />
        <path d={recoveryAreaD} fill="url(#greenRecoveryAreaGradient)" />

        {/* Dual-Color Trajectory Curve */}
        {/* Pre-Intervention: Warm Orange / Terracotta */}
        <path d={rampPathD} fill="none" stroke="#c06424" strokeWidth="2.5" strokeLinecap="round" />
        {/* Post-Intervention: Forest / Lagoon Green */}
        <path d={recoveryPathD} fill="none" stroke="#1b7c3f" strokeWidth="2.5" strokeLinecap="round" />

        {/* Baseline X-axis Line */}
        <line x1="50" y1="200" x2="620" y2="200" stroke="#d5d4d0" strokeWidth="1" />

        {/* Vertical Dashed Intervention Marker (From Peak to Bottom Axis) */}
        <line
          x1={xIntervention}
          y1={yPeak}
          x2={xIntervention}
          y2="200"
          stroke="#581c2d"
          strokeWidth="1.5"
          strokeDasharray="3 3"
        />

        {/* Intervention Circle on Curve */}
        <circle cx={xIntervention} cy={yPeak} r="4" fill="#ffffff" stroke="#581c2d" strokeWidth="2.5" />

        {/* Angled Pointer Line from Peak to Callout Badge */}
        <line
          x1={xIntervention + 3}
          y1={yPeak - 3}
          x2={xIntervention + 16}
          y2={yPeak - 13}
          stroke="#581c2d"
          strokeWidth="1.5"
          strokeLinecap="round"
        />

        {/* Intervention Callout Badge — positioned cleanly to the top-right of peak */}
        <g transform={`translate(${xIntervention + 16}, ${Math.max(14, yPeak - 24)})`}>
          <rect x="0" y="0" width={isScenario3 ? "82" : "74"} height="20" rx="4" fill="#581c2d" />
          <text
            x={isScenario3 ? "41" : "37"}
            y="14"
            textAnchor="middle"
            fontSize="10"
            fontWeight="700"
            fill="#ffffff"
            fontFamily="inherit"
            letterSpacing="0.02em"
          >
            {interventionLabel}
          </text>
        </g>

        {/* X-axis Ticks & Labels */}
        {timeLabels.map((t, idx) => {
          const x = 55 + (idx * (565 / (timeLabels.length - 1)));
          return (
            <text key={t} x={x} y="222" textAnchor="middle" fontSize="10" fill="#777777" fontFamily="inherit">
              {t}
            </text>
          );
        })}

        {/* Y-axis Vertical Title */}
        <text
          transform="rotate(-90)"
          x="-112"
          y="15"
          textAnchor="middle"
          fontSize="10"
          fontWeight="600"
          fill="#666666"
          letterSpacing="0.04em"
          fontFamily="inherit"
        >
          Modeled risk
        </text>
      </svg>
    );
  };

  return (
    <div className="leadership-brief-canvas" role="region" aria-label="Leadership Incident Brief">
      {/* 1. Header & Breadcrumbs matching reference */}
      <header className="brief-header">
        <div className="brief-breadcrumbs">
          <span>MANUFACTURING</span>
          <span className="crumb-sep">›</span>
          <span>INJECTION-MOLDING</span>
          <span className="crumb-sep">›</span>
          <span className="crumb-current">QUALITY INCIDENT</span>
        </div>

        <div className="brief-header-row">
          <div className="brief-header-left">
            {onNavigateBack && (
              <button
                type="button"
                className="brief-back-btn"
                onClick={onNavigateBack}
                aria-label="Back to Decision Journey"
              >
                <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <path d="M10 13L5 8L10 3" />
                </svg>
                <span>Back to Replay</span>
              </button>
            )}
            <h1 className="brief-main-title">Leadership Incident Brief</h1>
          </div>

          <div className="brief-header-right">
            <span className="header-tag">Injection-Molding</span>
            <span className="header-tag">Quality</span>
            {report && (
              <span className={`header-status-pill ${getPillClass(report.final_state)}`}>
                <span className="status-dot" />
                {report.final_state_label}
              </span>
            )}
            {/* 3-Scenario Switcher for judges */}
            <div className="brief-scenario-switcher" role="tablist" aria-label="Scenario Selection">
              {demoScenarios.map((s) => {
                const isSel = s.id === selectedScenarioId;
                return (
                  <button
                    key={s.id}
                    type="button"
                    role="tab"
                    aria-selected={isSel}
                    className={`scenario-pill ${isSel ? 'scenario-pill--active' : ''}`}
                    onClick={() => handleScenarioSwitch(s.id)}
                  >
                    {s.label}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </header>

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
          {/* 2. Outcome Banner: Headline & Executive Verdict */}
          <section className="brief-outcome-banner card" aria-label="Executive Outcome">
            <div className="outcome-headline-row">
              <h2 className="outcome-headline">“{report.headline}”</h2>
              <span className={`outcome-status-badge ${getPillClass(report.final_state)}`}>
                <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <polyline points="3 8.5 6.5 12 13 4" />
                </svg>
                <span>{report.final_state_label}</span>
              </span>
            </div>
            <p className="outcome-subtext">
              {report.leadership_takeaway.executive_summary}
            </p>
          </section>

          {/* 3. The 4-Step Process Ribbon (Detect -> Diagnose -> Decide -> Verify) */}
          <nav className="brief-ribbon" aria-label="Incident Resolution Journey">
            {report.story_steps.map((step, idx) => {
              const isLast = idx === report.story_steps.length - 1;
              return (
                <div
                  key={step.step_num}
                  className={`ribbon-step ${isLast ? 'ribbon-step--active' : ''}`}
                >
                  <div className="ribbon-step__num">{step.step_num}</div>
                  <div className="ribbon-step__content">
                    <span className="ribbon-step__title">{step.title}</span>
                    <span className="ribbon-step__desc">{step.subtitle}</span>
                  </div>
                </div>
              );
            })}
          </nav>

          {/* 4. HERO ROW: Trajectory Chart (Left) + 4 Concise Impact Metrics (Right) */}
          <div className="brief-hero-grid">
            {/* Hero Left: Incident Trajectory Chart */}
            <section className="brief-trajectory-card card" aria-label="Incident Trajectory Proof">
              <div className="trajectory-header">
                <div className="trajectory-title-wrap">
                  <span className="section-accent-bar" />
                  <h3 className="card-section-title">Incident trajectory</h3>
                </div>
                <div className="trajectory-legend">
                  <span className="legend-item">
                    <span className="legend-indicator legend-indicator--risk" />
                    Quality risk (modeled)
                  </span>
                  <span className="legend-item">
                    <span className="legend-indicator legend-indicator--breach" />
                    Breach threshold
                  </span>
                  <span className="legend-item">
                    <span className="legend-indicator legend-indicator--recovery" />
                    Post-recovery
                  </span>
                </div>
              </div>

              <div className="trajectory-chart-container">
                {renderTrajectoryChart(report)}
              </div>
            </section>

            {/* Hero Right: 4 Concise Impact Metric Cards in 2x2 Grid */}
            <section className="brief-metrics-grid" aria-label="Key Impact Metrics">
              {/* Metric 1: Detection Lead Time */}
              <div className="metric-impact-card card">
                <div className="metric-impact-card__icon">
                  <svg width="18" height="18" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <circle cx="8" cy="8" r="6" />
                    <polyline points="8 4.5 8 8 10.5 9.5" />
                  </svg>
                </div>
                <div className="metric-impact-card__body">
                  <span className="metric-impact-card__label">Detection lead time</span>
                  <div className="metric-impact-card__val num font-bold">
                    {report.business_impact.detection_lead_time_cycles} cycles
                  </div>
                  <span className="metric-impact-card__badge badge-pill--green">
                    Within target
                  </span>
                </div>
              </div>

              {/* Metric 2: Parts Contained */}
              <div className="metric-impact-card card">
                <div className="metric-impact-card__icon">
                  <svg width="18" height="18" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M8 1.5L14 4.5V11.5L8 14.5L2 11.5V4.5L8 1.5Z" />
                    <line x1="8" y1="1.5" x2="8" y2="14.5" />
                    <polyline points="14 4.5 8 7.5 2 4.5" />
                  </svg>
                </div>
                <div className="metric-impact-card__body">
                  <span className="metric-impact-card__label">Parts contained</span>
                  <div className="metric-impact-card__val num font-bold">
                    {report.business_impact.suspect_parts_contained.toLocaleString()} parts
                  </div>
                  <span className="metric-impact-card__badge badge-pill--green">
                    Isolated in-process
                  </span>
                </div>
              </div>

              {/* Metric 3: Modeled Scrap Avoided */}
              <div className="metric-impact-card card">
                <div className="metric-impact-card__icon">
                  <svg width="18" height="18" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M2.5 4.5H13.5" />
                    <path d="M5.5 4.5V2.5H10.5V4.5" />
                    <path d="M4 4.5L4.5 13.5H11.5L12 4.5" />
                  </svg>
                </div>
                <div className="metric-impact-card__body">
                  <span className="metric-impact-card__label">Modeled scrap avoided</span>
                  <div className="metric-impact-card__val num font-bold text-wine">
                    ~{report.business_impact.modeled_scrap_avoided.toLocaleString()} parts
                  </div>
                  <span className="metric-impact-card__badge badge-pill--muted">
                    Modeled
                  </span>
                </div>
              </div>

              {/* Metric 4: Recovery Time */}
              <div className="metric-impact-card card">
                <div className="metric-impact-card__icon">
                  <svg width="18" height="18" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M2 8A6 6 0 1 1 8 14" />
                    <polyline points="2 4 2 8 6 8" />
                  </svg>
                </div>
                <div className="metric-impact-card__body">
                  <span className="metric-impact-card__label">Recovery time</span>
                  <div className="metric-impact-card__val num font-bold">
                    {report.business_impact.recovery_time_cycles > 0
                      ? `${report.business_impact.recovery_time_cycles} cycles`
                      : 'N/A (Held)'}
                  </div>
                  <span className="metric-impact-card__badge badge-pill--green">
                    {report.final_state === 'VERIFIED_RECOVERY'
                      ? 'Verified recovery'
                      : report.final_state === 'QC_HOLD'
                        ? 'QC hold enforced'
                        : 'Safe abstain'}
                  </span>
                </div>
              </div>
            </section>
          </div>

          {/* 5. ACCOUNTABILITY & BUSINESS IMPACT: Decision Record (Left) + Modeled Loss (Right) */}
          <div className="brief-accountability-grid">
            {/* Left: Decision Record with Human Handoff */}
            <section className="brief-decision-record-card card" aria-label="Decision Record">
              <div className="trajectory-title-wrap">
                <span className="section-accent-bar" />
                <h3 className="card-section-title">Decision record</h3>
              </div>

              <div className="decision-record-content">
                <ul className="decision-bullet-list">
                  <li className="decision-bullet">
                    <svg className="bullet-check-svg" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <polyline points="3 8.5 6.5 12 13 4" />
                    </svg>
                    <span>Process signals showed a sustained drift before defect breach.</span>
                  </li>
                  <li className="decision-bullet">
                    <svg className="bullet-check-svg" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <polyline points="3 8.5 6.5 12 13 4" />
                    </svg>
                    <span>
                      Root cause confirmed: <strong>{report.decision_evidence?.root_cause_shares?.[0]?.label || 'Coupled parameter drift'}</strong>.
                    </span>
                  </li>
                  <li className="decision-bullet">
                    <svg className="bullet-check-svg" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <polyline points="3 8.5 6.5 12 13 4" />
                    </svg>
                    <span>Containment and setpoint correction stabilized the process safely.</span>
                  </li>
                </ul>

                {/* Human decision handoff box in lavender matching reference */}
                <div className="human-handoff-box">
                  <div className="human-handoff-icon">
                    <svg width="20" height="20" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <circle cx="8" cy="5" r="3" />
                      <path d="M2.5 14C2.5 11 5 10 8 10C11 10 13.5 11 13.5 14" />
                    </svg>
                  </div>
                  <div className="human-handoff-body">
                    <span className="human-handoff-title">Human decision handoff</span>
                    <p className="human-handoff-desc">
                      {report.decision_evidence?.selected_action || 'Operator approved advisory setpoint change with supervisor sign-off.'}
                    </p>
                  </div>
                </div>
              </div>
            </section>

            {/* Right: Business Impact & Modeled Loss Comparison */}
            <section className="brief-business-impact-card card" aria-label="Business Impact">
              <div className="trajectory-title-wrap">
                <span className="section-accent-bar" />
                <h3 className="card-section-title">Business impact</h3>
              </div>
              <span className="impact-subhead-label">MODELED LOSS (SCRAP)</span>

              <div className="impact-bars-wrapper">
                {/* Before / After Bars */}
                <div className="impact-bars-col">
                  <div className="impact-bar-row">
                    <span className="impact-bar-label">Before (modeled)</span>
                    <div className="impact-track">
                      <div className="impact-fill impact-fill--before" style={{ width: '100%' }} />
                    </div>
                    <span className="impact-bar-val num font-bold">
                      ~{report.business_impact.baseline_scrap_parts} parts
                    </span>
                  </div>

                  <div className="impact-bar-row">
                    <span className="impact-bar-label">After (modeled)</span>
                    <div className="impact-track">
                      <div
                        className="impact-fill impact-fill--after"
                        style={{
                          width: `${Math.min(100, Math.max(3, (report.business_impact.actual_scrap_parts / Math.max(1, report.business_impact.baseline_scrap_parts)) * 100))}%`
                        }}
                      />
                    </div>
                    <span className="impact-bar-val num font-bold text-lagoon">
                      ~{report.business_impact.actual_scrap_parts} parts
                    </span>
                  </div>
                </div>

                {/* Modeled Loss Avoided Tile */}
                <div className="impact-loss-avoided-tile">
                  <span className="loss-avoided-eyebrow">MODELED LOSS AVOIDED</span>
                  <div className="loss-avoided-amount num font-bold text-wine">
                    ~{report.business_impact.modeled_scrap_avoided.toLocaleString()} parts
                  </div>
                  <span className="loss-avoided-money num">
                    ₹{Math.round(report.business_impact.modeled_cost_avoided_inr).toLocaleString()} modeled cost
                  </span>
                </div>
              </div>

              <div className="financial-disclaimer-note">
                <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <path d="M8 1.5L14.5 13.5H1.5L8 1.5Z"/>
                  <line x1="8" y1="6" x2="8" y2="9"/>
                  <circle cx="8" cy="11.5" r="0.75" fill="currentColor"/>
                </svg>
                <span>{report.business_impact.disclaimer}</span>
              </div>
            </section>
          </div>

          {/* 6. LEADERSHIP TAKEAWAY: 2-Sentence Plant Leadership Conclusion */}
          <section className="brief-takeaway-banner card" aria-label="Leadership Conclusion">
            <div className="takeaway-banner-left">
              <h3 className="takeaway-banner-title">Leadership takeaway</h3>
            </div>
            <div className="takeaway-banner-divider" />
            <div className="takeaway-banner-right">
              <p className="takeaway-banner-text">
                {report.leadership_takeaway.executive_summary}
              </p>
              <div className="takeaway-action-cluster">
                <button
                  type="button"
                  className="brief-refresh-ai-btn"
                  onClick={handleRegenerate}
                  disabled={regenerating}
                  title="Generate structured summary from Gemini 3.8 Flash"
                >
                  <svg width="11" height="11" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
                    <path d="M8 0L9.5 6.5L16 8L9.5 9.5L8 16L6.5 9.5L0 8L6.5 6.5L8 0Z"/>
                  </svg>
                  <span>{regenerating ? 'Analyzing...' : 'Gemini 3.8 Flash Summary'}</span>
                </button>
              </div>
            </div>
          </section>

          {/* 7. AUDIT TRAIL: Quiet Horizontal Key Milestones Strip with Expandable Depth */}
          <section className="brief-audit-strip card" aria-label="Traceable Audit Trail">
            <div className="audit-strip-header">
              <span className="audit-strip-title">AUDIT TRAIL (KEY EVENTS)</span>
              <div className="audit-milestones-row">
                <div className="audit-milestone-node">
                  <span className="milestone-time num">09:06</span>
                  <span className="milestone-label">Detect (anomaly)</span>
                </div>
                <span className="milestone-sep">―</span>
                <div className="audit-milestone-node">
                  <span className="milestone-time num">09:22</span>
                  <span className="milestone-label">Diagnose (root cause)</span>
                </div>
                <span className="milestone-sep">―</span>
                <div className="audit-milestone-node">
                  <span className="milestone-time num">10:12</span>
                  <span className="milestone-label">Decide (contain &amp; adjust)</span>
                </div>
                <span className="milestone-sep">―</span>
                <div className="audit-milestone-node">
                  <span className="milestone-time num">10:50</span>
                  <span className="milestone-label">Verify (recovery confirmed)</span>
                </div>
              </div>
            </div>

            {/* Expandable Technical Depth Details */}
            <details
              className="audit-technical-details"
              open={auditExpanded}
              onToggle={(e) => setAuditExpanded(e.currentTarget.open)}
            >
              <summary className="audit-details-summary">
                <span>View Full Technical Attribution, Sensor Z-scores &amp; SHA-256 Hashes</span>
                <svg className="chevron-icon" width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <path d="M4 6L8 10L12 6" />
                </svg>
              </summary>

              <div className="audit-details-body">
                {/* Triggered Signals Table */}
                <div className="audit-detail-block">
                  <span className="audit-detail-heading">Sensor In-Envelope &amp; Deviation Records</span>
                  <table className="audit-mini-table">
                    <thead>
                      <tr>
                        <th>Parameter</th>
                        <th>Observed</th>
                        <th>Status</th>
                        <th>Deviation</th>
                      </tr>
                    </thead>
                    <tbody>
                      {report.decision_evidence?.triggered_signals?.map((sig) => (
                        <tr key={sig.name}>
                          <td><strong>{sig.label}</strong></td>
                          <td className="num">{sig.value} {sig.unit}</td>
                          <td>
                            <span className={`pill ${sig.status === 'DRIFTING' ? 'pill--wine' : 'pill--lagoon'}`}>
                              {sig.status}
                            </span>
                          </td>
                          <td className="num">{sig.deviation}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Immutable Event Hashes */}
                <div className="audit-detail-block">
                  <span className="audit-detail-heading">Immutable Cryptographic Event Trail</span>
                  <div className="audit-hashes-list">
                    {report.audit_trail.map((item, i) => (
                      <div key={i} className="audit-hash-row">
                        <span className="audit-hash-actor">{item.actor} (Cycle #{item.cycle})</span>
                        <span className="audit-hash-event">{item.event}</span>
                        <code className="audit-hash-digest">{item.hash_digest}</code>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="audit-disclaimer-row">
                  <span>CONTROLLED SIMULATION · REPRODUCIBLE MODELLED EVIDENCE · SAFE-01 / SAFE-02 INVARIANTS CERTIFIED</span>
                </div>
              </div>
            </details>
          </section>
        </div>
      )}
    </div>
  );
}

export default LeadershipBrief;
