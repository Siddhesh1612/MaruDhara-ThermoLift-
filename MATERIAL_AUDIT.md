# Project Materials Audit: THERMOLIFT / MaruDhara (SIH26120)

**Date of Audit:** 26 September 2026  
**Auditor:** Project-Materials Auditor (Antigravity)  
**Target System:** Physics-Informed Well-to-Surface Decision Twin for CSS + SRP Operations in a Baghewala-Style Heavy-Oil Well  
**Problem ID:** SIH26120 / PS 26120 (Oil India Limited)  

---

## 1. Inventory & Status of Expected Project Files

| Expected File | Status | Exact Path | Purpose | Missing / Conflict / Retrieval Note |
|---|---|---|---|---|
| `docs/PRD.md` | **FOUND (RETRIEVED)** | `C:\Users\HP\Desktop\SIH PRO\docs\PRD.md` | High-level product definition, scope boundaries, feature specifications, 48-hr build order, and operator workflow. | Retrieved from official handoff artifact `MARUDHARA_THERMOLIFT_TECHNICAL_MVP_REPORT.md` (35,577 bytes, identical content to `Downloads\MaruDhara _ THERMOLIFT.md`). Unrelated files named `PRD.md`, `01_PRD.md`, `PRD (1).md` found in `Downloads` were from legacy projects (`ClientLens`, `Smart Print`, `Digital Menu`). |
| `docs/TRD.md` | **FOUND (RETRIEVED)** | `C:\Users\HP\Desktop\SIH PRO\docs\TRD.md` | Technical requirements, module contracts, canonical equations, determinism requirements, testing specifications. | Retrieved and normalized from `TRD (2).md` (3,612 bytes). Collision suffix `(2)` resolved; older unrelated files `Downloads\TRD.md` (ClientLens) and `Downloads\TRD (1).md` (Digital Menu) were disqualified. |
| `docs/FLOW.md` | **FOUND (RETRIEVED)** | `C:\Users\HP\Desktop\SIH PRO\docs\FLOW.md` | Boot flow, simulation run-time flow, operator advisory action flow, diagnostics flow, validation flow, and DB persistence. | Retrieved and normalized from `FLOW (2).md` (2,075 bytes). Collision suffix `(2)` resolved; older files `FLOW.md` (ClientLens) and `FLOW (1).md` (Digital Menu) disqualified. |
| `docs/DB.md` | **FOUND (RETRIEVED)** | `C:\Users\HP\Desktop\SIH PRO\docs\DB.md` | PostgreSQL/Supabase & SQLite database strategy, connection parameters, 14 table specifications, and provenance rules. | Found in workspace root as `DB.md` (2,011 bytes) and placed into `docs/DB.md`. Matches THERMOLIFT requirements. |
| `docs/BACKEND.md` | **FOUND (RETRIEVED)** | `C:\Users\HP\Desktop\SIH PRO\docs\BACKEND.md` | Backend architecture tree, hard rules, key function signatures, persistence sequence per simulation run. | Retrieved and normalized from `BACKEND (1).md` (3,326 bytes). Suffix `(1)` resolved; older `Downloads\BACKEND.md` (Digital Menu Express server) disqualified. |
| `docs/FRONTEND.md` | **FOUND (RETRIEVED)** | `C:\Users\HP\Desktop\SIH PRO\docs\FRONTEND.md` | Streamlit UI architecture, 6-tab specification (Current State, What-If, Recommendation, SRP Diagnostics, Validation, 3D Layer), styling guide. | Retrieved and normalized from `FRONTEND (1).md` (2,799 bytes). Suffix `(1)` resolved; older `Downloads\FRONTEND.md` (Digital Menu React UI) disqualified. |
| `db/schema.sql` | **BLOCKED / MISSING** | Expected: `C:\Users\HP\Desktop\SIH PRO\db\schema.sql` | Postgres/Supabase DDL establishing the 14 application tables; designated as primary database source of truth. | **CRITICAL MISSING ASSET**: Referenced by `docs/DB.md` and `docs/BACKEND.md`, but no `.sql` file exists in the workspace, handoff zip, or downloads. Must be created strictly conforming to `DB.md` specifications prior to DB implementation. |
| `generate_synthetic.py` | **FOUND (RETRIEVED)** | `C:\Users\HP\Desktop\SIH PRO\generate_synthetic.py` | Generates 4 cycles (2,688 hourly observations) for well `BWG-SIM-001` and 60 scenario candidates with fixed seed 26120. | Retrieved directly from `Downloads\MARUDHARA_MVP_HANDOFF\generate_synthetic.py` (6,511 bytes). Contains authentic causal physics relationships. Not fabricated. |
| `ASSUMPTIONS.md` | **FOUND (RETRIEVED)** | `C:\Users\HP\Desktop\SIH PRO\ASSUMPTIONS.md` | 30-parameter prototype assumption register, justification, provenance classification, and real-deployment promotion criteria. | Retrieved directly from `Downloads\MARUDHARA_MVP_HANDOFF\ASSUMPTIONS.md` (3,683 bytes). Not fabricated. |
| `README.md` | **MISSING** | Expected: `C:\Users\HP\Desktop\SIH PRO\README.md` | Project overview, setup steps, quick-start commands, and architectural summary. | Missing from repository and handoff package. |
| `requirements.txt` | **MISSING** | Expected: `C:\Users\HP\Desktop\SIH PRO\requirements.txt` | Python dependencies (streamlit, plotly, pandas, numpy, sqlalchemy, pydantic, pytest, etc.). | Missing from repository and handoff package; needed for dependency management. |
| `.env` / configuration | **MISSING** | Expected: `C:\Users\HP\Desktop\SIH PRO\.env` | Environment configuration specifying `DATABASE_URL` (`sqlite:///data/thermolift.db`). | Missing; default connection string is documented in `docs/DB.md` and `docs/BACKEND.md`. |

