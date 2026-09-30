# THERMOLIFT / MaruDhara — Feature Upgrade Specification (SIH26120)

**Document Version:** 2.0.0  
**Status:** Approved Architectural Baseline & Upgrade Blueprint  
**Asset Target:** Baghewala Heavy Oil Field • Well `BWG-SIM-001` • Jodhpur Sandstone  
**Coupled System:** Cyclic Steam Stimulation (CSS) + Sucker Rod Pumping (SRP)

---

## 1. Current Baseline Overview

The initial prototype established an operational baseline with the following components:
1. **Database & Persistence:** SQLite database (`data/thermolift.db`) mapping 14 tables via SQLAlchemy models with strict single-entrypoint repository (`src/db/repository.py`).
2. **Synthetic Data Generation:** 4 cycles × 28 days (2,688 hourly records) generated deterministically using seed `26120`.
3. **Core Physics Modules:**
   - Thermal Balance: Lumped $dT/dt = (Q_{in} - Q_{rad} - Q_{vert} - Q_{prod}) / C_{eff}$ (`src/css_model.py`).
   - Viscosity Correlation: $\mu(T) = \mu_{ref} \cdot \exp(-k(T - T_{ref}))$ with enforced $d\mu/dT < 0$ (`src/viscosity_model.py`).
   - Inflow Model: Analytical productivity index $J = 0.00708 \frac{kh}{\mu B (\ln(r_e/r_w) - 0.75 + s)}$ (`src/inflow_model.py`).
   - SRP Model: Kinematic capacity, fillage, polished rod load, and synthetic dynamometer card (`src/srp_model.py`).
4. **Scenarios & Constraints:** 60-point parameter grid plus custom slider point evaluated against hard thresholds (fillage $\ge 52\%$, load $\le 62\,\text{kN}$, steam $\le 118\,\text{t}$).
5. **UI & 3D Visualization:** Streamlit dashboard with tabs for Current State, Simulator, Recommendation, Diagnostics, Validation, and interactive Three.js 3D physical digital twin.

---

## 2. Core Architecture Philosophy: The Single Coupled System

The central architectural imperative is that **CSS and SRP must behave as ONE COUPLED SYSTEM**.
An operational change in CSS propagates strictly through the causal chain:

$$\text{Steam Input } (m_s, t_{inj}, t_{soak}) \longrightarrow \text{Thermal Response } (T(t)) \longrightarrow \text{In-Situ Viscosity } (\mu(T))$$
$$\longrightarrow \text{Fluid Mobility \& Inflow } (J, q_{inflow}) \longrightarrow \text{Wellbore / SRP Response } (Fillage, Load, PPRL, MPRL)$$
$$\longrightarrow \text{Production, Energy \& Risk Metrics} \longrightarrow \text{Operational Constraints} \longrightarrow \text{Objective Scoring}$$

This relationship is:
- **Executable:** Evaluated directly through pure, typed Python functions.
- **Traceable:** Every candidate carries complete provenance, deterministic hashes, and unit-explicit fields.
- **Auditable:** Logged in the relational database with operator sign-off.
- **Shared:** Zero duplicate physics equations between independent and coupled optimization.

---

## 3. New Features by Priority

### P0 — Core Engineering Credibility
1. **Coupled-vs-Independent Ablation (`src/ablation.py`):**
   - **Mode A (Independent):** Optimizes CSS first in isolation, freezes the chosen thermal state, then optimizes SRP controls.
   - **Mode B (Coupled):** Jointly evaluates $(m_s, t_{soak}, \text{SPM}, S)$ across the complete causal chain simultaneously.
   - Shared physics, identical candidate bounds, limits, and objective definitions.
   - Comparison view showing KPI deltas (oil, steam, SOR, energy, fillage, load, risk, rejected candidates) and causal explanations.
