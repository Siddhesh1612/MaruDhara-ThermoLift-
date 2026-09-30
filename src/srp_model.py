import math
from typing import Any, Dict, List, Optional
import numpy as np

from src.schema import SRPResult

def calculate_srp_response(
    inflow_bpd: float,
    spm: float,
    stroke_m: float = 1.55,
    viscosity_kcp: float = 8.5,
    steam_mass_t: float = 100.0,
    k_capacity: float = 7.2,
    enforce_clip: bool = True
) -> SRPResult:
    """
    Quasi-dynamic Sucker Rod Pump (SRP) model:
    capacity = k * SPM * stroke
    fillage = (inflow / capacity) * 100
    load = base + a*μ + b*SPM + c*(100 - fillage)
    oil_rate = inflow * (0.64 + 0.0022 * fillage) - 0.045 * load
    energy = 11 + 0.72*SPM + 0.10*load + 0.02*steam
    risk = clip((load - 42)*2.0 + (58 - fillage)*0.45, 0, 100)
    Generates synthetic dynamometer card and extracts card features.
    """
    warnings = []
    if spm <= 0:
        spm = 6.0
        warnings.append("Non-positive SPM; defaulted to 6.0.")
    if stroke_m <= 0:
        stroke_m = 1.55
        warnings.append("Non-positive stroke length; defaulted to 1.55 m.")

    # 1. Capacity & Fillage
    capacity = k_capacity * spm * stroke_m
    raw_fillage = (inflow_bpd / max(capacity, 1.0)) * 100.0
    if enforce_clip:
        fillage = float(np.clip(raw_fillage, 35.0, 98.0))
    else:
        fillage = raw_fillage

    # 2. Rod Load
    # base = 25, a = 0.62, b = 2.7, c = 0.12
    raw_load = 25.0 + 0.62 * viscosity_kcp + 2.7 * spm + 0.12 * (100.0 - fillage)
    if enforce_clip:
        load = float(np.clip(raw_load, 25.0, 75.0))
    else:
        load = raw_load

    # 3. Production & Energy
    oil = inflow_bpd * (0.64 + 0.0022 * fillage) - 0.045 * load
    oil = max(oil, 5.0)

    energy = 11.0 + 0.72 * spm + 0.10 * load + 0.02 * steam_mass_t

    # 4. Risk Score
    risk = float(np.clip((load - 42.0) * 2.0 + (58.0 - fillage) * 0.45, 0.0, 100.0))

    # 5. Synthetic Dynamometer Card Generation (Load vs Position)
    # Generate 50 points around a crank rotation theta from 0 to 2*pi
    n_points = 50
    thetas = np.linspace(0, 2 * np.pi, n_points)
    # Position: s(theta) = stroke/2 * (1 - cos(theta))
    positions = (stroke_m / 2.0) * (1.0 - np.cos(thetas))

    # Upstroke (theta 0 -> pi): traveling valve closed, standing valve open, fluid load carried
    # Downstroke (theta pi -> 2*pi): traveling valve open, rod buoyant weight
    card_loads = []
    pprl = load * 1.08  # peak polished rod load
    mprl = load * 0.42  # minimum polished rod load

    # Fillage pound effect: if fillage < 75%, delay traveling valve opening on downstroke
    pound_factor = max(0.0, (75.0 - fillage) / 75.0)

    for th in thetas:
        if th <= np.pi:
            # Upstroke: load rises quickly to PPRL and has slight dynamic oscillation
            s_norm = th / np.pi
            ld = mprl + (pprl - mprl) * (1.0 - math.exp(-6.0 * s_norm)) + 1.2 * math.sin(2 * th)
        else:
            # Downstroke: load drops towards MPRL
            s_down = (th - np.pi) / np.pi
            if s_down < pound_factor:
                # Fluid pound: sudden sharp drop in load as plunger hits liquid
                ld = mprl + (pprl - mprl) * 0.45 * math.exp(-12.0 * s_down) - 2.5
            else:
                ld = mprl + 1.0 * math.sin(2 * th)
        card_loads.append(max(float(ld), 10.0))

    # Card features
    card_max = float(np.max(card_loads))
    card_min = float(np.min(card_loads))
    card_range = card_max - card_min
    card_mean = float(np.mean(card_loads))
    # Area: approximate trapezoidal integration of closed loop
    # area = integral of load over position
    dx = np.diff(positions)
    avg_l = (np.array(card_loads)[:-1] + np.array(card_loads)[1:]) / 2.0
    card_area = float(abs(np.sum(dx * avg_l)))
    card_repeatability = 98.5  # % synthetic standard repeatability

    card_features = {
        "max": round(card_max, 2),
        "min": round(card_min, 2),
        "range": round(card_range, 2),
        "area": round(card_area, 2),
        "mean": round(card_mean, 2),
        "repeatability": card_repeatability
    }

    card_curve = {
        "position_m": [round(float(p), 4) for p in positions],
        "load_kn": [round(float(l), 2) for l in card_loads]
    }

    return SRPResult(
        pump_capacity_bpd=round(capacity, 3),
        pump_fillage_pct=round(fillage, 3),
        srp_load_kn=round(load, 3),
        oil_rate_bpd=round(oil, 3),
        energy_kwh_bbl=round(energy, 3),
        risk_score=round(risk, 3),
        card_features=card_features,
        card_curve=card_curve,
        units={
            "pump_capacity_bpd": "bpd",
            "pump_fillage_pct": "%",
            "srp_load_kn": "kN",
            "oil_rate_bpd": "bpd",
            "energy_kwh_bbl": "kWh/bbl",
            "risk_score": "0-100"
        },
        warnings=warnings,
        model_metadata={
            "k_capacity": k_capacity,
            "spm": spm,
            "stroke_m": stroke_m,
            "pprl_kn": round(card_max, 2),
            "mprl_kn": round(card_min, 2)
        }
    )
