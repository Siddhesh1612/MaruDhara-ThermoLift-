from typing import Any, Dict, List, Optional, Tuple

from src.schema import ConstraintCheck, ScenarioResult
from src.db import repository

def get_operating_limits() -> Dict[str, float]:
    """Retrieve operating limits from repository with safe defaults."""
    try:
        limits = repository.get_limits()
        if limits:
            return limits
    except Exception:
        pass
    return {
        "min_pump_fillage_pct": 52.0,
        "max_srp_load_kn": 62.0,
        "max_steam_mass_t": 118.0,
        "min_spm": 5.0,
        "max_spm": 10.0,
        "min_stroke_m": 1.45,
        "max_stroke_m": 1.65,
    }

def check_scenario_constraints(
    scenario: ScenarioResult,
    limits: Optional[Dict[str, float]] = None
) -> ConstraintCheck:
    """
    Evaluate hard operational constraints for a single scenario.
    Calculates signed margins:
    - Load margin: Max Load - Actual Load (positive = safe buffer below limit)
    - Fillage margin: Actual Fillage - Min Fillage (positive = safe buffer above limit)
    - Steam margin: Max Steam - Actual Steam (positive = safe buffer within envelope)
    """
    if limits is None:
        limits = get_operating_limits()

    min_fillage = float(limits.get("min_pump_fillage_pct", 52.0))
    max_load = float(limits.get("max_srp_load_kn", 62.0))
    max_steam = float(limits.get("max_steam_mass_t", 118.0))

    reasons = []

    # 1. SRP Rod Load Constraint
    load_margin = round(max_load - scenario.srp_load_kn, 2)
    if scenario.srp_load_kn > max_load:
        reasons.append(
            f"SRP load ({scenario.srp_load_kn:.1f} kN) exceeds configurable limit ({max_load:.1f} kN), "
            f"margin: {load_margin:+.1f} kN"
        )

    # 2. Pump Fillage Constraint
    fillage_margin = round(scenario.pump_fillage_pct - min_fillage, 2)
    if scenario.pump_fillage_pct < min_fillage:
        reasons.append(
            f"Pump fillage ({scenario.pump_fillage_pct:.1f}%) below configurable minimum ({min_fillage:.1f}%), "
            f"margin: {fillage_margin:+.1f}%"
        )

    # 3. Steam Mass Constraint
    steam_margin = round(max_steam - scenario.steam_mass_t, 2)
    if scenario.steam_mass_t > max_steam:
        reasons.append(
            f"Steam input ({scenario.steam_mass_t:.1f} t) exceeds prototype envelope ({max_steam:.1f} t), "
            f"margin: {steam_margin:+.1f} t"
        )

    margins = {
        "fillage_margin_pct": fillage_margin,
        "load_margin_kn": load_margin,
        "steam_margin_t": steam_margin,
    }

    return ConstraintCheck(
        scenario_id=scenario.scenario_id,
        feasible=len(reasons) == 0,
        rejection_reasons=reasons,
        margins=margins
    )

def format_constraint_report(
    scenario: ScenarioResult,
    limits: Optional[Dict[str, float]] = None
) -> List[Dict[str, Any]]:
    """
    Exposes structured, auditable constraint margins for UI and audit logs:
    Constraint | Threshold | Actual | Signed Margin | Status | Explanation
    """
    if limits is None:
        limits = get_operating_limits()

    min_fillage = float(limits.get("min_pump_fillage_pct", 52.0))
    max_load = float(limits.get("max_srp_load_kn", 62.0))
    max_steam = float(limits.get("max_steam_mass_t", 118.0))

    fillage_margin = round(scenario.pump_fillage_pct - min_fillage, 2)
    load_margin = round(max_load - scenario.srp_load_kn, 2)
    steam_margin = round(max_steam - scenario.steam_mass_t, 2)

    return [
        {
            "constraint": "Pump Fillage",
            "threshold": f"{min_fillage:.1f} %",
            "actual": f"{scenario.pump_fillage_pct:.1f} %",
            "margin": f"{fillage_margin:+.1f} %",
            "status": "PASS" if fillage_margin >= 0 else "FAIL",
            "explanation": "Prevents pump gas interference, fluid pound, and mechanical barrel damage."
        },
        {
            "constraint": "Polished Rod Load",
            "threshold": f"{max_load:.1f} kN",
            "actual": f"{scenario.srp_load_kn:.1f} kN",
            "margin": f"{load_margin:+.1f} kN",
            "status": "PASS" if load_margin >= 0 else "FAIL",
            "explanation": "Guards against sucker rod tensile fatigue, parting risk, and gearbox overload."
        },
        {
            "constraint": "Steam Mass Input",
            "threshold": f"{max_steam:.1f} t",
            "actual": f"{scenario.steam_mass_t:.1f} t",
            "margin": f"{steam_margin:+.1f} t",
            "status": "PASS" if steam_margin >= 0 else "FAIL",
            "explanation": "Maintains operations within generator capacity and thermodynamic envelope."
        }
    ]

def apply_constraints(
    scenarios: List[ScenarioResult],
    limits: Optional[Dict[str, float]] = None
) -> Tuple[List[ScenarioResult], List[ScenarioResult]]:
    """
    Applies constraints to a collection of scenarios.
    Returns (feasible_scenarios, rejected_scenarios).
    """
    if limits is None:
        limits = get_operating_limits()

    feasible_list = []
    rejected_list = []

    for sc in scenarios:
        check = check_scenario_constraints(sc, limits)
        sc.feasible = check.feasible
        sc.rejection_reason = "; ".join(check.rejection_reasons)
        sc.constraint_margins = check.margins

        if sc.feasible:
            feasible_list.append(sc)
        else:
            rejected_list.append(sc)

    return feasible_list, rejected_list
