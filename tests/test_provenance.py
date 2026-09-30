import pytest
from src.schema import WellState
from src.provenance import compute_input_state_hash

def test_deterministic_state_hash_stability():
    w1 = WellState(
        well_id="BWG-SIM-001",
        timestamp="2026-03-30T10:00:00Z",
        phase="production",
        temperature_c=85.0,
        viscosity_kcp=1.2,
        reservoir_pressure_bar=45.0,
        bottomhole_pressure_bar=12.0,
        inflow_bpd=95.0,
        oil_rate_bpd=88.0,
        water_rate_bpd=7.0,
        pump_speed_spm=7.2,
        stroke_length_m=2.5,
        pump_fillage_pct=76.0,
        srp_load_kn=48.0,
        energy_kwh_bbl=22.0,
        srp_risk_score=15,
        data_quality="GOOD"
    )
    w2 = WellState(
        well_id="BWG-SIM-001",
        timestamp="2026-03-30T10:00:00Z",
        phase="production",
        temperature_c=85.0,
        viscosity_kcp=1.2,
        reservoir_pressure_bar=45.0,
        bottomhole_pressure_bar=12.0,
        inflow_bpd=95.0,
        oil_rate_bpd=88.0,
        water_rate_bpd=7.0,
        pump_speed_spm=7.2,
        stroke_length_m=2.5,
        pump_fillage_pct=76.0,
        srp_load_kn=48.0,
        energy_kwh_bbl=22.0,
        srp_risk_score=15,
        data_quality="GOOD"
    )

    hash1 = compute_input_state_hash(w1)
    hash2 = compute_input_state_hash(w2)

    assert len(hash1) == 16
    assert hash1 == hash2

def test_state_hash_sensitivity_to_perturbations():
    w1 = WellState(
        well_id="BWG-SIM-001",
        timestamp="2026-03-30T10:00:00Z",
        phase="production",
        temperature_c=85.0,
        viscosity_kcp=1.2,
        reservoir_pressure_bar=45.0,
        bottomhole_pressure_bar=12.0,
        inflow_bpd=95.0,
        oil_rate_bpd=88.0,
        water_rate_bpd=7.0,
        pump_speed_spm=7.2,
        stroke_length_m=2.5,
        pump_fillage_pct=76.0,
        srp_load_kn=48.0,
        energy_kwh_bbl=22.0,
        srp_risk_score=15
    )
    # Alter temperature slightly by 0.1 °C
    w2 = w1.model_copy(update={"temperature_c": 85.1})
    # Alter well_id
    w3 = w1.model_copy(update={"well_id": "BWG-SIM-002"})

    assert compute_input_state_hash(w1) != compute_input_state_hash(w2)
    assert compute_input_state_hash(w1) != compute_input_state_hash(w3)
