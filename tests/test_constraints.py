import pytest
from src.schema import ScenarioResult
from src.constraints import apply_constraints, check_scenario_constraints

def test_constraints_rejections_and_exact_reasons():
    """Verify invalid scenarios are rejected with exact descriptive reasons."""
    limits = {
        "min_pump_fillage_pct": 52.0,
        "max_srp_load_kn": 62.0,
        "max_steam_mass_t": 118.0
    }

    # 1. High Load Scenario
    sc_high_load = ScenarioResult(
        scenario_id="TEST-HIGH-LOAD",
        steam_mass_t=100.0,
        soak_h=48,
        pump_speed_spm=7.0,
        stroke_length_m=1.55,
        temperature_c=60.0,
        viscosity_kcp=8.0,
        inflow_bpd=45.0,
        oil_rate_bpd=30.0,
        pump_fillage_pct=65.0,
        srp_load_kn=65.5,  # > 62.0 kN
        energy_kwh_bbl=16.0,
        risk_score=50.0
    )
    check1 = check_scenario_constraints(sc_high_load, limits=limits)
    assert not check1.feasible
    assert any("SRP load" in r and "exceeds configurable limit" in r for r in check1.rejection_reasons)

    # 2. Low Fillage Scenario
    sc_low_fillage = ScenarioResult(
        scenario_id="TEST-LOW-FILLAGE",
        steam_mass_t=100.0,
        soak_h=48,
        pump_speed_spm=8.0,
        stroke_length_m=1.55,
        temperature_c=60.0,
        viscosity_kcp=8.0,
        inflow_bpd=28.0,
        oil_rate_bpd=18.0,
        pump_fillage_pct=45.0,  # < 52.0%
        srp_load_kn=50.0,
        energy_kwh_bbl=15.0,
        risk_score=20.0
    )
    check2 = check_scenario_constraints(sc_low_fillage, limits=limits)
    assert not check2.feasible
    assert any("Pump fillage" in r and "below configurable minimum" in r for r in check2.rejection_reasons)

    # 3. High Steam Scenario
    sc_high_steam = ScenarioResult(
        scenario_id="TEST-HIGH-STEAM",
        steam_mass_t=122.0,  # > 118.0 t
        soak_h=48,
        pump_speed_spm=7.0,
        stroke_length_m=1.55,
        temperature_c=65.0,
        viscosity_kcp=6.5,
        inflow_bpd=50.0,
        oil_rate_bpd=35.0,
        pump_fillage_pct=70.0,
        srp_load_kn=45.0,
        energy_kwh_bbl=17.0,
        risk_score=15.0
    )
    check3 = check_scenario_constraints(sc_high_steam, limits=limits)
    assert not check3.feasible
    assert any("Steam input" in r and "exceeds prototype envelope" in r for r in check3.rejection_reasons)

    # 4. Valid Feasible Scenario
    sc_valid = ScenarioResult(
        scenario_id="TEST-FEASIBLE",
        steam_mass_t=106.0,
        soak_h=48,
        pump_speed_spm=7.0,
        stroke_length_m=1.55,
        temperature_c=62.0,
        viscosity_kcp=7.0,
        inflow_bpd=48.0,
        oil_rate_bpd=32.0,
        pump_fillage_pct=68.0,
        srp_load_kn=44.0,
        energy_kwh_bbl=15.5,
        risk_score=10.0
    )
    check4 = check_scenario_constraints(sc_valid, limits=limits)
    assert check4.feasible
    assert len(check4.rejection_reasons) == 0

def test_apply_constraints_splits_lists():
    """Verify apply_constraints correctly groups feasible and rejected."""
    from src.scenario_engine import generate_scenario_candidates
    all_sc, feas, rej = generate_scenario_candidates()
    assert len(all_sc) >= 60
    assert len(feas) > 0
    assert len(rej) > 0
    assert len(feas) + len(rej) == len(all_sc)
    for f in feas:
        assert f.feasible
        assert f.rejection_reason == ""
    for r in rej:
        assert not r.feasible
        assert len(r.rejection_reason) > 0
