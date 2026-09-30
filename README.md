# THERMOLIFT / MaruDhara (SIH26120)

**Physics-Informed Well-to-Surface Decision Twin for Coupled CSS + SRP Operations in a Baghewala-Style Heavy-Oil Well**

*Smart India Hackathon 2026 • Problem Statement SIH26120 • Oil India Limited • Smart Automation*

---

> **PROTOTYPE MODE — REPRESENTATIVE SYNTHETIC DATA**  
> This prototype uses representative Baghewala-style synthetic data (fixed seed `26120`). It is not an Oil India telemetry replica, a field-calibrated model, or an autonomous control system. All recommendations are advisory and require operator sign-off.

---

## 1. Project Overview & Core Question

THERMOLIFT is a single-well decision-support digital twin answering one fundamental operational question:

> **"What happens to the entire well-to-surface system if CSS and/or SRP operating conditions change?"**

### The Coupled Causal Chain
```text
Steam Injection (90–122 t)
    └──> Reservoir Thermal Response (dT/dt lumped balance)
          └──> Heated Temperature (°C)
                └──> Heavy-Oil Viscosity Reduction (μ(T) exponential correlation)
                      └──> Fluid Mobility & Inflow Rate (PI * Δp)
                            └──> SRP Sucker Rod Pump Fillage & Load Response
                                  └──> Net Oil Production & Energy Trade-off
                                        └──> Configurable Constraints Screening
                                              └──> Advisory Recommendation & Audit Trail
```

---

## 2. Project Architecture & Directory Structure

```text
thermolift/
├── app.py                      # Streamlit 6-Tab Decision Twin Interface
├── .env                        # DATABASE_URL=sqlite:///data/thermolift.db
├── requirements.txt            # Python dependencies
├── README.md                   # Setup and execution guide
├── ASSUMPTIONS.md              # 30-parameter prototype assumption register
├── generate_synthetic.py       # Standalone reference generator script
├── MATERIAL_AUDIT.md           # Formal project-materials audit report
├── db/
│   ├── schema.sql              # PostgreSQL / Supabase / SQLite 14-table DDL
│   └── thermolift.db           # SQLite database (prototype)
├── data/
│   ├── synthetic_well.csv      # 2,688-hour benchmark telemetry (4 cycles × 28 days)
│   ├── scenario_catalogue.csv  # 60 pre-evaluated scenario combinations
│   ├── current_state.json      # Current well state snapshot
│   └── validation_split.json   # Chronological train/val/test split definition
├── config/
│   └── operating_limits.yaml   # Configurable prototype operational limits
├── src/
│   ├── schema.py               # Single source of truth for Pydantic contracts
│   ├── data_generator.py       # Seed 26120 generator; writes CSVs & seeds DB
│   ├── db/
│   │   ├── engine.py           # SQLAlchemy engine factory
│   │   ├── models.py           # Declarative ORM models for all 14 tables
│   │   ├── repository.py       # SOLE database access layer (typed read/write)
│   │   └── adapter.py          # Unified data interface with CSV fallback
│   ├── state_estimator.py      # Telemetry quality validation & WellState assembly
│   ├── css_model.py            # Lumped first-order thermal balance (dT/dt)
│   ├── viscosity_model.py      # Exponential viscosity correlation with monotonicity
│   ├── inflow_model.py         # Analytical PI and mobility inflow calculation
│   ├── srp_model.py            # Quasi-dynamic SRP response & dynamometer card
│   ├── srp_diagnostics.py      # Rules-first diagnostics (ROD_FLOATING, FLUID_POUND, etc.)
│   ├── scenario_engine.py      # 60-grid + custom point physics evaluator
│   ├── constraints.py          # Hard limits filter (fillage, load, steam envelope)
│   ├── optimizer.py            # Multi-objective weighted ranker & engineering rationale
│   ├── uncertainty.py          # 4-component illustrative confidence evaluation
│   └── validation.py           # Temporal backtest, physics checks, counterfactuals
├── tests/
│   ├── test_causality.py       # T↑ => μ↓ => inflow↑, fillage/load, SPM↑ => energy↑
│   ├── test_constraints.py     # Hard limits rejection with exact reasons
│   ├── test_reproducibility.py # Bit-identical CSV reproduction with seed 26120
│   └── test_validation_splits.py # Zero temporal leakage verification
└── docs/
    ├── PRD.md                  # Product Requirements Document
    ├── TRD.md                  # Technical Requirements & Design
    ├── FLOW.md                 # Runtime & Boot Data Flows
    ├── DB.md                   # Database Strategy & 14-Table Specification
    ├── BACKEND.md              # Backend Architecture & Pure-Function Contracts
    └── FRONTEND.md             # Streamlit UI 6-Tab Specification
```

