import math
from typing import Any, Dict, List, Optional

from src.schema import Confidence, ScenarioResult, WellState

def evaluate_confidence(
    scenario: ScenarioResult,
    current_state: Optional[WellState] = None,
    physics_residual: float = 0.0
) -> Confidence:
    """
    Computes illustrative confidence score across 4 transparent dimensions:
    1. Input completeness (telemetry quality)
    2. Support-range distance (proximity to nominal operating domain)
    3. Physics residual (differential balance discrepancy)
    4. Extrapolation penalty (out-of-bounds parameter requests)

    Enforces an actionable uncertainty gate:
    - GREEN: High confidence, data quality GOOD, residual <= 2.5 C. Unrestricted advisory.
    - AMBER: Marginal confidence or SUSPECT data or 2.5 C < residual <= 4.5 C. Advisory flagged for operator review.
    - RED: FAIL data quality or residual > 4.5 C or confidence < 50%. Recommendation SUPPRESSED.
    """
    warnings = []
    penalty = 0.0

    # 1. Input Completeness
    completeness = 1.0
    data_quality = current_state.data_quality if current_state else "GOOD"
    if data_quality == "GOOD":
        completeness = 1.0
    elif data_quality == "SUSPECT":
        completeness = 0.80
        penalty += 0.20
        warnings.append("Input data quality is SUSPECT; confidence discounted by 20%.")
    else:  # FAIL
        completeness = 0.30
        penalty += 0.65
        warnings.append("Input data quality is FAIL; sensor telemetry untrusted.")

    # 2. Support-Range Distance
    # Nominal envelope: steam 90-122 t, soak 36-72 h, spm 6-8
    support_dist = 0.0
    if scenario.steam_mass_t < 90.0 or scenario.steam_mass_t > 122.0:
        dist_steam = max(90.0 - scenario.steam_mass_t, scenario.steam_mass_t - 122.0) / 32.0
        support_dist += dist_steam * 0.10

    if scenario.soak_h < 36 or scenario.soak_h > 72:
        dist_soak = max(36 - scenario.soak_h, scenario.soak_h - 72) / 36.0
        support_dist += dist_soak * 0.08

    if scenario.pump_speed_spm < 6.0 or scenario.pump_speed_spm > 8.0:
        dist_spm = max(6.0 - scenario.pump_speed_spm, scenario.pump_speed_spm - 8.0) / 2.0
        support_dist += dist_spm * 0.12

    penalty += support_dist
    if support_dist > 0.05:
        warnings.append(f"Operating point deviates from nominal model support envelope (distance={support_dist:.2f}).")

    # 3. Physics Residual
    # Normalized penalty based on discrepancy
    res_penalty = min(physics_residual / 5.0, 1.0) * 0.15
    penalty += res_penalty
    if physics_residual > 2.5:
        warnings.append(f"Elevated physics residual ({physics_residual:.2f} °C > 2.5 °C threshold).")

    # 4. Extrapolation Penalty
    extrap_penalty = 0.0
    if scenario.steam_mass_t > 125.0 or scenario.steam_mass_t < 80.0:
        extrap_penalty += 0.15
        warnings.append("High steam extrapolation beyond validated prototype bounds.")
    if scenario.pump_speed_spm > 9.0 or scenario.pump_speed_spm < 5.0:
        extrap_penalty += 0.15
        warnings.append("High pump speed extrapolation beyond validated SRP operating limits.")

    penalty += extrap_penalty

    # Raw confidence
    raw_confidence = max(0.0, 1.0 - penalty)
    confidence_pct = round(raw_confidence * 100.0, 1)

    # Uncertainty Gate Determination
    gate_state = "GREEN"
    gate_reason = "Recommendation eligible; sensor telemetry and physics residual within nominal envelope."
    recommendation_suppressed = False
    downgrade = False

    if data_quality == "FAIL" or physics_residual > 4.5 or confidence_pct < 50.0:
        gate_state = "RED"
        recommendation_suppressed = True
        downgrade = True
        reasons = []
        if data_quality == "FAIL":
            reasons.append("data telemetry quality is FAIL")
        if physics_residual > 4.5:
            reasons.append(f"physics residual {physics_residual:.1f}°C exceeds critical threshold 4.5°C")
        if confidence_pct < 50.0:
            reasons.append(f"overall confidence {confidence_pct}% is below minimum 50% threshold")
        gate_reason = f"RECOMMENDATION SUPPRESSED: {'; '.join(reasons)}. Human inspection mandatory."
        warnings.append("CRITICAL: Recommendation suppressed by uncertainty gate.")
    elif data_quality == "SUSPECT" or physics_residual > 2.5 or confidence_pct < 70.0 or support_dist > 0.15:
        gate_state = "AMBER"
        downgrade = True
        reasons = []
        if data_quality == "SUSPECT":
            reasons.append("sensor telemetry is SUSPECT")
        if physics_residual > 2.5:
            reasons.append(f"physics residual {physics_residual:.1f}°C elevated")
        if confidence_pct < 70.0:
            reasons.append(f"confidence {confidence_pct}% in advisory review zone")
        gate_reason = f"OPERATOR CAUTION: {'; '.join(reasons)}. Recommend field verification before approving."
        warnings.append("Recommendation downgraded: requires operator verification before approval.")

    return Confidence(
        confidence_pct=confidence_pct,
        input_completeness=round(completeness, 2),
        support_distance=round(support_dist, 3),
        physics_residual=round(physics_residual, 3),
        extrapolation_penalty=round(extrap_penalty, 3),
        gate_state=gate_state,
        gate_reason=gate_reason,
        recommendation_suppressed=recommendation_suppressed,
        downgrade_applied=downgrade,
        label="ILLUSTRATIVE PROTOTYPE CONFIDENCE",
        warnings=warnings
    )
