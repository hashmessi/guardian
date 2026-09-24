import React from 'react';
import './ProcessStateTimeline.css';

const STEPS = [
  { id: 0, label: 'HEALTHY' },
  { id: 1, label: 'DRIFT' },
  { id: 2, label: 'RISK' },
  { id: 3, label: 'INTERVENTION' },
  { id: 4, label: 'RECOVERY' },
];

export function ProcessStateTimeline({ currentState = 'HEALTHY' }) {
  // Map API state machine status strings to step indices
  const getStepIndex = (state) => {
    switch (state) {
      case 'HEALTHY':
        return 0;
      case 'DRIFT_SUSPECTED':
      case 'DRIFT_CONFIRMED':
        return 1;
      case 'QUALITY_RISK_HIGH':
      case 'DIAGNOSING':
      case 'INTERVENTION_EVALUATION':
      case 'ABSTAIN':
      case 'QC_REQUIRED':
      case 'RECOMMEND':
        return 2;
      case 'APPLIED':
      case 'RECOVERY_CHECK':
        return 3;
      case 'VERIFIED':
      case 'INTERVENTION_MEMORY':
        return 4;
      default:
        return 0;
    }
  };

  const activeIndex = getStepIndex(currentState);
  const connectorFillPercent = activeIndex === 0 ? 0 : (activeIndex / (STEPS.length - 1)) * 100;

  return (
    <div className="state-timeline">
      <div className="state-timeline__header">
        <span className="state-timeline__title">PROCESS STATE PIPELINE</span>
        <span className="state-timeline__raw-state pill pill--mist num">
          STATE: {currentState}
        </span>
      </div>

      <div className="state-timeline__steps">
        <div className="state-timeline-connector">
          <div
            className="state-timeline-connector-fill"
            style={{ width: `${connectorFillPercent}%` }}
          />
        </div>

        {STEPS.map((step) => {
          const isCompleted = step.id < activeIndex;
          const isActive = step.id === activeIndex;
          const isFuture = step.id > activeIndex;

          let nodeClass = 'state-step-node--future';
          let labelClass = '';

          if (isActive) {
            nodeClass = 'state-step-node--active';
            labelClass = 'state-step-label--active';
          } else if (isCompleted) {
            nodeClass = 'state-step-node--completed';
            labelClass = 'state-step-label--completed';
          }

          return (
            <div key={step.id} className="state-step-item">
              <div className={`state-step-node ${nodeClass}`}>
                {isCompleted ? '✓' : step.id + 1}
              </div>
              <span className={`state-step-label ${labelClass}`}>
                {step.label}
              </span>
              {isActive && (
                <div className="state-step-pointer" title="Current Active State">
                  ▲
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default ProcessStateTimeline;
