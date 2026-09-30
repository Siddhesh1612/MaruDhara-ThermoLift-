# BACKEND — Implementation Guide

## Project Tree
thermolift/
├── app.py
├── .env                       # DATABASE_URL=sqlite:///data/thermolift.db
├── requirements.txt
├── db/
│   ├── schema.sql             # Postgres/Supabase DDL (source of truth)
│   └── thermolift.db          # generated SQLite (prototype)
├── data/                      # generated CSVs + current_state.json
├── config/
│   └── operating_limits.yaml  # defaults mirrored into operating_limits table
├── src/
│   ├── schema.py              # Pydantic models
│   ├── data_generator.py      # seed 26120; writes CSVs AND seeds DB
│   ├── db/
│   │   ├── engine.py          # SQLAlchemy engine from .env (SQLite/Postgres)
│   │   ├── repository.py      # ONLY DB entrypoint; typed read/write
│   │   └── adapter.py         # WellState input assembly, CSV fallback
│   ├── state_estimator.py
│   ├── css_model.py
│   ├── viscosity_model.py
│   ├── inflow_model.py
│   ├── srp_model.py
│   ├── srp_diagnostics.py
│   ├── scenario_engine.py
│   ├── constraints.py
│   ├── optimizer.py
│   ├── uncertainty.py
│   └── validation.py
├── tests/  (test_causality.py, test_constraints.py,
│            test_reproducibility.py, test_validation_splits.py)
└── docs/   (PRD, TRD, FLOW, DB, BACKEND, FRONTEND .md)

## Hard Rules
1. Physics modules: pure functions of typed inputs; NO streamlit/plotly imports;
   return (value, units, warnings, model_metadata).
2. Only repository.py touches the DB. Adapter exposes ONE interface so the
   synthetic source can later be replaced by OIL telemetry without rewrites.
3. Scenario engine reuses the same physics modules as live replay — no
   duplicated formulas.
4. Constraints apply BEFORE ranking; rejections carry exact reasons.
5. All thresholds/weights come from DB tables (config seeds them), never
   hardcoded in logic.
6. Recommendations are ADVISORY; operator action required; audit every action.
7. Provenance fields on every output: source_label, seed, model_version.

## Functions to Implement (key signatures)
- state_estimator.get_latest_state(session) -> WellState
- css_model.simulate_cycle(steam_mass_t, inj_h, soak_h, pres_bar, seed) -> ThermalResult
- viscosity_model.viscosity(T_c) -> ViscosityResult
- inflow_model.inflow(mu_kcp, p_r, p_wf, cfg) -> InflowResult
- srp_model.response(inflow_bpd, spm, stroke_m, mu_kcp) -> SRPResult (incl. card)
- srp_diagnostics.evaluate(history_df) -> list[Diagnostic]
- scenario_engine.run(user_inputs, session) -> list[ScenarioResult]
- constraints.apply(scenarios, session) -> (feasible, rejected)
- optimizer.rank(feasible, weights) -> ranked, contributions
- uncertainty.score(best, context) -> Confidence
- validation.run_all(session) -> list[ValidationResult]
- repository.* : upsert_well, bulk_insert_observations, insert_cycle,
  get_latest_state_rows, get_limits, get_weights, insert_model_run,
  insert_scenarios, insert_recommendation, update_recommendation_status,
  insert_audit, insert_diagnostics, insert_validation

## Persistence per Simulate
model_runs(1) → scenarios(61) → recommendations(1) → optional audit_log(1)
