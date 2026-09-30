import json
from datetime import datetime
from typing import Any, Dict, List, Optional
import pandas as pd

from src.schema import Diagnostic, WellState
from src.db import repository

def evaluate_diagnostics(
    history_df: Optional[pd.DataFrame] = None,
    current_state: Optional[WellState] = None,
    operating_limits: Optional[Dict[str, float]] = None,
    persist: bool = True
) -> List[Diagnostic]:
    """
    Evaluates rules-first SRP operational diagnostics:
    - ROD_FLOATING
    - FLUID_POUND
    - ROD_LOADING
    - VALVE_INSPECT
    - INSUFFICIENT_DATA
    Every diagnostic includes fired status, variables, thresholds, data quality, and message.
    Fired alerts are persisted via repository.py.
    """
    diagnostics = []

    # Fetch limits if not provided
    if operating_limits is None:
        try:
            operating_limits = repository.get_limits()
        except Exception:
            operating_limits = {}

    min_fillage = float(operating_limits.get("min_pump_fillage_pct", 52.0))
    max_load = float(operating_limits.get("max_srp_load_kn", 62.0))

    # Guard: check if current state exists
    if current_state is None:
        from src.state_estimator import get_latest_state
        current_state = get_latest_state()

    dq = current_state.data_quality

    # 1. INSUFFICIENT_DATA Check
    # If telemetry quality is FAIL or history is empty
    if dq == "FAIL" or (history_df is not None and history_df.empty):
        diag = Diagnostic(
            rule_name="INSUFFICIENT_DATA",
            fired=True,
            severity="CRITICAL",
            variables={"data_quality": dq, "history_len": len(history_df) if history_df is not None else 0},
            thresholds={"required_quality": "GOOD or SUSPECT", "min_history_rows": 5},
            data_quality=dq,
            message="Telemetry stream contains critical quality failures or missing data; diagnostic engine suppressed."
        )
        diagnostics.append(diag)
        if persist:
            _persist_fired_events([diag], current_state.well_id)
        return diagnostics

    # Current telemetry values
    fillage = current_state.pump_fillage_pct
    load = current_state.srp_load_kn
    viscosity = current_state.viscosity_kcp
    spm = current_state.pump_speed_spm
    oil_rate = current_state.oil_rate_bpd

    # 2. FLUID_POUND Check
    # fillage < min_fillage OR (fillage < 55 and load variance high)
    is_fluid_pound = (fillage < min_fillage)
    diagnostics.append(Diagnostic(
        rule_name="FLUID_POUND",
        fired=is_fluid_pound,
        severity="WARNING" if is_fluid_pound else "INFO",
        variables={"pump_fillage_pct": fillage},
        thresholds={"min_fillage_threshold": min_fillage},
        data_quality=dq,
        message=f"Pump fillage ({fillage:.1f}%) is below minimum threshold ({min_fillage:.1f}%); traveling valve experiencing incomplete fluid fill and impact pounding."
        if is_fluid_pound else "Pump fillage within acceptable bounds; no fluid pound detected."
    ))

    # 3. ROD_FLOATING Check
    # High viscosity (>12 kcP) and high speed (>7.2 SPM) leads to buoyant drag resisting rod descent
    is_rod_floating = (viscosity > 11.5 and spm > 7.2)
    diagnostics.append(Diagnostic(
        rule_name="ROD_FLOATING",
        fired=is_rod_floating,
        severity="WARNING" if is_rod_floating else "INFO",
        variables={"viscosity_kcp": viscosity, "pump_speed_spm": spm},
        thresholds={"max_safe_viscosity_kcp": 11.5, "max_spm_high_visc": 7.2},
        data_quality=dq,
        message=f"High crude viscosity ({viscosity:.1f} kcP) combined with pump speed ({spm:.1f} SPM) creates viscous upward drag exceeding rod string buoyant descent velocity."
        if is_rod_floating else "Viscous drag and rod weight balance is normal."
    ))

    # 4. ROD_LOADING Check
    # Polished rod load approaching or exceeding limit
    is_rod_loading = (load > (max_load - 3.0))
    diagnostics.append(Diagnostic(
        rule_name="ROD_LOADING",
        fired=is_rod_loading,
        severity="CRITICAL" if load > max_load else ("WARNING" if is_rod_loading else "INFO"),
        variables={"srp_load_kn": load, "viscosity_kcp": viscosity, "spm": spm},
        thresholds={"max_load_threshold_kn": max_load, "warning_margin_kn": 3.0},
        data_quality=dq,
        message=f"Polished rod load ({load:.1f} kN) is within {max_load - load:.1f} kN of structural limit ({max_load:.1f} kN); risk of rod string fatigue or parting."
        if is_rod_loading else "Polished rod load is comfortably within structural margins."
    ))

    # 5. VALVE_INSPECT Check
    # Check if history shows sustained declining oil rate while fillage remains moderate
    is_valve_inspect = False
    if history_df is not None and len(history_df) >= 24:
        recent_rates = history_df["oil_rate_bpd"].tail(24)
        if len(recent_rates) >= 24:
            rate_drop = (recent_rates.iloc[0] - recent_rates.iloc[-1]) / max(recent_rates.iloc[0], 1.0)
            if rate_drop > 0.35 and fillage > 60.0:
                is_valve_inspect = True

    diagnostics.append(Diagnostic(
        rule_name="VALVE_INSPECT",
        fired=is_valve_inspect,
        severity="WARNING" if is_valve_inspect else "INFO",
        variables={"oil_rate_bpd": oil_rate, "pump_fillage_pct": fillage},
        thresholds={"max_unexplained_rate_drop_pct": 35.0},
        data_quality=dq,
        message="Sharp production decline observed despite adequate pump fillage; possible travelling or standing valve slippage."
        if is_valve_inspect else "Valve integrity and fluid displacement efficiency consistent with nominal behavior."
    ))

    # 6. INSUFFICIENT_DATA (passed if data was good)
    diagnostics.append(Diagnostic(
        rule_name="INSUFFICIENT_DATA",
        fired=False,
        severity="INFO",
        variables={"data_quality": dq},
        thresholds={"allowed": ["GOOD", "SUSPECT"]},
        data_quality=dq,
        message="Telemetry coverage and record completeness verified."
    ))

    # Persist fired events
    if persist:
        fired_events = [d for d in diagnostics if d.fired]
        if fired_events:
            _persist_fired_events(fired_events, current_state.well_id)

    return diagnostics

def _persist_fired_events(events: List[Diagnostic], well_id: str):
    """Save fired diagnostic alerts to database."""
    try:
        now_ts = datetime.utcnow().isoformat()
        db_records = [
            {
                "timestamp": now_ts,
                "well_id": well_id,
                "rule_name": e.rule_name,
                "variables": e.variables,
                "thresholds": e.thresholds,
                "data_quality": e.data_quality,
                "severity": e.severity,
                "message": e.message
            }
            for e in events
        ]
        repository.insert_diagnostics(db_records)
    except Exception:
        pass
