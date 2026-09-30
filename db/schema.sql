-- THERMOLIFT / MaruDhara Database DDL (PostgreSQL / Supabase / SQLite)
-- Schema Definition for SIH26120 Decision Twin Prototype

-- 1. Wells Table
CREATE TABLE IF NOT EXISTS wells (
    well_id TEXT PRIMARY KEY,
    field_label TEXT NOT NULL,
    status TEXT NOT NULL,
    source_label TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP)
);

-- 2. Reservoir Properties Table
CREATE TABLE IF NOT EXISTS reservoir_properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    well_id TEXT NOT NULL REFERENCES wells(well_id),
    permeability_md DOUBLE PRECISION NOT NULL,
    thickness_m DOUBLE PRECISION NOT NULL,
    porosity_pct DOUBLE PRECISION NOT NULL,
    skin_factor DOUBLE PRECISION NOT NULL,
    drainage_radius_m DOUBLE PRECISION NOT NULL,
    wellbore_radius_m DOUBLE PRECISION NOT NULL,
    initial_pressure_bar DOUBLE PRECISION NOT NULL,
    initial_temperature_c DOUBLE PRECISION NOT NULL,
    status TEXT NOT NULL
);

-- 3. Fluid Properties Table
CREATE TABLE IF NOT EXISTS fluid_properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    well_id TEXT NOT NULL REFERENCES wells(well_id),
    ref_viscosity_kcp DOUBLE PRECISION NOT NULL,
    ref_temperature_c DOUBLE PRECISION NOT NULL,
    temp_coeff_k DOUBLE PRECISION NOT NULL,
    fvf_b DOUBLE PRECISION NOT NULL,
    status TEXT NOT NULL
);

-- 4. CSS Cycles Table
CREATE TABLE IF NOT EXISTS css_cycles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    well_id TEXT NOT NULL REFERENCES wells(well_id),
    cycle_id INTEGER NOT NULL,
    steam_mass_t DOUBLE PRECISION NOT NULL,
    steam_pressure_bar DOUBLE PRECISION NOT NULL,
    injection_duration_h INTEGER NOT NULL,
    soak_duration_h INTEGER NOT NULL,
    production_duration_h INTEGER NOT NULL
);

-- 5. Time Series Observations Table
CREATE TABLE IF NOT EXISTS time_series_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    well_id TEXT NOT NULL REFERENCES wells(well_id),
    field_label TEXT,
    cycle_id INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    phase TEXT NOT NULL,
    reservoir_pressure_bar DOUBLE PRECISION NOT NULL,
    bottomhole_pressure_bar DOUBLE PRECISION NOT NULL,
    steam_mass_t DOUBLE PRECISION NOT NULL,
    steam_pressure_bar DOUBLE PRECISION NOT NULL,
    steam_injection_duration_h INTEGER NOT NULL,
    soak_duration_h INTEGER NOT NULL,
    production_duration_h INTEGER NOT NULL,
    temperature_c DOUBLE PRECISION NOT NULL,
    viscosity_kcp DOUBLE PRECISION NOT NULL,
    inflow_bpd DOUBLE PRECISION NOT NULL,
    oil_rate_bpd DOUBLE PRECISION NOT NULL,
    water_rate_bpd DOUBLE PRECISION NOT NULL,
    pump_speed_spm DOUBLE PRECISION NOT NULL,
    stroke_length_m DOUBLE PRECISION NOT NULL,
    pump_fillage_pct DOUBLE PRECISION NOT NULL,
    srp_load_kn DOUBLE PRECISION NOT NULL,
    energy_kwh_bbl DOUBLE PRECISION NOT NULL,
    srp_risk_score INTEGER NOT NULL,
    data_quality TEXT NOT NULL,
    source_label TEXT NOT NULL,
    random_seed INTEGER NOT NULL
);

-- 6. Operating Limits Table
CREATE TABLE IF NOT EXISTS operating_limits (
    limit_name TEXT PRIMARY KEY,
    value DOUBLE PRECISION NOT NULL,
    unit TEXT NOT NULL,
    operator_bound TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL
);

-- 7. Assumptions Register Table
CREATE TABLE IF NOT EXISTS assumptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parameter_name TEXT NOT NULL UNIQUE,
    value_text TEXT NOT NULL,
    unit TEXT,
    justification TEXT NOT NULL,
    status TEXT NOT NULL
);

-- 8. Model Ranking Weights Table
CREATE TABLE IF NOT EXISTS model_weights (
    weight_name TEXT PRIMARY KEY,
    weight_value DOUBLE PRECISION NOT NULL,
    description TEXT
);

-- 9. Model Runs Table
CREATE TABLE IF NOT EXISTS model_runs (
    run_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    steam_mass_t DOUBLE PRECISION NOT NULL,
    soak_duration_h INTEGER NOT NULL,
    pump_speed_spm DOUBLE PRECISION NOT NULL,
    stroke_length_m DOUBLE PRECISION NOT NULL,
    candidate_count INTEGER NOT NULL,
    seed INTEGER NOT NULL,
    model_version TEXT NOT NULL
);

