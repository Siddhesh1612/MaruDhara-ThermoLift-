from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from src.schema import ValidationResult, WellState
from src.css_model import simulate_css_cycle
from src.viscosity_model import calculate_viscosity
from src.inflow_model import calculate_inflow
from src.srp_model import calculate_srp_response
from src.db.adapter import DataAdapter
from src.db import repository

COUNTERFACTUAL_LABEL = "MODEL-BASED COUNTERFACTUAL SIMULATION"

def run_temporal_validation(df: Optional[pd.DataFrame] = None) -> List[ValidationResult]:
    """
    Chronological-only backtesting without random shuffling or data leakage:
    Cycles 1-2 = Fit/Calibration
    Cycle 3 = Validation
    Cycle 4 = Test (Holdout)
    """
    if df is None or df.empty:
        adapter = DataAdapter()
        df = adapter.get_observations_history()

    if df.empty:
        return []

    results = []

    # Cycle 3 Validation
    c3 = df[df["cycle_id"] == 3]
    if not c3.empty:
        # Dynamic cycle simulation for cycle 3: steam=111, inj=40, soak=53
        sim3 = simulate_css_cycle(steam_mass_t=111.0, inj_h=40, soak_h=53, prod_h=672-40-53)
        actual3 = c3["temperature_c"].values
        min_len3 = min(len(actual3), len(sim3.temperature_trajectory_c))
        a3 = actual3[:min_len3]
        s3 = np.array(sim3.temperature_trajectory_c[:min_len3])
        temp_mae = float(np.mean(np.abs(a3 - s3)))
        temp_rmse = float(np.sqrt(np.mean((a3 - s3) ** 2)))

        results.append(ValidationResult(
            validation_type="TEMPORAL",
            cycle_id=3,
            metric_name="temp_mae_c",
            metric_value=round(temp_mae, 3),
            pass_fail="PASS" if temp_mae < 8.0 else "FAIL",
            details="Cycle 3 validation temperature MAE against lumped dynamic simulation"
        ))
        results.append(ValidationResult(
            validation_type="TEMPORAL",
            cycle_id=3,
            metric_name="temp_rmse_c",
            metric_value=round(temp_rmse, 3),
            pass_fail="PASS" if temp_rmse < 15.0 else "FAIL",
            details="Cycle 3 validation temperature RMSE against lumped dynamic simulation"
        ))

    # Cycle 4 Test (Holdout)
    c4 = df[df["cycle_id"] == 4]
    if not c4.empty:
        # Dynamic cycle simulation for cycle 4: steam=116, inj=42, soak=56
        sim4 = simulate_css_cycle(steam_mass_t=116.0, inj_h=42, soak_h=56, prod_h=672-42-56)
        actual4 = c4["temperature_c"].values
        min_len4 = min(len(actual4), len(sim4.temperature_trajectory_c))
        a4 = actual4[:min_len4]
        s4 = np.array(sim4.temperature_trajectory_c[:min_len4])
        temp_mae4 = float(np.mean(np.abs(a4 - s4)))
        temp_rmse4 = float(np.sqrt(np.mean((a4 - s4) ** 2)))

        results.append(ValidationResult(
            validation_type="TEMPORAL",
            cycle_id=4,
            metric_name="temp_mae_c",
            metric_value=round(temp_mae4, 3),
            pass_fail="PASS" if temp_mae4 < 8.0 else "FAIL",
            details="Cycle 4 test holdout temperature MAE against lumped dynamic simulation"
        ))
        results.append(ValidationResult(
            validation_type="TEMPORAL",
            cycle_id=4,
            metric_name="temp_rmse_c",
            metric_value=round(temp_rmse4, 3),
            pass_fail="PASS" if temp_rmse4 < 15.0 else "FAIL",
            details="Cycle 4 test holdout temperature RMSE against lumped dynamic simulation"
        ))

    return results

