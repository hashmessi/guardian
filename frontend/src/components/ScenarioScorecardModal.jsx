import React from 'react';
import './ScenarioScorecardModal.css';

export function ScenarioScorecardModal({ isOpen, onClose, scorecard, scenarioTitle }) {
  if (!isOpen || !scorecard) return null;

  const pillars = [
    { key: 'detection', label: '1. Early Drift Detection', data: scorecard.detection },
    { key: 'diagnosis', label: '2. Root Cause Isolation', data: scorecard.diagnosis },
    { key: 'intervention', label: '3. Constrained Intervention', data: scorecard.intervention },
    { key: 'recovery', label: '4. Recovery Verification', data: scorecard.recovery },
    { key: 'containment', label: '5. Scrap Containment', data: scorecard.containment },
    { key: 'counterfactual_proof', label: '6. Counterfactual Causality', data: scorecard.counterfactual_proof },
  ];

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="scenario-scorecard-modal" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="scorecard-header">
          <div className="scorecard-header-left">
            <span className="scorecard-tag">OPERATIONAL EVIDENCE SCORECARD</span>
            <h2 className="scorecard-title">{scorecard.scenario_title || scenarioTitle}</h2>
          </div>
          <div className="scorecard-header-right">
            <span className={`status-pill ${scorecard.overall_passed ? 'status-pill--pass' : 'status-pill--fail'}`}>
              {scorecard.overall_passed ? '✓ 7/7 PILLARS PASSED' : '⚠ VERIFICATION FAILED'}
            </span>
            <button className="scorecard-close-btn" onClick={onClose} aria-label="Close">✕</button>
          </div>
        </div>

        {/* Replay Context Subtitle */}
        <div className="scorecard-meta-bar">
          <span>Deterministic Seed Replay · {scorecard.total_cycles} Production Cycles</span>
          <span className="scorecard-category-badge">{scorecard.category?.toUpperCase()} REGIME</span>
        </div>

        {/* 7 Pillars Checklist */}
        <div className="scorecard-pillars-grid">
          {pillars.map((pillar) => (
            <div key={pillar.key} className={`pillar-card ${pillar.data?.passed ? 'pillar-card--pass' : 'pillar-card--fail'}`}>
              <div className="pillar-top">
                <span className="pillar-label">{pillar.label}</span>
                <span className={`pillar-badge ${pillar.data?.passed ? 'pillar-badge--pass' : 'pillar-badge--fail'}`}>
                  {pillar.data?.passed ? '✓ PASSED' : '✗ FAILED'}
                </span>
              </div>
              <div className="pillar-status-code">{pillar.data?.status_label}</div>
              <p className="pillar-detail">{pillar.data?.detail}</p>
              {pillar.data?.metrics && Object.keys(pillar.data.metrics).length > 0 && (
                <div className="pillar-metrics">
                  {Object.entries(pillar.data.metrics).map(([k, v]) => (
                    <span key={k} className="metric-chip">
                      <strong>{k.replace(/_/g, ' ')}:</strong> {typeof v === 'boolean' ? (v ? 'Yes' : 'No') : String(v)}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Honest Epistemic Disclaimer */}
        <div className="scorecard-disclaimer">
          <span className="disclaimer-badge">HONEST EPISTEMIC DECLARATION (SAFE-04)</span>
          <p>{scorecard.disclaimer || 'CONTROLLED SIMULATION · REPRODUCIBLE MODELLED EVIDENCE'}</p>
        </div>

        {/* Footer */}
        <div className="scorecard-footer">
          <span className="scorecard-summary-text">{scorecard.summary}</span>
          <button className="scorecard-action-btn" onClick={onClose}>CLOSE SCORECARD</button>
        </div>
      </div>
    </div>
  );
}
