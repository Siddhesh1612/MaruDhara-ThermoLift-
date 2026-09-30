from typing import Any, Dict, Optional, Tuple
import numpy as np

from src.schema import ThermalTargetResult, MODEL_VERSION
from src.css_model import simulate_css_cycle
from src.viscosity_model import calculate_viscosity
from src.inflow_model import calculate_inflow
from src.srp_model import calculate_srp_response
from src.constraints import get_operating_limits

def solve_minimum_steam(
    target_type: str = "VISCOSITY",
    target_value: float = 7.5,
    min_fillage_pct: float = 52.0,
    max_load_kn: float = 62.0,
    spm: float = 7.0,
    stroke_m: float = 1.55,
    soak_h: int = 48,
    steam_min_t: float = 70.0,
    steam_max_t: float = 125.0
) -> ThermalTargetResult:
    """
    Solves: 'What is the least steam intervention required to reach the thermal/viscosity state
    that makes the SRP cycle mechanically and economically viable?'

    Transparent, deterministic grid scan over allowable steam range.
    Uses canonical thermal, viscosity, inflow, and SRP response models.
    """
    target_type = target_type.upper()
    limits = get_operating_limits()
    max_allowed_steam = float(limits.get("max_steam_mass_t", 118.0))

    # Discrete step scan (1.0 t resolution)
    steam_candidates = np.linspace(steam_min_t, steam_max_t, int(steam_max_t - steam_min_t) + 1)

    best_feasible: Optional[ThermalTargetResult] = None
    limiting_reason = "No candidate in range satisfied target and mechanical constraints"

    for steam in steam_candidates:
        thermal = simulate_css_cycle(steam_mass_t=steam, inj_h=36, soak_h=soak_h, prod_h=588)
        temp = thermal.temperature_c
        visc = calculate_viscosity(temp).viscosity_kcp

        # Check target achievement
        if target_type == "VISCOSITY":
            target_met = visc <= target_value
        else: # TEMPERATURE
            target_met = temp >= target_value

        if not target_met:
            continue

        # Check coupled downstream mechanical constraints
        inflow = calculate_inflow(visc).inflow_bpd
        srp = calculate_srp_response(
            inflow_bpd=inflow,
            spm=spm,
            stroke_m=stroke_m,
            viscosity_kcp=visc,
            steam_mass_t=steam
        )

        fillage_ok = srp.pump_fillage_pct >= min_fillage_pct
        load_ok = srp.srp_load_kn <= max_load_kn
        steam_limit_ok = steam <= max_allowed_steam

        if not steam_limit_ok:
            limiting_reason = f"Required steam ({steam:.1f} t) exceeds prototype generator capacity ({max_allowed_steam:.1f} t)"
            continue
        if not fillage_ok:
            limiting_reason = f"Pump fillage ({srp.pump_fillage_pct:.1f}%) below minimum ({min_fillage_pct:.1f}%)"
            continue
        if not load_ok:
            limiting_reason = f"Polished rod load ({srp.srp_load_kn:.1f} kN) exceeds safety limit ({max_load_kn:.1f} kN)"
            continue

        # Found the first (minimum) feasible steam meeting all conditions!
        best_feasible = ThermalTargetResult(
            target_type=target_type,
            target_value=round(target_value, 2),
            min_feasible_steam_t=round(float(steam), 1),
            achieved=True,
            temperature_c=round(temp, 1),
            viscosity_kcp=round(visc, 2),
            inflow_bpd=round(inflow, 1),
            pump_fillage_pct=round(srp.pump_fillage_pct, 1),
            srp_load_kn=round(srp.srp_load_kn, 1),
            limiting_constraint=f"Target satisfied with fillage margin {srp.pump_fillage_pct - min_fillage_pct:+.1f}%, load margin {max_load_kn - srp.srp_load_kn:+.1f} kN",
            scenario_id=f"TARGET-OPT-{int(steam)}t",
            confidence_pct=88.0,
            explanation=f"Minimum steam of {steam:.1f} t heats reservoir to {temp:.1f} °C, lowering heavy oil viscosity to {visc:.2f} kcP to satisfy {target_type} target."
        )
        break

    if best_feasible is not None:
        return best_feasible

    # Target not reached within constraints
    # Evaluate at nominal steam limit to report gap
    nom_thermal = simulate_css_cycle(steam_mass_t=max_allowed_steam, inj_h=36, soak_h=soak_h, prod_h=588)
    nom_visc = calculate_viscosity(nom_thermal.temperature_c).viscosity_kcp
    nom_inflow = calculate_inflow(nom_visc).inflow_bpd
    nom_srp = calculate_srp_response(inflow_bpd=nom_inflow, spm=spm, stroke_m=stroke_m, viscosity_kcp=nom_visc, steam_mass_t=max_allowed_steam)

    return ThermalTargetResult(
        target_type=target_type,
        target_value=round(target_value, 2),
        min_feasible_steam_t=None,
        achieved=False,
        temperature_c=round(nom_thermal.temperature_c, 1),
        viscosity_kcp=round(nom_visc, 2),
        inflow_bpd=round(nom_inflow, 1),
        pump_fillage_pct=round(nom_srp.pump_fillage_pct, 1),
        srp_load_kn=round(nom_srp.srp_load_kn, 1),
        limiting_constraint=limiting_reason,
        scenario_id="UNACHIEVED-TARGET",
        confidence_pct=80.0,
        explanation=f"Target {target_type} of {target_value} could not be achieved within allowable steam envelope ({steam_min_t} - {max_allowed_steam} t) and mechanical limits."
    )
