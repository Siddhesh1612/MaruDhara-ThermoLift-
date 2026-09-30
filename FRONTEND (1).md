# FRONTEND — Streamlit UI Guide

## Global
- Top banner on EVERY page: "PROTOTYPE MODE — REPRESENTATIVE SYNTHETIC DATA".
- Sidebar: well selector (BWG-SIM-001), CSS phase indicator, data-quality badge.
- Units displayed beside every engineering value.
- recommendation/audit actions require confirmation.

## Tabs
### 1. Current State
- Metric cards: Temperature °C, Viscosity kCP, Reservoir/BHP bar, Inflow bpd,
  Oil rate bpd, Fillage %, SRP load kN, Energy kWh/bbl, Risk 0–100.
- Phase timeline strip (injection/soak/production colours).
- Provenance footer: source_label, seed, model_version, assumption status.

### 2. What-If Simulator (demo heart)
- Sliders: steam mass (90–122 t), soak (36–72 h), SPM (6–8), stroke (1.45–1.65 m).
- "Simulate" button → runs scenario_engine.
- Outputs:
  a) Physics chain chart: Temperature vs Viscosity over cycle (dual axis),
     phase-shaded (reuse existing figure style).
  b) Scenario scatter: energy proxy (x) vs oil-rate proxy (y);
     colour = feasible/rejected; ring = top ranked; hover = scenario_id + reasons.
  c) Comparison table with constraint margins; rejected rows show exact reason.
  d) Weight sliders (w_oil, w_steam, w_energy, w_risk) — visible, editable;
     re-rank live.

### 3. Recommendation Card
Fields: recommended scenario id · CSS controls · SRP controls · expected oil
proxy · steam/energy proxy · fillage/load · constraint margins · confidence %
[labelled illustrative] · WHY selected (engineering sentence, not "AI chose") ·
"What could invalidate this" · Operator action: Approve / Modify / Reject /
Annotate → writes audit row.

### 4. SRP Diagnostics
- Synthetic dynamometer card (load vs position) with features list.
- Active rules feed: ROD_FLOATING / FLUID_POUND / ROD_LOADING / VALVE_INSPECT /
  INSUFFICIENT_DATA — each with fired rule, thresholds, data quality.
- Low fillage and high load visibly mapped to the problem statement.

### 5. Validation
- Temporal: replay cycles 1–2 train / 3 val / 4 test; MAE/RMSE per cycle chart.
- Physics: monotonicity check badges (T↑⇒μ↓, μ↓⇒inflow↑, inflow⇒fillage).
- Counterfactual: baseline vs alternative action replay, labelled
  "MODEL-BASED COUNTERFACTUAL SIMULATION".

### 6. 3D Well Layer (last priority, visual only)
- Plotly 3D: reservoir zone colour = thermal state/phase; wellbore fluid colour
  = temperature/viscosity; pump icon = SPM + fillage/load/risk; surface = oil
  rate indicator; selected scenario = before/after overlay toggle.
- Rule: 3D REFLECTS computed state; never replaces the computational loop.

## Styling
Clean engineering aesthetic; Plotly template consistent with the existing
validation figure (cream background, orange T line, blue viscosity line,
green feasible / faded rejected dots).
