# MaruDhara / THERMOLIFT
## Technical MVP Building Report for SIH26120

**Physics-Informed Well-to-Surface Decision Twin for CSS + SRP Operations in a Baghewala-Style Heavy-Oil Well**

**Version:** 1.0 · **Status:** MVP build specification · **Prepared for:** Team InnoVerse · **Project identity:** THERMOLIFT presents MaruDhara

> **Prototype status:** The MVP uses a representative Baghewala-style synthetic well. It is not an Oil India telemetry replica, a calibrated field model, an autonomous control system, or evidence of actual Baghewala production improvement.

---

## 1. The project we are building

THERMOLIFT should not be implemented as a generic AI dashboard. The MVP is a functional, single-well decision-support system that answers one operational question:

> **What happens to the entire well-to-surface system if CSS and/or SRP operating conditions change?**

The system maintains a current well state, runs a reduced-order thermal model, converts temperature into viscosity and mobility, propagates the result into inflow and sucker rod pump (SRP) response, generates alternative CSS–SRP scenarios, rejects unsupported scenarios, ranks feasible options, and explains one advisory recommendation to an operator.

The core causal chain is:

```text
steam injection
    → reservoir thermal response
    → temperature
    → heavy-oil viscosity
    → mobility / inflow
    → SRP fillage and load
    → achievable production
    → resource and equipment trade-off
    → constrained advisory recommendation
```

This chain is the product. The 3D visualization is the presentation layer that makes the state visible; it must not be the computational core.

Oil India describes Baghewala as a Rajasthan heavy-oil field producing from Jodhpur Sandstone. Public Oil India material identifies cyclic steam stimulation (CSS) as the thermal recovery method and SRP as the artificial-lift method used for the viscous crude.[1] Oil India reports a public field-level viscosity range of approximately 10,000–13,000 cP at 50 °C.[1] These facts establish context. They do not provide the complete well-by-well telemetry, pump geometry, approved operating envelope, or calibration data required for a field-operational model.

---

## 2. Product boundaries and non-negotiable data policy

### 2.1 What the MVP does

The MVP demonstrates one representative well, one state-estimation pipeline, one CSS thermal cycle, one temperature–viscosity–inflow chain, one quasi-dynamic SRP response, a scenario engine, hard constraints, transparent ranking, uncertainty/data-quality gating, and visible validation.

The MVP can run with a local CSV and SQLite. The code must keep the physics modules separate from the interface so the synthetic source can later be replaced by authorised Oil India data without rewriting the application.

### 2.2 What the MVP does not claim

The MVP does not claim:

- actual Oil India telemetry or Baghewala well measurements;
- actual well-level production uplift;
- actual field operating limits or safe steam pressures;
- actual failure frequencies or SRP fault probabilities;
- Oil India calibration or field accuracy;
- autonomous field control;
- a full high-fidelity reservoir simulator;
- a full rod-string finite-element model for every well geometry;
- that synthetic validation metrics transfer to field performance.

Every UI page should display:

> **PROTOTYPE MODE — REPRESENTATIVE SYNTHETIC DATA**

Every generated value should carry provenance fields such as `source_label`, `random_seed`, `model_version`, `assumption_set`, and `timestamp`.

---

## 3. MVP definition of done

A reviewer should be able to start the application and demonstrate the following sequence:

1. A representative synthetic well loads.
2. The current temperature, viscosity, inflow, oil rate, pump fillage and SRP load are displayed.
3. CSS and SRP parameters can be changed.
4. The user presses **Simulate**.
5. The system calculates the CSS thermal response through injection, soak and production/cooling.
6. Temperature changes viscosity.
7. Viscosity changes mobility and inflow.
8. Inflow changes SRP load and pump fillage.
9. At least 50 candidate scenarios are generated.
10. Invalid scenarios are filtered using explicit hard constraints.
11. Feasible scenarios are ranked using a transparent objective.
12. One scenario is recommended.
13. The system explains why it was recommended.
14. Confidence, data quality and model-support range are visible.
15. Temporal, physics-consistency and counterfactual validation views are visible.
16. Synthetic and assumption labels are visible at every relevant result.

