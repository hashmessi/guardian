import React, { useState } from 'react';
import './InterventionRecovery.css';
import { usePolling, applyIntervention } from '../hooks/useApi';
import { CandidateTable } from '../components/CandidateTable';
import { RecommendationCard } from '../components/RecommendationCard';
import { RecoveryPanel } from '../components/RecoveryPanel';
import { AuditDrawer } from '../components/AuditDrawer';

export function InterventionRecovery() {
  const { data: recommendationData } = usePolling('/api/interventions/recommendation', 2000);
  const { data: recoveryData } = usePolling('/api/recovery/status', 2000);
  const { data: containmentData } = usePolling('/api/containment/window', 2000);
  const { data: driftData } = usePolling('/api/process/drift', 2000);
  const { data: riskData } = usePolling('/api/quality/risk', 2000);

  const [isApplying, setIsApplying] = useState(false);
  const [applied, setApplied] = useState(false);
  const [applyError, setApplyError] = useState(null);

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

  const showRecovery = applied || (recoveryData && recoveryData.recovery_status !== 'IDLE');

  return (
    <div id="panel-intervention" role="tabpanel" aria-labelledby="tab-intervention" className="intervention-recovery">
      {/* Top 2-Column Grid: Candidates on Left (7fr), Recommendation Contract on Right (5fr) */}
      <div className="intervention-top-grid">
        {/* Left Column (7fr): Evaluated Candidate Actions */}
        <div className="intervention-section">
          <span className="label-section">EVALUATED CORRECTIVE CANDIDATE ACTIONS</span>
          <CandidateTable
            candidates={recommendationData?.candidate_comparison || []}
            recommendedId="A1"
            isAbstain={isAbstain}
            abstainReason={recommendationData?.abstain_reason}
          />
        </div>

        {/* Right Column (5fr): 7-Field Recommendation Card & Apply Action */}
        <div className="intervention-section">
          <RecommendationCard
            recommendation={recommendationData}
            isAbstain={isAbstain}
            onApply={handleApply}
            isApplying={isApplying}
            applied={applied}
            applyError={applyError}
          />
        </div>
      </div>

      {/* Middle Section: Closed-Loop Recovery Verification (Full Width, Appears Post-Apply) */}
      {showRecovery && (
        <div className="intervention-section">
          <RecoveryPanel
            recoveryData={recoveryData}
            containmentData={containmentData}
            isVisible={true}
          />
        </div>
      )}

      {/* Bottom Section: In-Flow Collapsible Audit Trail Card */}
      <div className="intervention-section">
        <AuditDrawer
          driftData={driftData}
          riskData={riskData}
          recommendationData={recommendationData}
          recoveryData={recoveryData}
          containmentData={containmentData}
        />
      </div>
    </div>
  );
}

export default InterventionRecovery;
