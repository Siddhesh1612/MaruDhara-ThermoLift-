from datetime import datetime
from sqlalchemy import (
    Column, Integer, Float, String, Boolean, Text, ForeignKey, Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class WellModel(Base):
    __tablename__ = "wells"
    well_id = Column(String, primary_key=True)
    field_label = Column(String, nullable=False)
    status = Column(String, nullable=False)
    source_label = Column(String, nullable=False)
    created_at = Column(String, default=lambda: datetime.utcnow().isoformat())

class ReservoirPropertyModel(Base):
    __tablename__ = "reservoir_properties"
    id = Column(Integer, primary_key=True, autoincrement=True)
    well_id = Column(String, ForeignKey("wells.well_id"), nullable=False)
    permeability_md = Column(Float, nullable=False)
    thickness_m = Column(Float, nullable=False)
    porosity_pct = Column(Float, nullable=False)
    skin_factor = Column(Float, nullable=False)
    drainage_radius_m = Column(Float, nullable=False)
    wellbore_radius_m = Column(Float, nullable=False)
    initial_pressure_bar = Column(Float, nullable=False)
    initial_temperature_c = Column(Float, nullable=False)
    status = Column(String, nullable=False)

class FluidPropertyModel(Base):
    __tablename__ = "fluid_properties"
    id = Column(Integer, primary_key=True, autoincrement=True)
    well_id = Column(String, ForeignKey("wells.well_id"), nullable=False)
    ref_viscosity_kcp = Column(Float, nullable=False)
    ref_temperature_c = Column(Float, nullable=False)
    temp_coeff_k = Column(Float, nullable=False)
    fvf_b = Column(Float, nullable=False)
    status = Column(String, nullable=False)

class CSSCycleModel(Base):
    __tablename__ = "css_cycles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    well_id = Column(String, ForeignKey("wells.well_id"), nullable=False)
    cycle_id = Column(Integer, nullable=False)
    steam_mass_t = Column(Float, nullable=False)
    steam_pressure_bar = Column(Float, nullable=False)
    injection_duration_h = Column(Integer, nullable=False)
    soak_duration_h = Column(Integer, nullable=False)
    production_duration_h = Column(Integer, nullable=False)

class TimeSeriesObservationModel(Base):
    __tablename__ = "time_series_observations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    well_id = Column(String, ForeignKey("wells.well_id"), nullable=False)
    field_label = Column(String, default="Baghewala-style representative")
    cycle_id = Column(Integer, nullable=False)
    timestamp = Column(String, nullable=False)
    phase = Column(String, nullable=False)
    reservoir_pressure_bar = Column(Float, nullable=False)
    bottomhole_pressure_bar = Column(Float, nullable=False)
    steam_mass_t = Column(Float, nullable=False)
    steam_pressure_bar = Column(Float, nullable=False)
    steam_injection_duration_h = Column(Integer, nullable=False)
    soak_duration_h = Column(Integer, nullable=False)
    production_duration_h = Column(Integer, nullable=False)
    temperature_c = Column(Float, nullable=False)
    viscosity_kcp = Column(Float, nullable=False)
    inflow_bpd = Column(Float, nullable=False)
    oil_rate_bpd = Column(Float, nullable=False)
    water_rate_bpd = Column(Float, nullable=False)
    pump_speed_spm = Column(Float, nullable=False)
    stroke_length_m = Column(Float, nullable=False)
    pump_fillage_pct = Column(Float, nullable=False)
    srp_load_kn = Column(Float, nullable=False)
    energy_kwh_bbl = Column(Float, nullable=False)
    srp_risk_score = Column(Integer, nullable=False)
    data_quality = Column(String, nullable=False)
    source_label = Column(String, nullable=False)
    random_seed = Column(Integer, nullable=False)

    __table_args__ = (
        Index("idx_obs_well_ts", "well_id", "timestamp"),
    )

class OperatingLimitModel(Base):
    __tablename__ = "operating_limits"
    limit_name = Column(String, primary_key=True)
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    operator_bound = Column(String, nullable=False)
    description = Column(String)
    status = Column(String, nullable=False)

class AssumptionModel(Base):
    __tablename__ = "assumptions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    parameter_name = Column(String, unique=True, nullable=False)
    value_text = Column(String, nullable=False)
    unit = Column(String)
    justification = Column(String, nullable=False)
    status = Column(String, nullable=False)

class ModelWeightModel(Base):
    __tablename__ = "model_weights"
    weight_name = Column(String, primary_key=True)
    weight_value = Column(Float, nullable=False)
    description = Column(String)

class ModelRunModel(Base):
    __tablename__ = "model_runs"
    run_id = Column(String, primary_key=True)
    timestamp = Column(String, nullable=False)
    steam_mass_t = Column(Float, nullable=False)
    soak_duration_h = Column(Integer, nullable=False)
    pump_speed_spm = Column(Float, nullable=False)
    stroke_length_m = Column(Float, nullable=False)
    candidate_count = Column(Integer, nullable=False)
    seed = Column(Integer, nullable=False)
    model_version = Column(String, nullable=False)

class ScenarioModel(Base):
    __tablename__ = "scenarios"
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, ForeignKey("model_runs.run_id"), nullable=False)
    scenario_id = Column(String, nullable=False)
    steam_mass_t = Column(Float, nullable=False)
    soak_h = Column(Integer, nullable=False)
    pump_speed_spm = Column(Float, nullable=False)
    stroke_length_m = Column(Float, nullable=False)
    temperature_c = Column(Float, nullable=False)
    viscosity_kcp = Column(Float, nullable=False)
    inflow_bpd = Column(Float, nullable=False)
    oil_rate_bpd = Column(Float, nullable=False)
    pump_fillage_pct = Column(Float, nullable=False)
    srp_load_kn = Column(Float, nullable=False)
    energy_kwh_bbl = Column(Float, nullable=False)
    risk_score = Column(Float, nullable=False)
    feasible = Column(Boolean, nullable=False)
    rejection_reason = Column(Text)
    objective_score = Column(Float, nullable=False)
    input_state_hash = Column(String)
    model_version = Column(String)
    assumption_set = Column(String)
    random_seed = Column(Integer)
    margin_fillage = Column(Float)
    margin_load = Column(Float)
    margin_steam = Column(Float)
    norm_oil = Column(Float)
    norm_steam = Column(Float)
    norm_energy = Column(Float)
    norm_risk = Column(Float)
    norm_maint = Column(Float)
    p_wf_bar = Column(Float)
    pip_bar = Column(Float)
    whp_bar = Column(Float)
    flowline_p_bar = Column(Float)
    source_label = Column(String, nullable=False)

    __table_args__ = (
        Index("idx_scenarios_run", "run_id"),
        Index("idx_scenarios_hash", "input_state_hash"),
    )