The current fixed-seed generator creates **2,688 hourly well-state rows across four 28-day synthetic CSS cycles** and **60 CSS–SRP candidate scenarios**. The catalogue currently produces 32 feasible and 28 rejected candidates using configurable prototype thresholds. These are reproducible demonstration outputs, not field results.

---

## 4. Feature-to-implementation plan

Each feature below has a clear job, implementation path, output, validation check and boundary.

### Feature 1 — Provenance-aware synthetic well generator

**Purpose.** Provide a reproducible dataset before field telemetry is available.

**Inputs.** Fixed random seed, cycle parameters, synthetic thermal parameters, synthetic pressure and production baselines, pump settings, noise level, missingness level and event-injection settings.

**Implementation.** Use a Python generator with NumPy and Pandas. Generate the data in causal order rather than sampling each column independently:

```text
CSS control
  → thermal state
  → viscosity
  → mobility / inflow
  → SRP fillage / load / energy
  → oil rate and risk
```

Use `SEED = 26120` for the demonstration dataset. Create a phase label for every row: `injection`, `soak` or `production`. Add controlled sensor noise and preserve the noiseless latent state when validation requires it.

**Output.** `synthetic_well.csv`, `current_state.json`, `validation_split.json`, and `scenario_catalogue.csv`.

**Validation.** Confirm reproducibility from the same seed. Confirm that higher thermal input raises temperature, higher temperature lowers viscosity, lower viscosity raises mobility, and inflow affects pump fillage and load.

**Boundary.** Synthetic ranges are engineering test scenarios. They are not Baghewala limits.

### Feature 2 — Current well state

**Purpose.** Convert the latest accepted observations into a small state object that every downstream model consumes.

**State variables.**

```text
well_id
cycle_id and phase
reservoir pressure
bottomhole pressure
reservoir / near-well temperature
viscosity
inflow
oil and water rate
steam mass and injection pressure
pump speed and stroke
pump fillage
SRP load and energy proxy
risk score
data quality
model support range
```

**Implementation.** A `state_estimator.py` module should:

1. parse timestamps and units;
2. check missingness and stale values;
3. apply only training-window-fitted transformations;
4. retain the latest valid state;
5. emit a `data_quality` object and a list of rejected fields;
6. fail safely when the state is incomplete.

**Output.** A typed `WellState` object. The UI renders the same object in the current-state panel, the 3D layer and the recommendation audit trail.

**Validation.** Unit tests for missing fields, duplicated timestamps, invalid units, stale signals and out-of-support temperatures.

### Feature 3 — Reduced-order CSS thermal model

**Purpose.** Represent the thermal mechanism quickly enough to run many what-if scenarios while keeping assumptions visible.

Oil India describes the CSS workflow as steam injection, soak and production, followed by repeated cycles while economic.[1] A peer-reviewed CSS model represents steam, hot-water and cold zones, derives heating behaviour from energy conservation, and couples thermal conditions to flow properties.[2] A separate mathematical study reports diminishing heat-transfer rate during soak and rapid early near-wellbore temperature decline during production.[3]

**MVP implementation.** Use a phase state machine and a lumped energy balance. For each thermal zone `z`:

```text
dT_z/dt = (Q_in,z - Q_rad,z - Q_vertical,z - Q_produced,z) / C_eff,z
```

This equation is an engineering reduction of published energy-balance formulations, not a verbatim claim that the papers use this exact ODE. It is appropriate for an MVP because it is fast, auditable and easy to calibrate later.

During injection:

```text
Q_in ≈ m_steam × η_heat × [h_steam(T_in, p_in) − h_cond(T_z)]
```

During soak, set planned injection and production enthalpy terms to zero and apply radial and vertical loss terms. During production, subtract produced-fluid enthalpy and apply a faster early cooling term followed by slower conduction-dominated decline.

Track at minimum:

```text
phase_clock
T_steam, T_hot, T_cold
R_steam, R_hot or an equivalent heating-volume proxy
cumulative steam mass
heat-loss conductances
C_eff
injection efficiency
produced-fluid enthalpy
```