-- 10. Scenarios Table (with full provenance and margins)
CREATE TABLE IF NOT EXISTS scenarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES model_runs(run_id),
    scenario_id TEXT NOT NULL,
    steam_mass_t DOUBLE PRECISION NOT NULL,
    soak_h INTEGER NOT NULL,
    pump_speed_spm DOUBLE PRECISION NOT NULL,
    stroke_length_m DOUBLE PRECISION NOT NULL,
    temperature_c DOUBLE PRECISION NOT NULL,
    viscosity_kcp DOUBLE PRECISION NOT NULL,
    inflow_bpd DOUBLE PRECISION NOT NULL,
    oil_rate_bpd DOUBLE PRECISION NOT NULL,
    pump_fillage_pct DOUBLE PRECISION NOT NULL,
    srp_load_kn DOUBLE PRECISION NOT NULL,
    energy_kwh_bbl DOUBLE PRECISION NOT NULL,
    risk_score DOUBLE PRECISION NOT NULL,
    feasible INTEGER NOT NULL,
    rejection_reason TEXT,
    objective_score DOUBLE PRECISION NOT NULL,
    input_state_hash TEXT,
    model_version TEXT,
    assumption_set TEXT,
    random_seed INTEGER,
    margin_fillage DOUBLE PRECISION,
    margin_load DOUBLE PRECISION,
    margin_steam DOUBLE PRECISION,
    norm_oil DOUBLE PRECISION,
    norm_steam DOUBLE PRECISION,
    norm_energy DOUBLE PRECISION,
    norm_risk DOUBLE PRECISION,
    norm_maint DOUBLE PRECISION,
    p_wf_bar DOUBLE PRECISION,
    pip_bar DOUBLE PRECISION,
    whp_bar DOUBLE PRECISION,
    flowline_p_bar DOUBLE PRECISION,
    source_label TEXT NOT NULL
);

-- 11. Recommendations Table
CREATE TABLE IF NOT EXISTS recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES model_runs(run_id),
    scenario_id TEXT NOT NULL,
    css_controls TEXT NOT NULL,
    srp_controls TEXT NOT NULL,
    expected_oil_bpd DOUBLE PRECISION NOT NULL,
    expected_steam_t DOUBLE PRECISION NOT NULL,
    expected_energy_kwh_bbl DOUBLE PRECISION NOT NULL,
    expected_fillage_pct DOUBLE PRECISION NOT NULL,
    expected_load_kn DOUBLE PRECISION NOT NULL,
    constraint_margins TEXT NOT NULL,
    confidence_pct DOUBLE PRECISION NOT NULL,
    rationale TEXT NOT NULL,
    invalidators TEXT NOT NULL,
    operator_status TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 12. Audit Log Table
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    operator_user TEXT NOT NULL,
    action TEXT NOT NULL,
    target_id TEXT NOT NULL,
    old_status TEXT,
    new_status TEXT,
    notes TEXT
);

-- 13. Diagnostics Events Table
CREATE TABLE IF NOT EXISTS diagnostics_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    well_id TEXT NOT NULL,
    rule_name TEXT NOT NULL,
    variables TEXT NOT NULL,
    thresholds TEXT NOT NULL,
    data_quality TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL
);

-- 14. Validation Results Table
CREATE TABLE IF NOT EXISTS validation_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    validation_type TEXT NOT NULL,
    cycle_id INTEGER,
    metric_name TEXT NOT NULL,
    metric_value DOUBLE PRECISION NOT NULL,
    pass_fail TEXT NOT NULL,
    details TEXT
);

-- 15. Ablation Experiments Table (Independent vs Coupled)
CREATE TABLE IF NOT EXISTS ablation_experiments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    mode TEXT NOT NULL,
    scenario_id TEXT NOT NULL,
    expected_oil_bpd DOUBLE PRECISION NOT NULL,
    steam_mass_t DOUBLE PRECISION NOT NULL,
    sor DOUBLE PRECISION NOT NULL,
    energy_kwh_bbl DOUBLE PRECISION NOT NULL,
    pump_fillage_pct DOUBLE PRECISION NOT NULL,
    srp_load_kn DOUBLE PRECISION NOT NULL,
    risk_score DOUBLE PRECISION NOT NULL,
    maintenance_risk DOUBLE PRECISION NOT NULL,
    violations_count INTEGER NOT NULL,
    objective_score DOUBLE PRECISION NOT NULL,
    notes TEXT
);

-- 16. Pressure Chain Runs Table
CREATE TABLE IF NOT EXISTS pressure_chain_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scenario_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    p_res_bar DOUBLE PRECISION NOT NULL,
    p_wf_bar DOUBLE PRECISION NOT NULL,
    pip_bar DOUBLE PRECISION NOT NULL,
    whp_bar DOUBLE PRECISION NOT NULL,
    choke_dp_bar DOUBLE PRECISION NOT NULL,
    flowline_dp_bar DOUBLE PRECISION NOT NULL,
    separator_p_bar DOUBLE PRECISION NOT NULL,
    limiting_condition TEXT NOT NULL,
    surface_margin_bar DOUBLE PRECISION NOT NULL,
    feasible INTEGER NOT NULL
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_obs_well_ts ON time_series_observations(well_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_scenarios_run ON scenarios(run_id);
CREATE INDEX IF NOT EXISTS idx_scenarios_hash ON scenarios(input_state_hash);
CREATE INDEX IF NOT EXISTS idx_recs_run ON recommendations(run_id);
CREATE INDEX IF NOT EXISTS idx_audit_target ON audit_log(target_id);
CREATE INDEX IF NOT EXISTS idx_ablation_run ON ablation_experiments(run_id);
CREATE INDEX IF NOT EXISTS idx_pressure_sc ON pressure_chain_runs(scenario_id);
