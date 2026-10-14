import React, { useEffect } from 'react';
import './ContainmentTag.css';

/**
 * The paper artifact the shop floor actually consumes.
 *
 * Containing a lot in a database contains nothing: on a real floor the bin gets
 * a tag and someone signs it. This renders that tag from the live containment
 * record and prints it, so the loop ends where the plant's loop ends.
 *
 * Sign-off lines are deliberately blank -- the tag records a human decision and
 * must not pre-fill one.
 */
export function ContainmentTag({ isOpen, onClose, milestones, windowData, context }) {
  useEffect(() => {
    if (!isOpen) {
      return undefined;
    }
    const onKeyDown = (event) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) {
    return null;
  }

  const from = milestones?.suspect_lot_start;
  const to = milestones?.lot_release;
  const printedAt = new Date();

  return (
    <div className="ctag-overlay" role="dialog" aria-modal="true" aria-labelledby="ctag-heading">
      <div className="ctag-shell">
        <div className="ctag-shell__bar">
          <span>Suspect lot tag &mdash; print and attach to the bin</span>
          <div className="ctag-shell__actions">
            <button type="button" className="ctag-btn ctag-btn--primary" onClick={() => window.print()}>
              Print tag
            </button>
            <button type="button" className="ctag-btn" onClick={onClose}>
              Close
            </button>
          </div>
        </div>

        <article className="ctag" id="containment-tag-sheet">
          <header className="ctag__head">
            <div className="ctag__status" id="ctag-heading">
              {milestones?.lot_release != null ? 'RELEASED' : 'QUARANTINE HOLD'}
            </div>
            <div className="ctag__issuer">
              <strong>PROCESS GUARDIAN</strong>
              <span>Suspect lot containment tag</span>
            </div>
          </header>

          <section className="ctag__identity">
            <Field label="Machine" value={context?.machineId} />
            <Field label="Mold" value={context?.moldId} />
            <Field label="Part" value={context?.partId} />
            <Field label="Recipe" value={context?.recipeId} />
          </section>

          <section className="ctag__lot">
            <div className="ctag__lot-main">
              <span className="ctag__lot-label">Contained cycles</span>
              <span className="ctag__lot-range">
                {from != null ? `${from}` : '—'} &rarr; {to != null ? `${to}` : 'open'}
              </span>
            </div>
            <div className="ctag__lot-count">
              <span className="ctag__lot-label">Parts held</span>
              <span className="ctag__lot-qty">{windowData?.quarantined_part_count ?? '—'}</span>
            </div>
          </section>

          <section className="ctag__reason">
            <span className="ctag__field-label">Reason for hold</span>
            <p>
              Process drift detected at cycle {milestones?.drift_start ?? '—'}. Last verified good part at
              cycle {milestones?.last_verified_good ?? '—'}. Everything produced after that point is suspect
              until it is physically inspected and dispositioned.
            </p>
          </section>

          <section className="ctag__trail">
            <Row label="Last verified good" value={milestones?.last_verified_good} />
            <Row label="Drift detected" value={milestones?.drift_start} />
            <Row label="Correction applied" value={milestones?.action_applied} />
            <Row label="Process stabilized" value={milestones?.stabilized} />
            <Row label="Lot released" value={milestones?.lot_release} />
          </section>

          <section className="ctag__signoff">
            <div className="ctag__sign">
              <span className="ctag__sign-rule" />
              <span className="ctag__field-label">Quality inspector &mdash; name &amp; signature</span>
            </div>
            <div className="ctag__sign">
              <span className="ctag__sign-rule" />
              <span className="ctag__field-label">Date &amp; shift</span>
            </div>
            <div className="ctag__disposition">
              <span className="ctag__field-label">Disposition</span>
              <div className="ctag__boxes">
                <label>
                  <span className="ctag__box" /> Release
                </label>
                <label>
                  <span className="ctag__box" /> Sort 100%
                </label>
                <label>
                  <span className="ctag__box" /> Scrap
                </label>
              </div>
            </div>
          </section>

          <footer className="ctag__foot">
            Advisory only &mdash; Process Guardian does not write to the machine. Cycle numbers come from a
            simulated run. Printed {printedAt.toLocaleString()}.
          </footer>
        </article>
      </div>
    </div>
  );
}

function Field({ label, value }) {
  return (
    <div className="ctag__field">
      <span className="ctag__field-label">{label}</span>
      <span className="ctag__field-value">{value || '—'}</span>
    </div>
  );
}

function Row({ label, value }) {
  return (
    <div className="ctag__row">
      <span>{label}</span>
      <span className="ctag__row-value">{value != null ? `Cycle ${value}` : 'not reached'}</span>
    </div>
  );
}

export default ContainmentTag;