Use IAPWS-backed steam/water properties only where the implementation actually needs steam enthalpy. Keep a simple fallback for the synthetic demo and mark the fallback as an engineering approximation.

**Output.** Temperature trajectory, phase transitions, thermal state after the cycle, heat-loss explanation and a physics residual.

**Validation.** Phase order must be correct. Temperature must rise or hold during effective injection, decline during soak, and decline during production unless a new heat input is applied. The model must never produce negative heat capacity or impossible temperatures.

**Boundary.** This is not a transient multiphase reservoir simulator. It omits detailed heterogeneity, fracture growth, gravity override, phase-change kinetics and complete wellbore heat transfer.

### Feature 4 — Temperature-to-viscosity model

**Purpose.** Make the most important heavy-oil mechanism visible instead of hiding it inside a black-box production score.

Heavy-oil viscosity can vary substantially during thermal production and is a major recovery impediment.[4] Oil India’s public viscosity values are field-level context; they do not define a complete Baghewala rheology curve.[1]

**MVP implementation.** Use a configurable Arrhenius-like or exponential correlation:

```text
μ(T) = μ_ref × exp[β × (1/T − 1/T_ref)]
```

For the Arrhenius form, use absolute temperature in Kelvin. A simpler Celsius-domain expression may be used for the visual demo:

```text
μ(T) = μ_ref × exp[−k × (T − T_ref)]
```

The coefficient must be stored in `config/operating_limits.yaml` or a dedicated model config and labelled **synthetic / uncalibrated** until measured PVT or rheology data are available.

**Output.** Viscosity curve, current viscosity, change from baseline, extrapolation flag and uncertainty band.

**Validation.** A monotonicity test must pass over the supported temperature range: temperature increase must not increase viscosity in the normal operating regime.

**Boundary.** The simple model omits pressure dependence, shear-rate effects, water, gas, wax, asphaltene, composition and non-Newtonian behaviour.

### Feature 5 — Viscosity-to-inflow model

**Purpose.** Avoid an unjustified direct `steam → oil rate` mapping.

For a simple single-phase radial-flow proxy, productivity index can be written as:

```text
PI = 0.00708 × (k h / (μ B))
     / [ln(re / rw) − 0.75 + S]

q = PI × (p_r − p_wf)
```

The Kansas Geological Survey documents this productivity-index form and its units.[5] The relationship is useful because viscosity enters explicitly as a resistance term. At fixed geometry, permeability, thickness, formation-volume factor, skin and drawdown, lower viscosity raises PI approximately in proportion to `1/μ`.

**Implementation.** Use a `ProductivityConfig` with explicit fields for `k`, `h`, `B`, `re`, `rw`, `S`, reservoir pressure and flowing pressure. Keep the values configurable and mark them as synthetic unless authorised asset data are supplied.

**Output.** PI, inflow rate, drawdown, mobility, sensitivity to viscosity and input-support status.

**Validation.** Hold all other variables constant and check that lower viscosity increases PI and inflow. Reject nonpositive viscosity, impossible geometry and mixed units.

**Boundary.** This is a single-phase teaching/engineering proxy. It is not a calibrated multiphase inflow-performance relationship.

### Feature 6 — Quasi-dynamic SRP response

**Purpose.** Make CSS changes affect the surface lifting system.

A surface dynamometer card is polished-rod load versus position over one stroke. It combines fluid load, buoyant rod weight, acceleration, rod/tubing effects and friction.[6] Pump fillage can be expressed as effective plunger travel divided by maximum plunger travel, with the transfer point identifying load transfer between valves.[7]

**MVP implementation.** Begin with a transparent quasi-dynamic model, not a full rod-string finite-element solver:

```text
capacity_proxy = pump_displacement × stroke × SPM
pump_production = capacity_proxy × volumetric_efficiency
fillage = inflow / capacity_proxy × 100
load = base_load + fluid_load(μ, inflow) + speed_load(SPM)
energy = ρ g q H / η_pump
```

