from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from src.schema import (
    ScenarioResult, AblationKPIs, AblationComparison, MODEL_VERSION, ASSUMPTION_SET
)
from src.css_model import simulate_css_cycle
from src.viscosity_model import calculate_viscosity
from src.inflow_model import calculate_inflow
from src.srp_model import calculate_srp_response
from src.constraints import apply_constraints, get_operating_limits
from src.objective import evaluate_objective, get_ranking_weights
from src.scenario_engine import evaluate_single_candidate, DEFAULT_STEAM_GRID, DEFAULT_SOAK_GRID, DEFAULT_SPM_GRID, DEFAULT_STROKE_M

def run_independent_optimization(
    weights: Optional[Dict[str, float]] = None,
    limits: Optional[Dict[str, float]] = None,
    base_state_params: Optional[Dict[str, Any]] = None
) -> Tuple[ScenarioResult, List[ScenarioResult], int]:
    """
    MODE A — INDEPENDENT OPTIMIZATION:
    Step 1: CSS optimizer evaluates thermal and inflow recovery to select the best CSS state.
    Step 2: SRP optimizer operates on the FROZEN CSS thermal state to select pumping cadence.
    Uses the exact same canonical physics modules as coupled mode.
    Returns: (best_independent_scenario, evaluated_candidates, violations_count)
    """
    if weights is None:
        weights = get_ranking_weights()
    if limits is None:
        limits = get_operating_limits()

    # Step 1: Optimize CSS parameters (steam_mass, soak_h) under a nominal SRP baseline (SPM=7.0)
    css_candidates: List[Tuple[float, int, float, float]] = [] # steam, soak, inflow, score
    for steam in DEFAULT_STEAM_GRID:
        for soak in DEFAULT_SOAK_GRID:
            thermal = simulate_css_cycle(steam_mass_t=steam, inj_h=36, soak_h=soak, prod_h=588)
            visc = calculate_viscosity(thermal.temperature_c)
            inflow = calculate_inflow(visc.viscosity_kcp)
            # Proxy inflow merit minus steam cost
            css_merit = inflow.inflow_bpd - 0.25 * steam
            css_candidates.append((steam, soak, inflow.inflow_bpd, css_merit))

    # Select best CSS parameters independently
    best_css = max(css_candidates, key=lambda x: x[3])
    frozen_steam = best_css[0]
    frozen_soak = best_css[1]

    # Step 2: Optimize SRP parameters (SPM, stroke) on the frozen CSS state
    all_evaluated: List[ScenarioResult] = []
    for spm in DEFAULT_SPM_GRID:
        cand = evaluate_single_candidate(
            scenario_id=f"IND-S-{int(frozen_steam)}-{frozen_soak}-{int(spm)}",
            steam_mass_t=frozen_steam,
            soak_h=frozen_soak,
            spm=spm,
            stroke_m=DEFAULT_STROKE_M,
            base_state_params=base_state_params,
            source_label="INDEPENDENT_OPTIMIZER"
        )
        all_evaluated.append(cand)

    feasible_srp, rejected_srp = apply_constraints(all_evaluated, limits=limits)
    violations_count = len(rejected_srp)

    for sc in feasible_srp:
        evaluate_objective(sc, weights=weights)

    if feasible_srp:
        best_scenario = max(feasible_srp, key=lambda s: s.objective_score)
    else:
        # Fallback to least-rejected
        best_scenario = all_evaluated[0]

    return best_scenario, all_evaluated, violations_count

def run_coupled_optimization(
    weights: Optional[Dict[str, float]] = None,
    limits: Optional[Dict[str, float]] = None,
    base_state_params: Optional[Dict[str, Any]] = None
) -> Tuple[ScenarioResult, List[ScenarioResult], int]:
    """
    MODE B — COUPLED OPTIMIZATION:
    Jointly explores CSS (steam, soak) and SRP (spm, stroke) candidates simultaneously.
    Every candidate executes the full causal chain:
    steam -> thermal -> viscosity -> inflow -> SRP -> constraints -> objective.
    Uses the exact same candidate bounds, limits, and objective definitions as Mode A.
    Returns: (best_coupled_scenario, all_candidates, violations_count)
    """
    if weights is None:
        weights = get_ranking_weights()
    if limits is None:
        limits = get_operating_limits()

    all_candidates: List[ScenarioResult] = []
    for i, steam in enumerate(DEFAULT_STEAM_GRID, start=1):
        for soak in DEFAULT_SOAK_GRID:
            for spm in DEFAULT_SPM_GRID:
                sc_id = f"COUPLED-S-{i:02d}-{soak}-{int(spm)}"
                cand = evaluate_single_candidate(
                    scenario_id=sc_id,
                    steam_mass_t=steam,
                    soak_h=soak,
                    spm=spm,
                    stroke_m=DEFAULT_STROKE_M,
                    base_state_params=base_state_params,
                    source_label="COUPLED_OPTIMIZER"
                )
                all_candidates.append(cand)

    feasible_list, rejected_list = apply_constraints(all_candidates, limits=limits)
    violations_count = len(rejected_list)

    for sc in feasible_list:
        evaluate_objective(sc, weights=weights)

    if feasible_list:
        best_scenario = max(feasible_list, key=lambda s: s.objective_score)
    else:
        best_scenario = all_candidates[0]

    return best_scenario, all_candidates, violations_count

