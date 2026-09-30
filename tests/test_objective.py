from src.schema import ScenarioResult
from src.objective import (
    evaluate_objective,
    normalize_metric,
    ObjectiveBreakdown
)

def create_mock_scenario(scenario_id: str, oil: float, steam: float, energy: float, risk: float, maint: float) -> ScenarioResult:
    return ScenarioResult(
        scenario_id=scenario_id,
        steam_mass_t=steam,
        soak_h=48,
        pump_speed_spm=7.0,
        stroke_length_m=2.5,
        expected_oil_bpd=oil,
        oil_rate_bpd=oil,
        sor=steam / max(1.0, (oil / 6.2898) * 60.0),
        energy_kwh_bbl=energy,
        pump_fillage_pct=75.0,
        srp_load_kn=45.0,
        pprl_kn=45.0,
        mprl_kn=15.0,
        rod_stress_pct=60.0,
        floating_risk=0.05,
        maintenance_risk=maint,
        risk_score=risk,
        feasible=True
    )

def test_objective_contribution_sum_equals_score():
    s1 = create_mock_scenario("S1", oil=45.0, steam=100.0, energy=20.0, risk=25.0, maint=15.0)

    score, breakdown = evaluate_objective(s1)
    assert isinstance(breakdown, ObjectiveBreakdown)
    
    # Sum of signed contributions should equal total_score within floating point precision
    contrib_sum = sum(c.signed_contribution for c in breakdown.contributions.values())
    assert abs(contrib_sum - breakdown.total_score) < 1e-3
    assert abs(score - breakdown.total_score) < 1e-3

def test_objective_weights_deterministic_response():
    s2 = create_mock_scenario("S2", oil=35.0, steam=120.0, energy=25.0, risk=40.0, maint=20.0)

    # Oil-heavy weight configuration
    score_oil_heavy, _ = evaluate_objective(
        s2, weights={"w_oil": 1.0, "w_steam": 0.05, "w_energy": 0.05, "w_risk": 0.05, "w_maint": 0.05}
    )

    # Steam-penalty-heavy weight configuration
    score_steam_heavy, _ = evaluate_objective(
        s2, weights={"w_oil": 0.2, "w_steam": 0.8, "w_energy": 0.1, "w_risk": 0.05, "w_maint": 0.05}
    )

    # When steam penalty is heavily weighted, the high-steam scenario should have a lower score
    assert score_oil_heavy > score_steam_heavy

def test_objective_safe_zero_denominator():
    # normalize_metric with min_val == max_val should safely return 0.0 and avoid ZeroDivisionError
    norm = normalize_metric(50.0, 50.0, 50.0)
    assert norm == 0.0

