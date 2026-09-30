import json
from datetime import datetime
from contextlib import contextmanager
from typing import Any, Dict, List, Optional
import pandas as pd
from sqlalchemy import desc, text

from src.db.engine import get_engine, SessionLocal
from src.db.models import (
    Base, WellModel, ReservoirPropertyModel, FluidPropertyModel, CSSCycleModel,
    TimeSeriesObservationModel, OperatingLimitModel, AssumptionModel,
    ModelWeightModel, ModelRunModel, ScenarioModel, RecommendationModel,
    AuditLogModel, DiagnosticsEventModel, ValidationResultModel,
    AblationExperimentModel, PressureChainRunModel
)

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def init_db():
    """Initialize database tables and run migration for schema extensions."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    migrate_db()

def migrate_db():
    """Ensure all required columns exist in existing tables (SQLite safe)."""
    engine = get_engine()
    with engine.connect() as conn:
        try:
            # Check scenarios columns
            res = conn.execute(text("PRAGMA table_info(scenarios)")).fetchall()
            existing_cols = {row[1] for row in res}
            required_cols = {
                "input_state_hash": "TEXT",
                "model_version": "TEXT",
                "assumption_set": "TEXT",
                "random_seed": "INTEGER",
                "margin_fillage": "FLOAT",
                "margin_load": "FLOAT",
                "margin_steam": "FLOAT",
                "norm_oil": "FLOAT",
                "norm_steam": "FLOAT",
                "norm_energy": "FLOAT",
                "norm_risk": "FLOAT",
                "norm_maint": "FLOAT",
                "p_wf_bar": "FLOAT",
                "pip_bar": "FLOAT",
                "whp_bar": "FLOAT",
                "flowline_p_bar": "FLOAT"
            }
            for col, col_type in required_cols.items():
                if col not in existing_cols:
                    conn.execute(text(f"ALTER TABLE scenarios ADD COLUMN {col} {col_type}"))
            conn.commit()
        except Exception:
            pass

def upsert_well(well_data: Dict[str, Any]):
    """Insert or update well identity."""
    with session_scope() as session:
        well = session.query(WellModel).filter_by(well_id=well_data["well_id"]).first()
        if not well:
            well = WellModel(**well_data)
            session.add(well)
        else:
            for k, v in well_data.items():
                setattr(well, k, v)

def insert_cycle(cycle_data: Dict[str, Any]):
    """Insert a CSS cycle record."""
    with session_scope() as session:
        cycle = CSSCycleModel(**cycle_data)
        session.add(cycle)

def bulk_insert_observations(rows: List[Dict[str, Any]]):
    """Bulk insert time series observations efficiently."""
    if not rows:
        return
    with session_scope() as session:
        objects = [TimeSeriesObservationModel(**r) for r in rows]
        session.bulk_save_objects(objects)

def get_latest_state_rows(well_id: str = "BWG-SIM-001", limit: int = 1) -> List[Dict[str, Any]]:
    """Retrieve the most recent observation rows for a well."""
    with session_scope() as session:
        records = (
            session.query(TimeSeriesObservationModel)
            .filter_by(well_id=well_id)
            .order_by(desc(TimeSeriesObservationModel.timestamp))
            .limit(limit)
            .all()
        )
        return [
            {c.name: getattr(r, c.name) for c in r.__table__.columns}
            for r in records
        ]

def get_all_observations(well_id: str = "BWG-SIM-001") -> pd.DataFrame:
    """Retrieve all observations as a pandas DataFrame."""
    with session_scope() as session:
        records = (
            session.query(TimeSeriesObservationModel)
            .filter_by(well_id=well_id)
            .order_by(TimeSeriesObservationModel.timestamp.asc())
            .all()
        )
        data = [{c.name: getattr(r, c.name) for c in r.__table__.columns} for r in records]
        return pd.DataFrame(data)

def seed_operating_limits(limits_dict: Dict[str, Any]):
    """Seed default operating limits from dictionary/yaml."""
    with session_scope() as session:
        for name, item in limits_dict.items():
            existing = session.query(OperatingLimitModel).filter_by(limit_name=name).first()
            if not existing:
                rec = OperatingLimitModel(
                    limit_name=name,
                    value=float(item.get("value", 0.0)),
                    unit=str(item.get("unit", "")),
                    operator_bound=str(item.get("bound", "MAX")),
                    description=str(item.get("description", "")),
                    status=str(item.get("status", "CONFIGURABLE PROTOTYPE ASSUMPTION")),
                )
                session.add(rec)
            else:
                existing.value = float(item.get("value", existing.value))

def get_limits() -> Dict[str, float]:
    """Return dictionary of limit_name -> value."""
    with session_scope() as session:
        records = session.query(OperatingLimitModel).all()
        return {r.limit_name: r.value for r in records}

def seed_model_weights(weights_dict: Dict[str, float]):
    """Seed default ranking weights."""
    with session_scope() as session:
        for name, val in weights_dict.items():
            existing = session.query(ModelWeightModel).filter_by(weight_name=name).first()
            if not existing:
                rec = ModelWeightModel(weight_name=name, weight_value=float(val))
                session.add(rec)

def get_weights() -> Dict[str, float]:
    """Return dictionary of weight_name -> weight_value."""
    with session_scope() as session:
        records = session.query(ModelWeightModel).all()
        return {r.weight_name: r.weight_value for r in records}

def seed_assumptions(assumptions_list: List[Dict[str, Any]]):
    """Seed assumptions from register."""
    with session_scope() as session:
        for item in assumptions_list:
            existing = session.query(AssumptionModel).filter_by(parameter_name=item["parameter_name"]).first()
            if not existing:
                rec = AssumptionModel(**item)
                session.add(rec)

def get_assumptions() -> List[Dict[str, Any]]:
    """Return all assumptions."""
    with session_scope() as session:
        records = session.query(AssumptionModel).all()
        return [{c.name: getattr(r, c.name) for c in r.__table__.columns} for r in records]

def seed_properties(reservoir_data: Dict[str, Any], fluid_data: Dict[str, Any]):
    """Seed reservoir and fluid properties."""
    with session_scope() as session:
        res = session.query(ReservoirPropertyModel).filter_by(well_id=reservoir_data["well_id"]).first()
        if not res:
            session.add(ReservoirPropertyModel(**reservoir_data))
        flu = session.query(FluidPropertyModel).filter_by(well_id=fluid_data["well_id"]).first()
        if not flu:
            session.add(FluidPropertyModel(**fluid_data))

def get_properties(well_id: str = "BWG-SIM-001") -> Dict[str, Any]:
    """Retrieve reservoir and fluid properties."""
    with session_scope() as session:
        res = session.query(ReservoirPropertyModel).filter_by(well_id=well_id).first()
        flu = session.query(FluidPropertyModel).filter_by(well_id=well_id).first()
        return {
            "reservoir": {c.name: getattr(res, c.name) for c in res.__table__.columns} if res else {},
            "fluid": {c.name: getattr(flu, c.name) for c in flu.__table__.columns} if flu else {},
        }

def insert_model_run(run_data: Dict[str, Any]):
    """Insert a simulation run record."""
    with session_scope() as session:
        rec = ModelRunModel(**run_data)
        session.add(rec)

def insert_scenarios(scenarios: List[Dict[str, Any]]):
    """Insert evaluated candidate scenarios for a run."""
    if not scenarios:
        return
    valid_cols = {c.name for c in ScenarioModel.__table__.columns}
    with session_scope() as session:
        objects = []
        for s in scenarios:
            sd = s.copy()
            filtered = {k: v for k, v in sd.items() if k in valid_cols}
            if "constraint_margins" in sd and isinstance(sd["constraint_margins"], dict):
                filtered["margin_fillage"] = sd["constraint_margins"].get("fillage_margin_pct")
                filtered["margin_load"] = sd["constraint_margins"].get("load_margin_kn")
                filtered["margin_steam"] = sd["constraint_margins"].get("steam_margin_t")
            objects.append(ScenarioModel(**filtered))
        session.bulk_save_objects(objects)

def get_scenarios_for_run(run_id: str) -> List[Dict[str, Any]]:
    """Retrieve candidate scenarios for a run."""
    with session_scope() as session:
        records = session.query(ScenarioModel).filter_by(run_id=run_id).all()
        return [{c.name: getattr(r, c.name) for c in r.__table__.columns} for r in records]

def insert_recommendation(rec_data: Dict[str, Any]):
    """Insert recommendation record."""
    with session_scope() as session:
        # Convert dictionary fields to strings if needed
        data_to_insert = rec_data.copy()
        if isinstance(data_to_insert.get("constraint_margins"), dict):
            data_to_insert["constraint_margins"] = json.dumps(data_to_insert["constraint_margins"])
        rec = RecommendationModel(**data_to_insert)
        session.add(rec)

def get_latest_recommendation(run_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Get the latest recommendation, optionally for a specific run."""
    with session_scope() as session:
        q = session.query(RecommendationModel)
        if run_id:
            q = q.filter_by(run_id=run_id)
        rec = q.order_by(desc(RecommendationModel.id)).first()
        if not rec:
            return None
        res = {c.name: getattr(rec, c.name) for c in rec.__table__.columns}
        if isinstance(res.get("constraint_margins"), str):
            try:
                res["constraint_margins"] = json.loads(res["constraint_margins"])
            except Exception:
                pass
        return res

