import { useState, useEffect, useRef } from 'react';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Polls a backend endpoint at the specified interval in milliseconds.
 * Ensures clean component unmounting and reactive state tracking.
 */
export function usePolling(path, intervalMs = 2000) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;

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
          setLoading(false);
          setLastUpdated(new Date());
        }
      } catch (err) {
        if (isMounted.current) {
          setError(err.message || 'Failed to fetch telemetry');
          setLoading(false);
        }
      }
    };

    // Initial fetch immediately
    fetchData();

    // Polling interval
    const timer = setInterval(fetchData, intervalMs);

    return () => {
      isMounted.current = false;
      clearInterval(timer);
    };
  }, [path, intervalMs]);

  return { data, loading, error, lastUpdated };
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

