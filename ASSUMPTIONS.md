# THERMOLIFT / MaruDhara — Assumptions Register

The values below are prototype inputs for a reproducible synthetic demonstration. They are not approved Baghewala operating limits.

| Parameter | Value / range in current generator | Why selected | Status |
|---|---:|---|---|
| Random seed | `26120` | Reproducibility and project traceability | Synthetic |
| Well identity | `BWG-SIM-001` | Avoids inventing a real well number | Synthetic |
| Dataset horizon | 4 cycles × 28 days, hourly rows | Enough chronology for replay and holdout testing | Synthetic |
| CSS phases | injection → soak → production | Matches the public CSS process description | Literature-backed structure; synthetic timings |
| Steam mass | 90–122 t per scenario | Exercises low-to-high what-if actions | Synthetic |
| Soak duration | 36–72 h per scenario | Exercises soak trade-offs | Synthetic |
| Steam pressure | 31–34 bar in generator | Stable synthetic range for visualization | Synthetic |
| Reference temperature | 50 °C | Aligns with the public viscosity reference temperature | Literature-context anchor; not a control limit |
| Viscosity | Generated from explicit temperature function | Makes thermal mechanism auditable | Synthetic / uncalibrated |
| Thermal model | Lumped first-order balance | Fast, transparent, scenario-friendly | Engineering assumption |
| Heat-loss conductance | Configurable in code | Enables soak and production decline | Engineering assumption |
| Permeability, thickness, skin, radii | Configurable inflow parameters | Required by PI proxy | Engineering assumption / synthetic |
| SRP speed | 5–10 SPM scenario range | Exercises speed/fillage/risk trade-off | Synthetic |
| Stroke length | ~1.45–1.65 m in generator | Provides a stable synthetic pump-control dimension | Synthetic |
| Pump capacity factor | 7.2 × SPM × stroke | Keeps fillage in a visible operating range for the demo | Synthetic |
| Minimum pump fillage | 52% prototype filter | Creates feasible and rejected scenarios | Configurable prototype assumption |
| Maximum SRP load | 62 kN prototype filter | Creates a hard equipment-risk filter | Configurable prototype assumption |
| Maximum steam input | 118 t prototype filter | Creates a resource hard filter | Configurable prototype assumption |
| Energy objective | kWh/bbl proxy | Makes resource trade-off visible | Synthetic |
| SRP risk score | Rule-based 0–100 proxy | Avoids unsupported black-box diagnosis | Engineering assumption |
| Confidence | Data-quality/support/residual composite | Communicates uncertainty without claiming calibration | Engineering assumption |
| Validation split | cycles 1–2 / 3 / 4 | Chronological and leakage-safe demonstration | Methodological choice |
| Field calibration | Not performed | No authorised well-level telemetry provided | Explicit limitation |
| Autonomous control | Not implemented | MVP is decision support only | Explicit boundary |

## Source-backed context

Oil India publicly describes Baghewala heavy crude, Jodhpur Sandstone, CSS and SRP, and reports a public viscosity range at 50 °C. Public field-level values are context only. Any value used in the generator that is not explicitly tied to a public source remains synthetic.

## Promotion rule for real deployment

An assumption may be promoted to a field parameter only after the team has:

1. identified the authorised source and timestamp;
2. documented the unit and measurement method;
3. confirmed the well/structure to which the value applies;
4. defined the uncertainty or operating range;
5. validated the model against a time-separated dataset; and
6. obtained the required operator/asset-owner approval.