The MVP must also generate or ingest a synthetic load–position card. Compute maximum load, minimum load, load range, numerical card area, mean load, peak-to-peak load and cycle repeatability.

If enough inputs are available, add a one-dimensional, viscously damped rod-string approximation using surface load and position as boundary conditions. A higher-fidelity downhole card solver is a final-project extension, not an MVP blocker.

**Output.** Pump fillage, SRP load, production proxy, energy proxy, load card, card features, risk score and rule evidence.

**Validation.** Increasing inflow must alter fillage and load. Increasing SPM must alter capacity and energy. The system must display “insufficient card/data” instead of forcing a diagnosis.

**Boundary.** Published sample counts, fault thresholds and card percentages are study-specific precedents, not universal THERMOLIFT limits.[6]

### Feature 7 — Explainable SRP diagnostic layer

**Purpose.** Detect operating risk without pretending that a small synthetic dataset supports a reliable black-box classifier.

A hybrid SRP study combines dynamometer features and expert rules with deep-learning outputs, and reports that visually similar faults can overlap.[6] This supports a rules-first MVP with optional machine learning later.

**MVP rule examples.**

```text
IF pump_fillage < fillage_min AND load_range rises
THEN low-fillage / fluid-pound risk.

IF viscosity rises AND SPM rises AND maximum load rises
THEN rod-loading risk.

IF card area changes sharply while rate falls
THEN inspect valve leakage, friction or sensor quality.

IF load-position coverage is incomplete
THEN do not diagnose; display insufficient card data.
```

Every alert must show the fired rule, variables, thresholds and data-quality status. Use a rolling baseline for trends, not a single card in isolation.

**Output.** Risk class, severity, evidence list, confidence qualifier and escalation message.

**Validation.** Inject known synthetic events and measure detection precision, recall, false alarms and time-to-detection. Keep event labels separate from the normal production model.

### Feature 8 — Scenario engine

**Purpose.** Turn the twin into a what-if decision tool.

**Candidate inputs.**

```text
CSS: steam mass, injection duration, soak duration
SRP: pump speed, stroke length
```

Generate at least 50–100 combinations. The current deterministic demonstration uses 60 combinations across five steam levels, four soak durations and three SPM settings.

For every scenario, calculate:

```text
thermal trajectory
final temperature and viscosity
inflow and oil-rate proxy
pump fillage and SRP load
energy / steam proxy
risk score
constraint margins
uncertainty and support range
objective contributions
```

The scenario engine should use the same model modules as the current-state replay. It must not contain a second, hidden set of formulas.

### Feature 9 — Hard constraint engine

**Purpose.** Stop the ranking layer from selecting a high-production scenario that is unsupported or unsafe under the declared prototype envelope.

Potential configurable constraints include:

- maximum SRP load;
- minimum pump fillage;
- maximum steam input;
- pressure operating range;
- maximum energy or resource score;
- maximum change from the current pump setting;
- data-quality and model-support requirements.

Apply hard filters **before** ranking. Every rejected row needs an exact reason, such as:

> **Rejected:** pump fillage below the configurable prototype minimum.

Do not call these “OIL limits.” Store them as `CONFIGURABLE PROTOTYPE ASSUMPTION` until approved asset limits are available.

### Feature 10 — Transparent multi-objective ranking

**Purpose.** Choose a feasible compromise and explain it.

Use a transparent weighted objective for the MVP:

```text
score = w_oil × normalized_oil_benefit
      − w_steam × normalized_steam_intensity
      − w_energy × normalized_energy
      − w_risk × normalized_SRP_risk
```

The weights must be visible and editable. Hard constraints remain separate from soft objective terms. A final project can add a Pareto frontier, but the MVP should first show why one feasible scenario beats another.

The recommendation copy should read:

> **Scenario S-04-72-6 is recommended because it provides a favourable production/resource trade-off while satisfying all configured prototype constraints.**

It should not read:

> “AI selected Scenario 17.”

### Feature 11 — Uncertainty and data-quality gating

**Purpose.** Prevent a precise-looking output from being mistaken for a calibrated operating instruction.

Build an auditable MVP confidence object from:

