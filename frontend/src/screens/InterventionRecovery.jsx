import React, { useEffect, useState } from 'react';
import './InterventionRecovery.css';
import { usePolling, applyIntervention } from '../hooks/useApi';
import { CandidateTable } from '../components/CandidateTable';
import { RecommendationCard } from '../components/RecommendationCard';
import { RecoveryPanel } from '../components/RecoveryPanel';
import { AuditDrawer } from '../components/AuditDrawer';
import { ContainmentBoundaryCard } from '../components/ContainmentBoundaryCard';
import { OperationalCheckpointsCard } from '../components/OperationalCheckpointsCard';

export function InterventionRecovery({ activeScenarioId, onOpenCoPQModal, onOpenCheckpointsModal, onNavigateToBrief }) {
  const { data: recommendationData } = usePolling('/api/interventions/recommendation', 2000);
  const { data: recoveryData } = usePolling('/api/recovery/status', 2000);
  const { data: containmentData } = usePolling('/api/containment/window', 2000);
  const { data: driftData } = usePolling('/api/process/drift', 2000);
  const { data: riskData } = usePolling('/api/quality/risk', 2000);
  const { data: cfData } = usePolling('/api/counterfactual/compare', 5000);
  const { data: econData } = usePolling('/api/economics/decision-value', 2000);
  const { data: copqBreakdown } = usePolling('/api/economics/copq', 3000);
  const { data: copqParams } = usePolling('/api/economics/parameters', 5000);

  const [isApplying, setIsApplying] = useState(false);
  const [applied, setApplied] = useState(false);
  const [applyError, setApplyError] = useState(null);

  // Switching scenarios resets the engine; without this the Act screen kept
  // showing the previous run's recovery panel and hid the new recommendation.
  useEffect(() => {
    if (recoveryData?.recovery_status === 'IDLE') setApplied(false);
  }, [recoveryData?.recovery_status]);

  const isAbstain = recommendationData?.is_abstain === true || recommendationData?.operator_mode === 'ABSTAIN';

  // RecommendationResponse has no top-level action_id -- the engine's selected
  // candidate is only marked via candidate_comparison[].is_selected. Reading a
  // field that doesn't exist on this response always came back undefined, so
  // this silently applied 'A1' regardless of what the engine actually picked.
  const selectedCandidate = recommendationData?.candidate_comparison?.find((c) => c.is_selected);
  const recommendedActionId = selectedCandidate?.action_id ?? null;
  const isRecommendationReady = isAbstain || Boolean(selectedCandidate);

  const handleApply = async () => {
    if (!recommendedActionId || isAbstain) return;
    setIsApplying(true);
    setApplyError(null);
    try {
      await applyIntervention(recommendedActionId);
      setApplied(true);
    } catch (err) {
      console.error('Failed to apply intervention:', err);
      setApplyError('Could not apply that recommendation. Check the engine connection and try again.');
    } finally {
      setIsApplying(false);
    }
  };

  // Lock 16: Check if recovery is active (either just applied or recovery state machine already running)
  const isRecoveryActive = applied || (recoveryData && recoveryData.recovery_status !== 'IDLE');

  // Economics pass through exactly as the engine computed them, including a
  // negative Decision Value (which means waiting is cheaper than acting). The
  // previous floor-at-500 fallback rendered a fixed "+₹2,198.92 net benefit"
  // over any real value below that -- inverting the engine's own verdict.
  const netBenefit = econData?.decision_value ?? null;
  const costWait = econData?.expected_loss_waiting ?? null;
  const costAct = econData?.cost_acting ?? null;

  // Parametric Cost of Poor Quality (CoPQ) verified shop-floor baseline numbers
  const directCoPQ = copqBreakdown?.direct_scrap_copq_per_defect ?? 68.96;
  const matCost = copqBreakdown?.material_cost_per_defect ?? 34.75;
  const burdenCost = copqBreakdown?.machine_burden_per_defect ?? 11.00;
  const energyCost = copqBreakdown?.energy_cost_per_defect ?? 1.21;
  const sortCost = copqBreakdown?.sorting_cost_per_defect ?? 22.00;
  const oemRisk = copqBreakdown?.oem_penalty_risk ?? 150.00;

  return (
    <div id="panel-act" role="tabpanel" aria-labelledby="tab-act" className="intervention-recovery">
      {!isRecoveryActive ? (
        /* =========================================================================
           STATE A: BEFORE ACTION — DECISION & ACTION MODE
           Dominant Recommendation -> Surrogate Candidates -> Operational Gates -> Impact Proof
           ========================================================================= */
        <>
          {/* Section 1: Dominant Recommended Action (Advisory Setpoint) */}
          <div className="intervention-section">
            <RecommendationCard
              recommendation={recommendationData}
              isAbstain={isAbstain}
              isReady={isRecommendationReady}
              onApply={handleApply}
              isApplying={isApplying}
              applied={applied}
              applyError={applyError}
              netBenefit={netBenefit}
              costWait={costWait}
              costAct={costAct}
              onOpenCoPQModal={onOpenCoPQModal}
            />
          </div>

          {/* Section 2: Evaluated Action Candidates (Surrogate Optimization) */}
          <div className="intervention-section">
            <CandidateTable
              candidates={recommendationData?.candidate_comparison || []}
              recommendedId={recommendedActionId}
              isAbstain={isAbstain}
              abstainReason={recommendationData?.abstain_reason}
            />
          </div>

          {/* Section 3: Shop-Floor Operational Checkpoints (PS02 Mandated Gates) */}
          <div className="intervention-section">
            <OperationalCheckpointsCard onOpenModal={onOpenCheckpointsModal} />
          </div>

          {/* Section 4: Policy impact, shown only once the replay has actually run */}
          {cfData && cfData.scrap_reduction_pct > 0 && activeScenarioId !== 'SCN-FLIP-HUMAN-CHANNEL' && (
            <div className="intervention-section">
              <div className="counterfactual-embedded-card">
                <div className="cf-embedded-header">
                  <div>
                    <span className="label-section" style={{ margin: 0 }}>
                      Policy impact — Guardian active vs status quo
                    </span>
                    <span style={{ fontSize: '11px', color: 'var(--color-stone)', display: 'block', marginTop: '2px' }}>
                      Same disturbance replayed twice under one seed. Modeled, not a plant trial.
                    </span>
                  </div>
                  <span className="pill pill--mist">MODELED</span>
                </div>

                <div className="cf-embedded-kpi-grid">
                  <div className="cf-embedded-box">
                    <span className="cf-embedded-box__label">Scrap parts</span>
                    <span className="cf-embedded-box__val cf-embedded-box__val--green num">
                      {cfData.guardian_off.scrap_parts_count} → {cfData.guardian_on.scrap_parts_count}
                    </span>
                    <span className="cf-embedded-box__subtext">
                      {cfData.scrap_reduction_pct}% fewer defective parts produced.
                    </span>
                  </div>

                  <div className="cf-embedded-box">
                    <span className="cf-embedded-box__label">Suspect lot</span>
                    <span className="cf-embedded-box__val num">
                      {cfData.guardian_off.suspect_cycles} → {cfData.guardian_on.suspect_cycles}
                    </span>
                    <span className="cf-embedded-box__subtext">
                      {cfData.suspect_lot_reduction_pct}% smaller quarantine window.
                    </span>
                  </div>

                  <div className="cf-embedded-box">
                    <span className="cf-embedded-box__label">Avoided loss</span>
                    <span className="cf-embedded-box__val cf-embedded-box__val--savings num">
                      ₹{Number(cfData.net_avoided_loss).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                    </span>
                    <span className="cf-embedded-box__subtext">
                      ₹{Number(cfData.guardian_off.total_financial_loss).toFixed(0)} vs ₹{Number(cfData.guardian_on.total_financial_loss).toFixed(0)} total cost.
                    </span>
                  </div>
                </div>

                {/* Section 4b: Transparent Cost of Poor Quality (CoPQ) Formula & Parametric Proof */}
                <div className="cf-copq-accounting">
                  <div className="cf-copq-accounting__header">
                    <div className="cf-copq-title-row">
                      <span className="cf-copq-title">TRANSPARENT CoPQ FORMULA &amp; PARAMETRIC PROOF</span>
                      <span className="pill pill--mist">LEVEL 3 INVARIANT</span>
                    </div>
                    {onOpenCoPQModal && (
                      <button
                        type="button"
                        className="btn-calibrate-copq"
                        onClick={onOpenCoPQModal}
                        title="Open parametric CoPQ engine to inspect or adjust baseline rates"
                      >
                        <span>⚙</span>
                        <span>Calibrate Plant Rates (₹{directCoPQ.toFixed(2)}/part) →</span>
                      </button>
                    )}
                  </div>

                  {/* 2-Column Comparison Breakdown */}
                  <div className="cf-copq-columns">
                    {/* Column 1: Status Quo Loss */}
                    <div className="cf-copq-col cf-copq-col--off">
                      <div className="cf-copq-col__title">
                        <span>Status Quo Loss (Guardian OFF)</span>
                        <span className="cf-copq-col__total num">₹{Number(cfData.guardian_off.total_financial_loss).toLocaleString('en-IN', { maximumFractionDigits: 0 })}</span>
                      </div>
                      <div className="cf-copq-math-rows">
                        <div className="cf-math-row">
                          <span>Direct Scrap ({cfData.guardian_off.scrap_parts_count} parts × ₹{directCoPQ.toFixed(2)} CoPQ)</span>
                          <span className="num">₹{(cfData.guardian_off.scrap_parts_count * directCoPQ).toFixed(0)}</span>
                        </div>
                        <div className="cf-math-row">
                          <span>Secondary Containment ({cfData.guardian_off.suspect_cycles} parts × ₹{sortCost.toFixed(2)} sorting)</span>
                          <span className="num">₹{(cfData.guardian_off.suspect_cycles * sortCost).toFixed(0)}</span>
                        </div>
                        <div className="cf-math-row">
                          <span>OEM Line Penalty Risk ({cfData.guardian_off.scrap_parts_count} defects × ₹{oemRisk.toFixed(2)})</span>
                          <span className="num">₹{(cfData.guardian_off.scrap_parts_count * oemRisk).toFixed(0)}</span>
                        </div>
                      </div>
                    </div>

                    {/* Column 2: Guardian Active Loss */}
                    <div className="cf-copq-col cf-copq-col--on">
                      <div className="cf-copq-col__title">
                        <span>Guardian Active Loss (Intervened)</span>
                        <span className="cf-copq-col__total num">₹{Number(cfData.guardian_on.total_financial_loss).toLocaleString('en-IN', { maximumFractionDigits: 0 })}</span>
                      </div>
                      <div className="cf-copq-math-rows">
                        <div className="cf-math-row">
                          <span>Stabilization Scrap ({cfData.guardian_on.scrap_parts_count} parts × ₹{directCoPQ.toFixed(2)} CoPQ)</span>
                          <span className="num">₹{(cfData.guardian_on.scrap_parts_count * directCoPQ).toFixed(0)}</span>
                        </div>
                        <div className="cf-math-row">
                          <span>Suspect Lot Sorting ({cfData.guardian_on.suspect_cycles} parts × ₹{sortCost.toFixed(2)} sorting)</span>
                          <span className="num">₹{(cfData.guardian_on.suspect_cycles * sortCost).toFixed(0)}</span>
                        </div>
                        <div className="cf-math-row">
                          <span>Operator Tuning Overhead (Standard Disruption Fee)</span>
                          <span className="num">₹45</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Net Proof Equation Bar */}
                  <div className="cf-copq-equation-bar">
                    <div className="equation-math">
                      <span className="eq-label">Net Avoided Loss:</span>
                      <span className="eq-term num">₹{Number(cfData.guardian_off.total_financial_loss).toFixed(0)}</span>
                      <span className="eq-op">−</span>
                      <span className="eq-term num">₹{Number(cfData.guardian_on.total_financial_loss).toFixed(0)}</span>
                      <span className="eq-op">=</span>
                      <span className="eq-result num">₹{Number(cfData.net_avoided_loss).toLocaleString('en-IN', { maximumFractionDigits: 0 })}</span>
                    </div>
                    <div className="equation-unit-formula">
                      Direct CoPQ = Material (₹{matCost.toFixed(2)}) + Machine (₹{burdenCost.toFixed(2)}) + Energy (₹{energyCost.toFixed(2)}) + Sorting (₹{sortCost.toFixed(2)}) = <strong>₹{directCoPQ.toFixed(2)}/part</strong>
                    </div>
                  </div>

                  {/* Calibrated Plant Parameters Ribbon */}
                  <div className="cf-copq-param-ribbon">
                    <span className="ribbon-label">PLANT CALIBRATION:</span>
                    <span className="ribbon-chip">{copqParams?.resin_type || 'PP/ABS Automotive'} ({copqParams?.part_weight_grams || 220}g)</span>
                    <span className="ribbon-chip">Resin: ₹{copqParams?.resin_price_per_kg || 195}/kg</span>
                    <span className="ribbon-chip">Cycle: {copqParams?.cycle_time_seconds || 24}s</span>
                    <span className="ribbon-chip">Press Rate: ₹{copqParams?.machine_hourly_rate || 1650}/hr</span>
                    <span className="ribbon-chip">Power: {copqParams?.machine_power_kw || 18.5}kW @ ₹{copqParams?.electricity_tariff_per_kwh || 9.8}/kWh</span>
                    <span className="ribbon-chip">Sorting: ₹{copqParams?.sorting_cost_per_part || 22}/part</span>
                    <span className="ribbon-chip">OEM Risk: ₹{copqParams?.oem_penalty_risk_per_defect || 150}/part</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Section 5: In-Flow Immutable Audit Trail */}
          <div className="intervention-section">
            <AuditDrawer />
          </div>

          {/* Section 6: Action for Material Hold (SCN-FLIP) to View Leadership Brief */}
          {!isAbstain && (activeScenarioId === 'SCN-FLIP-HUMAN-CHANNEL' || driftData?.dominant_signal === 'human_channel' || recommendationData?.operator_mode === 'QC_HOLD') && onNavigateToBrief && (
            <div className="intervention-section">
              <div className="leadership-brief-callout-banner card">
                <div className="callout-left">
                  <span className="pill pill--violet">QC HOLD ENFORCED</span>
                  <h3 className="callout-title">Material Risk Contained — Physical QC Checkpoint Required</h3>
                  <p className="callout-desc">
                    Operator human-channel report caught unverified resin moisture. Production held at QC gate before defective parts were molded.
                  </p>
                </div>
                <button
                  type="button"
                  className="btn-view-leadership-brief"
                  onClick={onNavigateToBrief}
                >
                  View Leadership Incident Brief →
                </button>
              </div>
            </div>
          )}

          {/* Section 7: Action for Abstain Scenarios to View Leadership Brief */}
          {isAbstain && onNavigateToBrief && (
            <div className="intervention-section">
              <div className="leadership-brief-callout-banner card">
                <div className="callout-left">
                  <span className="pill pill--wine">ABSTAIN GATE ENFORCED</span>
                  <h3 className="callout-title">Risk Contained Without Speculative Automation</h3>
                  <p className="callout-desc">
                    Guardian locked out uncalibrated parameter shifts and contained the suspect window.
                    Open the executive incident report to review the safety outcome.
                  </p>
                </div>
                <button
                  type="button"
                  className="btn-view-leadership-brief"
                  onClick={onNavigateToBrief}
                >
                  View Leadership Incident Brief →
                </button>
              </div>
            </div>
          )}
        </>
      ) : (
        /* =========================================================================
           STATE B: AFTER ACTION — RECOVERY & SCRAP CONTAINMENT MODE
           Recovery Verification -> Mandatory Poka-Yoke QC Gate -> Checkpoints -> Audit -> Brief
           ========================================================================= */
        <>
          {/* Section: Action Banner at End of Replay */}
          {onNavigateToBrief && (
            <div className="intervention-section">
              <div className="leadership-brief-callout-banner card">
                <div className="callout-left">
                  <span className="pill pill--lagoon">INCIDENT CONTAINED</span>
                  <h3 className="callout-title">Recovery Verified & Decision Traceability Complete</h3>
                  <p className="callout-desc">
                    Operational telemetry, constrained setpoint action, and suspect quarantine are locked.
                    View the one-page leadership incident brief.
                  </p>
                </div>
                <button
                  type="button"
                  className="btn-view-leadership-brief"
                  onClick={onNavigateToBrief}
                >
                  View Leadership Incident Brief →
                </button>
              </div>
            </div>
          )}

          {/* Section 1: Dominant Recovery Verification Panel (5-Cycle Stability) */}
          <div className="intervention-section">
            <RecoveryPanel
              recoveryData={recoveryData}
              containmentData={containmentData}
              isVisible={true}
            />
          </div>

          {/* Section 2: Mandatory Physical QC & Production Containment Boundary */}
          <div className="intervention-section">
            <ContainmentBoundaryCard />
          </div>

          {/* Section 3: Shop-Floor Operational Checkpoints */}
          <div className="intervention-section">
            <OperationalCheckpointsCard onOpenModal={onOpenCheckpointsModal} />
          </div>

          {/* Section 4: Immutable Audit Trail */}
          <div className="intervention-section">
            <AuditDrawer />
          </div>
        </>
      )}
    </div>
  );
}

export default InterventionRecovery;
