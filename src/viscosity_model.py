import math
from typing import Any, Dict, Optional, Tuple
import numpy as np

from src.schema import ViscosityResult
from src.db.adapter import DataAdapter
from src.db import repository

# Canonical defaults matching fluid_properties table and generate_synthetic.py
DEFAULT_MU_REF = 13.2   # kcP at 50 °C for scenarios (13.0 for time-series base)
DEFAULT_T_REF = 50.0    # °C
DEFAULT_K_COEFF = 0.046 # 1/°C
MIN_BAND_KCP = 3.8
MAX_BAND_KCP = 15.5

def calculate_viscosity(
    temp_c: float,
    mu_ref: Optional[float] = None,
    t_ref: Optional[float] = None,
    k_coeff: Optional[float] = None,
    enforce_clip: bool = True
) -> ViscosityResult:
    """
    Computes heavy oil viscosity using exponential Arrhenius-type correlation:
    μ(T) = μ_ref * exp(-k * (T - T_ref))
    Parameters default from fluid_properties table.
    Enforces monotonicity: dμ/dT < 0.
    """
    warnings = []

    # Fetch from DB if not provided
    if mu_ref is None or t_ref is None or k_coeff is None:
        try:
            props = repository.get_properties("BWG-SIM-001")
            flu = props.get("fluid", {})
            if flu:
                mu_ref = mu_ref or flu.get("ref_viscosity_kcp", DEFAULT_MU_REF)
                t_ref = t_ref or flu.get("ref_temperature_c", DEFAULT_T_REF)
                k_coeff = k_coeff or flu.get("temp_coeff_k", DEFAULT_K_COEFF)
        except Exception:
            pass

    mu_ref = mu_ref if mu_ref is not None else DEFAULT_MU_REF
    t_ref = t_ref if t_ref is not None else DEFAULT_T_REF
    k_coeff = k_coeff if k_coeff is not None else DEFAULT_K_COEFF

    if temp_c < 30.0:
        warnings.append(f"Temperature {temp_c} °C is below valid model correlation range (>=30 °C).")
    if temp_c > 110.0:
        warnings.append(f"Temperature {temp_c} °C exceeds valid model correlation range (<=110 °C).")

    # Evaluate equation
    raw_viscosity = mu_ref * math.exp(-k_coeff * (temp_c - t_ref))

    # Monotonicity check: verify derivative is strictly negative
    d_mu_dt = -k_coeff * raw_viscosity
    monotonicity_passed = (d_mu_dt < 0) and (k_coeff > 0)

    # Optional clip to physical prototype operating band
    if enforce_clip:
        viscosity = float(np.clip(raw_viscosity, MIN_BAND_KCP, MAX_BAND_KCP))
    else:
        viscosity = raw_viscosity

    supported = (temp_c >= 45.0 and temp_c <= 95.0)
    if not supported:
        warnings.append("Operating temperature outside primary calibrated support band [45, 95] °C.")

    return ViscosityResult(
        viscosity_kcp=round(viscosity, 3),
        viscosity_band_kcp=(MIN_BAND_KCP, MAX_BAND_KCP),
        supported=supported,
        monotonicity_passed=monotonicity_passed,
        units={"viscosity_kcp": "kcP"},
        warnings=warnings,
        model_metadata={
            "mu_ref_kcp": mu_ref,
            "t_ref_c": t_ref,
            "k_coeff": k_coeff,
            "raw_viscosity_kcp": round(raw_viscosity, 4),
            "d_mu_dt": round(d_mu_dt, 5),
            "status": "UNCALIBRATED_SYNTHETIC"
        }
    )