---

## 3. Quick Start & Execution

### Prerequisites
- Python 3.10+ (tested on Python 3.13)
- Virtual environment recommended

### Installation
```bash
pip install -r requirements.txt
```

### Seed Database & Generate Synthetic Benchmark
```bash
python src/data_generator.py
```
*Output: 2,688 hourly records and 60 scenario candidates generated in `data/`, and all 14 tables initialized in `data/thermolift.db`.*

### Run Automated Pytest Suite
```bash
python -m pytest tests -v
```
*All 8 tests across causality, constraints, reproducibility, and temporal splits will pass.*

### Launch Streamlit Decision Twin
```bash
streamlit run app.py
```

---

## 4. UI Walkthrough (10 Industrial Tabs)

1. **Current State:**
   - 10 KPI metric cards with explicit units (Temperature, Viscosity, Reservoir/BHP, Inflow, Oil Rate, Fillage, SRP Load, Energy, Risk Score, CSS Phase).
   - Dynamic cycle telemetry chart with dual-axis overlay.
   - **Actionable Uncertainty Gate Badge:** Visualizing `GREEN` (Advisory Active), `AMBER` (Operator Caution), and `RED` (Recommendation Suppressed).
   - **Nodal Pressure Chain Profile:** Hydraulic gradient from $P_{res} \to P_{wf} \to PIP \to WHP \to Flowline \to P_{sep}$.
   - Complete data provenance: `source_label`, `random_seed`, `model_version`, and collision-resistant `input_state_hash`.

2. **What-If Simulator (Core Engine):**
   - Interactive sliders for steam mass (90–122 t), soak (36–72 h), SPM (6–8), and stroke (1.45–1.65 m).
   - Editable normalized multi-objective weights (`w_oil`, `w_steam`, `w_energy`, `w_risk`, `w_maint`).
   - "Run 61-Scenario Simulation" evaluates 61 candidates in `< 0.2s` using the identical coupled physics chain.
   - Energy vs. Oil trade-off scatter plot with feasible/rejected indicators and top candidate highlight.
   - Dual-axis Temperature vs. Viscosity trajectory with injection/soak/production phase bands.
   - Full scenario comparison table displaying exact rejection reasons and signed constraint margins.

3. **Recommendation Card:**
   - Advisory decision card displaying recommended scenario setpoints and composite score.
   - **Signed Constraint Margins:** Fillage margin ($\ge 52\%$), Rod load margin ($\le 62\text{ kN}$), Steam envelope margin ($\le 118\text{ t}$), and Surface WHP margin ($\le 14\text{ bar}$).
   - **Nearest-Alternative Feasible Trade-Off:** Side-by-side parameter and KPI delta comparison against the closest materially distinct feasible candidate.
   - Operator Action Buttons (**Approve**, **Modify**, **Reject**, **Annotate**) writing immutable audit records.

