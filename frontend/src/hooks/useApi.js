import { useState, useEffect, useRef } from 'react';

const BASE_URL = import.meta.env.VITE_API_URL !== undefined
  ? import.meta.env.VITE_API_URL
  : (typeof window !== 'undefined' && window.location.port === '5173' ? '' : 'http://localhost:8000');

/**
 * Polls a backend endpoint at the specified interval in milliseconds.
 * Ensures clean component unmounting and reactive state tracking.
 */
export function usePolling(path, intervalMs = 2000) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [failures, setFailures] = useState(0);
  const [lastUpdated, setLastUpdated] = useState(null);
  const isMounted = useRef(true);

  const fetchData = async () => {
    try {
      const response = await fetch(`${BASE_URL}${path}`);
      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}: ${response.statusText}`);
      }
      const json = await response.json();
      if (isMounted.current) {
        setData(json);
        setError(null);
        setFailures(0);
        setLoading(false);
        setLastUpdated(new Date());
      }
    } catch (err) {
      if (isMounted.current) {
        setError(err.message || 'Failed to fetch telemetry');
        // Counted, not latched: one dropped poll must not blank the screen
        // mid-demo, but a genuinely dead engine has to become undeniable.
        setFailures((prev) => prev + 1);
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    isMounted.current = true;

    // Initial fetch immediately
    fetchData();

    // Polling interval
    const timer = setInterval(fetchData, intervalMs);

    return () => {
      isMounted.current = false;
      clearInterval(timer);
    };
  }, [path, intervalMs]);

  return { data, loading, error, lastUpdated, failures, refresh: fetchData };
}

/**
 * Applies the demo intervention action against the Process Guardian closed-loop engine.
 */
export async function applyIntervention(actionId = null) {
  const payload = {
    machine_id: 'IMM-01',
    action_id: actionId,
    applied_by: 'DEMO_OPERATOR'
  };

  const response = await fetch(`${BASE_URL}/api/interventions/apply-demo`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Apply intervention failed [${response.status}]: ${errorText}`);
  }

  return await response.json();
}

/**
 * Submits a bounded shop-floor text confirmation (P0, scope_plan.md Sec.3) for one
 * of the 3 operational checkpoint gates. cycleIndex is required for 'spray_done'.
 */
export async function submitHumanChannelText(question, text, cycleIndex = null) {
  const response = await fetch(`${BASE_URL}/api/checkpoints/human-channel`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ question, text, cycle_index: cycleIndex })
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Human-channel submission failed [${response.status}]: ${errorText}`);
  }

  return await response.json();
}

/**
 * Records a mold-release spray application against a real cycle index.
 */
export async function recordMoldSpray(cycleIndex, operatorId = 'OP-OPERATOR') {
  const response = await fetch(`${BASE_URL}/api/checkpoints/spray`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ cycle_index: cycleIndex, operator_id: operatorId })
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Spray record failed [${response.status}]: ${errorText}`);
  }

  return await response.json();
}

/**
 * Resets the demo session to pristine baseline, creating an isolated run while preserving audit history.
 */
export async function resetDemoSession(machineId = 'IMM-01') {
  const response = await fetch(`${BASE_URL}/api/demo/reset`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      machine_id: machineId,
      seed_baseline: true,
      baseline_cycles: 60,
      notes: 'Frontend one-click replay reset'
    })
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Demo reset failed [${response.status}]: ${errorText}`);
  }

  return await response.json();
}

/**
 * Fetches economic impact evaluation with configurable scrap cost per part.
 */
export async function fetchEconomicImpact(partCost = 450.0, machineId = 'IMM-01') {
  const response = await fetch(`${BASE_URL}/api/demo/economic-impact?part_cost=${partCost}&machine_id=${machineId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch economic impact: ${response.statusText}`);
  }
  return await response.json();
}

/**
 * Fetches the 4-level industrial evidence framework contracts.
 */
export async function fetchEvidenceLevels() {
  const response = await fetch(`${BASE_URL}/api/evidence/levels`);
  if (!response.ok) {
    throw new Error(`Failed to fetch evidence levels: ${response.statusText}`);
  }
  return await response.json();
}

/**
 * Fetches external measured molding dataset benchmark and limits flaw analysis.
 */
export async function fetchExternalBenchmark() {
  const response = await fetch(`${BASE_URL}/api/evidence/external-benchmark`);
  if (!response.ok) {
    throw new Error(`Failed to fetch external benchmark: ${response.statusText}`);
  }
  return await response.json();
}

/**
 * Fetches the automated empirical grounding report comparing factory cases.
 */
export async function fetchGroundingReport() {
  const response = await fetch(`${BASE_URL}/api/evidence/grounding-report`);
  if (!response.ok) {
    throw new Error(`Failed to fetch grounding report: ${response.statusText}`);
  }
  return await response.json();
}

/**
 * Fetches parametric CoPQ configuration parameters.
 */
export async function fetchCoPQParameters() {
  const response = await fetch(`${BASE_URL}/api/economics/parameters`);
  if (!response.ok) {
    throw new Error(`Failed to fetch CoPQ parameters: ${response.statusText}`);
  }
  return await response.json();
}

/**
 * Updates parametric CoPQ configuration parameters.
 */
export async function updateCoPQParameters(params) {
  const response = await fetch(`${BASE_URL}/api/economics/parameters`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(params)
  });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to update CoPQ parameters [${response.status}]: ${errorText}`);
  }
  return await response.json();
}

/**
 * Fetches real-time Cost of Waiting vs Cost of Acting decision economics.
 */
export async function fetchDecisionValue() {
  const response = await fetch(`${BASE_URL}/api/economics/decision-value`);
  if (!response.ok) {
    throw new Error(`Failed to fetch decision value: ${response.statusText}`);
  }
  return await response.json();
}

/**
 * Lists available operational scenarios from the Scenario Registry.
 */
export async function listScenarios(heroOnly = false) {
  const response = await fetch(`${BASE_URL}/api/scenarios?hero_only=${heroOnly}`);
  if (!response.ok) {
    throw new Error(`Failed to list scenarios: ${response.statusText}`);
  }
  return await response.json();
}

/**
 * Selects an operational scenario and retrieves deterministic replay and scorecard.
 */
export async function selectScenario(scenarioId) {
  const response = await fetch(`${BASE_URL}/api/scenarios/${scenarioId}/select`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    }
  });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to select scenario [${response.status}]: ${errorText}`);
  }
  return await response.json();
}

/**
 * Fetches the 11-scenario Operational Validation Suite scorecard report.
 */
export async function fetchValidationSuite(runFresh = false) {
  const response = await fetch(`${BASE_URL}/api/scenarios/validation-suite?run_fresh=${runFresh}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch validation suite: ${response.statusText}`);
  }
  return await response.json();
}


