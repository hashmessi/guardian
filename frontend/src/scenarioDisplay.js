// Display-only renumbering for the locked demo scenarios (scope_plan Sec.4).
// The engine registry keeps its internal codes (SCN-06 / SCN-FLIP /
// SCN-08); the UI shows the demo order 1-3 everywhere per a user decision.
// Every point where a backend-supplied scenario title reaches the screen must
// go through scenarioDisplayLabel so the 06/FLIP/08 codes never leak to users.
const LABELS = {
  'SCN-06-COMPOUND': 'Scenario 1 — Compound Multi-Signal Drift',
  'SCN-FLIP-HUMAN-CHANNEL': 'Scenario 2 — Human-Channel Material Risk',
  'SCN-08-LOW-CONF-ABSTAIN': 'Scenario 3 — Out-of-Distribution Drift',
};

// Some payloads carry legacy titles without ids; match those too.
const LEGACY_TITLES = {
  'Scenario 06 — Compound Multi-Signal Drift':
    'SCN-06-COMPOUND',
  'Scenario FLIP — The One Demo That Wins (Human-Channel Material Risk)':
    'SCN-FLIP-HUMAN-CHANNEL',
  'Scenario FLIP — Human-Channel Material Risk':
    'SCN-FLIP-HUMAN-CHANNEL',
  'Scenario 08 — Low Confidence (Mandatory Abstain Safety Gate)':
    'SCN-08-LOW-CONF-ABSTAIN',
  'Scenario 08 — Out-of-Distribution Drift':
    'SCN-08-LOW-CONF-ABSTAIN',
};

export function scenarioDisplayLabel(scenarioId, legacyTitle) {
  if (scenarioId && LABELS[scenarioId]) return LABELS[scenarioId];
  const legacyId = legacyTitle ? LEGACY_TITLES[legacyTitle] : undefined;
  return (legacyId && LABELS[legacyId]) || legacyTitle || 'Scenario';
}
