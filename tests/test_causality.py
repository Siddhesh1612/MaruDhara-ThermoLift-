import pytest
from src.viscosity_model import calculate_viscosity
from src.inflow_model import calculate_inflow
from src.srp_model import calculate_srp_response

def test_temperature_viscosity_causality():
    """Verify T↑ => μ↓ across operating range."""
    temps = [45.0, 55.0, 65.0, 75.0, 85.0]
    viscosities = [calculate_viscosity(t).viscosity_kcp for t in temps]
    for i in range(len(viscosities) - 1):
        assert viscosities[i] > viscosities[i+1], (
            f"Viscosity monotonicity violated at T={temps[i]}: {viscosities[i]} <= {viscosities[i+1]}"
        )

def test_viscosity_inflow_causality():
    """Verify μ↓ => inflow↑ at constant drawdown."""
    viscosities = [14.0, 11.0, 8.0, 5.0]
    inflows = [calculate_inflow(v).inflow_bpd for v in viscosities]
    for i in range(len(inflows) - 1):
        assert inflows[i] < inflows[i+1], (
            f"Inflow monotonicity violated at μ={viscosities[i]}: {inflows[i]} >= {inflows[i+1]}"
        )

def test_inflow_srp_response_causality():
    """Verify inflow↑ => fillage↑ and load adjusts."""
    inflow_levels = [30.0, 45.0, 60.0, 75.0]
    responses = [calculate_srp_response(inf, spm=6.8, stroke_m=1.55) for inf in inflow_levels]
    fillages = [r.pump_fillage_pct for r in responses]
    for i in range(len(fillages) - 1):
        assert fillages[i] <= fillages[i+1], (
            f"Fillage monotonicity violated: {fillages[i]} > {fillages[i+1]}"
        )

def test_spm_energy_causality():
    """Verify SPM↑ => energy↑ at constant inflow."""
    spm_rates = [5.5, 6.5, 7.5, 8.5]
    energies = [calculate_srp_response(inflow_bpd=45.0, spm=s).energy_kwh_bbl for s in spm_rates]
    for i in range(len(energies) - 1):
        assert energies[i] < energies[i+1], (
            f"Energy monotonicity violated: {energies[i]} >= {energies[i+1]}"
        )