```text
input completeness
stale or stuck signals
physics residual
distance from synthetic operating envelope
scenario extrapolation distance
model residual / backtest error
```

The UI should show:

```text
Confidence: 82%   [illustrative, not calibrated]
Data quality: GOOD
Operating range: WITHIN MODEL ENVELOPE
Uncertainty: MODERATE
```

For high uncertainty, display:

> **Operator review recommended.**

Suppress or downgrade recommendations when data quality fails, the physics residual is high, or the scenario is outside the supported model range. Do not label this number “statistically calibrated” until a formal calibration method has been implemented.

### Feature 12 — Validation views

The MVP should visibly validate itself in three ways.

**Temporal validation.** Use earlier synthetic cycles for calibration and later cycles for validation/test. Use chronological rolling-origin or walk-forward folds. Fit imputation, scaling and preprocessing only within the training window. Do not randomly shuffle overlapping windows across time.[8] [9]

**Physics-consistency check.** Show that temperature increase lowers viscosity and lower viscosity increases mobility/inflow. Add residuals against the selected mechanistic model. Use normalized residuals only after their scale is established on a time-separated calibration set.

**Counterfactual replay.** Freeze the pre-intervention state and exogenous inputs. Compare the baseline controls with an alternative CSS–SRP action. Label the result as **model-based counterfactual simulation**, not an observed field effect.

Report MAE and RMSE where appropriate. Add interval coverage and width if uncertainty intervals are implemented. Report performance by cycle, regime, missingness burden and scenario seed.

---

## 5. End-to-end MVP architecture

![MaruDhara MVP architecture diagram](marudhara_mvp/architecture.png)

The complete architecture has four layers.

### Layer A — Data and provenance

```text
data/synthetic_well.csv
config/operating_limits.yaml
data schema and unit checks
SQLite MVP store
```

The data adapter must expose one interface regardless of whether the source is synthetic CSV, SQLite, or later Oil India telemetry. Each record should preserve source label and model version.

### Layer B — Physics and state modules

```text
state_estimator.py
css_model.py
viscosity_model.py
inflow_model.py
srp_model.py
```

These modules must be deterministic functions of typed inputs. They should not import Streamlit or Plotly. Each module returns values, warnings, units and model metadata.

### Layer C — Decision and governance modules

```text
scenario_engine.py
constraints.py
optimizer.py
uncertainty.py
validation.py
```

The scenario engine calls the same physics modules as the baseline replay. The constraint engine returns `feasible`, `constraint_margins` and `rejection_reasons`. The optimizer sees only feasible scenarios. The uncertainty module can downgrade the recommendation without changing the underlying prediction.

### Layer D — Interface and storage

```text
app.py
pages / dashboard components
Plotly charts
3D well state layer
SQLite recommendation audit
```

The UI should show current state, controls, scenario comparison, constraint status, recommendation, explanation, uncertainty and validation. The 3D well should reflect phase and risk state using simple indicators before any complex 3D integration is attempted.

### Suggested project tree

```text
thermolift/
├── app.py
├── requirements.txt
├── data/
│   ├── synthetic_well.csv
│   ├── scenario_catalogue.csv
│   └── README.md
├── src/
│   ├── schema.py
│   ├── data_generator.py
│   ├── data_quality.py
│   ├── state_estimator.py
│   ├── css_model.py
│   ├── viscosity_model.py
│   ├── inflow_model.py
│   ├── srp_model.py
│   ├── scenario_engine.py
│   ├── constraints.py
│   ├── optimizer.py
│   ├── uncertainty.py
│   └── validation.py
├── config/
│   └── operating_limits.yaml
├── docs/
│   ├── TECHNICAL_DESIGN.md
│   ├── ASSUMPTIONS.md
│   └── DATA_DICTIONARY.md
└── tests/
    ├── test_causality.py
    ├── test_constraints.py
    ├── test_reproducibility.py
    └── test_validation_splits.py
```

### Recommended stack

Use Python, NumPy, Pandas, SciPy where needed, Plotly and Streamlit for the MVP. Use IAPWS only where steam/water properties materially improve the CSS calculation. Use SQLite for the local recommendation audit and keep a repository interface that can move to PostgreSQL later.