---

## 2. Additional Approved Data & Architecture Assets Discovered

From `C:\Users\HP\Downloads\MARUDHARA_MVP_HANDOFF\` (and `MARUDHARA_MVP_HANDOFF.zip`), the following pre-generated benchmark assets were discovered and retrieved into the workspace:

1. `data/synthetic_well.csv` (526,399 bytes) — 2,688 hourly records across 4 cycles generated with seed 26120.
2. `data/scenario_catalogue.csv` (7,058 bytes) — 60 pre-evaluated CSS+SRP scenario combinations with objective rankings and rejection reasons.
3. `data/current_state.json` (785 bytes) — Tail observation representing current well state for live replay.
4. `data/validation_split.json` (212 bytes) — Chronological split definition (Cycles 1–2 train, Cycle 3 val, Cycle 4 test).
5. `docs/architecture.mmd` & `docs/architecture.png` (86,024 bytes) — Official architectural block diagram.
6. `docs/synthetic_validation_figure.png` (242,694 bytes) — Official benchmark validation figure (phase-shaded temperature trajectory and scenario trade-off scatter).

---

## 3. Detailed Document Analysis (Task 4 Findings)

### 3.1 Project Scope & Boundaries
- **Objective:** Single-well decision-support digital twin for coupled Cyclic Steam Stimulation (CSS) and Sucker Rod Pump (SRP) operations in a representative Baghewala-style heavy-oil well (`BWG-SIM-001`).
- **Core Operational Question:** *"What happens to the entire well-to-surface system if CSS and/or SRP operating conditions change?"*
- **Causal Flow:** $\text{Steam injection} \to \text{Thermal response} \to \text{Temperature} \to \text{Heavy-oil viscosity} \to \text{Mobility / Inflow} \to \text{SRP fillage \& load} \to \text{Production rate} \to \text{Resource trade-off} \to \text{Constrained advisory recommendation}$.
- **Explicit Non-Claims:**
  - Prototype uses synthetic Baghewala-style data; it is NOT an actual Oil India telemetry replica.
  - Does NOT claim field-calibrated accuracy or measured Baghewala production improvements.
  - Does NOT implement autonomous field control; all recommendations are advisory with human operator sign-off.
  - Avoids full 3D reservoir PDE simulation or FEA rod-string dynamics in the 48-hr MVP; uses verified reduced-order physics models.
  - 3D visualization is strictly a presentation layer reflecting computed states; it is never the computational core.

### 3.2 Required Modules & Contracts
- `src/schema.py`: Single source of truth for Pydantic models (`WellState`, `Scenario`, `ScenarioResult`, `ConstraintCheck`, `Recommendation`, `Confidence`, `Diagnostic`). Units must be explicitly included in field names.
- `src/data_generator.py`: Reproducible synthetic data generation using seed `26120`; generates time series and scenario catalogue, writes CSVs, and seeds the database.
- `src/db/engine.py`: SQLAlchemy engine factory reading `DATABASE_URL` from `.env` (SQLite for prototype, Supabase/PostgreSQL ready).
- `src/db/repository.py`: Sole database access layer; provides typed read/write functions for all 14 tables.
- `src/db/adapter.py`: Unifying data interface reading from DB with CSV fallback; shields application from data source shifts.
- `src/state_estimator.py`: Reads latest telemetry rows; returns typed `WellState` + `DataQuality`. Fails safe on gaps, stale data, duplicates, or corrupted units.
- `src/css_model.py`: Reduced-order lumped thermal model simulating injection $\to$ soak $\to$ production phases; outputs temperature trajectory, heat balances, and physics residuals.
- `src/viscosity_model.py`: Heavy-oil viscosity function $\mu(T)$; enforces physical monotonicity ($\partial \mu / \partial T < 0$).
- `src/inflow_model.py`: Inflow and Productivity Index (PI) calculation based on effective mobility and pressure drawdown.
- `src/srp_model.py`: Quasi-dynamic SRP response; calculates capacity, fillage %, rod load (kN), energy (kWh/bbl), and dynamometer card feature points.
- `src/srp_diagnostics.py`: Rules-first diagnostic engine; fires rules `ROD_FLOATING`, `FLUID_POUND`, `ROD_LOADING`, `VALVE_INSPECT`, or `INSUFFICIENT_DATA` (never guesses on partial cards).
- `src/scenario_engine.py`: Grid evaluator running $\ge 50$ (typically 60) candidate combinations through the identical physics modules.
- `src/constraints.py`: Hard limit filtering before ranking; rejects invalid candidates with explicit rejection reasons.
- `src/optimizer.py`: Multi-objective ranker on feasible scenarios using customizable linear weights.
- `src/uncertainty.py`: Computes 4-component confidence composite (completeness, support, residual, extrapolation); downgrades or suppresses recommendations if uncertain.
- `src/validation.py`: Chronological split evaluation, physics monotonicity verification, and counterfactual simulation.
- `app.py`: Streamlit frontend with 6 tabs; strictly consumes backend services without embedded physics equations.

### 3.3 Canonical Equations (Single Source of Truth)
All physics equations are defined in `generate_synthetic.py`, `docs/TRD.md`, and `docs/PRD.md`:

1. **Thermal Dynamics (CSS):**
   $$\frac{dT}{dt} = \frac{Q_{in} - Q_{rad} - Q_{vert} - Q_{prod}}{C_{eff}}$$
   - Injection: $T_{phase} = 54 + 4.2 \cdot \left(\frac{t_{inj}}{t_{inj,max}}\right)$
   - Soak: $T_{phase} = 62.5 + 5.0 \cdot \left(\frac{t_{soak}}{t_{soak,max}}\right)$
   - Production: $T_{phase} = 67.5 - 0.115 \cdot (t - t_{inj} - t_{soak})$
   - Enthalpy gain: $\Delta T_{gain} = 0.065 \cdot \text{steam\_mass\_t} + 0.08 \cdot \text{soak\_hours}$
   - Scenario temperature: $T = 57.0 + 0.10 \cdot (\text{steam} - 90) + 0.055 \cdot (\text{soak} - 36)$
2. **Viscosity ($\mu$):**
   $$\mu(T) = \mu_{ref} \cdot \exp\big(-k \cdot (T - T_{ref})\big)$$
   With $\mu_{ref} = 13.0\text{--}13.2\text{ kcP}$ at $T_{ref} = 50^\circ\text{C}$, $k = 0.046\text{ }^\circ\text{C}^{-1}$, clipped to $[3.8, 15.5]\text{ kcP}$.
3. **Mobility \& Inflow:**
   $$\text{Mobility} = \frac{50}{\mu} \quad (\text{clipped to } [1.8, 15.0])$$
   $$\text{Inflow } (q) = 23.0 + 3.2 \cdot \text{mobility} + 0.68 \cdot (p_r - p_{wf}) = \text{PI} \cdot \Delta p$$
4. **SRP Capacity \& Fillage:**
   $$\text{Capacity} = 7.2 \cdot \text{SPM} \cdot \text{stroke\_length\_m}$$
   $$\text{Pump fillage \%} = \left(\frac{\text{inflow}}{\text{capacity}}\right) \cdot 100 \quad (\text{clipped to } [35, 98]\%)$$
5. **SRP Rod Load:**
   $$\text{Load (kN)} = 25 + 0.62 \cdot \mu + 2.7 \cdot \text{SPM} + 0.12 \cdot (100 - \text{fillage}) \quad (\text{clipped to } [28, 58]\text{ kN})$$
6. **Oil Production Rate:**
   $$\text{Oil Rate (bpd)} = \text{inflow} \cdot (0.64 + 0.0022 \cdot \text{fillage}) - 0.045 \cdot \text{srp\_load}$$
7. **Energy Proxy:**
   $$\text{Energy (kWh/bbl)} = 11.0 + 0.72 \cdot \text{SPM} + 0.10 \cdot \text{srp\_load} + 0.02 \cdot \text{steam\_mass\_t}$$
8. **SRP Risk Score:**
   $$\text{Risk (0--100)} = \text{clip}\big((\text{srp\_load} - 42) \cdot 2.0 + (58 - \text{fillage}) \cdot 0.45,\; 0,\; 100\big)$$
9. **Multi-Objective Score:**
   $$\text{Score} = w_{oil} \cdot \text{oil} - w_{steam} \cdot \text{steam} - w_{energy} \cdot \text{energy} - w_{risk} \cdot \text{risk}$$
   Default weights: $w_{oil} = 1.0, w_{steam} = 0.0, w_{energy} = 0.45, w_{risk} = 0.25$.

### 3.4 Database Structure (14 Tables Specified)
As dictated by `docs/DB.md` and `docs/BACKEND.md`:
1. `wells` — Identity, field label, status, provenance.
2. `reservoir_properties` — $k, h, \phi, S, r_e, r_w, P_{init}, T_{init}$; status labels.
3. `fluid_properties` — $\mu_{ref}, T_{ref}, k, B$; status `UNCALIBRATED`.
4. `css_cycles` — Cycle number, steam mass, steam pressure, phase durations.
5. `time_series_observations` — Hourly telemetry rows (pressures, temperature, viscosity, inflow, rates, SPM, stroke, fillage, load, energy, risk, data quality, provenance).
6. `operating_limits` — Hard constraints (`min_fillage_pct` = 52%, `max_srp_load_kn` = 62 kN, `max_steam_mass_t` = 118 t).
7. `assumptions` — Assumption register from `ASSUMPTIONS.md`.
8. `model_weights` — Editable ranking objective weights.
9. `model_runs` — Metadata per simulation invocation.
10. `scenarios` — Generated candidate scenarios with calculated physics outputs and feasibility flags.
11. `recommendations` — Selected recommendation, engineering justification, confidence, operator status (`PENDING`, `APPROVED`, etc.).
12. `audit_log` — Immutable operator actions and timestamps.
13. `diagnostics_events` — SRP diagnostic alerts with rule evidence.
14. `validation_results` — Temporal backtest and monotonicity test metrics.

### 3.5 UI Requirements
- Persistent top banner: `"PROTOTYPE MODE — REPRESENTATIVE SYNTHETIC DATA"`.
- Sidebar: Well selector (`BWG-SIM-001`), phase status, data quality badge.
- Tab 1 (Current State): 8 KPI metric cards with units, phase timeline ribbon, provenance footer.
- Tab 2 (What-If Simulator): Sliders for steam mass, soak hours, SPM, stroke; Simulate button; dual-axis $T$ vs $\mu$ plot; trade-off scatter plot; scenario comparison table with rejection reasons; live weight re-ranking sliders.
- Tab 3 (Recommendation Card): Plain-language engineering rationale; constraint margins; uncertainty breakdown; operator action buttons (Approve / Modify / Reject / Annotate).
- Tab 4 (SRP Diagnostics): Dynamometer card (load vs position); active diagnostic rules feed with fired condition details.
- Tab 5 (Validation): Chronological cycle splits (1–2 train, 3 val, 4 test); monotonicity check badges; counterfactual replay.
- Tab 6 (3D Well Layer): Plotly 3D visual representation reflecting computed states.

### 3.6 Testing Requirements
- `test_causality.py`: Validates physical monotonicity ($T \uparrow \implies \mu \downarrow \implies \text{inflow} \uparrow$; $\text{inflow} \uparrow \implies \text{fillage}$/load; $\text{SPM} \uparrow \implies \text{energy} \uparrow$).
- `test_constraints.py`: Confirms rejection of out-of-envelope scenarios (load $> 62$ kN, fillage $< 52\%$, steam $> 118$ t) with exact reason strings.
- `test_reproducibility.py`: Confirms seed 26120 regenerates exact matching dataset.
- `test_validation_splits.py`: Enforces strict chronological ordering without data leakage.

### 3.7 Provenance Rules
- Every data point and database record must carry `source_label` (`SYNTHETIC`, `ENGINEERING`, `LITERATURE`, or `OIL_PUBLISHED`), `random_seed` (`26120`), and `model_version`.
- Any parameter that could be mistaken for an actual field operating limit must be tagged with its status:
  - `OIL_PUBLISHED`: Public context (e.g. Jodhpur Sandstone, ~10,000–13,000 cP at 50 °C).
  - `LITERATURE`: Scientific process descriptions (e.g. CSS phase progression).
  - `ENGINEERING`: Structural assumptions (e.g. lumped heat capacity equation, analytical PI proxy).
  - `SYNTHETIC`: Uncalibrated model choices (e.g. well ID `BWG-SIM-001`, numerical bounds, hourly noise).
- Promotion rule: No synthetic value may be used as a field operational limit without an authorized source, documented units, well/structure association, validated uncertainty, and operator approval.

### 3.8 Synthetic-Data Rules
- Random seed strictly fixed at `26120` (`np.random.default_rng(26120)`).
- Manual editing or tweaking of CSV values is strictly forbidden.
- 4 cycles $\times$ 28 days = 2,688 hourly records.
- Chronological train/val/test splits only; no random shuffling.
- Data quality states: `GOOD`, `SUSPECT`, `FAIL`. Fail-safe suppression of recommendations on low-quality data.

---

## 4. Conflict & Duplicate Resolution

| Conflicting Items Found | Analysis & Findings | Final Source of Truth |
|---|---|---|
| `BACKEND (1).md` vs `BACKEND.md` | `Downloads\BACKEND.md` belongs to an unrelated Node/Express restaurant ordering project. `BACKEND (1).md` in `SIH PRO` contains the authentic THERMOLIFT architecture and module contracts. | `docs/BACKEND.md` (copied from `BACKEND (1).md`). Original root file preserved. |
| `FRONTEND (1).md` vs `FRONTEND.md` | `Downloads\FRONTEND.md` belongs to the restaurant ordering project. `FRONTEND (1).md` contains the 6-tab Streamlit specification for THERMOLIFT. | `docs/FRONTEND.md` (copied from `FRONTEND (1).md`). Original root file preserved. |
| `TRD (2).md` vs `TRD (1).md` vs `TRD.md` | `TRD.md` belongs to `ClientLens`. `TRD (1).md` belongs to restaurant ordering. `TRD (2).md` is the authentic THERMOLIFT technical requirements document. | `docs/TRD.md` (copied from `TRD (2).md`). Original root file preserved. |
| `FLOW (2).md` vs `FLOW (1).md` vs `FLOW.md` | `FLOW.md` belongs to `ClientLens`. `FLOW (1).md` belongs to restaurant ordering. `FLOW (2).md` is the authentic THERMOLIFT runtime and data flows document. | `docs/FLOW.md` (copied from `FLOW (2).md`). Original root file preserved. |
| `MaruDhara _ THERMOLIFT.md` vs `MARUDHARA_THERMOLIFT_TECHNICAL_MVP_REPORT.md` | Both files are identical in text (35.5 kB). `MaruDhara _ THERMOLIFT.md` used temporary cloud image links; `MARUDHARA_THERMOLIFT_TECHNICAL_MVP_REPORT.md` inside `MARUDHARA_MVP_HANDOFF` uses local image paths. | `docs/PRD.md` (copied from `MARUDHARA_THERMOLIFT_TECHNICAL_MVP_REPORT.md`). |

---

## 5. Final Source-of-Truth Set

The established, authoritative source-of-truth set for the THERMOLIFT prototype is:

1. **System & Requirements Documentation:**
   - `docs/PRD.md` — Product scope, non-negotiable boundaries, and feature plan.
   - `docs/TRD.md` — Module contracts, canonical equations, and testing standards.
   - `docs/FLOW.md` — Runtime workflows, boot sequence, and diagnostic rules.
   - `docs/DB.md` — Database design, connection strategies, and table list.
   - `docs/BACKEND.md` — Implementation architecture, pure-function rules, and signatures.
   - `docs/FRONTEND.md` — Streamlit UI design, layout, charts, and styling guidelines.
   - `ASSUMPTIONS.md` — Authoritative parameter assumptions register and provenance rules.
2. **Causal Data Generation & Benchmark:**
   - `generate_synthetic.py` — Canonical mathematical logic and generator code (seed 26120).
   - `data/synthetic_well.csv` — Authentic 2,688-hour benchmark dataset.
   - `data/scenario_catalogue.csv` — 60-scenario benchmark grid.
   - `data/current_state.json` — Starting operational state for decision replay.
   - `data/validation_split.json` — Official chronological train/val/test splits.

---

## 6. Final Readiness Status

### **NOT READY**

**Blocking Issues:**
1. `db/schema.sql` is **BLOCKED / MISSING**: Although the 14 tables and design are comprehensively specified in `docs/DB.md` and `docs/BACKEND.md`, the physical DDL file `db/schema.sql` does not exist anywhere in the provided materials. Per Audit Item 9, `db/schema.sql` must be present and readable before database implementation begins.
2. `requirements.txt` is **MISSING**: Needs to be authored based on the audited module requirements (Streamlit, Plotly, Pandas, NumPy, SQLAlchemy, Pydantic, Pytest, PyYAML).
3. `.env` is **MISSING**: Needs to be authored with `DATABASE_URL=sqlite:///data/thermolift.db`.
4. `README.md` is **MISSING**: Needs to be authored with setup, run, and audit instructions.

**Action Required Prior to Implementation:**
Before implementing database repositories or application logic, `db/schema.sql` must be created strictly according to the 14 table contracts defined in `docs/DB.md`, along with `requirements.txt` and `.env`. No engineering data or operating limits may be invented outside of `ASSUMPTIONS.md` and `docs/TRD.md`.
