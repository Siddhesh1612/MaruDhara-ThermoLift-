from pathlib import Path
import numpy as np
import pandas as pd

SEED = 26120
rng = np.random.default_rng(SEED)
OUT = Path('/home/ubuntu/work/marudhara_mvp')
OUT.mkdir(parents=True, exist_ok=True)

rows = []
start = pd.Timestamp('2026-01-01 00:00:00')

# Representative, not field-calibrated, synthetic assumptions.
for cycle in range(1, 5):
    steam = 96 + cycle * 5
    steam_pressure = 31 + cycle * 0.8
    inj_hours = 34 + cycle * 2
    soak_hours = 44 + cycle * 3
    for hour in range(24 * 28):
        t = start + pd.Timedelta(days=(cycle - 1) * 34, hours=hour)
        phase_h = hour
        if phase_h < inj_hours:
            phase = 'injection'
        elif phase_h < inj_hours + soak_hours:
            phase = 'soak'
        else:
            phase = 'production'
        cycle_age = max(0, hour - inj_hours - soak_hours)
        if phase == 'injection':
            phase_temp = 54 + 4.2 * (phase_h / max(inj_hours, 1))
        elif phase == 'soak':
            phase_temp = 62.5 + 5.0 * ((phase_h - inj_hours) / max(soak_hours, 1))
        else:
            phase_temp = 67.5 - 0.115 * (phase_h - inj_hours - soak_hours)
        thermal_gain = 0.065 * steam + 0.08 * soak_hours
        temp = phase_temp + thermal_gain - 7.5 + 1.8 * np.sin(hour / 19) + rng.normal(0, 0.35)
        temp = float(np.clip(temp, 48, 82))
        viscosity = float(np.clip(13.0 * np.exp(-0.046 * (temp - 50)) + rng.normal(0, 0.16), 3.8, 15.5))
        pressure = float(24.5 - 0.006 * hour + 0.8 * np.sin(hour / 31) + rng.normal(0, 0.12))
        bottomhole = pressure - 2.8
        mobility = float(np.clip(50 / viscosity, 1.8, 15.0))
        inflow = float(np.clip(23.0 + 3.2 * mobility + 0.68 * (pressure - 20) + rng.normal(0, 0.55), 25, 78))
        spm = float(np.clip(6.5 + 0.35 * np.sin(hour / 17) + rng.normal(0, 0.08), 5.7, 7.4))
        stroke = float(np.clip(1.55 + 0.04 * np.sin(hour / 23), 1.45, 1.65))
        capacity = 7.2 * spm * stroke
        fillage = float(np.clip((inflow / max(capacity, 1)) * 100 + rng.normal(0, 1.4), 42, 96))
        srp_load = float(np.clip(25 + 0.62 * viscosity + 2.7 * spm + 0.12 * (100 - fillage) + rng.normal(0, 1.2), 28, 58))
        oil_rate = float(np.clip(inflow * (0.64 + 0.0022 * fillage) - 0.045 * srp_load + rng.normal(0, 0.7), 12, 68))
        water_rate = float(np.clip(7.5 + 0.03 * hour + rng.normal(0, 0.4), 4, 15))
        energy = float(np.clip(11.0 + 0.72 * spm + 0.10 * srp_load + 0.02 * steam + rng.normal(0, 0.25), 12, 24))
        load_risk = int(np.clip((srp_load - 42) * 2.0 + (58 - fillage) * 0.45, 0, 100))
        rows.append({
            'well_id': 'BWG-SIM-001', 'field_label': 'Baghewala-style representative',
            'cycle_id': cycle, 'timestamp': t.isoformat(), 'phase': phase,
            'reservoir_pressure_bar': round(pressure, 3), 'bottomhole_pressure_bar': round(bottomhole, 3),
            'steam_mass_t': round(steam, 3), 'steam_pressure_bar': round(steam_pressure, 3),
            'steam_injection_duration_h': inj_hours, 'soak_duration_h': soak_hours,
            'production_duration_h': 672 - inj_hours - soak_hours, 'temperature_c': round(temp, 3),
            'viscosity_kcp': round(viscosity, 3), 'inflow_bpd': round(inflow, 3),
            'oil_rate_bpd': round(oil_rate, 3), 'water_rate_bpd': round(water_rate, 3),
            'pump_speed_spm': round(spm, 3), 'stroke_length_m': round(stroke, 3),
            'pump_fillage_pct': round(fillage, 3), 'srp_load_kn': round(srp_load, 3),
            'energy_kwh_bbl': round(energy, 3), 'srp_risk_score': load_risk,
            'data_quality': 'GOOD', 'source_label': 'SYNTHETIC', 'random_seed': SEED,
        })

