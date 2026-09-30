from src.schema import ScenarioResult
from src.pressure_chain import evaluate_pressure_chain

def test_nodal_pressure_feasibility_and_monotonicity():
    s = ScenarioResult(
        scenario_id="S_TEST_NORMAL",
        steam_mass_t=105.0,
        soak_h=48,
        pump_speed_spm=7.0,
        stroke_length_m=2.5,
        expected_oil_bpd=30.0,
        oil_rate_bpd=30.0,
        viscosity_kcp=6.5,
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

    res = evaluate_pressure_chain(
        scenario=s,
        p_res_bar=24.5,
        p_sep_bar=3.5
    )

    # Monotonicity & surface checks
    assert res.p_res_bar > res.p_wf_bar  # Drawdown must be positive
    assert res.whp_bar > res.separator_p_bar  # Wellhead pressure must overcome separator
    assert res.feasible is True
    assert res.surface_margin_bar > 0.0

def test_surface_pressure_stall_rejection():
    """
    If separator backpressure is artificially elevated or liquid rate exceeds separator capacity,
    surface handling fails and rejection reason is populated.
    """
    s = ScenarioResult(
        scenario_id="S_TEST_HIGH_RATE",
        steam_mass_t=105.0,
        soak_h=48,
        pump_speed_spm=8.5,
        stroke_length_m=3.0,
        expected_oil_bpd=75.0,  # exceeds 65 bpd separator capacity
        oil_rate_bpd=75.0,
        viscosity_kcp=6.5,
        sor=5.0,
        energy_kwh_bbl=15.0,
        pump_fillage_pct=85.0,
        srp_load_kn=50.0,
        pprl_kn=50.0,
        mprl_kn=18.0,
        rod_stress_pct=65.0,
        floating_risk=0.05,
        maintenance_risk=0.10,
        feasible=True
    )

    res = evaluate_pressure_chain(
        scenario=s,
        p_res_bar=24.5,
        p_sep_bar=3.5
    )

    assert "separator" in res.rejection_reason.lower() or "whp" in res.rejection_reason.lower()
