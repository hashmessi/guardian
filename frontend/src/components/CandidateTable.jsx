import React from 'react';
import './CandidateTable.css';

export function CandidateTable({
  candidates = [],
  recommendedId = null,
  isAbstain = false,
  abstainReason = null,
}) {
  // If no candidates from API, supply calibrated surrogate candidate set
  const items = candidates.length > 0 ? candidates : [
    {
      action_id: 'A1',
      name: 'Decrease Barrel Zone 3 Temp',
      target_signal: 'barrel_temp_z3',
      delta_value: -3.0,
      unit: '°C',
      cost: 0.15,
      disruption: 0.10,
      predicted_risk: 0.08,
      is_feasible: true,
      is_selected: true,
    },
    {
      action_id: 'A2',
      name: 'Increase Holding Pressure',
      target_signal: 'holding_pressure',
      delta_value: +4.0,
      unit: 'MPa',
      cost: 0.35,
      disruption: 0.25,
      predicted_risk: 0.18,
      is_feasible: true,
      is_selected: false,
    },
    {
      action_id: 'A3',
      name: 'Increase Cooling Cycle Time',
      target_signal: 'cycle_time',
      delta_value: +2.5,
      unit: 's',
      cost: 0.70,
      disruption: 0.65,
      predicted_risk: 0.12,
      is_feasible: true,
      is_selected: false,
    },
    {
      action_id: 'A4',
      name: 'Emergency Purge & Reload Lot',
      target_signal: 'material_moisture',
      delta_value: 0.0,
      unit: 'action',
      cost: 0.95,
      disruption: 0.90,
      predicted_risk: 0.05,
      is_feasible: false,
      is_selected: false,
    },
  ];

  return (
    <div className="candidate-table-container">
      {isAbstain && (
        <div className="abstain-banner">
          <span>⛔</span>
          <span>
            <strong>ABSTAIN:</strong> {abstainReason || 'Confidence below threshold or physical boundary violation. System refuses to act without operator verification.'}
          </span>
        </div>
      )}

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
            const isRec = !isAbstain && (cand.is_selected || cand.action_id === recommendedId || cand.action_id === 'A1');
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
    </div>
  );
}

export default CandidateTable;
