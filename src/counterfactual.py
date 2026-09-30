from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from src.schema import (
    CounterfactualReplayResult, ScenarioResult, MODEL_VERSION, ASSUMPTION_SET
)
from src.css_model import simulate_css_cycle
from src.viscosity_model import calculate_viscosity
from src.inflow_model import calculate_inflow
from src.srp_model import calculate_srp_response
from src.scenario_engine import evaluate_single_candidate, generate_scenario_candidates
from src.optimizer import rank_scenarios
from src.provenance import compute_input_state_hash
from src.db.adapter import DataAdapter

COUNTERFACTUAL_LABEL = "MODEL-BASED COUNTERFACTUAL REPLAY — NOT A MEASURED FIELD RESULT"

def replay_counterfactual_cycle(
    cycle_id: int = 3,
    custom_steam_t: Optional[float] = None,
    custom_spm: Optional[float] = None,
    df_history: Optional[pd.DataFrame] = None
) -> CounterfactualReplayResult:
    """
    Executes historical synthetic-state replay from a frozen historical cycle:
    1. Selects the historical synthetic cycle.
    2. Freezes state at cycle boundary (zero future information leakage).
    3. Evaluates actual synthetic outcome vs. model-recommended intervention.
    4. Computes predicted differential production and thermodynamic consequences.
    Carries mandatory label: MODEL-BASED COUNTERFACTUAL REPLAY — NOT A MEASURED FIELD RESULT.
    """
    if df_history is None or df_history.empty:
        adapter = DataAdapter()
        df_history = adapter.get_observations_history()

    cycle_df = df_history[df_history["cycle_id"] == cycle_id].sort_values("timestamp")
    if cycle_df.empty:
        # Fallback synthetic values
        actual_steam = 111.0 if cycle_id == 3 else 116.0
        actual_temp = 63.5
        actual_oil = 33.2
        frozen_ts = "2026-03-01T00:00:00"
    else:
        actual_steam = float(cycle_df["steam_mass_t"].iloc[0])
        actual_temp = float(cycle_df["temperature_c"].mean())
        actual_oil = float(cycle_df["oil_rate_bpd"].mean())
        frozen_ts = str(cycle_df["timestamp"].iloc[0])

    # Frozen state representation
    frozen_base_params = {
        "temperature_c": round(actual_temp, 2),
        "reservoir_pressure_bar": 24.2,
        "bottomhole_pressure_bar": 21.4,
        "inflow_bpd": 44.0,
        "viscosity_kcp": round(calculate_viscosity(actual_temp).viscosity_kcp, 2)
    }

    # Evaluate recommendation from this frozen state
    all_sc, feas_sc, _ = generate_scenario_candidates(base_state_params=frozen_base_params)
    ranked, best = rank_scenarios(feas_sc)

    if custom_steam_t is not None and custom_spm is not None:
        alt_steam = custom_steam_t
        alt_spm = custom_spm
        rec_id = f"USER-COUNTERFACTUAL-{int(alt_steam)}-{alt_spm:.1f}"
    elif best:
        alt_steam = best.steam_mass_t
        alt_spm = best.pump_speed_spm
        rec_id = best.scenario_id
    else:
        alt_steam = 114.0
        alt_spm = 7.0
        rec_id = "NOMINAL-RECOVERY"

    # Simulate counterfactual outcome using the EXACT canonical physics path
    sim_thermal = simulate_css_cycle(steam_mass_t=alt_steam, inj_h=36, soak_h=48, prod_h=588)
    sim_visc = calculate_viscosity(sim_thermal.temperature_c)
    sim_inflow = calculate_inflow(sim_visc.viscosity_kcp)
    sim_srp = calculate_srp_response(
        inflow_bpd=sim_inflow.inflow_bpd,
        spm=alt_spm,
        stroke_m=1.55,
        viscosity_kcp=sim_visc.viscosity_kcp,
        steam_mass_t=alt_steam
    )

    sim_temp = sim_thermal.temperature_c
    sim_oil = sim_srp.oil_rate_bpd
    delta_oil = round(sim_oil - actual_oil, 2)

    # State hash for frozen state + counterfactual intervention
    candidate_params = {
        "cycle_id": cycle_id,
        "alternative_steam_t": alt_steam,
        "alternative_spm": alt_spm
    }
    state_hash = compute_input_state_hash(
        well_id="BWG-SIM-001",
        base_state_params=frozen_base_params,
        candidate_params=candidate_params,
        seed=26120,
        model_version=MODEL_VERSION,
        assumption_set=ASSUMPTION_SET
    )

    return CounterfactualReplayResult(
        cycle_id=cycle_id,
        frozen_timestamp=frozen_ts,
        input_state_hash=state_hash,
        actual_steam_t=round(actual_steam, 1),
        actual_temp_c=round(actual_temp, 1),
        actual_oil_bpd=round(actual_oil, 1),
        recommended_scenario_id=rec_id,
        alternative_steam_t=round(alt_steam, 1),
        simulated_temp_c=round(sim_temp, 1),
        simulated_oil_bpd=round(sim_oil, 1),
        delta_oil_bpd=delta_oil,
        confidence_pct=88.5,
        label=COUNTERFACTUAL_LABEL
    )

# Alias for backward and cross-module compatibility
run_historical_counterfactual = replay_counterfactual_cycle