def run_physics_validation() -> List[ValidationResult]:
    """
    Verifies fundamental physical monotonicity constraints:
    1. T↑ => μ↓ (viscosity strictly decreases with temperature)
    2. μ↓ => mobility↑ => inflow↑ (inflow increases with lower viscosity)
    3. Inflow↑ => fillage↑ (fillage increases with inflow at constant SPM)
    4. SPM↑ => energy↑ (energy consumption increases with pumping speed)
    """
    results = []

    # 1. Monotonicity: T vs μ
    temps = [50.0, 60.0, 70.0, 80.0]
    viscs = [calculate_viscosity(t).viscosity_kcp for t in temps]
    t_mu_mono = all(viscs[i] > viscs[i+1] for i in range(len(viscs)-1))
    results.append(ValidationResult(
        validation_type="PHYSICS",
        cycle_id=None,
        metric_name="thermal_viscosity_monotonicity",
        metric_value=1.0 if t_mu_mono else 0.0,
        pass_fail="PASS" if t_mu_mono else "FAIL",
        details="Temperature increase strictly decreases heavy crude viscosity (dT/dμ < 0)"
    ))

    # 2. Monotonicity: μ vs Inflow
    inflows = [calculate_inflow(v).inflow_bpd for v in viscs]  # Note: viscs is descending
    mu_inflow_mono = all(inflows[i] < inflows[i+1] for i in range(len(inflows)-1))
    results.append(ValidationResult(
        validation_type="PHYSICS",
        cycle_id=None,
        metric_name="viscosity_inflow_monotonicity",
        metric_value=1.0 if mu_inflow_mono else 0.0,
        pass_fail="PASS" if mu_inflow_mono else "FAIL",
        details="Viscosity reduction strictly increases reservoir mobility and inflow"
    ))

    # 3. Monotonicity: Inflow vs Fillage
    test_inflows = [30.0, 45.0, 60.0, 75.0]
    fillages = [calculate_srp_response(inf, spm=6.8).pump_fillage_pct for inf in test_inflows]
    inf_fil_mono = all(fillages[i] <= fillages[i+1] for i in range(len(fillages)-1))
    results.append(ValidationResult(
        validation_type="PHYSICS",
        cycle_id=None,
        metric_name="inflow_fillage_monotonicity",
        metric_value=1.0 if inf_fil_mono else 0.0,
        pass_fail="PASS" if inf_fil_mono else "FAIL",
        details="Inflow growth monotonically increases pump fillage at fixed pump geometry"
    ))

    # 4. Monotonicity: SPM vs Energy
    spm_rates = [5.5, 6.5, 7.5, 8.5]
    energies = [calculate_srp_response(inflow_bpd=45.0, spm=s).energy_kwh_bbl for s in spm_rates]
    spm_energy_mono = all(energies[i] < energies[i+1] for i in range(len(energies)-1))
    results.append(ValidationResult(
        validation_type="PHYSICS",
        cycle_id=None,
        metric_name="spm_energy_monotonicity",
        metric_value=1.0 if spm_energy_mono else 0.0,
        pass_fail="PASS" if spm_energy_mono else "FAIL",
        details="Pumping speed increases specific lift energy intensity (dE/dSPM > 0)"
    ))

    return results

