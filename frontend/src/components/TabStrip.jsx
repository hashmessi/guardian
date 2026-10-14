import React from 'react';
import './TabStrip.css';
import { usePolling } from '../hooks/useApi';

export function TabStrip({ activeTab, onTabChange }) {
  const { data: driftData } = usePolling('/api/process/drift', 2000);
  const { data: riskData } = usePolling('/api/quality/risk', 2000);

  const isDrifting = driftData?.drift === true || (driftData?.contributing_signals && driftData.contributing_signals.length > 0);
  const isHighRisk = riskData?.risk_state === 'HIGH' || (riskData?.risk_probability && riskData.risk_probability > 0.5);

  const stages = [
    {
      id: 'detect',
      alias: 'live',
      stepNum: '1',
      title: 'DETECT',
      question: 'Is production safe right now?',
      hasBadge: isDrifting,
      badgeText: isDrifting ? 'DRIFT ACTIVE' : 'STABLE',
      badgeClass: isDrifting ? 'stage-badge--alarm' : 'stage-badge--ok',
    },
    {
      id: 'diagnose',
      alias: 'diagnosis',
      stepNum: '2',
      title: 'DIAGNOSE',
      question: 'Why is it drifting & which parts are at risk?',
      hasBadge: isHighRisk,
      badgeText: isHighRisk ? 'RISK HIGH' : 'NORMAL',
      badgeClass: isHighRisk ? 'stage-badge--alarm' : 'stage-badge--ok',
    },
    {
      id: 'act',
      alias: 'intervention',
      stepNum: '3',
      title: 'ACT & VERIFY',
      question: 'What to do, what will it cost & did it recover?',
      hasBadge: true,
      badgeText: 'DECISION & RECOVERY',
      badgeClass: 'stage-badge--action',
    },
  ];

  return (
    <nav className="tab-strip" role="tablist" aria-label="Process Guardian Linear Decision Journey">
      <div className="tab-strip__nav-row">
        <div className="decision-journey-stepper">
          {stages.map((stage, idx) => {
            const isActive = activeTab === stage.id || activeTab === stage.alias;
            return (
              <React.Fragment key={stage.id}>
                <button
                  type="button"
                  id={`tab-${stage.id}`}
                  role="tab"
                  aria-selected={isActive}
                  aria-controls={`panel-${stage.id}`}
                  tabIndex={0}
                  className={`journey-step ${isActive ? 'journey-step--active' : ''}`}
                  onClick={() => onTabChange(stage.id)}
                >
                  <div className="journey-step__indicator">
                    <span className="journey-step__num">{stage.stepNum}</span>
                  </div>
                  <div className="journey-step__content">
                    <div className="journey-step__top">
                      <span className="journey-step__title">{stage.title}</span>
                      {stage.hasBadge && (
                        <span className={`stage-badge ${stage.badgeClass}`}>
                          {stage.badgeText}
                        </span>
                      )}
                    </div>
                    <div className="journey-step__question">{stage.question}</div>
                  </div>
                </button>
                {idx < stages.length - 1 && (
                  <div className="journey-step__arrow" aria-hidden="true">
                    →
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </nav>
  );
}

export default TabStrip;
