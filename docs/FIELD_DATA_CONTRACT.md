# THERMOLIFT / MaruDhara (SIH26120) — Field Data Ingestion Contract

## 1. Overview and Purpose
This document defines the formal engineering data contract for ingesting real field telemetry, well test measurements, and laboratory fluid PVT data from Oil India Limited (OIL) heavy oil assets (e.g., Baghewala / Rajasthan Basin).

The current THERMOLIFT v2.0 prototype operates with representative synthetic data generated from physical governing equations ($seed=26120$). This contract defines the exact interfaces, frequencies, quality gates, and error semantics required to calibrate and operate the coupled CSS+SRP digital twin on live field assets.

---

## 2. Ingestion Channels and Signal Specifications

### 2.1 Channel A: High-Frequency Electrical & Mechanical SRP Skid Telemetry
*Ingestion Cadence: 1 Hz to 10-second aggregations.*

| Signal Name | Physical Parameter | Engineering Unit | Valid Operating Range | Accuracy / Precision | Required Quality Gate |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `srp_motor_power_kw` | Active Motor Power | kW | 0.0 – 90.0 | $\pm 0.5$ kW | Negative values flagged FAIL |
| `srp_stroke_speed_spm` | Surface Pumping Frequency | strokes/min (spm) | 1.0 – 12.0 | $\pm 0.05$ spm | $spm < 0.5$ or $> 15$ FAIL |
| `srp_stroke_length_m` | Polish Rod Stroke Length | meters (m) | 1.0 – 4.0 | $\pm 0.01$ m | Step changes flagged SUSPECT |
| `srp_pprl_kn` | Peak Polished Rod Load | kN | 10.0 – 100.0 | $\pm 0.5$ kN | $PPRL < MPRL$ triggers FAIL |
| `srp_mprl_kn` | Minimum Polished Rod Load | kN | 0.0 – 50.0 | $\pm 0.5$ kN | $MPRL < 0$ flagged FAIL |
| `srp_dynacard_points` | Position-Load Dynacard Array | m, kN | $N=100-256$ pairs | $\pm 0.2$ kN | Loop self-intersection check |
| `srp_pump_fillage_pct` | Derived Surface Dynacard Fillage | % | 0.0 – 100.0 | $\pm 1.0$ % | Frozen value $> 6$h flagged SUSPECT |

### 2.2 Channel B: Thermal Injection & Surface Wellhead Skid
*Ingestion Cadence: 1-minute to 15-minute averaged intervals.*

| Signal Name | Physical Parameter | Engineering Unit | Valid Operating Range | Accuracy / Precision | Required Quality Gate |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `steam_inj_rate_t_h` | Steam Mass Rate | t/h | 0.0 – 15.0 | $\pm 0.1$ t/h | Spurious spikes ($> 20$) clamped |
| `steam_inj_pressure_bar`| Generator Outlet Pressure | bar gauge | 50.0 – 180.0 | $\pm 1.0$ bar | Out of range triggers FAIL |
| `steam_inj_temp_c` | Steam Temperature | °C | 250.0 – 350.0 | $\pm 1.5$ °C | Must match saturation curve $\pm 15$°C |
| `steam_quality_pct` | Steam Vapor Fraction ($X$) | % | 60.0 – 85.0 | $\pm 2.0$ % | $X < 50\%$ triggers alert |
| `cum_steam_injected_t` | Cumulative Cycle Steam | metric tonnes | 0.0 – 500.0 | $\pm 0.5$ t | Monotonic non-decreasing check |
| `surface_whp_bar` | Wellhead Flowing Pressure | bar gauge | 0.5 – 35.0 | $\pm 0.2$ bar | $WHP < P_{sep}$ triggers alarm |
| `casing_head_p_bar` | Annulus Casing Head Pressure | bar gauge | 0.0 – 25.0 | $\pm 0.2$ bar | Rising trend indicates gas buildup |

### 2.3 Channel C: Downhole Gauges / Permanent Downhole Sensors (PDG / DTS)
*Ingestion Cadence: 5-minute to hourly.*

| Signal Name | Physical Parameter | Engineering Unit | Valid Operating Range | Accuracy / Precision | Required Quality Gate |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `pdg_bottomhole_temp_c`| Bottomhole Flowing Temp ($T_{wf}$) | °C | 30.0 – 300.0 | $\pm 0.5$ °C | Thermal spike $> 15$°C/h SUSPECT |
| `pdg_bottomhole_p_bar` | Bottomhole Flowing Pressure ($P_{wf}$) | bar gauge | 3.0 – 80.0 | $\pm 0.2$ bar | $P_{wf} > P_{res}$ during flow FAIL |
| `dts_temp_profile` | Distributed Temp Fiber Array | °C vs Depth (m) | 30.0 – 320.0 | $\pm 1.0$ °C | Continuity check across joints |

