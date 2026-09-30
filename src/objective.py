from typing import Any, Dict, List, Optional, Tuple
from src.schema import ScenarioResult, ObjectiveBreakdown, ObjectiveContribution
from src.db import repository

# Canonical Default Weights (Steam penalty is non-zero and configurable)
DEFAULT_WEIGHTS: Dict[str, float] = {
    "w_oil": 1.0,
    "w_steam": 0.35,
    "w_energy": 0.45,
    "w_risk": 0.25,
    "w_maint": 0.15,
}

# Reference Normalization Bounds (Physical & Prototype Domain Boundaries)
NORMALIZATION_BOUNDS: Dict[str, Tuple[float, float]] = {
    "oil": (5.0, 60.0),       # Net oil rate (bpd)
    "steam": (70.0, 140.0),   # Steam mass (t)
    "energy": (10.0, 30.0),   # Energy consumption (kWh/bbl)
    "risk": (0.0, 100.0),     # SRP mechanical risk score (0-100)
    "maint": (0.0, 50.0),     # Maintenance/failure risk score (0-50)
}

def get_ranking_weights() -> Dict[str, float]:
    """Retrieve weights from repository with safe fallback to defaults."""
    try:
        w = repository.get_weights()
        if w:
            merged = DEFAULT_WEIGHTS.copy()
            merged.update(w)
            return merged
    except Exception:
        pass
    return DEFAULT_WEIGHTS.copy()

def normalize_metric(value: float, min_val: float, max_val: float) -> float:
    """
    Min-Max linear normalization bounded in [0.0, 1.0].
    Safely handles zero denominator and out-of-bound inputs.
    """
    denom = max_val - min_val
    if abs(denom) < 1e-6:
        return 0.0
    norm = (value - min_val) / denom
    return float(max(0.0, min(1.0, norm)))

def evaluate_objective(
    scenario: ScenarioResult,
    weights: Optional[Dict[str, float]] = None
) -> Tuple[float, ObjectiveBreakdown]:
    """
    Canonical, deterministic normalized objective function:
    Score = w_oil * norm_oil
          - w_steam * norm_steam
          - w_energy * norm_energy
          - w_risk * norm_risk
          - w_maint * norm_maint

    Returns: (total_score, breakdown)
    """
    if weights is None:
        weights = get_ranking_weights()

    w_oil = float(weights.get("w_oil", DEFAULT_WEIGHTS["w_oil"]))
    w_steam = float(weights.get("w_steam", DEFAULT_WEIGHTS["w_steam"]))
    w_energy = float(weights.get("w_energy", DEFAULT_WEIGHTS["w_energy"]))
    w_risk = float(weights.get("w_risk", DEFAULT_WEIGHTS["w_risk"]))
    w_maint = float(weights.get("w_maint", DEFAULT_WEIGHTS["w_maint"]))

    # 1. Normalize each term using canonical bounds
    norm_oil = normalize_metric(scenario.oil_rate_bpd, *NORMALIZATION_BOUNDS["oil"])
    norm_steam = normalize_metric(scenario.steam_mass_t, *NORMALIZATION_BOUNDS["steam"])
    norm_energy = normalize_metric(scenario.energy_kwh_bbl, *NORMALIZATION_BOUNDS["energy"])
    norm_risk = normalize_metric(scenario.risk_score, *NORMALIZATION_BOUNDS["risk"])
    norm_maint = normalize_metric(scenario.maintenance_risk, *NORMALIZATION_BOUNDS["maint"])

    # 2. Compute signed contributions
    contrib_oil = w_oil * norm_oil
    contrib_steam = - (w_steam * norm_steam)
    contrib_energy = - (w_energy * norm_energy)
    contrib_risk = - (w_risk * norm_risk)
    contrib_maint = - (w_maint * norm_maint)

    total_score = round(contrib_oil + contrib_steam + contrib_energy + contrib_risk + contrib_maint, 4)

    # 3. Cache normalized scores and contributions back on scenario
    scenario.norm_oil = round(norm_oil, 4)
    scenario.norm_steam = round(norm_steam, 4)
    scenario.norm_energy = round(norm_energy, 4)
    scenario.norm_risk = round(norm_risk, 4)
    scenario.norm_maint = round(norm_maint, 4)
    scenario.objective_score = total_score
    scenario.objective_contributions = {
        "oil_benefit": round(contrib_oil, 4),
        "steam_penalty": round(contrib_steam, 4),
        "energy_penalty": round(contrib_energy, 4),
        "risk_penalty": round(contrib_risk, 4),
        "maint_penalty": round(contrib_maint, 4),
    }

    breakdown = ObjectiveBreakdown(
        scenario_id=scenario.scenario_id,
        total_score=total_score,
        contributions={
            "oil": ObjectiveContribution(
                metric_name="Production Benefit",
                raw_value=round(scenario.oil_rate_bpd, 2),
                normalized_value=round(norm_oil, 4),
                weight=w_oil,
                signed_contribution=round(contrib_oil, 4),
                description=f"Net oil lift ({scenario.oil_rate_bpd:.1f} bpd)"
            ),
            "steam": ObjectiveContribution(
                metric_name="Steam Cost Penalty",
                raw_value=round(scenario.steam_mass_t, 2),
                normalized_value=round(norm_steam, 4),
                weight=w_steam,
                signed_contribution=round(contrib_steam, 4),
                description=f"Steam injected ({scenario.steam_mass_t:.1f} t)"
            ),
            "energy": ObjectiveContribution(
                metric_name="Energy Intensity Penalty",
                raw_value=round(scenario.energy_kwh_bbl, 2),
                normalized_value=round(norm_energy, 4),
                weight=w_energy,
                signed_contribution=round(contrib_energy, 4),
                description=f"Lift energy proxy ({scenario.energy_kwh_bbl:.1f} kWh/bbl)"
            ),
            "risk": ObjectiveContribution(
                metric_name="Mechanical Stress Penalty",
                raw_value=round(scenario.risk_score, 2),
                normalized_value=round(norm_risk, 4),
                weight=w_risk,
                signed_contribution=round(contrib_risk, 4),
                description=f"Rod & equipment risk score ({scenario.risk_score:.0f}/100)"
            ),
            "maint": ObjectiveContribution(
                metric_name="Maintenance Risk Penalty",
                raw_value=round(scenario.maintenance_risk, 2),
                normalized_value=round(norm_maint, 4),
                weight=w_maint,
                signed_contribution=round(contrib_maint, 4),
                description=f"Maintenance risk proxy ({scenario.maintenance_risk:.1f})"
            ),
        }
    )

    return total_score, breakdown
