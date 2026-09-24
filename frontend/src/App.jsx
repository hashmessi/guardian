import React, { useState } from 'react';
import './styles/global.css';
import { AppShell } from './components/AppShell';
import { TabStrip } from './components/TabStrip';
import { LiveProcess } from './screens/LiveProcess';
import { IncidentDiagnosis } from './screens/IncidentDiagnosis';
import { InterventionRecovery } from './screens/InterventionRecovery';

export function App() {
  const [activeTab, setActiveTab] = useState('live');

  const renderActiveScreen = () => {
    switch (activeTab) {
      case 'live':
        return <LiveProcess />;
      case 'diagnosis':
        return <IncidentDiagnosis />;
      case 'intervention':
        return <InterventionRecovery />;
      default:
        return <LiveProcess />;
    }
  };

  return (
    <AppShell activeTab={activeTab} onTabChange={setActiveTab}>
      <TabStrip activeTab={activeTab} onTabChange={setActiveTab} />
      <div style={{ marginTop: '20px' }}>
        {renderActiveScreen()}
      </div>
    </AppShell>
  );
}

export default App;
