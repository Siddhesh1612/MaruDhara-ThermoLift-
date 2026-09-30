# DB — Database Design

## Strategy
- Schema is **PostgreSQL-first** (Supabase-ready), stored in `db/schema.sql`.
- Prototype runs on **SQLite** through SQLAlchemy; the repository renders the
  same tables (TIMESTAMPTZ→TEXT, SERIAL→INTEGER, enums→TEXT+CHECK).
- Migration to Supabase = run `schema.sql` in Supabase SQL editor + change
  `DATABASE_URL` in `.env`. No application code changes.

## Connection
- `.env` → `DATABASE_URL=sqlite:///data/thermolift.db` (now)
- Later  → `DATABASE_URL=postgresql+psycopg2://user:pwd@host:5432/postgres`
- ONLY `src/db/repository.py` may open sessions.

## Tables (full DDL in db/schema.sql)
| Table | Purpose |
|---|---|
| wells | well identity + provenance |
| reservoir_properties | k, h, φ, skin, radii, P, T; status SYNTHETIC/ENGINEERING/OIL_PUBLISHED |
| fluid_properties | μ_ref, T_ref, k coefficient, FVF; labelled uncalibrated |
| css_cycles | per-cycle steam mass, pressure, injection/soak/production durations |
| time_series_observations | hourly rows — all dataset columns + provenance |
| operating_limits | configurable hard constraints (fillage min, load max, steam max…) |
| assumptions | assumption register: name, value, unit, status, justification |
| model_weights | ranking weights w_oil/w_steam/w_energy/w_risk (UI-editable) |
| model_runs | one row per Simulate click (inputs, candidate count, seed, model_version) |
| scenarios | every candidate + all computed outputs + feasible/rejection_reason |
| recommendations | chosen scenario, rationale, confidence, operator status |
| audit_log | every operator action with timestamp |
| diagnostics_events | rod-floating/fluid-pound/etc. alerts with rule evidence |
| validation_results | metric_name, cycle, value (MAE/RMSE/monotonic pass) |

## Provenance Rule
Every generated row carries `source_label` (SYNTHETIC/…), `random_seed`,
`model_version`. Any parameter that could be mistaken for a field limit must
carry status: OIL_PUBLISHED / LITERATURE / ENGINEERING / SYNTHETIC.
