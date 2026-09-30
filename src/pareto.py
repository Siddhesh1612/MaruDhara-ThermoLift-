from typing import List, Optional
from src.schema import ScenarioResult, ParetoCandidate, ParetoFrontierResult

def dominates(c1: ScenarioResult, c2: ScenarioResult) -> bool:
    """
    Checks if candidate c1 dominates c2 under 4 objectives:
    1. Maximize oil_rate_bpd (higher is better)
    2. Minimize steam_mass_t (lower is better)
    3. Minimize energy_kwh_bbl (lower is better)
    4. Minimize maintenance_risk (lower is better)

    c1 dominates c2 iff c1 is >= c2 in all objectives AND c1 > c2 in at least one objective.
    """
    better_or_equal = (
        c1.expected_oil_bpd >= c2.expected_oil_bpd and
        c1.steam_mass_t <= c2.steam_mass_t and
        c1.energy_kwh_bbl <= c2.energy_kwh_bbl and
        c1.maintenance_risk <= c2.maintenance_risk
    )

    strictly_better = (
        c1.expected_oil_bpd > c2.expected_oil_bpd or
        c1.steam_mass_t < c2.steam_mass_t or
        c1.energy_kwh_bbl < c2.energy_kwh_bbl or
        c1.maintenance_risk < c2.maintenance_risk
    )

    return better_or_equal and strictly_better

def compute_pareto_frontier(
    candidates: List[ScenarioResult],
    selected_scenario_id: Optional[str] = None
) -> ParetoFrontierResult:
    """
    Computes true multi-objective nondominated Pareto frontier across all feasible candidates.
    If infeasible candidates exist, they can be included or filtered; here we compute dominance
    across feasible candidates, marking any infeasible as dominated.
    """
    if not candidates:
        return ParetoFrontierResult(
            total_candidates=0,
            nondominated_count=0,
            selected_scenario_id=selected_scenario_id or "",
            candidates=[]
        )

    feasible_cands = [c for c in candidates if c.feasible]
    infeasible_cands = [c for c in candidates if not c.feasible]

    nondominated_set = set()

    for i, c1 in enumerate(feasible_cands):
        is_dominated = False
        for j, c2 in enumerate(feasible_cands):
            if i != j and dominates(c2, c1):
                is_dominated = True
                break
        if not is_dominated:
            nondominated_set.add(c1.scenario_id)

    pareto_candidates: List[ParetoCandidate] = []

    for c in candidates:
        is_nd = c.scenario_id in nondominated_set
        pareto_candidates.append(ParetoCandidate(
            scenario_id=c.scenario_id,
            oil_rate_bpd=round(c.expected_oil_bpd, 2),
            steam_mass_t=round(c.steam_mass_t, 2),
            energy_kwh_bbl=round(c.energy_kwh_bbl, 2),
            risk_score=round(c.maintenance_risk, 3),
            is_nondominated=is_nd,
            objective_score=round(c.objective_score, 4)
        ))

    # Determine default selected ID if not specified
    if not selected_scenario_id and candidates:
        # Pick the nondominated candidate with highest objective score
        nd_cands = [c for c in candidates if c.scenario_id in nondominated_set]
        if nd_cands:
            selected_scenario_id = max(nd_cands, key=lambda x: x.objective_score).scenario_id
        else:
            selected_scenario_id = candidates[0].scenario_id

    return ParetoFrontierResult(
        total_candidates=len(candidates),
        nondominated_count=len(nondominated_set),
        selected_scenario_id=selected_scenario_id,
        candidates=pareto_candidates
    )
