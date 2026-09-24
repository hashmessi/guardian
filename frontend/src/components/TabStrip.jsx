import React from 'react';
import './TabStrip.css';
import { usePolling } from '../hooks/useApi';

export function TabStrip({ activeTab, onTabChange }) {
  const { data: driftData } = usePolling('/api/process/drift', 2000);
  const { data: riskData } = usePolling('/api/quality/risk', 2000);

  const isDrifting = driftData?.drift === true || (driftData?.contributing_signals && driftData.contributing_signals.length > 0);
  const isHighRisk = riskData?.risk_state === 'HIGH' || (riskData?.risk_probability && riskData.risk_probability > 0.5);

  const tabs = [
    {
      id: 'live',
      label: 'Live Process',
      hasBadge: isDrifting,
      badgeType: 'wine',
    },
    {
      id: 'diagnosis',
      label: 'Incident Diagnosis',
      hasBadge: isHighRisk,
      badgeType: 'warning',
      badgeText: isHighRisk ? 'RISK' : null,
    },
    {
      id: 'intervention',
      label: 'Intervention + Recovery',
      hasBadge: false,
    },
  ];

  return (
    <nav className="tab-strip" role="tablist" aria-label="Process Guardian Screen Navigation">
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            id={`tab-${tab.id}`}
            role="tab"
            aria-selected={isActive}
            aria-controls={`panel-${tab.id}`}
            tabIndex={isActive ? 0 : -1}
            className={`tab-strip__tab ${isActive ? 'tab-strip__tab--active' : ''}`}
            onClick={() => onTabChange(tab.id)}
          >
            <span>{tab.label}</span>
            {tab.hasBadge && tab.badgeType === 'wine' && (
              <span className="tab-badge--wine" title="Drift detected on active signals" />
            )}
            {tab.hasBadge && tab.badgeType === 'warning' && (
              <span className="tab-badge--warning">{tab.badgeText}</span>
            )}
          </button>
        );
      })}
    </nav>
  );
}
