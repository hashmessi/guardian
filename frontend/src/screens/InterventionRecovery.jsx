import React, { useEffect, useState } from 'react';
import './InterventionRecovery.css';
import { usePolling, applyIntervention } from '../hooks/useApi';
import { CandidateTable } from '../components/CandidateTable';
import { RecommendationCard } from '../components/RecommendationCard';
import { RecoveryPanel } from '../components/RecoveryPanel';
import { AuditDrawer } from '../components/AuditDrawer';
import { ContainmentBoundaryCard } from '../components/ContainmentBoundaryCard';
import { OperationalCheckpointsCard } from '../components/OperationalCheckpointsCard';

export function InterventionRecovery({ onOpenCoPQModal, onOpenCheckpointsModal }) {
  const { data: recommendationData } = usePolling('/api/interventions/recommendation', 2000);
  const { data: recoveryData } = usePolling('/api/recovery/status', 2000);
  const { data: containmentData } = usePolling('/api/containment/window', 2000);
  const { data: driftData } = usePolling('/api/process/drift', 2000);
  const { data: riskData } = usePolling('/api/quality/risk', 2000);
  const { data: cfData } = usePolling('/api/counterfactual/compare?total_cycles=156', 5000);
  const { data: econData } = usePolling('/api/economics/decision-value', 2000);

  const [isApplying, setIsApplying] = useState(false);
  const [applied, setApplied] = useState(false);
  const [applyError, setApplyError] = useState(null);

  // Switching scenarios resets the engine; without this the Act screen kept
  // showing the previous run's recovery panel and hid the new recommendation.
  useEffect(() => {
    if (recoveryData?.recovery_status === 'IDLE') setApplied(false);
  }, [recoveryData?.recovery_status]);

  const isAbstain = recommendationData?.is_abstain === true || recommendationData?.operator_mode === 'ABSTAIN';

  const handleApply = async () => {
    setIsApplying(true);
    setApplyError(null);
    try {
      await applyIntervention(recommendationData?.action_id || 'A1');
      setApplied(true);
    } catch (err) {
      setApplyError(err.message || 'Failed to apply intervention');
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
              onApply={handleApply}
              isApplying={isApplying}
              applied={applied}
              applyError={applyError}
              netBenefit={netBenefit}
              costWait={costWait}
              costAct={costAct}
            />
          </div>

          {/* Section 2: Evaluated Action Candidates (Surrogate Optimization) */}
          <div className="intervention-section">
            <CandidateTable
              candidates={recommendationData?.candidate_comparison || []}
              recommendedId={recommendationData?.action_id || 'A1'}
              isAbstain={isAbstain}
              abstainReason={recommendationData?.abstain_reason}
            />
          </div>

          {/* Section 3: Shop-Floor Operational Checkpoints (PS02 Mandated Gates) */}
          <div className="intervention-section">
            <OperationalCheckpointsCard onOpenModal={onOpenCheckpointsModal} />
          </div>

          {/* Section 4: Policy impact, shown only once the replay has actually run */}
          {cfData && (
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
              </div>
            </div>
          )}

          {/* Section 5: In-Flow Immutable Audit Trail */}
          <div className="intervention-section">
            <AuditDrawer />
          </div>
        </>
      ) : (
        /* =========================================================================
           STATE B: AFTER ACTION — RECOVERY & SCRAP CONTAINMENT MODE
           Recovery Verification -> Mandatory Poka-Yoke QC Gate -> Checkpoints -> Audit
           ========================================================================= */
        <>
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
