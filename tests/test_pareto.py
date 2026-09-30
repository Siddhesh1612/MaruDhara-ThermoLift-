import pytest
from src.schema import ScenarioResult
from src.pareto import dominates, compute_pareto_frontier

def create_candidate(cid: str, oil: float, steam: float, energy: float, risk: float, feasible: bool = True) -> ScenarioResult:
    return ScenarioResult(
        scenario_id=cid,
        steam_mass_t=steam,
        soak_h=48,
        pump_speed_spm=7.0,
        stroke_length_m=2.5,
        expected_oil_bpd=oil,
        sor=steam / max(1.0, (oil / 6.2898) * 60.0),
        energy_kwh_bbl=energy,
        pump_fillage_pct=75.0,
        srp_load_kn=45.0,
        pprl_kn=45.0,
        mprl_kn=15.0,
        rod_stress_pct=60.0,
        floating_risk=0.05,
        maintenance_risk=risk,
        feasible=feasible
    )

def test_dominance_axioms():
    # c1 is strictly better than c2 in oil, and equal in all other dimensions
    c1 = create_candidate("C1", oil=100.0, steam=100.0, energy=20.0, risk=0.1)
    c2 = create_candidate("C2", oil=80.0, steam=100.0, energy=20.0, risk=0.1)
    assert dominates(c1, c2) is True
    assert dominates(c2, c1) is False

    # Trade-off: c3 has higher oil, but uses more steam
    c3 = create_candidate("C3", oil=110.0, steam=120.0, energy=20.0, risk=0.1)
    assert dominates(c1, c3) is False
    assert dominates(c3, c1) is False

def test_pareto_frontier_computation():
    c1 = create_candidate("C1", oil=100.0, steam=90.0, energy=18.0, risk=0.1)  # Strong front
    c2 = create_candidate("C2", oil=80.0, steam=110.0, energy=25.0, risk=0.2)  # Strictly dominated by C1
    c3 = create_candidate("C3", oil=115.0, steam=105.0, energy=19.0, risk=0.12) # Trade-off with C1 (more oil, more steam)
    c4 = create_candidate("C4", oil=70.0, steam=125.0, energy=30.0, risk=0.3)  # Heavily dominated

    candidates = [c1, c2, c3, c4]
    frontier = compute_pareto_frontier(candidates)

    assert frontier.total_candidates == 4
    assert frontier.nondominated_count == 2  # C1 and C3 are nondominated
    
    nd_ids = {c.scenario_id for c in frontier.candidates if c.is_nondominated}
    assert nd_ids == {"C1", "C3"}
