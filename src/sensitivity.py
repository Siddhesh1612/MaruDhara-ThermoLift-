from typing import List, Tuple, Dict, Optional
import copy
from src.schema import SensitivityItem, SensitivityAnalysisResult, ScenarioResult, WellState
from src.css_model import simulate_css_cycle
from src.viscosity_model import calculate_viscosity
from src.inflow_model import calculate_inflow
from src.srp_model import calculate_srp_response

def run_sensitivity_analysis(
    base_scenario: ScenarioResult,
    current_state: Optional[WellState] = None,
    perturbation_pcts: List[float] = [-20.0, -10.0, 10.0, 20.0]
) -> SensitivityAnalysisResult:
    """
    Performs deterministic One-At-A-Time (OAT) parameter sensitivity analysis around a base scenario.
    Evaluates how variations in controls and reservoir conditions alter key production & mechanical KPIs.
    """
    items: List[SensitivityItem] = []
    param_swings: Dict[str, float] = {}

    base_oil = max(0.1, base_scenario.expected_oil_bpd)
    base_sor = max(0.01, base_scenario.sor)
    base_fillage = max(1.0, base_scenario.pump_fillage_pct)
    base_load = max(1.0, base_scenario.srp_load_kn)
    base_energy = max(0.1, base_scenario.energy_kwh_bbl)
    base_risk = max(0.01, base_scenario.maintenance_risk)

    p_res = current_state.reservoir_pressure_bar if current_state else 24.5
    p_wf = current_state.bottomhole_pressure_bar if current_state else 20.3

    # Parameters to test
    param_configs = [
        ("steam_mass_t", base_scenario.steam_mass_t, 10.0),
        ("soak_h", float(base_scenario.soak_h), 6.0),
        ("pump_speed_spm", base_scenario.pump_speed_spm, 1.0),
        ("stroke_length_m", base_scenario.stroke_length_m, 0.2),
        ("reservoir_pressure_bar", p_res, 5.0),
    ]

    for param_name, base_val, min_val in param_configs:
        oil_min = float("inf")
        oil_max = float("-inf")

        for p_pct in perturbation_pcts:
            factor = 1.0 + (p_pct / 100.0)
            perturbed_val = max(min_val, base_val * factor)

            # Assign perturbed parameter
            steam = base_scenario.steam_mass_t
            soak = base_scenario.soak_h
            spm = base_scenario.pump_speed_spm
            stroke = base_scenario.stroke_length_m
            res_p = p_res

            if param_name == "steam_mass_t":
                steam = perturbed_val
            elif param_name == "soak_h":
                soak = int(round(perturbed_val))
            elif param_name == "pump_speed_spm":
                spm = perturbed_val
            elif param_name == "stroke_length_m":
                stroke = perturbed_val
            elif param_name == "reservoir_pressure_bar":
                res_p = perturbed_val

            # Authoritative physics evaluation
            css_res = simulate_css_cycle(
                steam_mass_t=steam,
                inj_h=36,
                soak_h=soak,
                prod_h=588
            )
            visc_res = calculate_viscosity(css_res.temperature_c)
            inf_res = calculate_inflow(
                viscosity_kcp=visc_res.viscosity_kcp,
                p_r_bar=res_p,
                p_wf_bar=p_wf
            )
            srp_res = calculate_srp_response(
                inflow_bpd=inf_res.inflow_bpd,
                spm=spm,
                stroke_m=stroke,
                viscosity_kcp=visc_res.viscosity_kcp,
                steam_mass_t=steam
            )

            # Key KPI calculation
            new_oil = max(0.0, srp_res.oil_rate_bpd)
            cum_oil_m3 = (new_oil / 6.2898) * 60.0
            new_sor = round(steam / max(cum_oil_m3, 0.1), 3)
            new_fillage = srp_res.pump_fillage_pct
            new_load = srp_res.srp_load_kn
            new_energy = srp_res.energy_kwh_bbl

            # Mechanical maintenance risk
            rod_stress = srp_res.card_features.get("rod_stress_pct", 65.0)
            stress_margin = max(0.0, (rod_stress - 70.0) / 30.0)
            underfill_margin = max(0.0, (75.0 - srp_res.pump_fillage_pct) / 25.0)
            new_risk = round(0.5 * stress_margin + 0.5 * underfill_margin, 3)

            # Percentage changes
            delta_oil_pct = round(((new_oil - base_oil) / base_oil) * 100.0, 2)
            delta_sor_pct = round(((new_sor - base_sor) / base_sor) * 100.0, 2)
            delta_fillage_pct = round(((new_fillage - base_fillage) / base_fillage) * 100.0, 2)
            delta_load_pct = round(((new_load - base_load) / base_load) * 100.0, 2)
            delta_energy_pct = round(((new_energy - base_energy) / base_energy) * 100.0, 2)
            delta_risk_pct = round(((new_risk - base_risk) / max(base_risk, 0.05)) * 100.0, 2)

            items.append(SensitivityItem(
                parameter=param_name,
                base_value=round(base_val, 2),
                perturbed_value=round(perturbed_val, 2),
                perturbation_pct=p_pct,
                delta_oil_pct=delta_oil_pct,
                delta_sor_pct=delta_sor_pct,
                delta_fillage_pct=delta_fillage_pct,
                delta_load_pct=delta_load_pct,
                delta_energy_pct=delta_energy_pct,
                delta_risk_pct=delta_risk_pct
            ))

            oil_min = min(oil_min, delta_oil_pct)
            oil_max = max(oil_max, delta_oil_pct)

        param_swings[param_name] = round(abs(oil_max - oil_min), 2)

    # Ranked importance by total oil swing
    ranked = sorted(param_swings.items(), key=lambda x: x[1], reverse=True)

    return SensitivityAnalysisResult(
        base_scenario_id=base_scenario.scenario_id,
        items=items,
        ranked_importance=ranked
    )