2. **Transparent Optimizer Objective (`src/objective.py`):**
   - Normalized multi-objective formulation:
     $$\text{Score} = w_{oil} \cdot \bar{B}_{oil} - w_{steam} \cdot \bar{P}_{steam} - w_{energy} \cdot \bar{P}_{energy} - w_{risk} \cdot \bar{R}_{mech} - w_{maint} \cdot \bar{R}_{maint}$$
   - Bounded min-max normalization with safe zero-denominator handling.
   - Exposes raw metrics, normalized scores, weights, and signed contributions.
3. **Single Authoritative Physics Path:**
   - Centralized model release (`MODEL_VERSION = "v2.0"`).
   - Strict rule: No UI or diagnostic script ever recalculates physics independently.
4. **Complete Candidate Provenance (`src/schema.py` & `src/scenario_engine.py`):**
   - Deterministic `input_state_hash` (SHA-256) over state inputs and parameters.
   - Provenance metadata: `scenario_id`, `well_id`, `timestamp`, `model_version`, `assumption_set`, `random_seed`, and component breakdowns.
5. **Constraint Margins (`src/constraints.py`):**
   - Signed margins: $\text{Margin} = \text{Actual} - \text{Threshold}$ (or $\text{Threshold} - \text{Actual}$ as appropriate).
   - Rejections contain: failed constraint name, threshold, actual, signed margin, and exact human-readable reason.

### P1 — High-Value Decision Support Features
6. **Counterfactual Replay / Time Machine (`src/counterfactual.py`):**
   - Selects a historical synthetic cycle state, freezes it, and simulates alternative operator actions.
   - Compares actual historical trajectory vs. model-based counterfactual with uncertainty bounds.
   - Mandatory label: `MODEL-BASED COUNTERFACTUAL REPLAY — NOT A MEASURED FIELD RESULT`.
7. **Minimum-Necessary-Steam / Thermal Target Solver (`src/thermal_target.py`):**
   - Answers: *"What is the least steam intervention required to reach the thermal/viscosity state that makes the SRP cycle mechanically and economically viable?"*
   - Target-based solver reporting minimum feasible steam, resulting states, and limiting constraints.
8. **Interactive SRP Diagnostic Card (`src/srp_diagnostics.py` & `src/srp_model.py`):**
   - Detailed surface and downhole cards: position, load, PPRL, MPRL, load span, area, fillage, and viscous drag.
   - Dynamic comparison: Baseline Card vs. Scenario Card with feature deltas.
9. **Wellbore-to-Surface Pressure Chain (`src/pressure_chain.py`):**
   - Reduced-order hydraulic gradient: $P_{res} \to \text{PIP} \to \text{WHP} \to \text{Choke} \to \text{Flowline} \to \text{Separator}$.
   - Surface backpressure constraints directly influence well inflow and pump feasibility.
10. **Actionable Uncertainty Gate (`src/uncertainty.py`):**
    - 4-component assessment: Data completeness, Model support, Residual uncertainty, and Extrapolation distance.
    - Tri-state action gate: `GREEN` (eligible), `AMBER` (warning), `RED` (suppressed recommendation).
11. **Nearest-Alternative Comparison (`src/nearest_alternative.py`):**
    - Normalized decision-space Euclidean distance:
      $$d(s_1, s_2) = \sqrt{\sum \left(\frac{x_{1,i} - x_{2,i}}{\Delta x_i}\right)^2}$$
    - Evaluates trade-offs between the optimal scenario and the closest distinct feasible alternative.

### P2 — Advanced Scientific Capabilities
12. **Sensitivity Analysis (`src/sensitivity.py`):**
    - One-at-a-time (OAT) deterministic parameter perturbations ($\pm 10\%$, $\pm 20\%$) across steam, soak, SPM, and stroke.
    - Ranked tornado metrics measuring output sensitivities.
13. **True Pareto Frontier (`src/pareto.py`):**
    - Strict multi-objective nondominated sorting (maximizing oil, minimizing steam, minimizing energy, minimizing mechanical risk).
    - Identifies true Pareto-optimal candidates without scalar weighting.
14. **Physics + Residual ML Pathway (`src/residual_ml.py`):**
    - Hybrid architecture: $\hat{y} = y_{physics} + \Delta y_{ML}$.
    - Optional, explainable Ridge/GBR residual model trained strictly on physical residual errors.