4. **SRP Diagnostics:**
   - Polished rod dynamometer card (Load vs. Position plot).
   - Extracted card features: Max (PPRL), Min (MPRL), Load Range, Mean Load, Card Area (Work), and Repeatability %.
   - Active diagnostic rules feed: `ROD_FLOATING`, `FLUID_POUND`, `ROD_LOADING`, `VALVE_INSPECT`, and `INSUFFICIENT_DATA`.

5. **Coupling Lab (Independent vs. Coupled Ablation):**
   - Controlled ablation experiment comparing Mode A (Sequential/Independent) vs. Mode B (Coupled).
   - Detailed side-by-side comparison across 15+ KPIs and calculated deltas ($\Delta$ Oil, $\Delta$ SOR, $\Delta$ Fillage, $\Delta$ Load, $\Delta$ Violations).
   - Neutral engineering causal explanation card.

6. **Thermal Target (Minimum Steam Solver):**
   - Solves: *"What is the minimum steam intervention required to achieve the heated viscosity or temperature that renders downstream SRP production mechanically viable?"*
   - Configurable target mode (Viscosity in kcP or Temperature in °C) with anticipated SRP pump speed.
   - Downstream mechanical feasibility check ensuring $\ge 52\%$ pump fillage and $\le 62\text{ kN}$ rod load.

7. **Time Machine (Historical Counterfactual Replay):**
   - Replays frozen historical cycles (1–4) under alternative operational decisions without lookahead data leakage.
   - Mandatory label: `"MODEL-BASED COUNTERFACTUAL REPLAY — NOT A MEASURED FIELD RESULT"`.
   - Visual trajectory comparison: Actual measured field telemetry vs. model-based counterfactual simulation.

8. **Sensitivity & Pareto:**
   - **Ranked Sensitivity Tornado Chart:** One-At-A-Time (OAT) parameter swings ($\pm 10\%, \pm 20\%$) across steam, soak, SPM, stroke, and reservoir pressure.
   - **True Multi-Objective Pareto Frontier:** Axiomatic nondominated sorting across Oil, Steam, Energy, and Risk.

9. **Validation & ML Residuals:**
   - Chronological backtesting metrics (Cycles 1–2 train, Cycle 3 val, Cycle 4 test holdout) with MAE and RMSE.
   - Physics monotonicity check badges verifying $dT/d\mu < 0$ and $d(\text{inflow})/d\mu < 0$.
   - **Explainable Ridge Residual ML:** Hybrid $T_{hybrid} = T_{physics} + \Delta T$ with L2-regularized bounded corrections ($\pm 4.0^\circ\text{C}$).
   - **Field Data Ingestion Contract:** Specification for telemetry ingestion from Oil India Limited assets (`docs/FIELD_DATA_CONTRACT.md`).

10. **Photorealistic 3D Model:**
    - Real-time Three.js physical digital twin featuring animated 4-bar crank-beam linkage, reciprocating polished rod, stuffing box, subsurface stratigraphic cutaway, and glowing heated reservoir.
    - Component inspector: click any mechanical component or telemetry pin to inspect technical parameters.

---

## 5. Running the Application & Automated Tests

### Run Automated Pytest Suite
```bash
python -m pytest tests -v
```
*(All 28 test suites covering physics causality, constraints, objective function, ablation, provenance, pressure chain, thermal targets, uncertainty gate, sensitivity, Pareto, and validation pass 100%).*

### Launch Streamlit Decision Twin
```bash
streamlit run app.py
```

---

## 6. Non-Negotiable Boundaries

- **Prototype Mode:** Uses representative Baghewala-style synthetic data (seed `26120`). Never claim autonomous control or unverified field calibration.
- **Single Authoritative Physics Path (`v2.0`):** All modules route through canonical physics functions in `src/css_model.py`, `src/viscosity_model.py`, `src/inflow_model.py`, and `src/srp_model.py`.
- **Pure Functions:** Physics modules never import Streamlit or Plotly.
- **Traceable Provenance:** Every scenario and candidate bears an SHA-256 `input_state_hash`, `model_version`, and `source_label`.
