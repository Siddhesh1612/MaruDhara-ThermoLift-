import math
from typing import List, Optional, Tuple, Dict
from src.schema import ScenarioResult, NearestAlternativeResult
from src.objective import evaluate_objective

def compute_decision_distance(s1: ScenarioResult, s2: ScenarioResult) -> float:
    """
    Computes normalized Euclidean distance between two scenarios across the 4 control dimensions:
    - steam_mass_t (range approx 80 to 130 -> span 50)
    - soak_h (range approx 24 to 96 -> span 72)
    - pump_speed_spm (range approx 4 to 10 -> span 6)
    - stroke_length_m (range approx 1.8 to 3.2 -> span 1.4)
    """
    d_steam = (s1.steam_mass_t - s2.steam_mass_t) / 50.0
    d_soak = (s1.soak_h - s2.soak_h) / 72.0
    d_spm = (s1.pump_speed_spm - s2.pump_speed_spm) / 6.0
    d_stroke = (s1.stroke_length_m - s2.stroke_length_m) / 1.4

    return math.sqrt(d_steam**2 + d_soak**2 + d_spm**2 + d_stroke**2)

def find_nearest_alternative(
    recommended: ScenarioResult,
    candidates: List[ScenarioResult],
    min_distance_threshold: float = 0.08
) -> Optional[NearestAlternativeResult]:
    """
    Finds the nearest materially distinct, feasible alternative scenario to the top recommendation.
    Materially distinct means normalized decision distance >= min_distance_threshold.
    """
    feasible_alternatives = [
        s for s in candidates
        if s.scenario_id != recommended.scenario_id and s.feasible
    ]

    if not feasible_alternatives:
        return None

    best_alt = None
    min_dist = float("inf")

    for cand in feasible_alternatives:
        dist = compute_decision_distance(recommended, cand)
        # Must be materially distinct to avoid reporting a virtually identical twin
        if dist >= min_distance_threshold and dist < min_dist:
            min_dist = dist
            best_alt = cand

    # If no alternative passed the threshold, pick the distinct one with minimum distance
    if best_alt is None:
        for cand in feasible_alternatives:
            dist = compute_decision_distance(recommended, cand)
            if dist > 0.001 and dist < min_dist:
                min_dist = dist
                best_alt = cand

    if best_alt is None:
        return None

    # Parameter deltas (alt - recommended)
    param_deltas = {
        "steam_mass_t": round(best_alt.steam_mass_t - recommended.steam_mass_t, 2),
        "soak_h": round(float(best_alt.soak_h - recommended.soak_h), 1),
        "pump_speed_spm": round(best_alt.pump_speed_spm - recommended.pump_speed_spm, 2),
        "stroke_length_m": round(best_alt.stroke_length_m - recommended.stroke_length_m, 2),
    }

    # KPI deltas (alt - recommended)
    kpi_deltas = {
        "expected_oil_bpd": round(best_alt.expected_oil_bpd - recommended.expected_oil_bpd, 2),
        "sor": round(best_alt.sor - recommended.sor, 3),
        "energy_kwh_bbl": round(best_alt.energy_kwh_bbl - recommended.energy_kwh_bbl, 2),
        "pump_fillage_pct": round(best_alt.pump_fillage_pct - recommended.pump_fillage_pct, 1),
        "srp_load_kn": round(best_alt.srp_load_kn - recommended.srp_load_kn, 2),
        "maintenance_risk": round(best_alt.maintenance_risk - recommended.maintenance_risk, 3),
        "objective_score": round(best_alt.objective_score - recommended.objective_score, 4),
    }

    # Contribution deltas
    _, bd_rec = evaluate_objective(recommended)
    _, bd_alt = evaluate_objective(best_alt)
    contrib_deltas = {}
    for metric in bd_rec.contributions:
        if metric in bd_alt.contributions:
            contrib_deltas[metric] = round(
                bd_alt.contributions[metric].signed_contribution - bd_rec.contributions[metric].signed_contribution, 4
            )

    # Margin deltas
    margin_deltas = {}
    for k in recommended.margins:
        if k in best_alt.margins:
            margin_deltas[k] = round(best_alt.margins[k] - recommended.margins[k], 2)

    # Build concise trade-off summary
    oil_diff = kpi_deltas["expected_oil_bpd"]
    steam_diff = param_deltas["steam_mass_t"]
    sor_diff = kpi_deltas["sor"]
    score_diff = kpi_deltas["objective_score"]

    summary_parts = []
    if oil_diff > 0:
        summary_parts.append(f"+{oil_diff:.1f} bpd higher oil")
    elif oil_diff < 0:
        summary_parts.append(f"{oil_diff:.1f} bpd lower oil")
    else:
        summary_parts.append("equal oil")

    if steam_diff > 0:
        summary_parts.append(f"requires +{steam_diff:.1f} t more steam (SOR {sor_diff:+.2f})")
    elif steam_diff < 0:
        summary_parts.append(f"saves {abs(steam_diff):.1f} t steam (SOR {sor_diff:+.2f})")
    else:
        summary_parts.append("same steam")

    summary_parts.append(f"composite score delta: {score_diff:+.3f}")
    trade_off = f"Alternative ({best_alt.scenario_id}): {', '.join(summary_parts)}."

    return NearestAlternativeResult(
        recommended=recommended,
        alternative=best_alt,
        decision_distance=round(min_dist, 3),
        parameter_deltas=param_deltas,
        kpi_deltas=kpi_deltas,
        contribution_deltas=contrib_deltas,
        margin_deltas=margin_deltas,
        trade_off_summary=trade_off
    )
