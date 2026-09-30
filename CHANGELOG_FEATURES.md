# CHANGELOG: THERMOLIFT / MaruDhara Feature Upgrade (v2.0)

## Overview
This document records the master architectural and scientific feature upgrades implemented for the THERMOLIFT / MaruDhara (SIH26120) prototype, upgrading it from an initial baseline into a defensible, traceable, experiment-oriented coupled CSS+SRP decision twin.

---

### [v2.0] — Coupled Twin Physics, Provenance, Ablation & Analytical Upgrade

#### P0: Core Coupled Twin Integrity & Traceability
- **Coupled-vs-Independent Ablation Engine (`src/ablation.py`):**
  - Implemented Mode A (Independent/Sequential: optimize CSS based purely on inflow merit, freeze reservoir state, then optimize SRP) vs. Mode B (Coupled: joint simultaneous optimization).
  - Both modes run on identical physics equations, candidate search spaces, and multi-objective weights.
  - Automatically extracts 15+ KPIs, computed deltas ($\Delta$ Oil, $\Delta$ SOR, $\Delta$ Fillage, $\Delta$ Load, $\Delta$ Score, $\Delta$ Violations), and neutral physical causal explanations.
- **Canonical Transparent Normalized Multi-Objective (`src/objective.py`):**
  - Enforced deterministic Min-Max normalization within physical and prototype domain boundaries:
    $$\text{Score} = w_{oil} \tilde{y}_{oil} - w_{steam} \tilde{y}_{steam} - w_{energy} \tilde{y}_{energy} - w_{risk} \tilde{y}_{risk} - w_{maint} \tilde{y}_{maint}$$
  - Configurable non-zero default steam penalty ($w_{steam} = 0.35$).
  - Safe zero-denominator guards preventing numerical division by zero.
  - Generates detailed `ObjectiveBreakdown` with signed contributions for full operator transparency.
- **Candidate Provenance & Deterministic State Hash (`src/provenance.py`):**
  - Generates a collision-resistant 16-character SHA-256 state hash covering well ID, reservoir conditions, CSS/SRP setpoints, seed (26120), and model version (`v2.0`).
  - Added `input_state_hash`, `model_version`, `assumption_set`, and `source_label` columns to the database schema.
- **Signed Constraint Margins (`src/constraints.py`):**
  - Implemented signed margin calculations:
    - Pump fillage margin: $\text{actual} - \text{threshold}$ (positive = safe buffer above min 52%).
    - Rod load margin: $\text{threshold} - \text{actual}$ (positive = safe buffer below max 62 kN).
    - Steam envelope margin: $\text{threshold} - \text{actual}$ (positive = safe buffer below max 118 t).
    - Surface WHP margin: $\text{threshold} - \text{actual}$ (positive = safe buffer below max 14 bar).
  - Transparently formatted in candidate rejection logs and recommendation cards.
- **Database Schema Migration (`db/schema.sql`, `src/db/repository.py`):**
  - Migrated SQLite database `data/thermolift.db` to v2.0 schema using non-destructive `ALTER TABLE` checks.
  - Added new audit tables: `ablation_experiments` and `pressure_chain_runs`.

#### P1: Actionable Operations & Engineering Usability
- **Actionable Uncertainty Gate (`src/uncertainty.py`):**
  - Upgraded confidence evaluator with an explicit three-state operational gate:
    - `GREEN`: Data quality GOOD, residual $\le 2.5^\circ\text{C}$, confidence $\ge 70\%$. Advisory fully active.
    - `AMBER`: Data quality SUSPECT or residual in $(2.5^\circ\text{C}, 4.5^\circ\text{C}]$. Operator warning badge displayed.
    - `RED`: Data quality FAIL or residual $> 4.5^\circ\text{C}$. Advisory suppressed (`recommendation_suppressed = True`).
- **Minimum-Necessary-Steam Target Solver (`src/thermal_target.py`):**
  - Solves: *"What is the least steam intervention required to achieve the heated viscosity or temperature that renders downstream SRP production mechanically viable?"*
  - Discrete step scan over allowable steam range enforcing downstream fillage ($\ge 52\%$) and rod load ($\le 62\text{ kN}$) constraints.
- **Wellbore-to-Surface Nodal Pressure Chain (`src/pressure_chain.py`):**
  - Evaluates hydraulic gradient: $P_{res} \to P_{wf} \to PIP \to WHP \to Flowline \to P_{sep}$.
  - Viscosity-dependent flowline and choke frictional pressure loss modelling.
  - Rejects scenarios that exceed surface working pressure limits ($WHP > 14\text{ bar}$) or separator liquid capacity ($> 65\text{ bpd}$).
- **Nearest-Alternative Comparison (`src/nearest_alternative.py`):**
  - Computes normalized Euclidean decision-space distance across steam, soak, SPM, and stroke length.
  - Identifies the closest materially distinct feasible candidate to the top recommendation and generates a clear engineering trade-off comparison.
- **Counterfactual Time Machine (`src/counterfactual.py`):**
  - Replays frozen historical cycle states under alternative operational setpoints without future data leakage.
  - Mandatory label: `"MODEL-BASED COUNTERFACTUAL REPLAY — NOT A MEASURED FIELD RESULT"`.

#### P2: Advanced Scientific Extensions & Field Readiness
- **Deterministic Sensitivity Analysis (`src/sensitivity.py`):**
  - One-At-A-Time (OAT) parameter perturbations ($\pm 10\%, \pm 20\%$) across steam mass, soak duration, pump speed, stroke length, and reservoir pressure.
  - Computes percentage swings in oil, SOR, fillage, load, energy, and maintenance risk to render ranked tornado charts.
- **True Multi-Objective Pareto Frontier (`src/pareto.py`):**
  - Axiomatic nondominated sorting across 4 objectives: maximize oil, minimize steam, minimize energy, minimize mechanical risk.
  - Identifies exact Pareto frontier candidates versus dominated candidates.
- **Explainable Physics + Residual ML (`src/residual_ml.py`):**
  - Bounded Ridge regression ($\alpha = 5.0$) on top of analytical CSS thermodynamics:
    $$T_{hybrid} = T_{physics} + \Delta T, \quad \Delta T \in [-4.0^\circ\text{C}, +4.0^\circ\text{C}]$$
  - Clean fallback to pure physics when uncalibrated.
- **Field Data Ingestion Contract (`docs/FIELD_DATA_CONTRACT.md`):**
  - Comprehensive specification for telemetry ingestion across 5 channels (surface SRP skid, steam skid, downhole PDG/DTS, test separator, fluid PVT).

#### Test Suite Expansion
- 28 automated Pytest test suites passing 100%:
  - `test_ablation.py`: CSS-to-SRP causal propagation and ablation comparison contracts.
  - `test_advanced_analytics.py`: Sensitivity OAT perturbations, nearest-alternative discovery, and Ridge residual bounds.
  - `test_objective.py`: Normalized score calculation, contribution sum identity, and zero-denominator stability.
  - `test_pareto.py`: Dominance axioms and non-dominated sorting accuracy.
  - `test_pressure_chain.py`: Nodal monotonicity and surface constraint rejection.
  - `test_provenance.py`: Deterministic state hash stability and input perturbation sensitivity.
  - `test_thermal_target.py`: Minimum steam discovery and limiting constraint binding.
  - `test_uncertainty_gate.py`: GREEN/AMBER/RED transitions and recommendation suppression.
  - Baseline tests (`test_causality.py`, `test_constraints.py`, `test_reproducibility.py`, `test_validation_splits.py`).