def run_counterfactual_simulation(
    baseline_controls: Dict[str, float],
    alternative_controls: Dict[str, float]
) -> Dict[str, Any]:
    """
    Executes a model-based counterfactual simulation by freezing the initial state
    and comparing system trajectories between Baseline and Alternative operational decisions.
    Must display exactly: 'MODEL-BASED COUNTERFACTUAL SIMULATION'.
    """
    # 1. Baseline Run
    b_steam = float(baseline_controls.get("steam_mass_t", 98.0))
    b_soak = int(baseline_controls.get("soak_h", 48))
    b_spm = float(baseline_controls.get("pump_speed_spm", 6.5))
    b_stroke = float(baseline_controls.get("stroke_length_m", 1.55))

    b_thermal = simulate_css_cycle(b_steam, soak_h=b_soak)
    b_visc = calculate_viscosity(b_thermal.temperature_c)
    b_inflow = calculate_inflow(b_visc.viscosity_kcp)
    b_srp = calculate_srp_response(b_inflow.inflow_bpd, b_spm, b_stroke, b_visc.viscosity_kcp, b_steam)

    # 2. Alternative Run
    a_steam = float(alternative_controls.get("steam_mass_t", 114.0))
    a_soak = int(alternative_controls.get("soak_h", 60))
    a_spm = float(alternative_controls.get("pump_speed_spm", 7.5))
    a_stroke = float(alternative_controls.get("stroke_length_m", 1.55))

    a_thermal = simulate_css_cycle(a_steam, soak_h=a_soak)
    a_visc = calculate_viscosity(a_thermal.temperature_c)
    a_inflow = calculate_inflow(a_visc.viscosity_kcp)
    a_srp = calculate_srp_response(a_inflow.inflow_bpd, a_spm, a_stroke, a_visc.viscosity_kcp, a_steam)

    deltas = {
        "delta_steam_t": round(a_steam - b_steam, 2),
        "delta_temp_c": round(a_thermal.temperature_c - b_thermal.temperature_c, 2),
        "delta_viscosity_kcp": round(a_visc.viscosity_kcp - b_visc.viscosity_kcp, 3),
        "delta_inflow_bpd": round(a_inflow.inflow_bpd - b_inflow.inflow_bpd, 2),
        "delta_oil_rate_bpd": round(a_srp.oil_rate_bpd - b_srp.oil_rate_bpd, 2),
        "delta_fillage_pct": round(a_srp.pump_fillage_pct - b_srp.pump_fillage_pct, 2),
        "delta_load_kn": round(a_srp.srp_load_kn - b_srp.srp_load_kn, 2),
        "delta_energy_kwh_bbl": round(a_srp.energy_kwh_bbl - b_srp.energy_kwh_bbl, 2),
        "delta_risk_score": round(a_srp.risk_score - b_srp.risk_score, 1),
    }

    return {
        "label": COUNTERFACTUAL_LABEL,
        "baseline": {
            "controls": {"steam_mass_t": b_steam, "soak_h": b_soak, "spm": b_spm, "stroke_m": b_stroke},
            "temperature_c": b_thermal.temperature_c,
            "viscosity_kcp": b_visc.viscosity_kcp,
            "inflow_bpd": b_inflow.inflow_bpd,
            "oil_rate_bpd": b_srp.oil_rate_bpd,
            "fillage_pct": b_srp.pump_fillage_pct,
            "load_kn": b_srp.srp_load_kn,
            "energy_kwh_bbl": b_srp.energy_kwh_bbl,
            "risk_score": b_srp.risk_score,
            "trajectory": b_thermal.temperature_trajectory_c
        },
        "alternative": {
            "controls": {"steam_mass_t": a_steam, "soak_h": a_soak, "spm": a_spm, "stroke_m": a_stroke},
            "temperature_c": a_thermal.temperature_c,
            "viscosity_kcp": a_visc.viscosity_kcp,
            "inflow_bpd": a_inflow.inflow_bpd,
            "oil_rate_bpd": a_srp.oil_rate_bpd,
            "fillage_pct": a_srp.pump_fillage_pct,
            "load_kn": a_srp.srp_load_kn,
            "energy_kwh_bbl": a_srp.energy_kwh_bbl,
            "risk_score": a_srp.risk_score,
            "trajectory": a_thermal.temperature_trajectory_c
        },
        "deltas": deltas
    }

def run_all_validations(persist: bool = True) -> List[ValidationResult]:
    """Runs all temporal and physics validations and optionally persists them to DB."""
    results = []
    results.extend(run_temporal_validation())
    results.extend(run_physics_validation())

    if persist and results:
        try:
            records = [
                {
                    "validation_type": r.validation_type,
                    "cycle_id": r.cycle_id,
                    "metric_name": r.metric_name,
                    "metric_value": r.metric_value,
                    "pass_fail": r.pass_fail,
                    "details": r.details
                }
                for r in results
            ]
            repository.insert_validation(records)
        except Exception:
            pass

    return results