---

## 6. Synthetic data design and current generated assets

### 6.1 Dataset structure

The generator creates:

- `synthetic_well.csv`: 2,688 hourly rows across four cycles;
- `scenario_catalogue.csv`: 60 candidate CSS–SRP actions;
- `current_state.json`: the latest state snapshot;
- `validation_split.json`: cycle 1–2 calibration, cycle 3 validation, cycle 4 test;
- `synthetic_validation_figure.png`: cycle replay and feasible/rejected scenario figure.

Each row includes:

```text
well_id, field_label, cycle_id, timestamp, phase
reservoir_pressure_bar, bottomhole_pressure_bar
steam_mass_t, steam_pressure_bar
steam_injection_duration_h, soak_duration_h, production_duration_h
temperature_c, viscosity_kcp, inflow_bpd
oil_rate_bpd, water_rate_bpd
pump_speed_spm, stroke_length_m, pump_fillage_pct
srp_load_kn, energy_kwh_bbl, srp_risk_score
data_quality, source_label, random_seed
```

### 6.2 Causal generation logic

The generator first creates the phase and thermal state. It then computes viscosity, mobility, inflow, pump capacity, fillage, load, energy and rate. This prevents the dataset from looking statistically plausible while violating the intended physics.

The generator also adds small measurement noise. The noiseless relationships remain deterministic and can be used as ground truth for prototype validation.

### 6.3 Synthetic operating envelope

The current demonstration uses configurable prototype thresholds such as a minimum pump fillage, a maximum SRP load, a maximum steam input and an energy proxy. These values exist to exercise the constraint engine. They should be moved into configuration and renamed as **engineering assumptions** before the team shows the system to an external reviewer.

### 6.4 Public benchmark resources

The UCI 3W dataset contains multivariate oil-well time-series instances with pressure, temperature and gas-lift variables, missing values and event labels.[10] Its project documentation notes a mixture of historical/real, simulated and hand-drawn instances.[11] It is useful for pipeline smoke tests, missingness handling and event-detection design. It is not Baghewala telemetry.

The Open Porous Media Norne case is an open simulator benchmark for black-oil reservoir studies.[12] It can help test counterfactual simulation patterns, but it is also not a Baghewala field dataset.

The first generated figure below is intentionally modest. It shows the phase-labelled thermal replay and the feasible/rejected scenario cloud. It is a validation aid for the MVP, not a field-performance chart.

![Synthetic cycle replay and scenario trade-off](marudhara_mvp/synthetic_validation_figure.png)

---

## 7. Recommendation and operator workflow

The dashboard should tell a short, auditable story:

1. The selected well is in production after a CSS cycle.
2. Temperature is cooling and viscosity is rising.
3. Inflow is changing the SRP fillage/load balance.
4. Several CSS–SRP combinations are simulated.
5. High-risk or unsupported combinations are rejected before ranking.
6. One feasible combination is recommended.
7. The reason, objective contribution, constraints, uncertainty and predicted response are displayed.
8. The operator can approve, modify, reject or annotate the advisory action.
9. The resulting state can be replayed against the baseline.

The recommendation card should include:

```text
Recommended scenario
CSS controls
SRP controls
Expected oil-rate proxy
Steam / energy proxy
Pump fillage and SRP load
Hard constraints and margins
Confidence / uncertainty
Why selected
What could invalidate the recommendation
Operator action: approve / modify / reject
```

No action should be automatically sent to a field control system in the MVP.

---

## 8. What makes THERMOLIFT different

### 8.1 The coupling is the feature

Many dashboards can show temperature, production and pump metrics as separate cards. THERMOLIFT treats them as one causal decision problem. A CSS change is allowed to alter SRP conditions through temperature, viscosity and inflow. That is the central engineering contribution.

### 8.2 The system is physics-informed without pretending to be high fidelity

The MVP uses reduced-order balances, a visible viscosity law, a transparent inflow equation and a quasi-dynamic SRP response. This is more defensible than a black-box model that produces a rate without showing why it changed. It is also more achievable than a full reservoir simulator in a 48-hour build window.

