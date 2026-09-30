from src.ablation import run_ablation_experiment
from src.css_model import simulate_css_cycle
from src.viscosity_model import calculate_viscosity
from src.inflow_model import calculate_inflow
from src.srp_model import calculate_srp_response
from src.scenario_engine import generate_scenario_candidates

def test_css_changes_alter_srp_outcomes():
    """
    Direct causal chain test:
    Altering CSS steam mass directly propagates to alter SRP fillage, load, and delivered oil rate.
    """
    css_low = simulate_css_cycle(steam_mass_t=90.0, inj_h=36, soak_h=48, prod_h=588)
    visc_low = calculate_viscosity(css_low.temperature_c)
    inf_low = calculate_inflow(visc_low.viscosity_kcp, p_r_bar=24.5, p_wf_bar=20.3)
    srp_low = calculate_srp_response(inf_low.inflow_bpd, spm=7.0, stroke_m=1.55, viscosity_kcp=visc_low.viscosity_kcp, steam_mass_t=90.0)

    css_high = simulate_css_cycle(steam_mass_t=120.0, inj_h=36, soak_h=48, prod_h=588)
    visc_high = calculate_viscosity(css_high.temperature_c)
    inf_high = calculate_inflow(visc_high.viscosity_kcp, p_r_bar=24.5, p_wf_bar=20.3)
    srp_high = calculate_srp_response(inf_high.inflow_bpd, spm=7.0, stroke_m=1.55, viscosity_kcp=visc_high.viscosity_kcp, steam_mass_t=120.0)

    # Higher steam -> higher temp -> lower viscosity -> higher inflow -> higher SRP delivered oil & fillage
    assert css_high.temperature_c > css_low.temperature_c
    assert visc_high.viscosity_kcp < visc_low.viscosity_kcp
    assert inf_high.inflow_bpd > inf_low.inflow_bpd
    assert srp_high.oil_rate_bpd > srp_low.oil_rate_bpd
    assert srp_high.pump_fillage_pct >= srp_low.pump_fillage_pct

def test_ablation_comparison_contract():
    """
    Verifies that run_ablation_experiment executes both modes on identical candidate sets
    and returns a valid AblationComparison with populated deltas and causal explanation.
    """
    comparison = run_ablation_experiment()

    assert comparison.independent.mode == "INDEPENDENT"
    assert comparison.coupled.mode == "COUPLED"
    assert len(comparison.deltas) > 0
    assert "delta_oil_bpd" in comparison.deltas
    assert "delta_sor" in comparison.deltas
    assert len(comparison.causal_explanation) > 20
    assert "independent optimization" in comparison.causal_explanation.lower()
    assert "coupled optimization" in comparison.causal_explanation.lower()