def update_recommendation_status(
    run_id: str,
    new_status: str,
    notes: str = "",
    operator_user: str = "operator"
):
    """Update recommendation status and insert an audit log record."""
    with session_scope() as session:
        rec = session.query(RecommendationModel).filter_by(run_id=run_id).order_by(desc(RecommendationModel.id)).first()
        old_status = rec.operator_status if rec else "UNKNOWN"
        if rec:
            rec.operator_status = new_status
            rec.updated_at = datetime.utcnow().isoformat()
        
        audit_entry = AuditLogModel(
            timestamp=datetime.utcnow().isoformat(),
            operator_user=operator_user,
            action=f"RECOMMENDATION_{new_status.upper()}",
            target_id=run_id,
            old_status=old_status,
            new_status=new_status,
            notes=notes,
        )
        session.add(audit_entry)

def insert_audit(audit_data: Dict[str, Any]):
    """Insert a single audit log entry."""
    with session_scope() as session:
        entry = AuditLogModel(**audit_data)
        session.add(entry)

def get_audit_logs(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve recent audit logs."""
    with session_scope() as session:
        records = session.query(AuditLogModel).order_by(desc(AuditLogModel.id)).limit(limit).all()
        return [{c.name: getattr(r, c.name) for c in r.__table__.columns} for r in records]

def insert_diagnostics(events: List[Dict[str, Any]]):
    """Insert diagnostics events."""
    if not events:
        return
    with session_scope() as session:
        objects = []
        for e in events:
            ed = e.copy()
            if isinstance(ed.get("variables"), dict):
                ed["variables"] = json.dumps(ed["variables"])
            if isinstance(ed.get("thresholds"), dict):
                ed["thresholds"] = json.dumps(ed["thresholds"])
            objects.append(DiagnosticsEventModel(**ed))
        session.bulk_save_objects(objects)

def get_recent_diagnostics(well_id: str = "BWG-SIM-001", limit: int = 20) -> List[Dict[str, Any]]:
    """Retrieve recent diagnostics events."""
    with session_scope() as session:
        records = (
            session.query(DiagnosticsEventModel)
            .filter_by(well_id=well_id)
            .order_by(desc(DiagnosticsEventModel.id))
            .limit(limit)
            .all()
        )
        results = []
        for r in records:
            d = {c.name: getattr(r, c.name) for c in r.__table__.columns}
            if isinstance(d.get("variables"), str):
                try: d["variables"] = json.loads(d["variables"])
                except Exception: pass
            if isinstance(d.get("thresholds"), str):
                try: d["thresholds"] = json.loads(d["thresholds"])
                except Exception: pass
            results.append(d)
        return results

def insert_validation(results: List[Dict[str, Any]]):
    """Insert validation results."""
    if not results:
        return
    with session_scope() as session:
        objects = [ValidationResultModel(**r) for r in results]
        session.bulk_save_objects(objects)

def get_validation_results() -> List[Dict[str, Any]]:
    """Retrieve all validation results."""
    with session_scope() as session:
        records = session.query(ValidationResultModel).all()
        return [{c.name: getattr(r, c.name) for c in r.__table__.columns} for r in records]

def insert_ablation_experiment(data: Dict[str, Any]):
    """Insert an ablation experiment record (Independent vs Coupled)."""
    with session_scope() as session:
        rec = AblationExperimentModel(**data)
        session.add(rec)

def get_ablation_experiments(run_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve ablation experiment records."""
    with session_scope() as session:
        q = session.query(AblationExperimentModel)
        if run_id:
            q = q.filter_by(run_id=run_id)
        records = q.order_by(desc(AblationExperimentModel.id)).all()
        return [{c.name: getattr(r, c.name) for c in r.__table__.columns} for r in records]

def insert_pressure_chain_run(data: Dict[str, Any]):
    """Insert a wellbore-to-surface pressure chain run."""
    with session_scope() as session:
        rec = PressureChainRunModel(**data)
        session.add(rec)

def get_pressure_chain_run(scenario_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve pressure chain run for a scenario."""
    with session_scope() as session:
        rec = session.query(PressureChainRunModel).filter_by(scenario_id=scenario_id).first()
        if not rec:
            return None
        return {c.name: getattr(rec, c.name) for c in rec.__table__.columns}
