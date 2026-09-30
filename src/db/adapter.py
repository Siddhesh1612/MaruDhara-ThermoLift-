import json
from pathlib import Path
from typing import Any, Dict, Optional
import pandas as pd
import yaml

from src.db import repository

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"

class DataAdapter:
    """Unified data access adapter with DB primary and CSV fallback."""

    def __init__(self, well_id: str = "BWG-SIM-001"):
        self.well_id = well_id

    def get_latest_observation(self) -> Dict[str, Any]:
        """Fetch latest telemetry record from DB or fallback to current_state.json."""
        try:
            rows = repository.get_latest_state_rows(self.well_id, limit=1)
            if rows:
                return rows[0]
        except Exception:
            pass

        # Fallback to current_state.json or tail of synthetic_well.csv
        state_file = DATA_DIR / "current_state.json"
        if state_file.exists():
            data = json.loads(state_file.read_text())
            if isinstance(data, list) and len(data) > 0:
                return data[0]
            if isinstance(data, dict):
                return data

        csv_file = DATA_DIR / "synthetic_well.csv"
        if csv_file.exists():
            df = pd.read_csv(csv_file)
            return df.iloc[-1].to_dict()

        raise RuntimeError("No telemetry source available (DB and CSV fallback both unavailable).")

    def get_observations_history(self) -> pd.DataFrame:
        """Fetch full time-series history from DB or fallback to synthetic_well.csv."""
        try:
            df = repository.get_all_observations(self.well_id)
            if not df.empty:
                return df
        except Exception:
            pass

        csv_file = DATA_DIR / "synthetic_well.csv"
        if csv_file.exists():
            return pd.read_csv(csv_file)

        return pd.DataFrame()

    def get_scenario_catalogue(self) -> pd.DataFrame:
        """Fetch pre-evaluated scenarios or fallback to scenario_catalogue.csv."""
        csv_file = DATA_DIR / "scenario_catalogue.csv"
        if csv_file.exists():
            return pd.read_csv(csv_file)
        return pd.DataFrame()

    def get_operating_limits(self) -> Dict[str, float]:
        """Fetch operating limits from DB or fallback to config/operating_limits.yaml."""
        try:
            limits = repository.get_limits()
            if limits:
                return limits
        except Exception:
            pass

        yaml_file = CONFIG_DIR / "operating_limits.yaml"
        if yaml_file.exists():
            with open(yaml_file, "r") as f:
                cfg = yaml.safe_load(f)
                return {k: float(v["value"]) for k, v in cfg.get("operating_limits", {}).items()}

        # Safe defaults
        return {
            "min_pump_fillage_pct": 52.0,
            "max_srp_load_kn": 62.0,
            "max_steam_mass_t": 118.0,
            "min_spm": 5.0,
            "max_spm": 10.0,
            "min_stroke_m": 1.45,
            "max_stroke_m": 1.65,
        }

    def get_model_weights(self) -> Dict[str, float]:
        """Fetch ranking weights from DB or fallback to config."""
        try:
            weights = repository.get_weights()
            if weights:
                return weights
        except Exception:
            pass

        yaml_file = CONFIG_DIR / "operating_limits.yaml"
        if yaml_file.exists():
            with open(yaml_file, "r") as f:
                cfg = yaml.safe_load(f)
                return {k: float(v) for k, v in cfg.get("default_weights", {}).items()}

        return {"w_oil": 1.0, "w_steam": 0.0, "w_energy": 0.45, "w_risk": 0.25}