### 2.4 Channel D: Periodic Production Well Tests & Lab PVT
*Ingestion Cadence: Daily to weekly well test; quarterly PVT sample.*

| Signal Name | Physical Parameter | Engineering Unit | Valid Operating Range | Test Standard |
| :--- | :--- | :--- | :--- | :--- |
| `test_liquid_rate_m3_d`| 24-hr Test Separator Liquid | $\text{m}^3/\text{day}$ | 1.0 – 50.0 | Coriolis / Turbine Test Separator |
| `test_water_cut_pct` | Basic Sediment & Water (BS&W) | % vol | 5.0 – 95.0 | Centrifuge / Karl Fischer titration |
| `test_gas_oil_ratio` | GOR | $\text{m}^3/\text{m}^3$ | 0.0 – 50.0 | Orifice meter on test separator |
| `pvt_dead_oil_viscosity`| Viscosity vs Temp Table | cP @ [40, 60, 80, 100°C] | 50 – 50,000 cP | ASTM D445 / Rotational Rheometer |
| `pvt_oil_density_api` | Crude Specific Gravity | °API | 12.0 – 19.0 | Hydrometer / ASTM D1298 |

---

## 3. Data Ingestion Architecture & Data Quality Classification

Each inbound measurement telemetry frame is passed through the `IngestionValidator` prior to persistence into the `well_telemetry` table.

```
[ Field RTU / SCADA / Historian ]
              │ (OPC-UA / MQTT / Modbus TCP)
              ▼
    ┌───────────────────┐
    │ Schema Validation │ ── (Bad schema, missing timestamp) ──► Dead Letter Queue
    └─────────┬─────────┘
              ▼
    ┌───────────────────┐
    │ Quality Gate Rule │
    └─────────┬─────────┘
              ├─► GOOD: Within valid physical envelope, sensors reporting normally.
              ├─► SUSPECT: Sensor drift, timestamp jitter, or mild physics discrepancy.
              └─► FAIL: Disconnected, impossible physics, or frozen signal > 24 hrs.
              ▼
    ┌───────────────────┐
    │ Uncertainty Gate  │
    └─────────┬─────────┘
              ├─► If GOOD    ──► Uncertainty Gate = GREEN (Recommendations Unrestricted)
              ├─► If SUSPECT ──► Uncertainty Gate = AMBER (Operator Warning Badge Displayed)
              └─► If FAIL    ──► Uncertainty Gate = RED (Advisories Automatically Suppressed)
```

---

## 4. Calibration & Physics-Residual Learning Workflow

When field data arrives, THERMOLIFT updates its internal models via a three-tier hierarchical calibration:

1. **Analytical Physics Baseline (Zero Data Drift):**
   - The authoritative thermodynamic balance (Boberg-Lantz) and Navier-Stokes heavy oil drag correlations govern production predictions.
2. **First-Tier Parameter Regression (Monthly / Per Cycle):**
   - Historical temperature profiles fit reservoir thermal conductivity ($k_{res}$) and overburden loss factor ($F_{loss}$).
   - Downhole $P_{wf}$ and flow tests fit Darcy permeability-thickness product ($k \cdot h$) and skin factor ($S$).
3. **Second-Tier Residual ML (Ridge Hybrid Pathway):**
   - If physical residual $T_{field} - T_{model} > 1.0$°C, the bounded L2-regularized Ridge model (`src/residual_ml.py`) learns the systematic discrepancy:
     $$\Delta T = \mathbf{w}^T \mathbf{x} + b, \quad \|\mathbf{w}\|_2 \le \lambda$$
   - Corrections are hard-bounded within $[-4.0^\circ\text{C}, +4.0^\circ\text{C}]$.
   - If residual $> 4.5^\circ\text{C}$, the uncertainty gate trips to `RED` and suppresses recommendations until model recalibration.

---

## 5. Security, Provenance, and Operator Audit Trail
- All ingested batches generate an SHA-256 state hash stored in `input_state_hash`.
- Field measurements are strictly separated from synthetic models via the `source_label` column (`"FIELD"` vs `"SYNTHETIC"`).
- Synthetic twin predictions must never overwrite actual raw telemetry records.