def extract_kpis(scenario: ScenarioResult, mode: str, violations: int) -> AblationKPIs:
    """Extract standard comparison KPIs for independent vs coupled evaluation."""
    cum_oil_month = scenario.oil_rate_bpd * 28.0
    sor = scenario.steam_mass_t / max(cum_oil_month * 0.158987, 0.01)
    pprl = round(scenario.srp_load_kn * 1.08, 2)
    mprl = round(scenario.srp_load_kn * 0.42, 2)
    rod_stress = round((pprl / 62.0) * 100.0, 1) # % of max allowable 62 kN
    floating_risk = round(float(max(0.0, min(100.0, (scenario.viscosity_kcp - 7.0) * 8.5 + (scenario.pump_speed_spm - 6.5) * 6.0))), 1)

    return AblationKPIs(
        mode=mode,
        chosen_scenario_id=scenario.scenario_id,
        steam_mass_t=scenario.steam_mass_t,
        soak_h=scenario.soak_h,
        pump_speed_spm=scenario.pump_speed_spm,
        stroke_length_m=scenario.stroke_length_m,
        expected_oil_bpd=scenario.oil_rate_bpd,
        sor=round(sor, 3),
        energy_kwh_bbl=scenario.energy_kwh_bbl,
        pump_fillage_pct=scenario.pump_fillage_pct,
        srp_load_kn=scenario.srp_load_kn,
        pprl_kn=pprl,
        mprl_kn=mprl,
        rod_stress_pct=rod_stress,
        floating_risk=floating_risk,
        maintenance_risk=scenario.maintenance_risk,
        violations_count=violations,
        confidence_pct=scenario.confidence_pct,
        objective_score=scenario.objective_score
    )

def run_ablation_experiment(
    weights: Optional[Dict[str, float]] = None,
    limits: Optional[Dict[str, float]] = None,
    base_state_params: Optional[Dict[str, Any]] = None
) -> AblationComparison:
    """
    Executes the full coupled vs. independent ablation experiment.
    Computes side-by-side KPI comparison, deltas, and neutral causal explanation.
    """
    ind_sc, ind_all, ind_violations = run_independent_optimization(weights, limits, base_state_params)
    coup_sc, coup_all, coup_violations = run_coupled_optimization(weights, limits, base_state_params)

    kpi_ind = extract_kpis(ind_sc, "INDEPENDENT", ind_violations)
    kpi_coup = extract_kpis(coup_sc, "COUPLED", coup_violations)

    deltas = {
        "delta_oil_bpd": round(kpi_coup.expected_oil_bpd - kpi_ind.expected_oil_bpd, 2),
        "delta_steam_t": round(kpi_coup.steam_mass_t - kpi_ind.steam_mass_t, 2),
        "delta_sor": round(kpi_coup.sor - kpi_ind.sor, 3),
        "delta_energy_kwh": round(kpi_coup.energy_kwh_bbl - kpi_ind.energy_kwh_bbl, 2),
        "delta_fillage_pct": round(kpi_coup.pump_fillage_pct - kpi_ind.pump_fillage_pct, 1),
        "delta_srp_load_kn": round(kpi_coup.srp_load_kn - kpi_ind.srp_load_kn, 2),
        "delta_rod_stress_pct": round(kpi_coup.rod_stress_pct - kpi_ind.rod_stress_pct, 1),
        "delta_floating_risk": round(kpi_coup.floating_risk - kpi_ind.floating_risk, 1),
        "delta_score": round(kpi_coup.objective_score - kpi_ind.objective_score, 4),
        "delta_violations": coup_violations - ind_violations
    }

    # Neutral causal explanation of measured differences
    explanation = (
        f"In independent optimization, CSS parameters are selected based on uncoupled inflow merit "
        f"without visibility into SRP displacement capacity or rod friction. This resulted in {kpi_ind.steam_mass_t:.0f} t steam "
        f"and {kpi_ind.pump_speed_spm:.1f} SPM, yielding {kpi_ind.expected_oil_bpd:.1f} bpd with pump fillage at {kpi_ind.pump_fillage_pct:.1f}%. "
        f"In contrast, coupled optimization simultaneously evaluates thermal viscosity reduction and mechanical pump fillage. "
        f"The coupled solver selected {kpi_coup.steam_mass_t:.0f} t steam with {kpi_coup.pump_speed_spm:.1f} SPM, "
        f"shifting net oil rate by {deltas['delta_oil_bpd']:+.1f} bpd, rod load by {deltas['delta_srp_load_kn']:+.1f} kN, "
        f"and objective score by {deltas['delta_score']:+.4f}."
    )

    return AblationComparison(
        independent=kpi_ind,
        coupled=kpi_coup,
        deltas=deltas,
        causal_explanation=explanation
    )
