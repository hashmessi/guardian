import React, { useEffect, useState } from 'react';
import './DetectionComparison.css';
import { fetchExternalBenchmark } from '../hooks/useApi';

/**
 * The one comparison that answers "why not just use the machine's own alarms?".
 *
 * Both detectors are shown at the same false-alarm rate on good parts, because a
 * detector allowed more false line stops would otherwise win by crying wolf. All
 * figures are computed live by the engine on the replica dataset -- nothing here
 * is a hardcoded headline number.
 */
export function DetectionComparison() {
  const [state, setState] = useState({ status: 'loading', data: null, error: null });

  useEffect(() => {
    let alive = true;
    fetchExternalBenchmark()
      .then((data) => alive && setState({ status: 'ready', data, error: null }))
      .catch((err) => alive && setState({ status: 'error', data: null, error: err.message }));
    return () => {
      alive = false;
    };
  }, []);

  if (state.status === 'loading') {
    return (
      <section className="dc" aria-busy="true">
        <div className="dc__skeleton" />
        <div className="dc__skeleton dc__skeleton--wide" />
      </section>
    );
  }

  if (state.status === 'error') {
    return (
      <section className="dc dc--error" role="alert">
        <h2 className="dc__title">Detection comparison unavailable</h2>
        <p className="dc__error-text">
          The engine did not answer, so this panel is showing nothing rather than a remembered number.
          <span className="dc__error-detail">{state.error}</span>
        </p>
      </section>
    );
  }

  const flaw = state.data?.machine_limits_flaw_analysis;
  if (!flaw) {
    return null;
  }

  const univariateCatch = flaw.conventional_spc_catch_rate;
  const multivariateCatch = flaw.guardian_multivariate_catch_rate;
  const curve = flaw.detection_tradeoff_curve || [];

  return (
    <section className="dc" aria-labelledby="dc-title">
      <header className="dc__head">
        <h2 className="dc__title" id="dc-title">
          The defects your machine&rsquo;s own limits accept
        </h2>
        <p className="dc__standfirst">
          Every parameter inside tolerance, {flaw.escaped_defects_percentage}% of the defects still got
          through. Both detectors below stop the same share of good parts, so neither wins by alarming
          more often.
        </p>
      </header>

      <div className="dc__verdicts">
        <div className="dc__verdict dc__verdict--spc">
          <span className="dc__verdict-label">Machine parameter limits</span>
          <span className="dc__verdict-value">{univariateCatch}%</span>
          <span className="dc__verdict-caption">
            of defects caught &middot; {flaw.escaped_defects_count} of {flaw.total_defective_parts} defective
            parts passed every individual limit
          </span>
          <span className="dc__verdict-tag dc__verdict-tag--pass">ALL PARAMETERS IN TOLERANCE</span>
        </div>

        <div className="dc__verdict dc__verdict--guardian">
          <span className="dc__verdict-label">Process Guardian (multivariate)</span>
          <span className="dc__verdict-value">{multivariateCatch}%</span>
          <span className="dc__verdict-caption">
            of the same defects caught at the same {flaw.matched_false_alarm_rate_pct}% false-alarm rate
            &middot; {flaw.guardian_rescued_defects_count} the limits had accepted
          </span>
          <span className="dc__verdict-tag dc__verdict-tag--act">
            {/* Null when the machine limits caught nothing at all, where a
                multiplier would be meaningless rather than impressive. */}
            {flaw.catch_rate_uplift_at_equal_cost
              ? `${flaw.catch_rate_uplift_at_equal_cost}× MORE AT THE SAME OPERATOR COST`
              : 'CAUGHT DEFECTS THE LIMITS MISSED ENTIRELY'}
          </span>
        </div>
      </div>

      {curve.length > 0 && (
        <details className="dc__details">
          <summary>What a looser alarm budget buys</summary>
          <table className="dc__table">
            <caption>
              A plant chooses its own tolerance for false line stops. This is the trade-off, not a single
              cherry-picked operating point.
            </caption>
            <thead>
              <tr>
                <th scope="col">Good parts stopped</th>
                <th scope="col">Defects caught</th>
              </tr>
            </thead>
            <tbody>
              {curve.map((point) => (
                <tr key={point.false_alarm_budget_pct}>
                  <th scope="row" className="num">
                    {point.good_parts_stopped_pct}%
                  </th>
                  <td className="num">{point.defects_caught_pct}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </details>
      )}

      <footer className="dc__provenance">
        <span className="dc__provenance-tag">{state.data.data_provenance}</span>
        <span>
          Computed live on {flaw.total_evaluated_parts} parts replicating the design of{' '}
          <a href={state.data.citation_url} target="_blank" rel="noreferrer noopener">
            {state.data.citation}
          </a>
          . Not the original measured parts, and not a plant result.
        </span>
      </footer>
    </section>
  );
}

export default DetectionComparison;