class RecommendationModel(Base):
    __tablename__ = "recommendations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, ForeignKey("model_runs.run_id"), nullable=False)
    scenario_id = Column(String, nullable=False)
    css_controls = Column(String, nullable=False)
    srp_controls = Column(String, nullable=False)
    expected_oil_bpd = Column(Float, nullable=False)
    expected_steam_t = Column(Float, nullable=False)
    expected_energy_kwh_bbl = Column(Float, nullable=False)
    expected_fillage_pct = Column(Float, nullable=False)
    expected_load_kn = Column(Float, nullable=False)
    constraint_margins = Column(Text, nullable=False)
    confidence_pct = Column(Float, nullable=False)
    rationale = Column(Text, nullable=False)
    invalidators = Column(Text, nullable=False)
    operator_status = Column(String, nullable=False, default="PENDING")
    updated_at = Column(String, default=lambda: datetime.utcnow().isoformat())

    __table_args__ = (
        Index("idx_recs_run", "run_id"),
    )

class AuditLogModel(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(String, nullable=False, default=lambda: datetime.utcnow().isoformat())
    operator_user = Column(String, nullable=False)
    action = Column(String, nullable=False)
    target_id = Column(String, nullable=False)
    old_status = Column(String)
    new_status = Column(String)
    notes = Column(Text)

    __table_args__ = (
        Index("idx_audit_target", "target_id"),
    )

class DiagnosticsEventModel(Base):
    __tablename__ = "diagnostics_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(String, nullable=False, default=lambda: datetime.utcnow().isoformat())
    well_id = Column(String, nullable=False)
    rule_name = Column(String, nullable=False)
    variables = Column(Text, nullable=False)
    thresholds = Column(Text, nullable=False)
    data_quality = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    message = Column(Text, nullable=False)

class ValidationResultModel(Base):
    __tablename__ = "validation_results"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(String, nullable=False, default=lambda: datetime.utcnow().isoformat())
    validation_type = Column(String, nullable=False)
    cycle_id = Column(Integer)
    metric_name = Column(String, nullable=False)
    metric_value = Column(Float, nullable=False)
    pass_fail = Column(String, nullable=False)
    details = Column(Text)

class AblationExperimentModel(Base):
    __tablename__ = "ablation_experiments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, nullable=False)
    timestamp = Column(String, nullable=False, default=lambda: datetime.utcnow().isoformat())
    mode = Column(String, nullable=False)  # "INDEPENDENT" or "COUPLED"
    scenario_id = Column(String, nullable=False)
    expected_oil_bpd = Column(Float, nullable=False)
    steam_mass_t = Column(Float, nullable=False)
    sor = Column(Float, nullable=False)
    energy_kwh_bbl = Column(Float, nullable=False)
    pump_fillage_pct = Column(Float, nullable=False)
    srp_load_kn = Column(Float, nullable=False)
    risk_score = Column(Float, nullable=False)
    maintenance_risk = Column(Float, nullable=False)
    violations_count = Column(Integer, nullable=False)
    objective_score = Column(Float, nullable=False)
    notes = Column(Text)

    __table_args__ = (
        Index("idx_ablation_run", "run_id"),
    )

class PressureChainRunModel(Base):
    __tablename__ = "pressure_chain_runs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    scenario_id = Column(String, nullable=False)
    timestamp = Column(String, nullable=False, default=lambda: datetime.utcnow().isoformat())
    p_res_bar = Column(Float, nullable=False)
    p_wf_bar = Column(Float, nullable=False)
    pip_bar = Column(Float, nullable=False)
    whp_bar = Column(Float, nullable=False)
    choke_dp_bar = Column(Float, nullable=False)
    flowline_dp_bar = Column(Float, nullable=False)
    separator_p_bar = Column(Float, nullable=False)
    limiting_condition = Column(String, nullable=False)
    surface_margin_bar = Column(Float, nullable=False)
    feasible = Column(Boolean, nullable=False)

    __table_args__ = (
        Index("idx_pressure_sc", "scenario_id"),
    )
