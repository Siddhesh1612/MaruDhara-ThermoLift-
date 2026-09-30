from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from src.schema import WellState
from src.db.adapter import DataAdapter
from src.db import repository

class StateEstimator:
    """Estimates and validates the current well state from latest telemetry."""

    def __init__(self, well_id: str = "BWG-SIM-001"):
        self.well_id = well_id
        self.adapter = DataAdapter(well_id)

    def validate_telemetry(self, rows: List[Dict[str, Any]]) -> Tuple[str, List[str]]:
        """
        Validate telemetry stream for:
        - missing data
        - stale data
        - duplicate timestamps
        - invalid units / physical range violations
        Returns (data_quality, warnings)
        """
        if not rows:
            return "FAIL", ["No telemetry data available."]

        warnings = []
        latest = rows[0]

        # 1. Check Missing Data (Null or NaN in critical fields)
        critical_fields = [
            "temperature_c", "viscosity_kcp", "reservoir_pressure_bar",
            "bottomhole_pressure_bar", "inflow_bpd", "pump_fillage_pct",
            "srp_load_kn", "pump_speed_spm"
        ]
        for field in critical_fields:
            val = latest.get(field)
            if val is None or (isinstance(val, float) and pd.isna(val)):
                warnings.append(f"Missing critical telemetry field: {field}")

        # 2. Check Unit / Range Bounds
        temp = latest.get("temperature_c")
        if temp is not None:
            if temp < 20.0 or temp > 150.0:
                warnings.append(f"Temperature out of physical operating bounds: {temp} °C")

        visc = latest.get("viscosity_kcp")
        if visc is not None:
            if visc <= 0.0 or visc > 100.0:
                warnings.append(f"Viscosity out of physical bounds: {visc} kcP")

        pres = latest.get("reservoir_pressure_bar")
        if pres is not None and pres < 0.0:
            warnings.append(f"Negative reservoir pressure detected: {pres} bar")

        fillage = latest.get("pump_fillage_pct")
        if fillage is not None and (fillage < 0.0 or fillage > 120.0):
            warnings.append(f"Invalid pump fillage: {fillage} %")

        load = latest.get("srp_load_kn")
        if load is not None and (load < 0.0 or load > 150.0):
            warnings.append(f"Invalid SRP load: {load} kN")

        # 3. Check Duplicate Timestamps and Stale Data across recent history
        if len(rows) > 1:
            ts_list = [r.get("timestamp") for r in rows if r.get("timestamp")]
            if len(ts_list) != len(set(ts_list)):
                warnings.append("Duplicate timestamps detected in recent observations.")

            # Check if frozen/flatline data
            temp_history = [r.get("temperature_c") for r in rows if r.get("temperature_c") is not None]
            if len(temp_history) >= 8 and len(set(temp_history)) == 1:
                warnings.append("Stale telemetry detected (sensor flatline across 8+ steps).")

        # Determine Data Quality
        if any("Missing critical" in w or "Negative reservoir" in w or "out of physical" in w for w in warnings):
            data_quality = "FAIL"
        elif warnings:
            data_quality = "SUSPECT"
        else:
            data_quality = "GOOD"

        return data_quality, warnings

    def get_latest_state(self, limit: int = 5) -> WellState:
        """Assembles and returns a validated typed WellState."""
        try:
            recent_rows = repository.get_latest_state_rows(self.well_id, limit=limit)
        except Exception:
            recent_rows = []

        if not recent_rows:
            # Fallback to adapter
            single_obs = self.adapter.get_latest_observation()
            recent_rows = [single_obs]

        latest = recent_rows[0]
        data_quality, warnings = self.validate_telemetry(recent_rows)

        return WellState(
            well_id=self.well_id,
            timestamp=str(latest.get("timestamp", datetime.utcnow().isoformat())),
            phase=str(latest.get("phase", "production")),
            temperature_c=float(latest.get("temperature_c", 60.0)),
            viscosity_kcp=float(latest.get("viscosity_kcp", 8.5)),
            reservoir_pressure_bar=float(latest.get("reservoir_pressure_bar", 24.0)),
            bottomhole_pressure_bar=float(latest.get("bottomhole_pressure_bar", 21.2)),
            inflow_bpd=float(latest.get("inflow_bpd", 45.0)),
            oil_rate_bpd=float(latest.get("oil_rate_bpd", 32.0)),
            water_rate_bpd=float(latest.get("water_rate_bpd", 8.0)),
            pump_speed_spm=float(latest.get("pump_speed_spm", 6.8)),
            stroke_length_m=float(latest.get("stroke_length_m", 1.55)),
            pump_fillage_pct=float(latest.get("pump_fillage_pct", 65.0)),
            srp_load_kn=float(latest.get("srp_load_kn", 46.0)),
            energy_kwh_bbl=float(latest.get("energy_kwh_bbl", 16.5)),
            srp_risk_score=int(latest.get("srp_risk_score", 15)),
            data_quality=data_quality,
            source_label=str(latest.get("source_label", "SYNTHETIC")),
            random_seed=int(latest.get("random_seed", 26120)),
            model_version="v1.0"
        )

def get_latest_state(well_id: str = "BWG-SIM-001") -> WellState:
    """Convenience function returning typed WellState."""
    estimator = StateEstimator(well_id)
    return estimator.get_latest_state()
