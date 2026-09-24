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
