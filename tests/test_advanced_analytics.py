from src.schema import ScenarioResult, WellState
from src.sensitivity import run_sensitivity_analysis
from src.nearest_alternative import find_nearest_alternative
from src.residual_ml import hybrid_residual_predictor, ResidualMLPredictor

def test_sensitivity_analysis_execution():
    base = ScenarioResult(
        scenario_id="BASE",
        steam_mass_t=100.0,
        soak_h=48,
        pump_speed_spm=7.0,
        stroke_length_m=1.55,
        expected_oil_bpd=33.0,
        sor=0.7,
        energy_kwh_bbl=22.0,
        pump_fillage_pct=68.0,
        srp_load_kn=50.0,
        maintenance_risk=20.0,
        feasible=True
    )
    result = run_sensitivity_analysis(base, perturbation_pcts=[-10.0, 10.0])
    assert result.base_scenario_id == "BASE"
    assert len(result.items) > 0
    assert len(result.ranked_importance) > 0

def test_nearest_alternative_discovery():
    rec = ScenarioResult(
        scenario_id="REC",
        steam_mass_t=100.0,
        soak_h=48,
        pump_speed_spm=7.0,
        stroke_length_m=1.55,
        expected_oil_bpd=35.0,
        sor=0.68,
        energy_kwh_bbl=22.0,
        pump_fillage_pct=72.0,
        srp_load_kn=48.0,
        maintenance_risk=18.0,
        objective_score=0.25,
        feasible=True
    )
    alt = ScenarioResult(
        scenario_id="ALT",
        steam_mass_t=115.0,
        soak_h=60,
        pump_speed_spm=8.0,
        stroke_length_m=1.55,
        expected_oil_bpd=38.0,
        sor=0.72,
        energy_kwh_bbl=24.0,
        pump_fillage_pct=76.0,
        srp_load_kn=52.0,
        maintenance_risk=22.0,
        objective_score=0.22,
        feasible=True
    )
    res = find_nearest_alternative(rec, [rec, alt], min_distance_threshold=0.05)
    assert res is not None
    assert res.alternative.scenario_id == "ALT"
    assert res.decision_distance > 0.05
    assert len(res.trade_off_summary) > 10

def test_residual_ml_boundedness_and_fallback():
    predictor = ResidualMLPredictor(max_correction_c=4.0)
    # Unfitted predictor falls back cleanly to 0.0 correction
    correction_unfitted = predictor.predict_residual_correction(100.0, 48.0)
    assert correction_unfitted == 0.0

    # Fitted predictor produces bounded correction within [-4.0, +4.0] C
    predictor.fit_synthetic_baseline()
    correction_fitted = predictor.predict_residual_correction(120.0, 36.0)
    assert -4.0 <= correction_fitted <= 4.0

    hybrid_t, delta = predictor.get_hybrid_temperature(60.0, 120.0, 36.0)
    assert abs(hybrid_t - (60.0 + delta)) < 1e-4