df = pd.DataFrame(rows)
df.to_csv(OUT / 'synthetic_well.csv', index=False)

# Compact scenario catalogue used by the report and UI.
scenarios = []
for i, steam in enumerate([90, 98, 106, 114, 122], start=1):
    for soak in [36, 48, 60, 72]:
        for spm in [6, 7, 8]:
            temp = 57.0 + 0.10 * (steam - 90) + 0.055 * (soak - 36)
            viscosity = 13.2 * np.exp(-0.046 * (temp - 50))
            mobility = 50 / viscosity
            inflow = 23 + 3.2 * mobility + 0.68 * 4.2
            fillage = np.clip((inflow / (7.2 * spm * 1.55)) * 100, 35, 98)
            load = 25 + 0.62 * viscosity + 2.7 * spm + 0.12 * (100 - fillage)
            oil = inflow * (0.64 + 0.0022 * fillage) - 0.045 * load
            energy = 11 + 0.72 * spm + 0.10 * load + 0.02 * steam
            risk = np.clip((load - 42) * 2.0 + (58 - fillage) * 0.45, 0, 100)
            reasons = []
            if load > 62: reasons.append('SRP load exceeds configurable limit')
            if fillage < 52: reasons.append('pump fillage below configurable minimum')
            if steam > 118: reasons.append('steam input exceeds prototype envelope')
            feasible = len(reasons) == 0
            score = oil - 0.45 * energy - 0.25 * risk
            scenarios.append({
                'scenario_id': f'S-{i:02d}-{soak}-{spm}', 'steam_mass_t': steam,
                'soak_h': soak, 'pump_speed_spm': spm, 'temperature_c': round(temp, 3),
                'viscosity_kcp': round(viscosity, 3), 'inflow_bpd': round(inflow, 3),
                'oil_rate_bpd': round(oil, 3), 'pump_fillage_pct': round(fillage, 3),
                'srp_load_kn': round(load, 3), 'energy_kwh_bbl': round(energy, 3),
                'risk_score': round(risk, 3), 'feasible': feasible,
                'rejection_reason': '; '.join(reasons) if reasons else '',
                'objective_score': round(score, 3), 'source_label': 'SYNTHETIC',
            })

scenarios_df = pd.DataFrame(scenarios)
scenarios_df.sort_values(['feasible', 'objective_score'], ascending=[False, False]).to_csv(OUT / 'scenario_catalogue.csv', index=False)

# Aggregate current-state and validation summaries.
state = df.tail(1).copy()
state.to_json(OUT / 'current_state.json', orient='records', indent=2)
validation = {
    'seed': SEED,
    'calibration_cycles': [1, 2],
    'validation_cycle': [3],
    'test_cycle': [4],
    'note': 'Synthetic metrics are demonstration outputs only and are not field accuracy.'
}
(OUT / 'validation_split.json').write_text(pd.Series(validation).to_json(indent=2))

print(f'Wrote {len(df)} time-series rows to {OUT / "synthetic_well.csv"}')
print(f'Wrote {len(scenarios_df)} scenario rows to {OUT / "scenario_catalogue.csv"}')
print('Top feasible scenario:')
print(scenarios_df[scenarios_df.feasible].sort_values('objective_score', ascending=False).head(1).to_string(index=False))
