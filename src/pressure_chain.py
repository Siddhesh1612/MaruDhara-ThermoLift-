from typing import Any, Dict, Optional
from src.schema import PressureChainResult, ScenarioResult

# Reduced-Order Surface Constraints
SURFACE_LIMITS = {
    "max_whp_bar": 14.0,           # Maximum allowable wellhead working pressure
    "max_flowline_p_bar": 10.5,    # Maximum gathering line backpressure
    "separator_p_bar": 3.5,        # Field battery separator operating pressure
    "max_separator_liquid_bpd": 65.0 # Battery liquid separation capacity
}

def evaluate_pressure_chain(
    scenario: ScenarioResult,
    p_res_bar: float = 24.2,
    p_sep_bar: float = 3.5
) -> PressureChainResult:
    """
    Evaluates reduced-order wellbore-to-surface hydraulic pressure chain:
    Reservoir Pressure -> Bottomhole Flowing (Pwf) -> Pump Intake Pressure (PIP)
    -> Wellhead Pressure (WHP) -> Choke -> Flowline -> Separator.

    Explicitly reduced-order; models physical hydraulic loss with viscosity coupling.
    Ensures surface handling constraints influence operational feasibility.
    """
    q = max(scenario.oil_rate_bpd, 1.0)
    mu = max(scenario.viscosity_kcp, 1.0)

    # 1. Reservoir to Bottomhole (Darcy inflow drawdown)
    drawdown = max(0.5, q / 14.5)
    p_wf = round(max(14.0, p_res_bar - drawdown), 2)

    # 2. Wellbore to Pump Intake (PIP)
    # Intake friction and hydrostatic head to pump suction (-56m)
    pip = round(max(10.0, p_wf - 1.8), 2)

    # 3. Dynamic surface choke & flowline drops (viscous friction loss)
    # Higher crude viscosity sharply elevates flowline frictional pressure drop: dP ~ mu^0.35 * q
    flowline_dp = round(1.8 * (q / 30.0) * ((mu / 7.5) ** 0.35), 2)
    choke_dp = round(1.2 * ((q / 30.0) ** 1.3) * ((mu / 7.5) ** 0.2), 2)

    # 4. Surface Pressures
    whp = round(p_sep_bar + flowline_dp + choke_dp, 2)
    flowline_p = round(p_sep_bar + flowline_dp, 2)

    # 5. Surface Constraints & Feasibility
    max_whp = SURFACE_LIMITS["max_whp_bar"]
    max_flowline_p = SURFACE_LIMITS["max_flowline_p_bar"]
    max_sep_liq = SURFACE_LIMITS["max_separator_liquid_bpd"]

    whp_margin = round(max_whp - whp, 2)
    flowline_margin = round(max_flowline_p - flowline_p, 2)
    sep_capacity_margin = round(max_sep_liq - q, 1)

    reasons = []
    limiting = "Normal Flow (Wellhead & Flowline within limits)"

    if whp > max_whp:
        reasons.append(f"WHP ({whp:.1f} bar) exceeds surface rating ({max_whp:.1f} bar)")
        limiting = "Excessive Wellhead Backpressure"
    elif flowline_p > max_flowline_p:
        reasons.append(f"Flowline pressure ({flowline_p:.1f} bar) exceeds limit ({max_flowline_p:.1f} bar)")
        limiting = "Flowline Viscous Backpressure Bottleneck"
    elif q > max_sep_liq:
        reasons.append(f"Liquid rate ({q:.1f} bpd) exceeds separator capacity ({max_sep_liq:.1f} bpd)")
        limiting = "Separator Liquid Handling Limit"

    is_feasible = len(reasons) == 0
    surface_margin = min(whp_margin, flowline_margin)

    # Cache back to scenario
    scenario.p_wf_bar = p_wf
    scenario.pip_bar = pip
    scenario.whp_bar = whp
    scenario.flowline_p_bar = flowline_p

    return PressureChainResult(
        scenario_id=scenario.scenario_id,
        p_res_bar=round(p_res_bar, 2),
        p_wf_bar=p_wf,
        pip_bar=pip,
        whp_bar=whp,
        choke_dp_bar=choke_dp,
        flowline_dp_bar=flowline_dp,
        separator_p_bar=round(p_sep_bar, 2),
        limiting_condition=limiting,
        surface_margin_bar=surface_margin,
        feasible=is_feasible,
        rejection_reason="; ".join(reasons)
    )
