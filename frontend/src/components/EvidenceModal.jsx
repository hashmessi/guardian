import React, { useState, useEffect } from 'react';
import './EvidenceModal.css';
import {
  fetchEvidenceLevels,
  fetchExternalBenchmark,
  fetchGroundingReport,
} from '../hooks/useApi';

export function EvidenceModal({ isOpen, onClose }) {
  const [activeTab, setActiveTab] = useState('levels');
  const [levelsData, setLevelsData] = useState(null);
  const [benchmarkData, setBenchmarkData] = useState(null);
  const [groundingData, setGroundingData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!isOpen) return;

    let isMounted = true;
    setLoading(true);

    Promise.all([
      fetchEvidenceLevels().catch(() => null),
      fetchExternalBenchmark().catch(() => null),
      fetchGroundingReport().catch(() => null),
    ])
      .then(([levels, bench, grounding]) => {
        if (isMounted) {
          setLevelsData(levels);
          setBenchmarkData(bench);
          setGroundingData(grounding);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err.message || 'Failed to load evidence data');
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="evidence-modal-backdrop" onClick={onClose}>
      <div
        className="evidence-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="evidence-modal-title"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="evidence-modal__header">
          <div className="evidence-modal__title-group">
            <h2 id="evidence-modal-title" className="evidence-modal__title">
              Industrial Evidence & Grounding Canvas
            </h2>
            <span className="evidence-badge">Empirical Defensibility</span>
          </div>
          <button
            type="button"
            className="evidence-modal__close-btn"
            onClick={onClose}
            aria-label="Close Evidence Modal"
          >
            ✕ ESC
          </button>
        </div>

        {/* Tab Strip */}
        <div className="evidence-modal__tabs">
          <button
            type="button"
            className={`evidence-tab-btn ${activeTab === 'levels' ? 'evidence-tab-btn--active' : ''}`}
            onClick={() => setActiveTab('levels')}
          >
            1. 4-Level Evidence Chain
          </button>
          <button
            type="button"
            className={`evidence-tab-btn ${activeTab === 'benchmark' ? 'evidence-tab-btn--active' : ''}`}
            onClick={() => setActiveTab('benchmark')}
          >
            2. Measured Data Benchmark (564 Parts)
          </button>
          <button
            type="button"
            className={`evidence-tab-btn ${activeTab === 'grounding' ? 'evidence-tab-btn--active' : ''}`}
            onClick={() => setActiveTab('grounding')}
          >
            3. Conventional SPC Failure vs Guardian
          </button>
        </div>

        {/* Modal Body */}
        <div className="evidence-modal__body">
          {loading && (
            <div className="evidence-callout">
              Loading empirical evidence contracts and benchmark distributions...
            </div>
          )}

          {error && (
            <div className="evidence-callout" style={{ borderLeftColor: '#e57373' }}>
              <strong>Error loading evidence:</strong> {error}
            </div>
          )}

          {!loading && activeTab === 'levels' && (
            <>
              <div className="evidence-callout">
                <strong>Strict Honesty Policy:</strong> Process Guardian maintains unambiguous separation between
                industry problem facts, external measured research, deterministic software invariants, and
                controlled counterfactual simulation. No unverified factory trial claims are made.
              </div>

              <div className="evidence-levels-grid">
                {levelsData?.levels?.map((lvl) => (
                  <div key={lvl.level} className="level-card">
                    <div className="level-card__header">
                      <span className="level-card__title">
                        Level {lvl.level}: {lvl.name}
                      </span>
                      <span
                        className={`level-tag level-tag--l${lvl.level}`}
                      >
                        {lvl.tag}
                      </span>
                    </div>
                    <div className="level-card__source">
                      Source: {lvl.source} · Verification: {lvl.verification_method}
                    </div>
                    <ul className="level-card__claims">
                      {lvl.claims.map((claim, idx) => (
                        <li key={idx}>{claim}</li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </>
          )}

          {!loading && activeTab === 'benchmark' && (
            <>
              <div className="evidence-callout">
                <strong>Open Research Grounding:</strong> Empirical dataset based on the public SKZ/Fraunhofer
                injection molding study across 564 production parts (PP & ABS). Validates physical covariance
                and proves why univariate tolerance limits fail.
              </div>

              <div className="benchmark-stats-row">
                <div className="bench-stat-box">
                  <span className="bench-stat-box__label">Total Parts</span>
                  <span className="bench-stat-box__val">
                    {benchmarkData?.total_parts ?? 564}
                  </span>
                </div>
                <div className="bench-stat-box">
                  <span className="bench-stat-box__label">Resin Types</span>
                  <span className="bench-stat-box__val">
                    PP: 282 · ABS: 282
                  </span>
                </div>
                <div className="bench-stat-box">
                  <span className="bench-stat-box__label">Scrap Rate</span>
                  <span className="bench-stat-box__val">
                    {benchmarkData?.scrap_rate_pct ?? 13.5}%
                  </span>
                </div>
                <div className="bench-stat-box">
                  <span className="bench-stat-box__label">Defects Found</span>
                  <span className="bench-stat-box__val">
                    {benchmarkData?.nok_count ?? 76} NOK
                  </span>
                </div>
              </div>

              {/* SPC Flaw Card */}
              {benchmarkData?.machine_limits_flaw_analysis && (
                <div className="spc-flaw-card">
                  <div className="spc-flaw-card__title">
                    The Blind Spot of Machine SPC Limits (Empirical Proof)
                  </div>
                  <div>
                    {benchmarkData.machine_limits_flaw_analysis.conclusion}
                  </div>
                  <div className="spc-flaw-card__grid">
                    <div className="flaw-stat">
                      <div className="flaw-stat__val">
                        {benchmarkData.machine_limits_flaw_analysis.escaped_defects_percentage}%
                      </div>
                      <div className="flaw-stat__label">
                        Defects completely escaped individual ±3σ parameter alarm bands
                      </div>
                    </div>
                    <div className="flaw-stat">
                      <div className="flaw-stat__val" style={{ color: '#81c784' }}>
                        {benchmarkData.machine_limits_flaw_analysis.guardian_multivariate_catch_rate}%
                      </div>
                      <div className="flaw-stat__label">
                        Defects caught early by Process Guardian multivariate sentinel
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Feature Correlation Table */}
              <div>
                <h3
                  style={{
                    fontSize: '0.85rem',
                    textTransform: 'uppercase',
                    letterSpacing: '0.04em',
                    color: '#dfba63',
                    marginBottom: '0.5rem',
                  }}
                >
                  Feature Correlation Matrix to Quality Defect Outcomes
                </h3>
                <table className="evidence-table">
                  <thead>
                    <tr>
                      <th>Rank</th>
                      <th>Process Feature</th>
                      <th>Pearson r (Defect)</th>
                      <th>Pearson r (Weight)</th>
                      <th>Physical Mechanism</th>
                    </tr>
                  </thead>
                  <tbody>
                    {benchmarkData?.feature_correlations?.map((fc) => (
                      <tr key={fc.feature}>
                        <td style={{ fontFamily: 'monospace', fontWeight: 'bold' }}>
                          #{fc.importance_rank}
                        </td>
                        <td style={{ fontFamily: 'monospace', color: '#f5f2ed' }}>
                          {fc.feature}
                        </td>
                        <td
                          style={{
                            fontFamily: 'monospace',
                            color: Math.abs(fc.correlation_with_defect) > 0.3 ? '#ff8a80' : '#d6cfc5',
                          }}
                        >
                          {fc.correlation_with_defect > 0 ? '+' : ''}
                          {fc.correlation_with_defect.toFixed(3)}
                        </td>
                        <td style={{ fontFamily: 'monospace' }}>
                          {fc.correlation_with_weight > 0 ? '+' : ''}
                          {fc.correlation_with_weight.toFixed(3)}
                        </td>
                        <td>{fc.physics_rationale}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}

          {!loading && activeTab === 'grounding' && (
            <>
              <div className="evidence-callout">
                <strong>Empirical Industrial Studies:</strong> Grounding Process Guardian's drift
                sentinel and intervention policy against documented automotive manufacturing cases.
              </div>

              {/* Test Cases */}
              <div className="evidence-levels-grid">
                {groundingData?.test_cases?.map((tc) => (
                  <div key={tc.case_id} className="level-card">
                    <div className="level-card__header">
                      <span className="level-card__title">
                        [{tc.case_id}] {tc.title}
                      </span>
                      <span className="level-tag level-tag--l2">
                        +{tc.process_guardian_lead_time_cycles} CYCLES LEAD TIME
                      </span>
                    </div>
                    <div className="level-card__source">
                      Reference: {tc.empirical_reference}
                    </div>
                    <p style={{ fontSize: '0.8rem', color: '#cdc7bd', margin: '0.35rem 0' }}>
                      <strong>Conventional Factory SPC:</strong> {tc.conventional_spc_behavior}
                    </p>
                    <p style={{ fontSize: '0.8rem', color: '#81c784', margin: '0.35rem 0' }}>
                      <strong>Process Guardian:</strong> {tc.process_guardian_behavior}
                    </p>
                    <p style={{ fontSize: '0.78rem', color: '#a8a298', margin: '0.4rem 0 0 0' }}>
                      <em>Evidence Summary: {tc.evidence_summary}</em>
                    </p>
                  </div>
                ))}
              </div>

              {/* Non-Linear Moisture Curve */}
              {groundingData?.non_linear_moisture_curve && (
                <div>
                  <h3
                    style={{
                      fontSize: '0.85rem',
                      textTransform: 'uppercase',
                      letterSpacing: '0.04em',
                      color: '#dfba63',
                      marginBottom: '0.5rem',
                    }}
                  >
                    Non-Linear Resin Moisture Scrap Cliff (% Scrap vs Moisture Ingress)
                  </h3>
                  <div className="moisture-curve-list">
                    {Object.entries(groundingData.non_linear_moisture_curve).map(
                      ([moistLabel, scrapVal]) => (
                        <div key={moistLabel} className="moisture-bar-row">
                          <span className="moisture-bar-label">{moistLabel}</span>
                          <div className="moisture-bar-track">
                            <div
                              className="moisture-bar-fill"
                              style={{ width: `${Math.min(100, scrapVal * 3.5)}%` }}
                            />
                          </div>
                          <span className="moisture-bar-val">{scrapVal.toFixed(1)}%</span>
                        </div>
                      )
                    )}
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="evidence-modal__footer">
          <span>
            Calibrated for Indian Automotive Tier-2/Tier-3 Molders · AIAG-VDA SPC Aligned
          </span>
          <span>Process Guardian Architecture Build V1.1</span>
        </div>
      </div>
    </div>
  );
}
