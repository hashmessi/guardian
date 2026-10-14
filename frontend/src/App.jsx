import React, { useState } from 'react';
import './styles/global.css';
import { AppShell } from './components/AppShell';
import { TabStrip } from './components/TabStrip';
import { FrontPage } from './screens/FrontPage';
import { LiveProcess } from './screens/LiveProcess';
import { IncidentDiagnosis } from './screens/IncidentDiagnosis';
import { InterventionRecovery } from './screens/InterventionRecovery';

export function App() {
  const [activeTab, setActiveTab] = useState('scenarios');
  const [showCoPQModal, setShowCoPQModal] = useState(false);
  const [showScorecardModal, setShowScorecardModal] = useState(false);
  const [showValidationSuiteModal, setShowValidationSuiteModal] = useState(false);
  const [showCheckpointsModal, setShowCheckpointsModal] = useState(false);

  const openCoPQModal = () => setShowCoPQModal(true);
  const openScorecardModal = () => setShowScorecardModal(true);
  const openValidationSuiteModal = () => setShowValidationSuiteModal(true);
  const openCheckpointsModal = () => setShowCheckpointsModal(true);

  const renderActiveScreen = () => {
    switch (activeTab) {
      case 'scenarios':
      case 'frontpage':
      case 'overview':
        return (
          <FrontPage
            onSelectScenario={(scenarioId) => setActiveTab('detect')}
            onOpenScorecard={openScorecardModal}
            onOpenValidationSuite={openValidationSuiteModal}
            onOpenCoPQModal={openCoPQModal}
            onNavigateToLive={(tab) => setActiveTab(tab || 'detect')}
          />
        );
      case 'detect':
      case 'live':
        return <LiveProcess onProceed={() => setActiveTab('diagnose')} />;
      case 'diagnose':
      case 'diagnosis':
        return (
          <IncidentDiagnosis
            onProceed={() => setActiveTab('act')}
            onOpenCoPQModal={openCoPQModal}
          />
        );
      case 'act':
      case 'intervention':
      case 'counterfactual':
        return (
          <InterventionRecovery
            onOpenCoPQModal={openCoPQModal}
            onOpenCheckpointsModal={openCheckpointsModal}
          />
        );
      default:
        return (
          <FrontPage
            onSelectScenario={(scenarioId) => setActiveTab('detect')}
            onOpenScorecard={openScorecardModal}
            onOpenValidationSuite={openValidationSuiteModal}
            onOpenCoPQModal={openCoPQModal}
            onNavigateToLive={(tab) => setActiveTab(tab || 'detect')}
          />
        );
    }
  };

  return (
    <AppShell
      activeTab={activeTab}
      onTabChange={setActiveTab}
      showCoPQModal={showCoPQModal}
      setShowCoPQModal={setShowCoPQModal}
      showScorecardModal={showScorecardModal}
      setShowScorecardModal={setShowScorecardModal}
      showValidationSuiteModal={showValidationSuiteModal}
      setShowValidationSuiteModal={setShowValidationSuiteModal}
      showCheckpointsModal={showCheckpointsModal}
      setShowCheckpointsModal={setShowCheckpointsModal}
    >
      <TabStrip activeTab={activeTab} onTabChange={setActiveTab} />
      <div style={{ marginTop: '16px' }}>
        {renderActiveScreen()}
      </div>
    </AppShell>
  );
}

export default App;
