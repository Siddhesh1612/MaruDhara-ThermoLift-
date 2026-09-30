import pytest
from src.schema import WellState, ScenarioResult
from src.uncertainty import evaluate_confidence

def get_base_scenario():
    return ScenarioResult(
        scenario_id="S_TEST",
        steam_mass_t=105.0,
        soak_h=48,
        pump_speed_spm=7.0,
        stroke_length_m=2.5,
        expected_oil_bpd=85.0,
        sor=7.8,
        energy_kwh_bbl=22.0,
        pump_fillage_pct=78.0,
        srp_load_kn=45.0,
        pprl_kn=45.0,
        mprl_kn=15.0,
        rod_stress_pct=60.0,
        floating_risk=0.05,
        maintenance_risk=0.15,
        feasible=True
    )

def test_uncertainty_gate_green_state():
    scenario = get_base_scenario()
    state = WellState(
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
        pump_speed_spm=7.0,
        stroke_length_m=2.5,
        pump_fillage_pct=78.0,
        srp_load_kn=45.0,
        energy_kwh_bbl=22.0,
        srp_risk_score=15,
        data_quality="GOOD"
    )

    conf = evaluate_confidence(scenario, current_state=state, physics_residual=0.8)

    assert conf.gate_state == "GREEN"
    assert conf.recommendation_suppressed is False
    assert conf.confidence_pct >= 75.0

def test_uncertainty_gate_amber_state():
    scenario = get_base_scenario()
    # Suspect data quality triggers AMBER
    state = WellState(
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
        pump_speed_spm=7.0,
        stroke_length_m=2.5,
        pump_fillage_pct=78.0,
        srp_load_kn=45.0,
        energy_kwh_bbl=22.0,
        srp_risk_score=15,
        data_quality="SUSPECT"
    )

    conf = evaluate_confidence(scenario, current_state=state, physics_residual=1.5)

    assert conf.gate_state == "AMBER"
    assert conf.downgrade_applied is True
    assert conf.recommendation_suppressed is False

def test_uncertainty_gate_red_suppression():
    scenario = get_base_scenario()
    # Data quality FAIL triggers RED and suppresses recommendation
    state_fail = WellState(
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
        pump_speed_spm=7.0,
        stroke_length_m=2.5,
        pump_fillage_pct=78.0,
        srp_load_kn=45.0,
        energy_kwh_bbl=22.0,
        srp_risk_score=15,
        data_quality="FAIL"
    )

    conf_fail = evaluate_confidence(scenario, current_state=state_fail, physics_residual=0.5)
    assert conf_fail.gate_state == "RED"
    assert conf_fail.recommendation_suppressed is True

    # High physics residual (> 4.5 C) also triggers RED suppression
    state_good = state_fail.model_copy(update={"data_quality": "GOOD"})
    conf_res = evaluate_confidence(scenario, current_state=state_good, physics_residual=5.2)
    assert conf_res.gate_state == "RED"
    assert conf_res.recommendation_suppressed is True
