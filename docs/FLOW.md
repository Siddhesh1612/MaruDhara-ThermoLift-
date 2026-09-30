# FLOW — Runtime & Data Flows

## 1. Boot Flow
python src/data_generator.py            # once: writes CSVs + seeds DB via repository
streamlit run app.py                    # adapter loads latest WellState → dashboard

## 2. Simulation Flow ("Simulate" click)
1. UI collects {steam_mass, soak_h, spm, stroke} sliders
2. scenario_engine builds 5×4×3 grid (60) ∪ user custom point
3. EACH candidate runs the SAME chain as live replay:
   css_model → viscosity_model → inflow_model → srp_model
4. constraints.apply() → feasible list + rejected-with-reasons
5. optimizer.rank(feasible) → sorted + contributions
6. uncertainty.score(best) → confidence, support, downgrade flag
7. Persist: model_runs → scenarios → recommendations rows
8. UI renders: comparison table, constraint status, recommendation card,
   T-vs-μ physics chart, trade-off scatter, dynamometer card, rod diagnostics

## 3. Operator Action Flow
Recommendation → Approve / Modify / Reject / Annotate
→ recommendations.status updated + audit_log row
→ optional counterfactual replay (baseline vs action, labelled model-based)

## 4. Diagnostics Flow (rolling window over observations)
- fillage < min AND load_range rising        → ROD_FLOATING / FLUID_POUND
- μ rising AND SPM rising AND max load rising → ROD_LOADING
- card area drops sharply while rate falls    → VALVE_INSPECT
- incomplete card coverage                    → INSUFFICIENT_DATA (never diagnose)
Every alert: fired rule + variables + thresholds + data-quality status
→ diagnostics_events table.

## 5. Validation Flow (Validation tab)
Temporal: fit cycles 1–2 → predict 3 → test 4; MAE/RMSE per cycle.
Physics: monotonicity checks + residuals vs mechanistic model.
Counterfactual: freeze state; baseline vs alternative action.

## 6. DB Flow
wells → css_cycles → time_series_observations
operating_limits / assumptions / fluid_properties → constraints & model params
model_runs → scenarios → recommendations → audit_log
validation_results, diagnostics_events written by their modules.
