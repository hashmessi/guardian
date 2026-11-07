import React from 'react';
import './CandidateTable.css';

export function CandidateTable({
  candidates = [],
  recommendedId = null,
  isAbstain = false,
  abstainReason = null,
}) {
  // No surrogate rows: a failed/empty engine response renders an honest empty
  // state. Fabricated candidates on this screen were indistinguishable from
  // engine output and could mislead a real operator (13-UI-REVIEW pillar 6).
  const items = candidates || [];

  return (
    <div className="candidate-table-container" id="candidate-table-container">
      <div className="candidate-table-header">
        <div className="candidate-table-title-group">
          <span className="label-section" style={{ margin: 0 }}>
            EVALUATED ACTION CANDIDATES
          </span>
          <span className="candidate-table-subtitle">
            Surrogate Constrained Optimization · Minimum-Cost Feasible Selection
          </span>
        </div>
        {items.length > 0 && (
          <span className="pill pill--mist">
            {items.length} {items.length === 1 ? 'CANDIDATE' : 'CANDIDATES'} EVALUATED
          </span>
        )}
      </div>

      {isAbstain && (
        <div className="abstain-banner">
          <span className="pill pill--wine">SAFETY POLICY ACTIVE</span>
          <span>
            <strong>ABSTAIN:</strong> {abstainReason || 'Confidence below threshold or physical boundary violation. System refuses to act without operator verification.'}
          </span>
        </div>
      )}

      {items.length === 0 ? (
        <div className="candidate-empty">
          Awaiting engine candidate evaluation — the table fills when the engine returns scored
          intervention candidates.
        </div>
      ) : (
        <table className="candidate-table" aria-label="Intervention Candidate Comparison">
        <thead>
          <tr>
            <th>Action</th>
            <th>Adjustment</th>
            <th>Predicted Risk</th>
            <th>Cost Score</th>
            <th>Disruption</th>
            <th>Constraint Status</th>
          </tr>
        </thead>
        <tbody>
          {items.map((cand) => {
            // Highlight ONLY the engine's actual selection (is_selected flag or
            // matching recommended action id from the engine result). Never
            // default to a remembered action id — an unhighlighted table is
            // honest; a wrong highlight is not.
            const isRec = !isAbstain && (cand.is_selected || (recommendedId != null && cand.action_id === recommendedId));
            const predRiskPct = (cand.predicted_risk * 100);

            let rowClass = '';
            if (isAbstain) {
              rowClass = 'candidate-row--abstain';
            } else if (isRec) {
              rowClass = 'candidate-row--recommended';
            }

            return (
              <tr key={cand.action_id} className={rowClass}>
                <td>
                  <div className="candidate-action-name">
                    <span className="candidate-action-id pill pill--mist">{cand.action_id}</span>
                    <span>{cand.name}</span>
                    {isRec && (
                      <span className="pill pill--wine" style={{ fontSize: '9px', padding: '1px 6px' }}>
                        MIN-COST
                      </span>
                    )}
                  </div>
                </td>
                <td className="num">
                  {cand.delta_value > 0 ? `+${cand.delta_value}` : cand.delta_value} {cand.unit}
                </td>
                <td>
                  <span
                    className="num"
                    style={{
                      fontWeight: 'var(--fw-data)',
                      color: predRiskPct > 50 ? 'var(--color-wine)' : predRiskPct > 20 ? 'var(--color-violet)' : 'var(--color-lagoon)',
                    }}
                  >
                    {predRiskPct.toFixed(1)}%
                  </span>
                </td>
                <td className="num">{Number(cand.cost).toFixed(2)}</td>
                <td className="num">{Number(cand.disruption).toFixed(2)}</td>
                <td>
                  <span className={`pill ${cand.is_feasible ? 'pill--lagoon' : 'pill--wine'}`}>
                    {cand.is_feasible ? 'FEASIBLE' : 'BLOCKED'}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
        </table>
      )}
    </div>
  );
}

export default CandidateTable;
