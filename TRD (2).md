# TRD — Technical Requirements & Design

## 1. Module Contracts (src/)
| Module | Inputs | Outputs | Rules |
|---|---|---|---|
| schema.py | — | Pydantic: WellState, Scenario, ScenarioResult, ConstraintCheck, Recommendation, Confidence, Diagnostic | Single source of types; units in field names |
| data_generator.py | seed=26120 | timeseries + scenario catalogue; writes CSVs AND seeds DB | Preserve existing causal generation logic |
| db/repository.py | SQLAlchemy session | typed reads/writes | ONLY module touching the DB |
| db/adapter.py | DATABASE_URL | DataFrames / WellState inputs | One interface: CSV-fallback, SQLite now, Postgres/Supabase later |
| state_estimator.py | latest rows | WellState + DataQuality | Fails safe on gaps/stale/dupes; rejects bad units |
| css_model.py | steam_mass, inj_h, soak_h, p | T trajectory, phase machine, Q_in/Q_loss terms, physics residual | dT/dt=(Q_in−Q_rad−Q_vert−Q_prod)/C_eff; IAPWS optional w/ fallback |
| viscosity_model.py | T, fluid params | μ(T), band, support flag | μ=μ_ref·exp(−k(T−T_ref)); monotonicity enforced |
| inflow_model.py | μ, p_r, p_wf, ProductivityConfig | PI, mobility, inflow | PI=0.00708·(kh/μB)/[ln(re/rw)−0.75+S]; q=PI·Δp |
| srp_model.py | inflow, SPM, stroke, μ | fillage, load, energy, card features | capacity=k·SPM·stroke; fillage=inflow/capacity·100 |
| srp_diagnostics.py | card features + rolling baseline | fired rules incl. ROD_FLOATING, FLUID_POUND, ROD_LOADING, VALVE_INSPECT, INSUFFICIENT_DATA | Rules-first; each alert shows rule+thresholds+data quality |
| scenario_engine.py | user ranges | ≥50 ScenarioResult | Calls SAME physics modules — no second formula set anywhere |
| constraints.py | ScenarioResult | feasible, margins, rejection_reasons | Limits read from operating_limits table |
| optimizer.py | feasible only | ranked + objective contributions | score=w_oil·oil−w_steam·steam−w_energy·energy−w_risk·risk; weights editable |
| uncertainty.py | run context | Confidence{completeness, support, residual, extrapolation} | Can downgrade/suppress; never edits prediction |
| validation.py | cycles 1–4 | temporal MAE/RMSE, physics pass, counterfactual diff | Chronological splits only; no shuffle |
| app.py | — | Streamlit UI | UI renders results only; zero physics in UI |

## 2. Canonical Equations (defined once, reused everywhere)
- Thermal: lumped first-order balance; phase state machine injection→soak→production.
- Viscosity: μ(T)=μ_ref·exp(−k·(T−T_ref)) Celsius demo form; params from
  fluid_properties table, status SYNTHETIC/UNCALIBRATED.
- Inflow: single-phase PI proxy; mobility=k/(μB).
- SRP: fillage=inflow/(k·SPM·stroke)·100; load=base+a·μ+b·SPM+c·(100−fillage);
  energy proxy per problem dataset; synthetic load–position card
  (max/min/range/area/mean/repeatability).
- Ranking: transparent linear weighted objective on normalized terms.

## 3. Determinism & Performance
- Fixed seed 26120; pytest asserts identical CSV regeneration.
- Vectorized scenario evaluation (NumPy), ≤5 s for 60 candidates.

## 4. Tests (pytest)
- test_causality: T↑⇒μ↓⇒inflow↑; inflow↑⇒fillage/load change; SPM↑⇒energy↑.
- test_constraints: invalid scenarios rejected with exact reasons.
- test_reproducibility: seed 26120 → identical CSVs.
- test_validation_splits: chronological only, no leakage.

## 5. Error Handling
- Missing/stale sensor → quality flag; rec suppressed if FAIL.
- Out-of-support scenario → extrapolation flag + confidence penalty.
- DB unavailable → read-only CSV fallback via adapter.
