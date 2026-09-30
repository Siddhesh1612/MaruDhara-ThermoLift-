from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from src.schema import ScenarioResult, MODEL_VERSION, ASSUMPTION_SET
from src.css_model import simulate_css_cycle
from src.viscosity_model import calculate_viscosity
from src.inflow_model import calculate_inflow
from src.srp_model import calculate_srp_response
from src.constraints import apply_constraints
from src.provenance import compute_input_state_hash

# Canonical grid settings
DEFAULT_STEAM_GRID = [90.0, 98.0, 106.0, 114.0, 122.0]
DEFAULT_SOAK_GRID = [36, 48, 60, 72]
DEFAULT_SPM_GRID = [6.0, 7.0, 8.0]
DEFAULT_STROKE_M = 1.55

DEFAULT_BASE_STATE = {
    "temperature_c": 58.5,
    "reservoir_pressure_bar": 24.2,
    "bottomhole_pressure_bar": 21.4,
    "inflow_bpd": 44.0,
    "viscosity_kcp": 9.2
}

def evaluate_single_candidate(
    scenario_id: str,
    steam_mass_t: float,
    soak_h: int,
    spm: float,
    stroke_m: float = DEFAULT_STROKE_M,
    base_state_params: Optional[Dict[str, Any]] = None,
    source_label: str = "SYNTHETIC"
) -> ScenarioResult:
    """
    Executes the exact coupled physics chain:
    css_model -> viscosity_model -> inflow_model -> srp_model
    Zero duplicate equations.
    Embeds complete provenance and deterministic state hash.
    """
    if base_state_params is None:
        base_state_params = DEFAULT_BASE_STATE.copy()

    # 1. Thermal response
    thermal_res = simulate_css_cycle(
        steam_mass_t=steam_mass_t,
        inj_h=36,
        soak_h=soak_h,
        prod_h=588
    )
    temp = thermal_res.temperature_c

    # 2. Viscosity response
    visc_res = calculate_viscosity(temp)
    viscosity = visc_res.viscosity_kcp

    # 3. Inflow / mobility response
    inflow_res = calculate_inflow(viscosity)
    inflow = inflow_res.inflow_bpd

    # 4. SRP response
    srp_res = calculate_srp_response(
        inflow_bpd=inflow,
        spm=spm,
        stroke_m=stroke_m,
        viscosity_kcp=viscosity,
        steam_mass_t=steam_mass_t
    )

    # 5. Derived engineering and pressure metrics
    oil_m3_month = max(srp_res.oil_rate_bpd * 28.0 * 0.158987, 0.01)
    sor = round(steam_mass_t / oil_m3_month, 3)
    maint_risk = round(
        float(max(5.0, min(50.0, 0.45 * srp_res.srp_load_kn + 0.35 * max(0.0, 60.0 - srp_res.pump_fillage_pct)))),
        2
    )

    # Reduced-order wellbore hydraulics
    p_wf = round(max(15.0, 24.2 - (inflow / 25.0)), 2)
    pip = round(max(12.0, p_wf - 1.6), 2)
    whp = round(max(6.0, pip - 11.2), 2)
    flowline_p = round(max(3.0, whp - 3.2), 2)

    # 6. Deterministic input state hash
    candidate_params = {
        "steam_mass_t": steam_mass_t,
        "soak_h": soak_h,
        "pump_speed_spm": spm,
        "stroke_length_m": stroke_m
    }
    state_hash = compute_input_state_hash(
        well_id="BWG-SIM-001",
        base_state_params=base_state_params,
        candidate_params=candidate_params,
        seed=26120,
        model_version=MODEL_VERSION,
        assumption_set=ASSUMPTION_SET
    )

    return ScenarioResult(
        scenario_id=scenario_id,
        steam_mass_t=round(steam_mass_t, 2),
        soak_h=int(soak_h),
        pump_speed_spm=round(spm, 2),
        stroke_length_m=round(stroke_m, 2),
        temperature_c=temp,
        viscosity_kcp=viscosity,
        inflow_bpd=inflow,
        oil_rate_bpd=srp_res.oil_rate_bpd,
        pump_fillage_pct=srp_res.pump_fillage_pct,
        srp_load_kn=srp_res.srp_load_kn,
        energy_kwh_bbl=srp_res.energy_kwh_bbl,
        risk_score=srp_res.risk_score,
        maintenance_risk=maint_risk,
        sor=sor,
        p_wf_bar=p_wf,
        pip_bar=pip,
        whp_bar=whp,
        flowline_p_bar=flowline_p,
        feasible=True,
        rejection_reason="",
        constraint_margins={},
        objective_score=0.0,
        objective_contributions={},
        confidence_pct=85.0,
        input_state_hash=state_hash,
        model_version=MODEL_VERSION,
        assumption_set=ASSUMPTION_SET,
        random_seed=26120,
        source_label=source_label
    )

def generate_scenario_candidates(
    custom_point: Optional[Dict[str, float]] = None,
    limits: Optional[Dict[str, float]] = None,
    base_state_params: Optional[Dict[str, Any]] = None
) -> Tuple[List[ScenarioResult], List[ScenarioResult], List[ScenarioResult]]:
    """
    Generates 60 grid combinations + 1 custom point (total 61 candidates).
    Applies hard constraints before ranking.
    Returns (all_scenarios, feasible_scenarios, rejected_scenarios).
    """
    all_candidates: List[ScenarioResult] = []

    # 1. 5 x 4 x 3 Grid = 60 Scenarios
    for i, steam in enumerate(DEFAULT_STEAM_GRID, start=1):
        for soak in DEFAULT_SOAK_GRID:
            for spm in DEFAULT_SPM_GRID:
                sc_id = f"S-{i:02d}-{soak}-{int(spm)}"
                cand = evaluate_single_candidate(
                    scenario_id=sc_id,
                    steam_mass_t=steam,
                    soak_h=soak,
                    spm=spm,
                    stroke_m=DEFAULT_STROKE_M,
                    base_state_params=base_state_params,
                    source_label="SYNTHETIC"
                )
                all_candidates.append(cand)

    # 2. Custom User Slider Point
    if custom_point:
        cust_steam = float(custom_point.get("steam_mass_t", 100.0))
        cust_soak = int(custom_point.get("soak_h", 48))
        cust_spm = float(custom_point.get("pump_speed_spm", 6.8))
        cust_stroke = float(custom_point.get("stroke_length_m", 1.55))

        cust_cand = evaluate_single_candidate(
            scenario_id="CUSTOM-USER-POINT",
            steam_mass_t=cust_steam,
            soak_h=cust_soak,
            spm=cust_spm,
            stroke_m=cust_stroke,
            base_state_params=base_state_params,
            source_label="USER_SIMULATE"
        )
        all_candidates.append(cust_cand)

    # 3. Apply Hard Constraints Before Ranking
    feasible_list, rejected_list = apply_constraints(all_candidates, limits=limits)

    return all_candidates, feasible_list, rejected_list

def to_dataframe(scenarios: List[ScenarioResult]) -> pd.DataFrame:
    """Helper to convert list of ScenarioResult to DataFrame."""
    records = []
    for s in scenarios:
        d = s.model_dump()
        records.append(d)
    return pd.DataFrame(records)
