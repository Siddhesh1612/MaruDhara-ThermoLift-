from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

MODEL_VERSION: str = "v2.0"
ASSUMPTION_SET: str = "DEFAULT_PROTOTYPE_v2.0"

class WellState(BaseModel):
    well_id: str = "BWG-SIM-001"
    timestamp: str
    phase: str
    temperature_c: float
    viscosity_kcp: float
    reservoir_pressure_bar: float
    bottomhole_pressure_bar: float
    inflow_bpd: float
    oil_rate_bpd: float
    water_rate_bpd: float
    pump_speed_spm: float
    stroke_length_m: float
    pump_fillage_pct: float
    srp_load_kn: float
    energy_kwh_bbl: float
    srp_risk_score: int
    data_quality: str = "GOOD"
    source_label: str = "SYNTHETIC"
    random_seed: int = 26120
    model_version: str = MODEL_VERSION

class ThermalResult(BaseModel):
    temperature_c: float
    temperature_trajectory_c: List[float] = Field(default_factory=list)
    phase: str = "production"
    q_in_kw: float = 0.0
    q_loss_kw: float = 0.0
    physics_residual: float = 0.0
    units: Dict[str, str] = Field(default_factory=lambda: {
        "temperature_c": "°C",
        "q_in_kw": "kW",
        "q_loss_kw": "kW",
        "physics_residual": "°C"
    })
    warnings: List[str] = Field(default_factory=list)
    model_metadata: Dict[str, Any] = Field(default_factory=dict)

class ViscosityResult(BaseModel):
    viscosity_kcp: float
    viscosity_band_kcp: Tuple[float, float] = (3.8, 15.5)
    supported: bool = True
    monotonicity_passed: bool = True
    units: Dict[str, str] = Field(default_factory=lambda: {"viscosity_kcp": "kcP"})
    warnings: List[str] = Field(default_factory=list)
    model_metadata: Dict[str, Any] = Field(default_factory=dict)

class InflowResult(BaseModel):
    inflow_bpd: float
    productivity_index_bpd_bar: float
    mobility_proxy: float
    drawdown_bar: float
    units: Dict[str, str] = Field(default_factory=lambda: {
        "inflow_bpd": "bpd",
        "productivity_index_bpd_bar": "bpd/bar",
        "drawdown_bar": "bar"
    })
    warnings: List[str] = Field(default_factory=list)
    model_metadata: Dict[str, Any] = Field(default_factory=dict)

class SRPResult(BaseModel):
    pump_capacity_bpd: float
    pump_fillage_pct: float
    srp_load_kn: float
    oil_rate_bpd: float
    energy_kwh_bbl: float
    risk_score: float
    card_features: Dict[str, float] = Field(default_factory=dict)
    card_curve: Dict[str, List[float]] = Field(default_factory=dict)
    units: Dict[str, str] = Field(default_factory=lambda: {
        "pump_capacity_bpd": "bpd",
        "pump_fillage_pct": "%",
        "srp_load_kn": "kN",
        "oil_rate_bpd": "bpd",
        "energy_kwh_bbl": "kWh/bbl",
        "risk_score": "0-100"
    })
    warnings: List[str] = Field(default_factory=list)
    model_metadata: Dict[str, Any] = Field(default_factory=dict)

class Diagnostic(BaseModel):
    rule_name: str
    fired: bool
    severity: str = "INFO"  # INFO, WARNING, CRITICAL
    variables: Dict[str, Any] = Field(default_factory=dict)
    thresholds: Dict[str, Any] = Field(default_factory=dict)
    data_quality: str = "GOOD"
    message: str

class Scenario(BaseModel):
    scenario_id: str
    steam_mass_t: float
    soak_h: int
    pump_speed_spm: float
    stroke_length_m: float = 1.55

class ScenarioResult(BaseModel):
    scenario_id: str
    steam_mass_t: float
    soak_h: int
    pump_speed_spm: float
    stroke_length_m: float = 1.55
    temperature_c: float = 65.0
    viscosity_kcp: float = 8.5
    inflow_bpd: float = 40.0
    oil_rate_bpd: float = 35.0
    expected_oil_bpd: float = 35.0
    pump_fillage_pct: float = 75.0
    srp_load_kn: float = 45.0
    pprl_kn: float = 45.0
    mprl_kn: float = 15.0
    rod_stress_pct: float = 60.0
    floating_risk: float = 0.05
    energy_kwh_bbl: float = 20.0
    risk_score: float = 20.0
    maintenance_risk: float = 15.0
    sor: float = 0.0
    p_wf_bar: float = 21.4
    pip_bar: float = 19.8
    whp_bar: float = 8.5
    flowline_p_bar: float = 5.2
    feasible: bool = True
    rejection_reason: str = ""
    constraint_margins: Dict[str, float] = Field(default_factory=dict)
    margins: Dict[str, float] = Field(default_factory=dict)
    objective_score: float = 0.0
    objective_contributions: Dict[str, float] = Field(default_factory=dict)
    norm_oil: float = 0.0
    norm_steam: float = 0.0
    norm_energy: float = 0.0
    norm_risk: float = 0.0
    norm_maint: float = 0.0
    confidence_pct: float = 85.0
    input_state_hash: str = ""
    model_version: str = MODEL_VERSION
    assumption_set: str = ASSUMPTION_SET
    random_seed: int = 26120
    source_label: str = "SYNTHETIC"

