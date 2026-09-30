import hashlib
import json
from typing import Any, Dict, Optional

def compute_input_state_hash(
    well_id: Any = "BWG-SIM-001",
    base_state_params: Optional[Dict[str, Any]] = None,
    candidate_params: Optional[Dict[str, Any]] = None,
    seed: int = 26120,
    model_version: str = "v2.0",
    assumption_set: str = "DEFAULT_PROTOTYPE_v2.0"
) -> str:
    """
    Computes a deterministic, collision-resistant 16-character SHA-256 hash
    representing the exact well state, physics model version, assumption set,
    random seed, and candidate parameters.
    Supports either explicit parameters or a WellState object as the first argument.
    """
    if hasattr(well_id, "well_id"):  # WellState object passed
        ws = well_id
        actual_well_id = getattr(ws, "well_id", "BWG-SIM-001")
        actual_seed = getattr(ws, "random_seed", 26120)
        actual_model_version = getattr(ws, "model_version", "v2.0")
        actual_assumption = getattr(ws, "assumption_set", "DEFAULT_PROTOTYPE_v2.0")
        base_state = {
            "temperature_c": getattr(ws, "temperature_c", 58.5),
            "reservoir_pressure_bar": getattr(ws, "reservoir_pressure_bar", 24.2),
            "bottomhole_pressure_bar": getattr(ws, "bottomhole_pressure_bar", 21.4),
            "viscosity_kcp": getattr(ws, "viscosity_kcp", 9.2),
            "inflow_bpd": getattr(ws, "inflow_bpd", 44.0),
            "oil_rate_bpd": getattr(ws, "oil_rate_bpd", 35.0),
            "pump_speed_spm": getattr(ws, "pump_speed_spm", 7.0),
            "stroke_length_m": getattr(ws, "stroke_length_m", 1.55),
            "data_quality": getattr(ws, "data_quality", "GOOD"),
            "timestamp": getattr(ws, "timestamp", ""),
        }
        candidate = candidate_params or {}
    else:
        actual_well_id = str(well_id)
        actual_seed = int(seed)
        actual_model_version = str(model_version)
        actual_assumption = str(assumption_set)
        base_state = base_state_params or {}
        candidate = candidate_params or {}

    canonical_dict = {
        "well_id": str(actual_well_id),
        "base_state": {
            k: (round(float(v), 4) if isinstance(v, (int, float)) else str(v))
            for k, v in sorted(base_state.items())
        },
        "candidate": {
            k: (round(float(v), 4) if isinstance(v, (int, float)) else str(v))
            for k, v in sorted(candidate.items())
        },
        "seed": actual_seed,
        "model_version": actual_model_version,
        "assumption_set": actual_assumption,
    }
    payload = json.dumps(canonical_dict, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
