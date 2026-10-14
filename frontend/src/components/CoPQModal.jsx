import React, { useState, useEffect } from 'react';
import './CoPQModal.css';
import { fetchCoPQParameters, updateCoPQParameters } from '../hooks/useApi';

const DEFAULT_PARAMS = {
  resin_type: 'PP / ABS Automotive Grade',
  resin_price_per_kg: 195.0,
  part_weight_grams: 220.0,
  runner_scrap_fraction: 0.08,
  regrind_recovery_credit: 0.25,
  machine_hourly_rate: 1650.0,
  cycle_time_seconds: 24.0,
  machine_power_kw: 18.5,
  electricity_tariff_per_kwh: 9.80,
  sorting_cost_per_part: 22.0,
  oem_penalty_risk_per_defect: 150.0,
};

export function CoPQModal({ isOpen, onClose }) {
  const [params, setParams] = useState(DEFAULT_PARAMS);
  const [loading, setLoading] = useState(false);
  const [saveStatus, setSaveStatus] = useState(null);

  useEffect(() => {
    if (isOpen) {
      loadParams();
    }
  }, [isOpen]);

  const loadParams = async () => {
    try {
      const data = await fetchCoPQParameters();
      if (data) {
        setParams(data);
      }
    } catch (err) {
      console.warn('Using default CoPQ parameters:', err.message);
    }
  };

  if (!isOpen) return null;

  const handleChange = (field, val) => {
    setParams((prev) => ({
      ...prev,
      [field]: typeof prev[field] === 'number' ? Number(val) : val,
    }));
  };

  // Real-time client preview math
  const partKg = (params.part_weight_grams || 220) / 1000.0;
  const grossKg = partKg * (1.0 + (params.runner_scrap_fraction || 0.08));
  const matCost = grossKg * (params.resin_price_per_kg || 195) * (1.0 - (params.regrind_recovery_credit || 0.25));
  const burdenCost = ((params.machine_hourly_rate || 1650) / 3600.0) * (params.cycle_time_seconds || 24);
  const energyCost = (params.machine_power_kw || 18.5) * ((params.cycle_time_seconds || 24) / 3600.0) * (params.electricity_tariff_per_kwh || 9.8);
  const sortCost = params.sorting_cost_per_part || 22;
  const directCoPQ = matCost + burdenCost + energyCost + sortCost;
  const totalCoPQ = directCoPQ + (params.oem_penalty_risk_per_defect || 150);

  const handleSave = async () => {
    setLoading(true);
    setSaveStatus(null);
    try {
      await updateCoPQParameters(params);
      setSaveStatus('✓ Parameters saved & active across decision engine');
      setTimeout(() => {
        setSaveStatus(null);
        onClose();
      }, 700);
    } catch (err) {
      setSaveStatus(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleResetDefaults = () => {
    setParams(DEFAULT_PARAMS);
  };

  return (
    <div className="modal-backdrop" onClick={onClose} role="dialog" aria-modal="true" aria-labelledby="copq-modal-title">
      <div className="copq-modal" onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="copq-modal__header">
          <div>
            <div className="copq-modal__title-row">
              <h2 id="copq-modal-title" className="copq-modal__title">
                PARAMETRIC COST OF POOR QUALITY (CoPQ) ENGINE
              </h2>
              <span className="pill pill--mist">CONFIGURABLE PLANT MODEL</span>
            </div>
            <p className="copq-modal__subtitle">
              Configurable manufacturing cost model for Indian Tier-2/Tier-3 automotive injection molders.
            </p>
          </div>
          <button type="button" className="copq-modal__close" onClick={onClose} aria-label="Close modal">
            ✕
          </button>
        </div>

        {/* Modal Body: 2-Column Layout (Inputs on Left, Live Breakdown on Right) */}
        <div className="copq-modal__body">
          {/* Left Column: Sliders & Inputs */}
          <div className="copq-form">
            <span className="label-section">1. RESIN &amp; PART SPECIFICATIONS</span>
            <div className="copq-field-grid">
              <div className="copq-field">
                <label>Resin Price (₹/kg)</label>
                <div className="input-with-unit">
                  <input
                    type="number"
                    step="5"
                    value={params.resin_price_per_kg}
                    onChange={(e) => handleChange('resin_price_per_kg', e.target.value)}
                  />
                  <span>₹/kg</span>
                </div>
              </div>
              <div className="copq-field">
                <label>Part Weight (grams)</label>
                <div className="input-with-unit">
                  <input
                    type="number"
                    step="10"
                    value={params.part_weight_grams}
                    onChange={(e) => handleChange('part_weight_grams', e.target.value)}
                  />
                  <span>g</span>
                </div>
              </div>
              <div className="copq-field">
                <label>Runner Scrap Fraction</label>
                <div className="input-with-unit">
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="0.5"
                    value={params.runner_scrap_fraction}
                    onChange={(e) => handleChange('runner_scrap_fraction', e.target.value)}
                  />
                  <span>{(params.runner_scrap_fraction * 100).toFixed(0)}%</span>
                </div>
              </div>
              <div className="copq-field">
                <label>Regrind Recovery Credit</label>
                <div className="input-with-unit">
                  <input
                    type="number"
                    step="0.05"
                    min="0"
                    max="0.5"
                    value={params.regrind_recovery_credit}
                    onChange={(e) => handleChange('regrind_recovery_credit', e.target.value)}
                  />
                  <span>{(params.regrind_recovery_credit * 100).toFixed(0)}%</span>
                </div>
              </div>
            </div>

            <span className="label-section" style={{ marginTop: '12px' }}>2. PRESS &amp; ENERGY BURDEN</span>
            <div className="copq-field-grid">
              <div className="copq-field">
                <label>Machine Burden Rate (₹/hr)</label>
                <div className="input-with-unit">
                  <input
                    type="number"
                    step="50"
                    value={params.machine_hourly_rate}
                    onChange={(e) => handleChange('machine_hourly_rate', e.target.value)}
                  />
                  <span>₹/hr</span>
                </div>
              </div>
              <div className="copq-field">
                <label>Nominal Cycle Time</label>
                <div className="input-with-unit">
                  <input
                    type="number"
                    step="1"
                    value={params.cycle_time_seconds}
                    onChange={(e) => handleChange('cycle_time_seconds', e.target.value)}
                  />
                  <span>sec</span>
                </div>
              </div>
              <div className="copq-field">
                <label>Active Power Draw</label>
                <div className="input-with-unit">
                  <input
                    type="number"
                    step="1"
                    value={params.machine_power_kw}
                    onChange={(e) => handleChange('machine_power_kw', e.target.value)}
                  />
                  <span>kW</span>
                </div>
              </div>
              <div className="copq-field">
                <label>Electricity Tariff (₹/kWh)</label>
                <div className="input-with-unit">
                  <input
                    type="number"
                    step="0.2"
                    value={params.electricity_tariff_per_kwh}
                    onChange={(e) => handleChange('electricity_tariff_per_kwh', e.target.value)}
                  />
                  <span>₹/kWh</span>
                </div>
              </div>
            </div>

            <span className="label-section" style={{ marginTop: '12px' }}>3. CONTAINMENT SORTING &amp; OEM RISK</span>
            <div className="copq-field-grid">
              <div className="copq-field">
                <label>Secondary Sorting Labor</label>
                <div className="input-with-unit">
                  <input
                    type="number"
                    step="2"
                    value={params.sorting_cost_per_part}
                    onChange={(e) => handleChange('sorting_cost_per_part', e.target.value)}
                  />
                  <span>₹/part</span>
                </div>
              </div>
              <div className="copq-field">
                <label>OEM Line Stoppage Risk</label>
                <div className="input-with-unit">
                  <input
                    type="number"
                    step="25"
                    value={params.oem_penalty_risk_per_defect}
                    onChange={(e) => handleChange('oem_penalty_risk_per_defect', e.target.value)}
                  />
                  <span>₹/defect</span>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Live Itemized Breakdown Card */}
          <div className="copq-summary-card">
            <span className="label-section">LIVE ITEMIZED CoPQ BREAKDOWN</span>
            <div className="copq-summary-table">
              <div className="summary-row">
                <span>Resin Material Scrap:</span>
                <span className="num">₹{matCost.toFixed(2)}</span>
              </div>
              <div className="summary-row">
                <span>Machine Hour Burden:</span>
                <span className="num">₹{burdenCost.toFixed(2)}</span>
              </div>
              <div className="summary-row">
                <span>Energy Electricity Consumption:</span>
                <span className="num">₹{energyCost.toFixed(2)}</span>
              </div>
              <div className="summary-row">
                <span>Secondary Containment Sorting:</span>
                <span className="num">₹{sortCost.toFixed(2)}</span>
              </div>
              <div className="summary-row summary-row--direct">
                <span>Direct Scrap at Press:</span>
                <span className="num">₹{directCoPQ.toFixed(2)}</span>
              </div>
              <div className="summary-row">
                <span>Downstream OEM Stoppage Risk:</span>
                <span className="num">₹{Number(params.oem_penalty_risk_per_defect || 150).toFixed(2)}</span>
              </div>
              <div className="summary-row summary-row--total">
                <span>Comprehensive Unit CoPQ:</span>
                <span className="num">₹{totalCoPQ.toFixed(2)}</span>
              </div>
            </div>

            <div className="copq-insight-box">
              <div className="copq-insight-title">Shop-Floor Decision Insight:</div>
              <p>
                In a typical 500-part shift run, catching drift <strong>14 cycles earlier</strong> saves{' '}
                <strong>₹{(14 * directCoPQ).toLocaleString('en-IN', { maximumFractionDigits: 0 })}</strong> in direct press scrap and prevents{' '}
                <strong>₹{(14 * (params.sorting_cost_per_part || 22)).toFixed(0)}</strong> in unnecessary secondary containment inspection.
              </p>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="copq-modal__footer">
          <div className="footer-left">
            <button type="button" className="btn-secondary" onClick={handleResetDefaults} disabled={loading}>
              ↺ Reset to Tier-2 Defaults
            </button>
            {saveStatus && <span className="save-status-msg">{saveStatus}</span>}
          </div>
          <div className="footer-right">
            <button type="button" className="btn-secondary" onClick={onClose} disabled={loading}>
              Cancel
            </button>
            <button type="button" className="btn-primary" onClick={handleSave} disabled={loading}>
              {loading ? 'Saving...' : '✓ Apply Parameters to Decision Loop'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