### 8.3 Constraints come before optimization

The system does not rank every numerical combination and then add a warning after the fact. It filters infeasible scenarios first. A reviewer can see exactly why a scenario was rejected.

### 8.4 The recommendation is reviewable

The digital-twin literature supports an ongoing loop of data processing, simulation, inverse-model updating, recommendation, operator review, implementation and response tracking.[13] [14] THERMOLIFT brings this pattern into the MVP with an advisory recommendation and an audit trail instead of claiming autonomous control.

### 8.5 Data honesty is part of the product

The system explicitly distinguishes public Baghewala context, literature-backed model structure, synthetic values, configurable assumptions and future field data. This makes the project stronger, not weaker. It avoids an easy-to-criticise claim that a synthetic demonstration represents Oil India performance.

### 8.6 The prototype is designed for replacement

The synthetic adapter can be replaced by a real-data adapter. The state schema, model interfaces, constraints and validation split remain. This gives the project a credible path from hackathon prototype to field-calibration plan.

---

## 9. 48-hour build order

### Priority 1 — Data generator and schema

Generate the four-cycle dataset, add provenance, document assumptions and implement reproducibility tests.

### Priority 2 — CSS thermal state

Implement phase transitions and the reduced-order temperature model. Plot temperature against time.

### Priority 3 — Temperature, viscosity and inflow

Implement the explicit viscosity law and PI-based inflow proxy. Add monotonic physics tests.

### Priority 4 — SRP response

Implement fillage, load and energy proxies. Add a synthetic dynamometer card and transparent rules.

### Priority 5 — Scenario engine

Generate 50–100 candidates using the same model functions.

### Priority 6 — Constraints

Filter candidates and return exact rejection reasons.

### Priority 7 — Ranking

Rank only feasible candidates using visible weights.

### Priority 8 — Recommendation

Render the selected scenario, rationale, margins and operator review state.

### Priority 9 — Uncertainty

Add input-quality flags, support-range distance and confidence qualifiers.

### Priority 10 — Validation

Add rolling-origin metrics, monotonic physics checks and counterfactual replay.

### Priority 11 — Streamlit polish

Make the dashboard readable and engineering-oriented.

### Priority 12 — 3D integration

Connect phase, heat state, production state and risk to the existing 3D layer.

If time becomes limited, do not sacrifice the computational pipeline to improve visual polish.

---

## 10. Team responsibilities

A practical team split is:

**Data and reproducibility owner.** Maintains the generator, schema, seed, provenance and assumptions.

**CSS and inflow owner.** Maintains the phase state machine, thermal model, viscosity relationship and inflow model.

**SRP owner.** Maintains pump response, card features, diagnostic rules and risk outputs.

**Decision and validation owner.** Maintains scenario generation, constraints, ranking, uncertainty and validation views.

**Interface and integration owner.** Maintains Streamlit, Plotly, 3D state rendering, recommendation UX and screenshots.

All changes should include a short model note: input units, equation, assumption status, output units and test case.

---

## 11. Known limitations and final-project extensions

The MVP will not resolve all field complexities. The main limitations are a reduced-order thermal model, synthetic data, a simplified inflow relationship, a quasi-dynamic SRP model, configurable rather than authorised constraints and a rules-first diagnostic layer.

The final project can extend the MVP with authorised historical data, PVT/rheology calibration, measured thermal cycles, well-specific pump geometry, downhole dynamometer cards, higher-fidelity rod-string modelling, facility/network constraints, formal uncertainty calibration, rolling domain-shift evaluation, a multi-well scheduler, live data ingestion and change-management integration.

Those extensions should be framed as a calibration and deployment pathway. They should not be presented as already solved by the hackathon prototype.

---

## 12. Reference implementation checklist

Before demo day, confirm:

