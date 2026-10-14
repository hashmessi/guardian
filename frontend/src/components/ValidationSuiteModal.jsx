import React, { useState, useEffect } from 'react';
import './ValidationSuiteModal.css';
import { fetchValidationSuite } from '../hooks/useApi';

export function ValidationSuiteModal({ isOpen, onClose, onSelectScenario }) {
  const [suiteData, setSuiteData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadSuite = async (fresh = false) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchValidationSuite(fresh);
      setSuiteData(data);
    } catch (err) {
      setError(err.message || 'Failed to execute validation suite');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadSuite(false);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const metrics = suiteData?.metrics || {};
  const scorecards = suiteData?.scorecards || [];

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="validation-suite-modal" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="suite-header">
          <div className="suite-header-left">
            <span className="suite-tag">OPERATIONAL VALIDATION SUITE</span>
            <h2 className="suite-title">Automotive PS02 Multi-Scenario Decision Proof</h2>
          </div>
          <div className="suite-header-right">
            <button
              className="suite-rerun-btn"
              onClick={() => loadSuite(true)}
              disabled={loading}
              title="Re-execute every scenario in sequence"
            >
              {loading ? 'RUNNING…' : '↺ RE-RUN ALL'}
            </button>
            <button className="suite-close-btn" onClick={onClose} aria-label="Close">✕</button>
          </div>
        </div>

        {/* Loading Indicator */}
        {loading && (
          <div className="suite-loading-banner">
            <span className="suite-spinner" />
            <span>Executing deterministic 11-scenario validation pipeline...</span>
          </div>
        )}

        {/* Error Banner */}
        {error && <div className="suite-error-banner">Error: {error}</div>}

        {/* Summary Metric Ribbon */}
        {suiteData && (
          <div className="suite-kpi-ribbon">
            <div className="kpi-box">
              <span className="kpi-num highlight-cyan num">
                {metrics.total_scenarios_passed} / {metrics.total_scenarios_evaluated}
              </span>
              <span className="kpi-lbl">Scenarios Passed</span>
            </div>
            <div className="kpi-box">
              <span className="kpi-num highlight-green num">
                {metrics.correct_detection_rate_pct}%
              </span>
              <span className="kpi-lbl">Correct Detection</span>
            </div>
            <div className="kpi-box">
              <span className="kpi-num highlight-amber num">
                {metrics.false_intervention_rate_pct}%
              </span>
              <span className="kpi-lbl">False Interventions</span>
            </div>
            <div className="kpi-box">
              <span className="kpi-num highlight-green num">
                {metrics.recovery_verification_rate_pct}%
              </span>
              <span className="kpi-lbl">Recovery Verified</span>
            </div>
            <div className="kpi-box">
              <span className="kpi-num highlight-indigo num">
                {metrics.containment_correctness_pct}%
              </span>
              <span className="kpi-lbl">Containment Correct</span>
            </div>
            <div className="kpi-box">
              <span className="kpi-num highlight-purple num">
                {metrics.unsafe_release_prevention_pct}%
              </span>
              <span className="kpi-lbl">Unsafe Release Blocked</span>
            </div>
          </div>
        )}

        {/* Scenario results */}
        <div className="suite-table-container">
          <table className="suite-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Scenario Title</th>
                <th>Category</th>
                <th>Detection</th>
                <th>Intervention</th>
                <th>Recovery</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {scorecards.map((sc) => (
                <tr key={sc.scenario_id} className={sc.overall_passed ? 'row-pass' : 'row-fail'}>
                  <td className="num id-cell">{sc.scenario_id}</td>
                  <td className="title-cell">
                    <strong>{sc.scenario_title}</strong>
                  </td>
                  <td>
                    <span className="cat-chip">{sc.category?.toUpperCase()}</span>
                  </td>
                  <td>
                    <span className={`cell-tag ${sc.detection?.passed ? 'cell-tag--pass' : 'cell-tag--fail'}`}>
                      {sc.detection?.passed ? '✓ Confirmed' : '✗ Failed'}
                    </span>
                  </td>
                  <td>
                    <span className={`cell-tag ${sc.intervention?.passed ? 'cell-tag--pass' : 'cell-tag--fail'}`}>
                      {sc.intervention?.passed ? '✓ Optimized' : '✗ Failed'}
                    </span>
                  </td>
                  <td>
                    <span className={`cell-tag ${sc.recovery?.passed ? 'cell-tag--pass' : 'cell-tag--fail'}`}>
                      {sc.recovery?.passed ? '✓ Verified' : '✗ Failed'}
                    </span>
                  </td>
                  <td>
                    <span className={`badge-pill ${sc.overall_passed ? 'badge-pill--pass' : 'badge-pill--fail'}`}>
                      {sc.overall_passed ? 'PASSED' : 'FAILED'}
                    </span>
                  </td>
                  <td>
                    <button
                      className="load-scn-btn"
                      onClick={() => {
                        if (onSelectScenario) {
                          onSelectScenario(sc.scenario_id);
                          onClose();
                        }
                      }}
                      title="Load and replay this scenario on the main operational dashboard"
                    >
                      LOAD REPLAY
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Epistemic Honesty Disclosure */}
        <div className="suite-disclaimer-box">
          <span className="disclaimer-title">AUTOMOTIVE EVALUATION EVIDENCE STANDARD (SAFE-04)</span>
          <p>{suiteData?.disclaimer}</p>
        </div>

        {/* Footer */}
        <div className="suite-footer">
          <span className="suite-footer-summary">
            {`Every scenario replayed through the same engine under a fixed seed${
              report?.metrics?.total_scenarios_evaluated
                ? ` (${report.metrics.total_scenarios_passed}/${report.metrics.total_scenarios_evaluated} passing)`
                : ''
            }.`}
          </span>
          <button className="suite-close-action-btn" onClick={onClose}>CLOSE SUITE</button>
        </div>
      </div>
    </div>
  );
}
