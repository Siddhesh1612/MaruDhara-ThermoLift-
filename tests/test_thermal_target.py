from src.thermal_target import solve_minimum_steam

def test_thermal_target_temperature_feasibility():
    """
    Tests finding the minimum steam mass required to achieve a bottomhole temperature (e.g. 58 C).
    """
    res = solve_minimum_steam(
        target_type="TEMPERATURE",
        target_value=58.0,
        spm=7.0,
        stroke_m=1.55,
        soak_h=48
    )

    assert res.achieved is True
    assert res.min_feasible_steam_t is not None
    assert 70.0 <= res.min_feasible_steam_t <= 125.0
    assert res.temperature_c >= 57.5
    assert res.pump_fillage_pct >= 52.0  # Must satisfy SRP fillage constraint
    assert res.srp_load_kn <= 62.0      # Must satisfy SRP load constraint

def test_thermal_target_viscosity_feasibility():
    """
    Tests finding minimum steam to lower heavy oil viscosity to <= 8.5 kcP.
    """
    res = solve_minimum_steam(
        target_type="VISCOSITY",
        target_value=8.5,
        spm=7.0,
        stroke_m=1.55,
        soak_h=48
    )

    assert res.achieved is True
    assert res.min_feasible_steam_t is not None
    assert res.viscosity_kcp <= 8.55

def test_unachievable_thermal_target():
    """
    If operator requests physically impossible temperature (e.g. 350 C in low-steam prototype envelope),
    the solver must report achieved = False and explain the limiting constraint.
    """
    res = solve_minimum_steam(
        target_type="TEMPERATURE",
        target_value=350.0,
        spm=7.0,
        stroke_m=1.55,
        soak_h=48
    )

    assert res.achieved is False
    assert res.min_feasible_steam_t is None
    assert len(res.explanation) > 10