15. **Field-Data Calibration Contract (`docs/FIELD_DATA_CONTRACT.md`):**
    - Specification for real-world SCADA, dynamometer, and laboratory PVT ingestion.

---

## 4. Database Schema Upgrades

The schema in `db/schema.sql` and SQLAlchemy models in `src/db/models.py` are extended to support:
- `scenarios`: Added `input_state_hash`, `model_version`, `assumption_set`, `seed`, `p_wf_bar`, `pip_bar`, `whp_bar`, `flowline_p_bar`, `margin_fillage`, `margin_load`, `margin_steam`, `norm_oil`, `norm_steam`, `norm_energy`, `norm_risk`, `norm_maint`.
- `ablation_experiments`: Records mode (`INDEPENDENT` vs `COUPLED`), chosen scenario, execution time, and summary KPIs.
- `pressure_chain_runs`: Records nodal pressures across the hydraulic chain.
- `model_weights`: Extended to include $w_{maint}$ alongside $w_{oil}, w_{steam}, w_{energy}, w_{risk}$.

---

## 5. UI Architecture & Tab Structure

Preserving all existing visual work while integrating the enhanced modules:
1. **📊 Current State:** 10 KPI cards, live WellState, Pressure Chain summary, and Uncertainty Gate badge.
2. **⚡ What-If Simulator:** Real-time coupled sliders, normalized objective contribution breakdown, signed constraint margins, and trade-off scatter.
3. **🔬 Coupling Lab:** Side-by-side Independent vs. Coupled ablation matrix, KPI deltas, and causal mechanism narrative.
4. **🎯 Recommendation:** Chosen scenario, trade-off radar, nearest feasible alternative comparison, and operator audit actions.
5. **📈 SRP Diagnostics:** Interactive dynamometer cards (Baseline vs. Scenario), PPRL/MPRL, fluid pound, and rule alerts.
6. **⏳ Time Machine:** Historical synthetic state selector, actual vs. model-based counterfactual trajectory, and deviation metrics.
7. **🎯 Thermal Target:** Minimum-necessary-steam solver based on target viscosity or temperature.
8. **🌪️ Sensitivity & Pareto:** Ranked tornado charts and true nondominated Pareto frontier.
9. **🔬 Validation:** Chronological validation splits, monotonicity checks, and counterfactual validation.
10. **🌐 Photorealistic 3D Model:** High-fidelity Three.js wellbore-to-surface twin reflecting the authoritative state.

---

## 6. Testing & Quality Assurance Plan

- **Existing Tests:** Ensure all 8 baseline unit tests continue to pass without modification.
- **New Tests:**
  1. `test_objective.py`: Contribution sums equal score; weight sensitivity; zero-denominator handling.
  2. `test_ablation.py`: CSS changes alter SRP outcomes; independent vs. coupled execution consistency.
  3. `test_provenance.py`: Deterministic hash stability; state change alters hash; parameter change alters hash.
  4. `test_pressure_chain.py`: Nodal pressure monotonicity ($P_{res} > \text{PIP} > \text{WHP} > P_{sep}$); surface constraints enforce feasibility.
  5. `test_thermal_target.py`: Target viscosity yields minimum feasible steam; constraints bound solution.
  6. `test_uncertainty_gate.py`: High penalty forces AMBER/RED; RED suppresses recommendation; raw predictions unaltered.
  7. `test_pareto.py`: Nondominated sorting satisfies Pareto dominance axioms.

---

## 7. Migration Notes & Limitations

- **Migration:** Schema extensions use `IF NOT EXISTS` and optional column additions compatible with SQLite and PostgreSQL.
- **Limitations:**
  - All dataset telemetry remains synthetic (seed `26120`).
  - No autonomous well control is claimed; system operates strictly as advisory decision support.
  - Multi-phase flow in the pressure chain uses a validated reduced-order hydraulic proxy rather than full transient multiphase simulation.