class ConstraintCheck(BaseModel):
    scenario_id: str
    feasible: bool
    rejection_reasons: List[str] = Field(default_factory=list)
    margins: Dict[str, float] = Field(default_factory=dict)

class Recommendation(BaseModel):
    run_id: str
    scenario_id: str
    css_controls: str
    srp_controls: str
    expected_oil_bpd: float
    expected_steam_t: float
    expected_energy_kwh_bbl: float
    expected_fillage_pct: float
    expected_load_kn: float
    constraint_margins: Dict[str, float] = Field(default_factory=dict)
    confidence_pct: float
    rationale: str
    invalidators: str
    operator_status: str = "PENDING"
    updated_at: Optional[str] = None

class Confidence(BaseModel):
    confidence_pct: float
    input_completeness: float = 1.0
    support_distance: float = 0.0
    physics_residual: float = 0.0
    extrapolation_penalty: float = 0.0
    gate_state: str = "GREEN"  # "GREEN", "AMBER", "RED"
    gate_reason: str = "Recommendation eligible; data and residual within bounds"
    recommendation_suppressed: bool = False
    downgrade_applied: bool = False
    label: str = "ILLUSTRATIVE PROTOTYPE CONFIDENCE"
    warnings: List[str] = Field(default_factory=list)

class ValidationResult(BaseModel):
    validation_type: str  # "TEMPORAL", "PHYSICS", "COUNTERFACTUAL"
    cycle_id: Optional[int] = None
    metric_name: str
    metric_value: float
    pass_fail: str  # "PASS", "FAIL"
    details: str = ""

# --- P0.2 / P1 / P2 Extended Data Contracts ---

class ObjectiveContribution(BaseModel):
    metric_name: str
    raw_value: float
    normalized_value: float
    weight: float
    signed_contribution: float
    description: str

class ObjectiveBreakdown(BaseModel):
    scenario_id: str
    total_score: float
    contributions: Dict[str, ObjectiveContribution] = Field(default_factory=dict)

class AblationKPIs(BaseModel):
    mode: str  # "INDEPENDENT" or "COUPLED"
    chosen_scenario_id: str
    steam_mass_t: float
    soak_h: int
    pump_speed_spm: float
    stroke_length_m: float
    expected_oil_bpd: float
    sor: float
    energy_kwh_bbl: float
    pump_fillage_pct: float
    srp_load_kn: float
    pprl_kn: float
    mprl_kn: float
    rod_stress_pct: float
    floating_risk: float
    maintenance_risk: float
    violations_count: int
    confidence_pct: float
    objective_score: float

class AblationComparison(BaseModel):
    independent: AblationKPIs
    coupled: AblationKPIs
    deltas: Dict[str, float] = Field(default_factory=dict)
    causal_explanation: str = ""

class PressureChainResult(BaseModel):
    scenario_id: str
    p_res_bar: float
    p_wf_bar: float
    pip_bar: float
    whp_bar: float
    choke_dp_bar: float
    flowline_dp_bar: float
    separator_p_bar: float
    limiting_condition: str
    surface_margin_bar: float
    feasible: bool
    rejection_reason: str = ""

class ThermalTargetResult(BaseModel):
    target_type: str  # "TEMPERATURE" or "VISCOSITY"
    target_value: float
    min_feasible_steam_t: Optional[float] = None
    achieved: bool = False
    temperature_c: float = 0.0
    viscosity_kcp: float = 0.0
    inflow_bpd: float = 0.0
    pump_fillage_pct: float = 0.0
    srp_load_kn: float = 0.0
    limiting_constraint: str = ""
    scenario_id: str = ""
    confidence_pct: float = 85.0
    explanation: str = ""

class CounterfactualReplayResult(BaseModel):
    cycle_id: int
    frozen_timestamp: str
    input_state_hash: str
    actual_steam_t: float
    actual_temp_c: float
    actual_oil_bpd: float
    recommended_scenario_id: str
    alternative_steam_t: float
    simulated_temp_c: float
    simulated_oil_bpd: float
    delta_oil_bpd: float
    confidence_pct: float
    label: str = "MODEL-BASED COUNTERFACTUAL REPLAY — NOT A MEASURED FIELD RESULT"

class NearestAlternativeResult(BaseModel):
    recommended: ScenarioResult
    alternative: ScenarioResult
    decision_distance: float
    parameter_deltas: Dict[str, float]
    kpi_deltas: Dict[str, float]
    contribution_deltas: Dict[str, float]
    margin_deltas: Dict[str, float]
    trade_off_summary: str

class SensitivityItem(BaseModel):
    parameter: str
    base_value: float
    perturbed_value: float
    perturbation_pct: float
    delta_oil_pct: float
    delta_sor_pct: float
    delta_fillage_pct: float
    delta_load_pct: float
    delta_energy_pct: float
    delta_risk_pct: float

class SensitivityAnalysisResult(BaseModel):
    base_scenario_id: str
    items: List[SensitivityItem] = Field(default_factory=list)
    ranked_importance: List[Tuple[str, float]] = Field(default_factory=list)

class ParetoCandidate(BaseModel):
    scenario_id: str
    oil_rate_bpd: float
    steam_mass_t: float
    energy_kwh_bbl: float
    risk_score: float
    is_nondominated: bool
    objective_score: float

class ParetoFrontierResult(BaseModel):
    total_candidates: int
    nondominated_count: int
    selected_scenario_id: str
    candidates: List[ParetoCandidate] = Field(default_factory=list)