- [ ] `source_label` is visible in the UI.
- [ ] The fixed random seed reproduces the dataset.
- [ ] Units are displayed beside every engineering variable.
- [ ] Model parameters are configurable and documented.
- [ ] Synthetic values are never described as measured Baghewala values.
- [ ] CSS phase transitions are visible.
- [ ] Temperature changes viscosity.
- [ ] Viscosity changes inflow.
- [ ] Inflow changes SRP fillage/load.
- [ ] At least 50 scenarios are generated.
- [ ] Constraints are applied before ranking.
- [ ] Rejection reasons are visible.
- [ ] Recommendation reasons are visible.
- [ ] Uncertainty and data quality are visible.
- [ ] Temporal validation is chronological.
- [ ] Counterfactual replay is labelled as model-based.
- [ ] Operator approval is required.
- [ ] The 3D layer reflects the state rather than replacing it.
- [ ] The code, assumptions, architecture diagram and run instructions are in the repository.

---

## References

[1]: https://www.oil-india.com/rajasthan-fields "Oil India Limited — Rajasthan Fields"

[2]: https://www.mdpi.com/1996-1073/15/5/1757 "A Production Performance Model of the Cyclic Steam Stimulation Process in Multilayer Heavy Oil Reservoirs"

[3]: https://pubs.aip.org/aip/pof/article/37/4/047110/3342003/Reservoir-heating-in-cyclic-steam-stimulation-for "Reservoir heating in cyclic steam stimulation for heavy oil recovery"

[4]: https://onepetro.org/ogf/article-pdf/4/01/66/2208398/spe-157360-pa.pdf "Prediction of Heavy-Oil Viscosities With a Simple Correlation Approach"

[5]: https://www.kgs.ku.edu/software/DST/HELP/horner/qa_fluid.html "Quantitative Analysis: Fluid / Productivity Index"

[6]: https://www.mdpi.com/1996-1073/16/7/3170 "A Hybrid Approach of the Deep Learning Method and Rule-Based Method for Fault Diagnosis of Sucker Rod Pumping Wells"

[7]: https://hs.weatherford.com/knowledge/srp-solution-logic "SRP Solution Logic"

[8]: https://otexts.com/fpp3/tscv.html "Time series cross-validation"

[9]: https://www.ibm.com/think/topics/data-leakage-machine-learning "What is data leakage in machine learning?"

[10]: https://archive.ics.uci.edu/dataset/540/3w+dataset "UCI Machine Learning Repository — 3W Dataset"

[11]: https://github.com/ricardovvargas/3w_dataset "3W Dataset project repository"

[12]: https://opm-project.org/?page_id=559 "Open Porous Media Initiative — Open datasets"

[13]: https://www.digitaltwinconsortium.org/pdf/2021_March_JoI_Design_and_Implementation_of_a_Digital_Twin_for_Live_Petroleum_Production_Optimization_SA.pdf "Design and Implementation of a Digital Twin for Live Petroleum Production Optimization: Data Processing and Simulation"

[14]: https://www.controleng.com/digital-twins-for-live-petroleum-production-optimization/ "Digital twins for live petroleum production optimization"

[15]: https://pangea.stanford.edu/ERE/pdf/pereports/PhD/Wang03.pdf "Development and Applications of Production Optimization Techniques for Petroleum Fields"

[16]: https://pangea.stanford.edu/ERE/pdf/pereports/PhD/Sarma06.pdf "Efficient Closed-Loop Optimal Control of Petroleum Reservoirs Under Uncertainty"

---

## Appendix A — Current generated artifacts

The current reproducible artifacts are stored beside this report:

```text
/home/ubuntu/work/marudhara_mvp/generate_synthetic.py
/home/ubuntu/work/marudhara_mvp/synthetic_well.csv
/home/ubuntu/work/marudhara_mvp/scenario_catalogue.csv
/home/ubuntu/work/marudhara_mvp/current_state.json
/home/ubuntu/work/marudhara_mvp/validation_split.json
/home/ubuntu/work/marudhara_mvp/architecture.mmd
/home/ubuntu/work/marudhara_mvp/architecture.png
/home/ubuntu/work/marudhara_mvp/synthetic_validation_figure.png
```

The generator is the source of truth for the current synthetic outputs. If an assumption changes, regenerate the CSVs and record the change in the report version and assumptions file.
