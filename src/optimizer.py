from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from src.schema import ScenarioResult, ObjectiveBreakdown
from src.objective import evaluate_objective, get_ranking_weights, DEFAULT_WEIGHTS

def rank_scenarios(
    feasible_scenarios: List[ScenarioResult],
    weights: Optional[Dict[str, float]] = None
) -> Tuple[List[ScenarioResult], Optional[ScenarioResult]]:
    """
    Ranks feasible scenarios using ONE authoritative normalized objective function:
    Score = w_oil*norm_oil - w_steam*norm_steam - w_energy*norm_energy - w_risk*norm_risk - w_maint*norm_maint
    Ranks feasible scenarios ONLY.
    Computes individual signed objective contributions for every scenario.
    Returns (ranked_feasible_scenarios, best_scenario).
    """
    if weights is None:
        weights = get_ranking_weights()

    for sc in feasible_scenarios:
        # Calculate SOR proxy: Steam mass (t) / (Cumulative/Monthly oil volume equivalent in m3)
        oil_m3_est = max(sc.oil_rate_bpd * 28.0 * 0.158987, 0.1)
        sc.sor = round(sc.steam_mass_t / oil_m3_est, 3)

        # Estimate maintenance risk proxy based on rod stress, fillage starvation, and cycle SPM
        sc.maintenance_risk = round(
            float(max(5.0, min(50.0, 0.45 * sc.srp_load_kn + 0.35 * max(0.0, 60.0 - sc.pump_fillage_pct)))),
            2
        )

        evaluate_objective(sc, weights=weights)

    # Sort descending by objective score; tie-break on oil rate descending
    ranked = sorted(
        feasible_scenarios,
        key=lambda s: (s.objective_score, s.oil_rate_bpd),
        reverse=True
    )
    best = ranked[0] if ranked else None

    return ranked, best

def generate_recommendation_text(scenario: ScenarioResult) -> Tuple[str, str]:
    """
    Generates plain-language engineering recommendation and invalidating conditions.
    Strictly avoids 'AI selected Scenario X'.
    """
    fillage_margin = scenario.constraint_margins.get("fillage_margin_pct", 0.0)
    load_margin = scenario.constraint_margins.get("load_margin_kn", 0.0)
    steam_margin = scenario.constraint_margins.get("steam_margin_t", 0.0)

    rationale = (
        f"Scenario {scenario.scenario_id} is recommended because it provides a favourable "
        f"production/resource trade-off (projected oil rate: {scenario.oil_rate_bpd:.1f} bpd, "
        f"energy intensity: {scenario.energy_kwh_bbl:.1f} kWh/bbl, steam input: {scenario.steam_mass_t:.1f} t) "
        f"while satisfying all configured prototype constraints (pump fillage margin: {fillage_margin:+.1f}%, "
        f"rod load margin: {load_margin:+.1f} kN, steam envelope margin: {steam_margin:+.1f} t)."
    )

    invalidators = (
        "1. Rapid near-wellbore cooling faster than lumped heat capacity loss model. "
        "2. In-situ emulsion or sand ingress altering effective fluid mobility below 1.8. "
        "3. Surface flowline backpressure exceeding bottomhole design assumptions. "
        "4. Mechanical rod fatigue or traveling valve slippage detected on dynamometer card."
    )

    return rationale, invalidators
