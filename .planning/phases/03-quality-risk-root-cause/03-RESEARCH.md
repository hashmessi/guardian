# Phase 3: Quality Risk + Root-Cause Evidence — Research & Architecture

## Mathematical & Technical Design

### 1. Temporal Feature Engineering (QRSK-02)
For each incoming cycle $t$ and process parameter $j \in \{1 \dots M\}$:
- **Instantaneous state**: Value $x_{t, j}$, standardized $z$-score $z_{t, j} = \frac{x_{t, j} - \mu_j}{\sigma_j}$, raw baseline delta $\Delta_{t, j} = x_{t, j} - \mu_j$.
- **Short & Medium Rolling Moments**:
  - Rolling mean $\bar{x}_{t, j}^{(W)}$ for $W \in \{5, 15\}$.
  - Rolling standard deviation $s_{t, j}^{(W)}$ and ratio to baseline $\frac{s_{t, j}^{(W)}}{\sigma_j}$.
  - Rolling min, max, and peak-to-peak spread.
- **Dynamic Trends**: Rolling least-squares linear slope $\beta_{t, j}$ and trend coefficient $R_{t, j}^2$.
- **Lags & Differences**: Lag-1 $x_{t-1, j}$, Lag-2 $x_{t-2, j}$, first difference $\Delta x_t = x_t - x_{t-1}$, second difference $\Delta^2 x_t$.
- **Domain-Specific Physics Interaction Terms**:
  - Thermal gradient: $\text{gradient}_{\text{nozzle}} = T_{\text{nozzle}} - T_{\text{z5}}$
  - Barrel heating gradient: $T_{\text{z3}} - T_{\text{z1}}$
  - Effective melt temperature: $T_{\text{eff}} = 0.50 T_{\text{z3}} + 0.30 T_{\text{z4}} + 0.20 T_{\text{nozzle}}$
  - Pressure transfer index: $\frac{P_{\text{peak}}}{P_{\text{inj}}}$
  - Packing pressure ratio: $\frac{P_{\text{hold}}}{P_{\text{peak}}}$
  - Cooling ratio: $\frac{t_{\text{cool}}}{t_{\text{cycle}}}$
  - Moisture index: $M_{\text{resin}} \times T_{\text{eff}}$
  - Cushion proxy / volumetric metric: $\propto P_{\text{hold}} \times t_{\text{hold}}$

### 2. Calibrated Probability Estimation (QRSK-01, QRSK-03, QRSK-04)
- **Model**: `XGBClassifier` trained on multi-regime simulation history (nominal, thermal drift, pressure drift, moisture drift, cycle instability, sensor jitter).
- **Probability Calibration**: `CalibratedClassifierCV(method='sigmoid', cv='prefit')` (Platt scaling) or `method='isotonic'` to guarantee that $P(\text{Defect}) = 0.70$ corresponds to an empirical 70% defect rate.
- **Confidence Score**: Derived from prediction margin, ensemble variance, and feature distance within the training manifold:
  $$\text{Confidence} = 1.0 - 2 \cdot |P - 0.5| \cdot (1 - \text{manifold\_density})$$
- **State Classification**:
  - `LOW` ($P < 0.30$): Safe production.
  - `MEDIUM` ($0.30 \le P \le 0.70$): Quality risk watch state, sample part inspection recommended.
  - `HIGH` ($P > 0.70$): Immediate quality risk, triggers intervention engine evaluation.

### 3. Root-Cause Attribution & Honest Evidence Generation (ROOT-01, ROOT-02, ROOT-03)
- **Attribution Computation**: Combines tree feature attribution (SHAP values / gain importances) with standardized parameter divergence ($|z_{t, j}| \cdot |\beta_{t, j}|$).
- **Percentage Normalization**:
  $$\text{Contribution}_j = \frac{\max(0, A_j)}{\sum_{k} \max(0, A_k)} \times 100\% \quad \left(\sum_j \text{Contribution}_j \equiv 100.0\%\right)$$
- **Evidence Formatting**: Itemizes concrete empirical observations:
  - "Zone 3 temperature shifted $+3.2^\circ\text{C}$ ($+4.9\sigma$) from baseline with steady $+0.20^\circ\text{C}/\text{cycle}$ trend"
  - "Peak injection pressure dropped $-5.8\text{ bar}$ ($-4.1\sigma$) due to lowered melt viscosity"
- **Epistemic Honesty Constraint**:
  - Language filter enforces strict terms: `"likely contributor"`, `"observed evidence"`, `"modeled effect"`, `"confidence: 85%"`.
  - Forbids deterministic causal claims: `"guaranteed cause"`, `"proven root cause"`, `"defect definitely caused by"`.
