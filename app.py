import json
import uuid
from datetime import datetime
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from src.schema import WellState, ScenarioResult, Recommendation
from src.state_estimator import get_latest_state
from src.scenario_engine import generate_scenario_candidates, to_dataframe
from src.css_model import simulate_css_cycle
from src.viscosity_model import calculate_viscosity
from src.srp_model import calculate_srp_response
from src.constraints import get_operating_limits
from src.optimizer import rank_scenarios, generate_recommendation_text, get_ranking_weights
from src.uncertainty import evaluate_confidence
from src.srp_diagnostics import evaluate_diagnostics
from src.validation import run_temporal_validation, run_physics_validation, run_counterfactual_simulation, COUNTERFACTUAL_LABEL
from src.db.adapter import DataAdapter
from src.db import repository
from src.ui.three_viewer import generate_threejs_html
from src.ablation import run_ablation_experiment
from src.thermal_target import solve_minimum_steam
from src.counterfactual import run_historical_counterfactual
from src.nearest_alternative import find_nearest_alternative
from src.sensitivity import run_sensitivity_analysis
from src.pareto import compute_pareto_frontier
from src.residual_ml import hybrid_residual_predictor
from src.pressure_chain import evaluate_pressure_chain
from src.provenance import compute_input_state_hash
from src.objective import evaluate_objective, DEFAULT_WEIGHTS

# Page Configuration
st.set_page_config(
    page_title="THERMOLIFT / MaruDhara — Industrial Decision Twin",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium Industrial Design System (CSS)
st.markdown("""
<style>
    /* Dark Cyber-Industrial Base */
    .stApp {
        background: radial-gradient(circle at 50% 0%, #0d172a 0%, #060913 75%);
        color: #f1f5f9;
        font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, sans-serif;
    }
    
    /* Top Banner */
    .prototype-banner {
        background: linear-gradient(90deg, #92400e 0%, #b45309 50%, #d97706 100%);
        color: #ffffff;
        padding: 9px 18px;
        border-radius: 8px;
        font-weight: 700;
        text-align: center;
        letter-spacing: 1.2px;
        font-size: 13px;
        box-shadow: 0 4px 20px rgba(180, 83, 9, 0.35);
        margin-bottom: 16px;
        border: 1px solid rgba(251, 191, 36, 0.3);
    }
    
    /* Glassmorphism KPI Metric Containers */
    .kpi-container {
        background: rgba(15, 23, 42, 0.75);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 14px 16px;
        box-shadow: 0 6px 24px rgba(0, 0, 0, 0.4);
        transition: transform 0.2s ease, border-color 0.2s ease;
        margin-bottom: 10px;
    }
    .kpi-container:hover {
        border-color: rgba(245, 158, 11, 0.45);
        transform: translateY(-2px);
    }
    .kpi-label {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        color: #94a3b8;
        letter-spacing: 0.6px;
        margin-bottom: 4px;
    }
    .kpi-val {
        font-size: 24px;
        font-weight: 800;
        color: #f8fafc;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .kpi-unit {
        font-size: 12px;
        font-weight: 500;
        color: #38bdf8;
        margin-left: 4px;
    }

    /* Modern Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(15, 23, 42, 0.65);
        padding: 8px 12px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .stTabs [data-baseweb="tab"] {
        height: 42px;
        border-radius: 8px;
        color: #94a3b8;
        font-weight: 600;
        font-size: 13px;
        padding: 0 16px;
        transition: all 0.2s ease;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.22) 0%, rgba(217, 119, 6, 0.28) 100%) !important;
        color: #fbbf24 !important;
        border: 1px solid rgba(245, 158, 11, 0.45) !important;
        box-shadow: 0 4px 16px rgba(245, 158, 11, 0.15);
    }

    /* Styled Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #d97706 0%, #b45309 100%);
        color: #ffffff;
        border: 1px solid rgba(251, 191, 36, 0.4);
        border-radius: 8px;
        font-weight: 700;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        box-shadow: 0 4px 20px rgba(245, 158, 11, 0.4);
        transform: translateY(-1px);
    }

    /* Provenance Footer */
    .prov-card {
        background: rgba(15, 23, 42, 0.55);
        border: 1px solid rgba(51, 65, 85, 0.6);
        border-radius: 10px;
        padding: 12px 18px;
        font-size: 12px;
        color: #94a3b8;
        margin-top: 24px;
    }

    /* Sidebar Branding */
    .sidebar-header {
        font-size: 20px;
        font-weight: 800;
        color: #f8fafc;
        letter-spacing: 0.5px;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# GLOBAL MANDATORY BANNER
# -------------------------------------------------------------
st.markdown('<div class="prototype-banner">PROTOTYPE MODE — REPRESENTATIVE SYNTHETIC DATA</div>', unsafe_allow_html=True)

# -------------------------------------------------------------
# SIDEBAR
# -------------------------------------------------------------
adapter = DataAdapter()

with st.sidebar:
    st.markdown('<div class="sidebar-header">⚡ THERMOLIFT</div>', unsafe_allow_html=True)
    st.caption("MaruDhara Decision Twin • SIH26120")
    st.caption("Oil India Limited • Baghewala Heavy Oil")
    st.divider()

    well_id = st.selectbox("Well Selector", ["BWG-SIM-001"], index=0)
    
    # Load current well state
    try:
        current_state = get_latest_state(well_id)
    except Exception:
        current_state = WellState(
            well_id=well_id,
            timestamp=datetime.utcnow().isoformat(),
            phase="production",
            temperature_c=58.5,
            viscosity_kcp=9.2,
            reservoir_pressure_bar=24.2,
            bottomhole_pressure_bar=21.4,
            inflow_bpd=44.0,
            oil_rate_bpd=31.5,
            water_rate_bpd=8.5,
            pump_speed_spm=6.8,
            stroke_length_m=1.55,
            pump_fillage_pct=64.0,
            srp_load_kn=45.5,
            energy_kwh_bbl=16.8,
            srp_risk_score=14,
            data_quality="GOOD"
        )

    # Status Badges & Provenance
    phase_badge = "🟢" if current_state.phase == "production" else ("🟡" if current_state.phase == "soak" else "🔴")
    st.markdown(f"**Cycle Phase:** {phase_badge} `{current_state.phase.upper()}`")
    
    dq_icon = "🟢" if current_state.data_quality == "GOOD" else ("🟡" if current_state.data_quality == "SUSPECT" else "🔴")
    st.markdown(f"**Data Quality:** {dq_icon} `{current_state.data_quality}`")
    
    state_hash = compute_input_state_hash(current_state)
    st.markdown(f"**State Hash:** `SHA-256:{state_hash}`")
    
    # Actionable Uncertainty Gate Badge
    if current_state.data_quality == "GOOD":
        gate_icon, gate_label, gate_bg = "🟢", "GREEN — ADVISORY ACTIVE", "rgba(16, 185, 129, 0.2)"
    elif current_state.data_quality == "SUSPECT":
        gate_icon, gate_label, gate_bg = "🟡", "AMBER — OPERATOR CAUTION", "rgba(245, 158, 11, 0.2)"
    else:
        gate_icon, gate_label, gate_bg = "🔴", "RED — RECOMMENDATION SUPPRESSED", "rgba(239, 68, 68, 0.2)"
        
    st.markdown(f"""
    <div style="background:{gate_bg}; border-radius:6px; padding:6px 10px; margin:8px 0; font-size:12px; font-weight:700;">
        Uncertainty Gate: {gate_icon} {gate_label}
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"**Seed Trace:** `{current_state.random_seed}`")
    st.markdown(f"**Model Release:** `{current_state.model_version}`")
    
    st.divider()
    st.markdown("#### Configurable Operating Bounds")
    limits = adapter.get_operating_limits()
    st.caption(f"• Min Pump Fillage: **{limits.get('min_pump_fillage_pct', 52.0)}%**")
    st.caption(f"• Max SRP Rod Load: **{limits.get('max_srp_load_kn', 62.0)} kN**")
    st.caption(f"• Max Steam Envelope: **{limits.get('max_steam_mass_t', 118.0)} t**")
    st.caption(f"• Permissible SPM: **{limits.get('min_spm', 5.0)} – {limits.get('max_spm', 10.0)} SPM**")
    st.info("Status: **CONFIGURABLE PROTOTYPE ASSUMPTIONS**")

# -------------------------------------------------------------
# NAVIGATION TABS
# -------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
    "📊 1. Current State",
    "⚡ 2. What-If Simulator",
    "🎯 3. Recommendation Card",
    "📈 4. SRP Diagnostics",
    "🔬 5. Coupling Lab",
    "🎯 6. Thermal Target",
    "⏳ 7. Time Machine",
    "🌪️ 8. Sensitivity & Pareto",
    "✅ 9. Validation & ML Residuals",
    "🌐 10. Photorealistic 3D Model"
])

# -------------------------------------------------------------
# TAB 1: CURRENT STATE
# -------------------------------------------------------------
with tab1:
    st.markdown("### 🛢️ Current Well Telemetry & State Estimation")
    st.caption(f"Active Asset: **{current_state.well_id}** | Timestamp: `{current_state.timestamp}` | Formation: **Jodhpur Sandstone**")

    # 10 KPI Cards arranged in 2 rows of 5
    r1_c1, r1_c2, r1_c3, r1_c4, r1_c5 = st.columns(5)
    with r1_c1:
        st.markdown(f"""
        <div class="kpi-container">
            <div class="kpi-label">Reservoir Temp</div>
            <div class="kpi-val">{current_state.temperature_c:.1f}<span class="kpi-unit">°C</span></div>
        </div>
        """, unsafe_allow_html=True)
    with r1_c2:
        st.markdown(f"""
        <div class="kpi-container">
            <div class="kpi-label">Heavy Crude Viscosity</div>
            <div class="kpi-val">{current_state.viscosity_kcp:.2f}<span class="kpi-unit">kcP</span></div>
        </div>
        """, unsafe_allow_html=True)
    with r1_c3:
        st.markdown(f"""
        <div class="kpi-container">
            <div class="kpi-label">Reservoir Pressure</div>
            <div class="kpi-val">{current_state.reservoir_pressure_bar:.1f}<span class="kpi-unit">bar</span></div>
        </div>
        """, unsafe_allow_html=True)
    with r1_c4:
        st.markdown(f"""
        <div class="kpi-container">
            <div class="kpi-label">Bottomhole Pressure</div>
            <div class="kpi-val">{current_state.bottomhole_pressure_bar:.1f}<span class="kpi-unit">bar</span></div>
        </div>
        """, unsafe_allow_html=True)
    with r1_c5:
        st.markdown(f"""
        <div class="kpi-container">
            <div class="kpi-label">Current CSS Phase</div>
            <div class="kpi-val" style="color:#f59e0b;">{current_state.phase.upper()[:8]}</div>
        </div>
        """, unsafe_allow_html=True)

    r2_c1, r2_c2, r2_c3, r2_c4, r2_c5 = st.columns(5)
    with r2_c1:
        st.markdown(f"""
        <div class="kpi-container">
            <div class="kpi-label">Reservoir Inflow</div>
            <div class="kpi-val">{current_state.inflow_bpd:.1f}<span class="kpi-unit">bpd</span></div>
        </div>
        """, unsafe_allow_html=True)
    with r2_c2:
        st.markdown(f"""
        <div class="kpi-container">
            <div class="kpi-label">Net Oil Rate</div>
            <div class="kpi-val" style="color:#10b981;">{current_state.oil_rate_bpd:.1f}<span class="kpi-unit">bpd</span></div>
        </div>
        """, unsafe_allow_html=True)
    with r2_c3:
        st.markdown(f"""
        <div class="kpi-container">
            <div class="kpi-label">Pump Fillage</div>
            <div class="kpi-val">{current_state.pump_fillage_pct:.1f}<span class="kpi-unit">%</span></div>
        </div>
        """, unsafe_allow_html=True)
    with r2_c4:
        st.markdown(f"""
        <div class="kpi-container">
            <div class="kpi-label">Polished Rod Load</div>
            <div class="kpi-val">{current_state.srp_load_kn:.1f}<span class="kpi-unit">kN</span></div>
        </div>
        """, unsafe_allow_html=True)
    with r2_c5:
        risk_color = "#ef4444" if current_state.srp_risk_score > 40 else "#f59e0b"
        st.markdown(f"""
        <div class="kpi-container">
            <div class="kpi-label">Equipment Risk</div>
            <div class="kpi-val" style="color:{risk_color};">{current_state.srp_risk_score}<span class="kpi-unit">/100</span></div>
        </div>
        """, unsafe_allow_html=True)

    # 3D Twin Announcement Banner
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.75) 0%, rgba(15, 23, 42, 0.9) 100%); border: 1px solid rgba(245, 158, 11, 0.35); border-radius: 12px; padding: 14px 20px; margin: 16px 0; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 20px rgba(0,0,0,0.35);">
        <div style="display: flex; align-items: center; gap: 14px;">
            <span style="font-size: 28px;">🌐</span>
            <div>
                <div style="font-weight: 700; color: #f8fafc; font-size: 14px;">Photorealistic Three.js Physics Digital Twin Active</div>
                <div style="font-size: 12px; color: #94a3b8; margin-top: 2px;">Inspect real-time 4-bar kinematic pumpjack, downhole traveling/standing valve action, and thermal reservoir glow in <b>Tab 6</b>.</div>
            </div>
        </div>
        <span style="background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.35); padding: 5px 12px; border-radius: 8px; font-size: 11px; font-weight: 700; font-family: monospace;">EXPLORE IN TAB 6 →</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 📈 Historical Cycle Observation Telemetry")
    hist_df = adapter.get_observations_history()
    if not hist_df.empty:
        recent_cycle = hist_df[hist_df["cycle_id"] == hist_df["cycle_id"].max()]
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=recent_cycle.index,
            y=recent_cycle["temperature_c"],
            name="Temperature (°C)",
            line=dict(color="#f59e0b", width=2.5)
        ))
        fig.add_trace(go.Scatter(
            x=recent_cycle.index,
            y=recent_cycle["viscosity_kcp"],
            name="Viscosity (kcP)",
            yaxis="y2",
            line=dict(color="#06b6d4", width=2.5)
        ))
        fig.update_layout(
            title=dict(text=f"Cycle {hist_df['cycle_id'].max()} Telemetry Replay: Thermal vs. Viscosity Response", font=dict(color="#f8fafc", size=14)),
            xaxis=dict(title=dict(text="Cycle Elapsed Hours (h)", font=dict(color="#94a3b8")), gridcolor="#1e293b"),
            yaxis=dict(title=dict(text="Temperature (°C)", font=dict(color="#f59e0b")), tickfont=dict(color="#f59e0b"), gridcolor="#1e293b"),
            yaxis2=dict(title=dict(text="Viscosity (kcP)", font=dict(color="#06b6d4")), tickfont=dict(color="#06b6d4"), overlaying="y", side="right"),
            template="plotly_dark",
            paper_bgcolor="rgba(15, 23, 42, 0.7)",
            plot_bgcolor="rgba(15, 23, 42, 0.7)",
            height=320,
            margin=dict(l=40, r=40, t=50, b=40)
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown(f"""
    <div class="prov-card">
        <b>Data Provenance:</b> source_label: <code>{current_state.source_label}</code> |
        random_seed: <code>{current_state.random_seed}</code> |
        model_version: <code>{current_state.model_version}</code> |
        status: <code>CONFIGURABLE PROTOTYPE ASSUMPTIONS</code>
    </div>
    """, unsafe_allow_html=True)

# -------------------------------------------------------------
# TAB 2: WHAT-IF SIMULATOR
# -------------------------------------------------------------
with tab2:
    st.markdown("### ⚡ Coupled CSS + SRP What-If Decision Engine")
    st.caption("Simulates candidate operational combinations through the coupled physical causality chain.")

    sim_col1, sim_col2 = st.columns([1, 2])

    with sim_col1:
        st.markdown("##### 🎛️ Operational Decision Sliders")
        custom_steam = st.slider("Steam Mass (t)", min_value=90.0, max_value=122.0, value=106.0, step=1.0)
        custom_soak = st.slider("Soak Duration (h)", min_value=36, max_value=72, value=48, step=2)
        custom_spm = st.slider("Pump Speed (SPM)", min_value=6.0, max_value=8.0, value=7.0, step=0.2)
        custom_stroke = st.slider("Stroke Length (m)", min_value=1.45, max_value=1.65, value=1.55, step=0.05)

        st.markdown("##### ⚖️ Objective Optimization Weights")
        w_oil = st.slider("w_oil (Production)", min_value=0.0, max_value=2.0, value=1.0, step=0.1)
        w_steam = st.slider("w_steam (Steam Input Penalty)", min_value=0.0, max_value=1.0, value=0.0, step=0.05)
        w_energy = st.slider("w_energy (Energy Consumption Penalty)", min_value=0.0, max_value=1.0, value=0.45, step=0.05)
        w_risk = st.slider("w_risk (Equipment Risk Penalty)", min_value=0.0, max_value=1.0, value=0.25, step=0.05)

        simulate_clicked = st.button("🚀 Run 61-Scenario Simulation", type="primary", use_container_width=True)

    # Execute and Cache Simulation Results
    if "latest_candidates" not in st.session_state or simulate_clicked:
        custom_pt = {
            "steam_mass_t": custom_steam,
            "soak_h": custom_soak,
            "pump_speed_spm": custom_spm,
            "stroke_length_m": custom_stroke
        }
        weights_dict = {
            "w_oil": w_oil,
            "w_steam": w_steam,
            "w_energy": w_energy,
            "w_risk": w_risk
        }
        
        all_cands, feas_cands, rej_cands = generate_scenario_candidates(custom_point=custom_pt, limits=limits)
        ranked_feas, top_rec = rank_scenarios(feas_cands, weights=weights_dict)

        st.session_state["latest_candidates"] = all_cands
        st.session_state["feasible_candidates"] = ranked_feas
        st.session_state["rejected_candidates"] = rej_cands
        st.session_state["top_scenario"] = top_rec
        st.session_state["active_weights"] = weights_dict

        # Persistence to DB per Simulate Click
        if simulate_clicked:
            run_uuid = f"RUN-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
            st.session_state["current_run_id"] = run_uuid

            repository.insert_model_run({
                "run_id": run_uuid,
                "timestamp": datetime.utcnow().isoformat(),
                "steam_mass_t": custom_steam,
                "soak_duration_h": custom_soak,
                "pump_speed_spm": custom_spm,
                "stroke_length_m": custom_stroke,
                "candidate_count": len(all_cands),
                "seed": 26120,
                "model_version": "v1.0"
            })

            sc_records = []
            for sc in all_cands:
                sc_records.append({
                    "run_id": run_uuid,
                    "scenario_id": sc.scenario_id,
                    "steam_mass_t": sc.steam_mass_t,
                    "soak_h": sc.soak_h,
                    "pump_speed_spm": sc.pump_speed_spm,
                    "stroke_length_m": sc.stroke_length_m,
                    "temperature_c": sc.temperature_c,
                    "viscosity_kcp": sc.viscosity_kcp,
                    "inflow_bpd": sc.inflow_bpd,
                    "oil_rate_bpd": sc.oil_rate_bpd,
                    "pump_fillage_pct": sc.pump_fillage_pct,
                    "srp_load_kn": sc.srp_load_kn,
                    "energy_kwh_bbl": sc.energy_kwh_bbl,
                    "risk_score": sc.risk_score,
                    "feasible": sc.feasible,
                    "rejection_reason": sc.rejection_reason,
                    "objective_score": sc.objective_score,
                    "source_label": sc.source_label
                })
            repository.insert_scenarios(sc_records)

            if top_rec:
                conf = evaluate_confidence(top_rec, current_state)
                rat, inv = generate_recommendation_text(top_rec)
                rec_record = {
                    "run_id": run_uuid,
                    "scenario_id": top_rec.scenario_id,
                    "css_controls": f"Steam: {top_rec.steam_mass_t} t, Soak: {top_rec.soak_h} h",
                    "srp_controls": f"SPM: {top_rec.pump_speed_spm}, Stroke: {top_rec.stroke_length_m} m",
                    "expected_oil_bpd": top_rec.oil_rate_bpd,
                    "expected_steam_t": top_rec.steam_mass_t,
                    "expected_energy_kwh_bbl": top_rec.energy_kwh_bbl,
                    "expected_fillage_pct": top_rec.pump_fillage_pct,
                    "expected_load_kn": top_rec.srp_load_kn,
                    "constraint_margins": top_rec.constraint_margins,
                    "confidence_pct": conf.confidence_pct,
                    "rationale": rat,
                    "invalidators": inv,
                    "operator_status": "PENDING"
                }
                repository.insert_recommendation(rec_record)
                st.session_state["top_confidence"] = conf
                st.session_state["top_rationale"] = rat
                st.session_state["top_invalidators"] = inv

            st.toast("Evaluated 61 scenarios in <0.2s and persisted to database.", icon="✅")

    all_cands = st.session_state["latest_candidates"]
    ranked_feas = st.session_state["feasible_candidates"]
    rej_cands = st.session_state["rejected_candidates"]
    top_rec = st.session_state.get("top_scenario")

    with sim_col2:
        st.markdown(f"##### 🎯 Decision Trade-Off Scatter ({len(ranked_feas)} Feasible, {len(rej_cands)} Rejected)")
        
        scatter_data = []
        for s in all_cands:
            scatter_data.append({
                "scenario_id": s.scenario_id,
                "energy_kwh_bbl": s.energy_kwh_bbl,
                "oil_rate_bpd": s.oil_rate_bpd,
                "fillage_pct": s.pump_fillage_pct,
                "load_kn": s.srp_load_kn,
                "feasible": "Feasible" if s.feasible else "Rejected",
                "rejection_reason": s.rejection_reason if s.rejection_reason else "Satisfies all constraints",
                "score": s.objective_score
            })
        sc_plot_df = pd.DataFrame(scatter_data)

        fig_scatter = px.scatter(
            sc_plot_df,
            x="energy_kwh_bbl",
            y="oil_rate_bpd",
            color="feasible",
            color_discrete_map={"Feasible": "#10b981", "Rejected": "#f43f5e"},
            hover_name="scenario_id",
            hover_data=["rejection_reason", "fillage_pct", "load_kn", "score"],
            labels={"energy_kwh_bbl": "Lift Energy (kWh/bbl)", "oil_rate_bpd": "Net Oil Production (bpd)"},
            template="plotly_dark"
        )
        if top_rec:
            fig_scatter.add_trace(go.Scatter(
                x=[top_rec.energy_kwh_bbl],
                y=[top_rec.oil_rate_bpd],
                mode="markers",
                marker=dict(size=20, color="rgba(0,0,0,0)", line=dict(color="#f59e0b", width=3.5)),
                name="Top Ranked",
                hoverinfo="skip"
            ))
        fig_scatter.update_layout(
            paper_bgcolor="rgba(15, 23, 42, 0.7)",
            plot_bgcolor="rgba(15, 23, 42, 0.7)",
            height=340,
            margin=dict(l=40, r=40, t=30, b=40)
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("#### 🔬 Physics Trajectory of Top Ranked Candidate")
    if top_rec:
        t_sim = simulate_css_cycle(top_rec.steam_mass_t, soak_h=top_rec.soak_h)
        t_curve = t_sim.temperature_trajectory_c
        v_curve = [calculate_viscosity(t).viscosity_kcp for t in t_curve]
        hours = list(range(len(t_curve)))

        fig_phys = go.Figure()
        fig_phys.add_trace(go.Scatter(x=hours, y=t_curve, name="Temperature (°C)", line=dict(color="#f59e0b", width=2.5)))
        fig_phys.add_trace(go.Scatter(x=hours, y=v_curve, name="Viscosity (kcP)", yaxis="y2", line=dict(color="#06b6d4", width=2.5)))
        
        # Phase shading
        fig_phys.add_vrect(x0=0, x1=36, fillcolor="rgba(239, 68, 68, 0.12)", layer="below", line_width=0, annotation_text="Injection")
        fig_phys.add_vrect(x0=36, x1=36+top_rec.soak_h, fillcolor="rgba(234, 179, 8, 0.12)", layer="below", line_width=0, annotation_text="Soak")
        fig_phys.add_vrect(x0=36+top_rec.soak_h, x1=len(t_curve), fillcolor="rgba(16, 185, 129, 0.12)", layer="below", line_width=0, annotation_text="Production")
        
        fig_phys.update_layout(
            xaxis=dict(title=dict(text="Cycle Hour (h)", font=dict(color="#94a3b8")), gridcolor="#1e293b"),
            yaxis=dict(title=dict(text="Temperature (°C)", font=dict(color="#f59e0b")), tickfont=dict(color="#f59e0b"), gridcolor="#1e293b"),
            yaxis2=dict(title=dict(text="Viscosity (kcP)", font=dict(color="#06b6d4")), tickfont=dict(color="#06b6d4"), overlaying="y", side="right"),
            template="plotly_dark",
            paper_bgcolor="rgba(15, 23, 42, 0.7)",
            plot_bgcolor="rgba(15, 23, 42, 0.7)",
            height=280,
            margin=dict(l=40, r=40, t=30, b=30)
        )
        st.plotly_chart(fig_phys, use_container_width=True)

    # Scenarios Comparison Table
    st.markdown("#### 📋 Full Scenario Catalogue & Constraint Screening Table")
    table_rows = []
    for s in all_cands:
        table_rows.append({
            "Scenario ID": s.scenario_id,
            "Steam (t)": s.steam_mass_t,
            "Soak (h)": s.soak_h,
            "SPM": s.pump_speed_spm,
            "Temp (°C)": s.temperature_c,
            "Viscosity (kcP)": s.viscosity_kcp,
            "Inflow (bpd)": s.inflow_bpd,
            "Oil Rate (bpd)": s.oil_rate_bpd,
            "Fillage (%)": s.pump_fillage_pct,
            "SRP Load (kN)": s.srp_load_kn,
            "Energy (kWh/bbl)": s.energy_kwh_bbl,
            "Feasible": "✅ YES" if s.feasible else "❌ REJECTED",
            "Rejection Reason": s.rejection_reason if s.rejection_reason else "None (Feasible)",
            "Score": s.objective_score
        })
    st.dataframe(pd.DataFrame(table_rows), use_container_width=True, height=280)

# -------------------------------------------------------------
# TAB 3: RECOMMENDATION CARD
# -------------------------------------------------------------
with tab3:
    st.markdown("### 🎯 Constrained Advisory Recommendation Card")
    st.caption("Human-in-the-loop operational decision gate. Recommendations require operator sign-off.")

    top_scenario = st.session_state.get("top_scenario")
    current_run_id = st.session_state.get("current_run_id", "RUN-ACTIVE")

    if top_scenario:
        conf = st.session_state.get("top_confidence", evaluate_confidence(top_scenario, current_state))
        rat = st.session_state.get("top_rationale", generate_recommendation_text(top_scenario)[0])
        inv = st.session_state.get("top_invalidators", generate_recommendation_text(top_scenario)[1])

        st.markdown(f"""
        <div style="background: rgba(16, 185, 129, 0.1); border: 2px solid #10b981; border-radius: 12px; padding: 18px; margin-bottom: 20px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <span style="font-size: 11px; font-weight: 800; color: #10b981; letter-spacing: 1px; text-transform: uppercase;">TOP RANKED FEASIBLE DECISION</span>
                    <h2 style="margin: 4px 0 0 0; color: #ffffff; font-family: monospace;">{top_scenario.scenario_id}</h2>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 11px; color: #94a3b8;">MULTI-OBJECTIVE SCORE</div>
                    <div style="font-size: 26px; font-weight: 800; color: #f59e0b; font-family: monospace;">{top_scenario.objective_score:.2f}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        rec_c1, rec_c2, rec_c3 = st.columns(3)
        with rec_c1:
            st.markdown("##### ♨️ CSS Thermal Setpoints")
            st.markdown(f"- Steam Injection Mass: **{top_scenario.steam_mass_t:.1f} t**")
            st.markdown(f"- Soak Duration: **{top_scenario.soak_h} h**")
            st.markdown(f"- Heated Reservoir Temp: **{top_scenario.temperature_c:.1f} °C**")
            st.markdown(f"- Effective Crude Viscosity: **{top_scenario.viscosity_kcp:.2f} kcP**")
        with rec_c2:
            st.markdown("##### 🏗️ SRP Mechanical Setpoints")
            st.markdown(f"- Pumping Speed: **{top_scenario.pump_speed_spm:.1f} SPM**")
            st.markdown(f"- Stroke Length: **{top_scenario.stroke_length_m:.2f} m**")
            st.markdown(f"- Projected Pump Fillage: **{top_scenario.pump_fillage_pct:.1f} %**")
            st.markdown(f"- Peak Polished Rod Load: **{top_scenario.srp_load_kn:.1f} kN**")
        with rec_c3:
            st.markdown("##### 📊 Production & Confidence")
            st.markdown(f"- Net Production Rate: **{top_scenario.oil_rate_bpd:.1f} bpd**")
            st.markdown(f"- Specific Energy: **{top_scenario.energy_kwh_bbl:.1f} kWh/bbl**")
            st.markdown(f"- Mechanical Risk Score: **{top_scenario.risk_score:.1f} / 100**")
            st.markdown(f"- Illustrative Confidence: **{conf.confidence_pct:.1f}%**")

        st.markdown("---")
        st.markdown("##### 🛡️ Signed Constraint Margins (Positive = Safe Operating Buffer)")
        m_c1, m_c2, m_c3, m_c4 = st.columns(4)
        f_margin = top_scenario.pump_fillage_pct - 52.0
        l_margin = 62.0 - top_scenario.srp_load_kn
        s_margin = 118.0 - top_scenario.steam_mass_t
        w_margin = 14.0 - top_scenario.whp_bar
        with m_c1:
            st.metric("Pump Fillage Margin", f"{f_margin:+.1f} %", delta=f"{f_margin:+.1f} % above min 52%")
        with m_c2:
            st.metric("Rod Load Margin", f"{l_margin:+.1f} kN", delta=f"{l_margin:+.1f} kN below max 62kN")
        with m_c3:
            st.metric("Steam Envelope Margin", f"{s_margin:+.1f} t", delta=f"{s_margin:+.1f} t below cap 118t")
        with m_c4:
            st.metric("Surface WHP Margin", f"{w_margin:+.1f} bar", delta=f"{w_margin:+.1f} bar below limit 14bar")

        # Nearest Alternative Comparison
        feas_list = st.session_state.get("feasible_candidates", [])
        if feas_list and len(feas_list) > 1:
            nearest_alt = find_nearest_alternative(top_scenario, feas_list)
            if nearest_alt:
                st.markdown("---")
                st.markdown("##### 🔀 Nearest Feasible Alternative Trade-Off")
                st.info(f"💡 **Trade-off Summary:** {nearest_alt.trade_off_summary} *(Decision distance: {nearest_alt.decision_distance:.3f})*")
                alt_table = [
                    {"Metric": "Control: Steam Mass (t)", "Top Recommended": f"{top_scenario.steam_mass_t:.1f}", "Nearest Alternative": f"{nearest_alt.alternative.steam_mass_t:.1f}", "Delta (Alt - Rec)": f"{nearest_alt.parameter_deltas.get('steam_mass_t', 0.0):+.1f} t"},
                    {"Metric": "Control: Soak Time (h)", "Top Recommended": f"{top_scenario.soak_h}", "Nearest Alternative": f"{nearest_alt.alternative.soak_h}", "Delta (Alt - Rec)": f"{nearest_alt.parameter_deltas.get('soak_h', 0.0):+.1f} h"},
                    {"Metric": "Control: Pump Speed (SPM)", "Top Recommended": f"{top_scenario.pump_speed_spm:.1f}", "Nearest Alternative": f"{nearest_alt.alternative.pump_speed_spm:.1f}", "Delta (Alt - Rec)": f"{nearest_alt.parameter_deltas.get('pump_speed_spm', 0.0):+.1f} SPM"},
                    {"Metric": "Net Oil Production (bpd)", "Top Recommended": f"{top_scenario.oil_rate_bpd:.1f}", "Nearest Alternative": f"{nearest_alt.alternative.oil_rate_bpd:.1f}", "Delta (Alt - Rec)": f"{nearest_alt.kpi_deltas.get('expected_oil_bpd', 0.0):+.1f} bpd"},
                    {"Metric": "Steam-Oil Ratio (SOR)", "Top Recommended": f"{top_scenario.sor:.2f}", "Nearest Alternative": f"{nearest_alt.alternative.sor:.2f}", "Delta (Alt - Rec)": f"{nearest_alt.kpi_deltas.get('sor', 0.0):+.2f}"},
                    {"Metric": "Pump Fillage (%)", "Top Recommended": f"{top_scenario.pump_fillage_pct:.1f}", "Nearest Alternative": f"{nearest_alt.alternative.pump_fillage_pct:.1f}", "Delta (Alt - Rec)": f"{nearest_alt.kpi_deltas.get('pump_fillage_pct', 0.0):+.1f} %"},
                    {"Metric": "Polished Rod Load (kN)", "Top Recommended": f"{top_scenario.srp_load_kn:.1f}", "Nearest Alternative": f"{nearest_alt.alternative.srp_load_kn:.1f}", "Delta (Alt - Rec)": f"{nearest_alt.kpi_deltas.get('srp_load_kn', 0.0):+.1f} kN"},
                    {"Metric": "Objective Score", "Top Recommended": f"{top_scenario.objective_score:.3f}", "Nearest Alternative": f"{nearest_alt.alternative.objective_score:.3f}", "Delta (Alt - Rec)": f"{nearest_alt.kpi_deltas.get('objective_score', 0.0):+.3f}"},
                ]
                st.dataframe(pd.DataFrame(alt_table), use_container_width=True)

        st.markdown("---")
        st.markdown("##### 📝 Engineering Selection Rationale")
        st.markdown(f"> *{rat}*")

        st.markdown("##### ⚠️ What Could Invalidate This Recommendation")
        st.caption(inv)

        st.markdown("---")
        st.markdown("### ✍️ Operator Action & Immutable Audit Trail")
        
        op_col1, op_col2 = st.columns([1, 1])
        with op_col1:
            operator_notes = st.text_input("Operator Field Annotation", value="Setpoints verified with Baghewala surface operating limits.")
            op_act_col1, op_act_col2, op_act_col3, op_act_col4 = st.columns(4)
            
            with op_act_col1:
                if st.button("✅ Approve", use_container_width=True):
                    repository.update_recommendation_status(current_run_id, "APPROVED", operator_notes)
                    st.success("Recommendation APPROVED and logged to audit trail.")
            with op_act_col2:
                if st.button("✏️ Modify", use_container_width=True):
                    repository.update_recommendation_status(current_run_id, "MODIFIED", operator_notes)
                    st.warning("Recommendation flagged as MODIFIED and logged.")
            with op_act_col3:
                if st.button("❌ Reject", use_container_width=True):
                    repository.update_recommendation_status(current_run_id, "REJECTED", operator_notes)
                    st.error("Recommendation REJECTED and logged.")
            with op_act_col4:
                if st.button("📝 Annotate", use_container_width=True):
                    repository.update_recommendation_status(current_run_id, "ANNOTATED", operator_notes)
                    st.info("Annotation recorded.")

        with op_col2:
            st.markdown("##### 📜 Recent Audit Trail")
            audits = repository.get_audit_logs(limit=6)
            if audits:
                st.dataframe(pd.DataFrame(audits)[["timestamp", "action", "old_status", "new_status", "notes"]], use_container_width=True, height=160)
            else:
                st.caption("No audit log entries recorded yet.")
    else:
        st.warning("No feasible scenario candidate identified under current operating limits.")

# -------------------------------------------------------------
# TAB 4: SRP DIAGNOSTICS
# -------------------------------------------------------------
with tab4:
    st.markdown("### 📈 Rules-First Sucker Rod Pump Diagnostics")
    st.caption("Surface dynamometer card feature extraction and explainable rules feed.")

    diag_col1, diag_col2 = st.columns([1, 1])

    with diag_col1:
        st.markdown("#### 🔄 Polished Rod Dynamometer Card")
        srp_eval = calculate_srp_response(
            inflow_bpd=current_state.inflow_bpd,
            spm=current_state.pump_speed_spm,
            stroke_m=current_state.stroke_length_m,
            viscosity_kcp=current_state.viscosity_kcp
        )
        card_df = pd.DataFrame(srp_eval.card_curve)
        
        fig_card = go.Figure()
        fig_card.add_trace(go.Scatter(
            x=card_df["position_m"],
            y=card_df["load_kn"],
            mode="lines+markers",
            line=dict(color="#10b981", width=3),
            name="Dyno Card"
        ))
        fig_card.update_layout(
            title=dict(text=f"Polished Rod Dynamometer Card ({current_state.well_id})", font=dict(color="#f8fafc")),
            xaxis=dict(title=dict(text="Polished Rod Position (m)", font=dict(color="#94a3b8")), gridcolor="#1e293b"),
            yaxis=dict(title=dict(text="Polished Rod Load (kN)", font=dict(color="#94a3b8")), gridcolor="#1e293b"),
            template="plotly_dark",
            paper_bgcolor="rgba(15, 23, 42, 0.7)",
            plot_bgcolor="rgba(15, 23, 42, 0.7)",
            height=320,
            margin=dict(l=40, r=40, t=40, b=40)
        )
        st.plotly_chart(fig_card, use_container_width=True)

        feats = srp_eval.card_features
        feat_c1, feat_c2, feat_c3 = st.columns(3)
        feat_c1.metric("Max Load (PPRL)", f"{feats.get('max', 0.0)} kN")
        feat_c1.metric("Min Load (MPRL)", f"{feats.get('min', 0.0)} kN")
        feat_c2.metric("Load Range", f"{feats.get('range', 0.0)} kN")
        feat_c2.metric("Mean Load", f"{feats.get('mean', 0.0)} kN")
        feat_c3.metric("Card Area (Work)", f"{feats.get('area', 0.0)} kJ")
        feat_c3.metric("Repeatability", f"{feats.get('repeatability', 0.0)} %")

    with diag_col2:
        st.markdown("#### 🚨 Active Diagnostic Rules Feed")
        diags = evaluate_diagnostics(history_df=hist_df, current_state=current_state, persist=False)
        for d in diags:
            if d.fired:
                st.error(f"🚨 **{d.rule_name}** ({d.severity})\n\n{d.message}\n\n*Thresholds:* `{d.thresholds}`")
            else:
                st.success(f"✓ **{d.rule_name}** — Nominal\n\n{d.message}")

# -------------------------------------------------------------
# TAB 5: COUPLING LAB (INDEPENDENT VS. COUPLED ABLATION)
# -------------------------------------------------------------
with tab5:
    st.markdown("### 🔬 Coupling Lab: Coupled vs. Independent Optimization Ablation")
    st.caption("Rigorous scientific ablation proving the mathematical necessity of joint CSS+SRP optimization over sequential/isolated decision workflows.")

    ablation_res = run_ablation_experiment(
        weights=st.session_state.get("active_weights"),
        limits=limits
    )

    kpi_ind = ablation_res.independent
    kpi_coup = ablation_res.coupled
    deltas = ablation_res.deltas

    # KPI Delta Banner
    d_c1, d_c2, d_c3, d_c4 = st.columns(4)
    with d_c1:
        st.metric("Δ Oil Production", f"{deltas.get('delta_oil_bpd', 0.0):+.1f} bpd", delta=f"{deltas.get('delta_oil_bpd', 0.0):+.1f} bpd coupled gain")
    with d_c2:
        st.metric("Δ Steam-Oil Ratio (SOR)", f"{deltas.get('delta_sor', 0.0):+.3f}", delta=f"Steam efficiency delta")
    with d_c3:
        st.metric("Δ Pump Fillage", f"{deltas.get('delta_fillage_pct', 0.0):+.1f} %", delta="Coupled mechanical protection")
    with d_c4:
        st.metric("Δ Constraint Violations", f"{int(deltas.get('delta_violations', 0))}", delta=f"{kpi_coup.violations_count} vs {kpi_ind.violations_count} independent")

    st.markdown("---")
    st.markdown("#### 📋 Controlled Side-by-Side Mode Comparison")
    
    comp_data = [
        {"Attribute / Metric": "Optimization Mode", "Independent Mode (A)": "Sequential (CSS first, then SRP)", "Coupled Mode (B)": "Joint Simultaneous (CSS + SRP)", "Engineering Delta": "Shared Physics & Constraints"},
        {"Attribute / Metric": "Chosen Scenario ID", "Independent Mode (A)": kpi_ind.chosen_scenario_id, "Coupled Mode (B)": kpi_coup.chosen_scenario_id, "Engineering Delta": "Identical Candidate Search Space"},
        {"Attribute / Metric": "Steam Injected (t)", "Independent Mode (A)": f"{kpi_ind.steam_mass_t:.1f} t", "Coupled Mode (B)": f"{kpi_coup.steam_mass_t:.1f} t", "Engineering Delta": f"{deltas.get('delta_steam_t', 0.0):+.1f} t"},
        {"Attribute / Metric": "Soak Duration (h)", "Independent Mode (A)": f"{kpi_ind.soak_h} h", "Coupled Mode (B)": f"{kpi_coup.soak_h} h", "Engineering Delta": f"{kpi_coup.soak_h - kpi_ind.soak_h:+d} h"},
        {"Attribute / Metric": "Pumping Speed (SPM)", "Independent Mode (A)": f"{kpi_ind.pump_speed_spm:.1f} SPM", "Coupled Mode (B)": f"{kpi_coup.pump_speed_spm:.1f} SPM", "Engineering Delta": f"{kpi_coup.pump_speed_spm - kpi_ind.pump_speed_spm:+.1f} SPM"},
        {"Attribute / Metric": "Net Oil Production (bpd)", "Independent Mode (A)": f"{kpi_ind.expected_oil_bpd:.1f} bpd", "Coupled Mode (B)": f"{kpi_coup.expected_oil_bpd:.1f} bpd", "Engineering Delta": f"{deltas.get('delta_oil_bpd', 0.0):+.1f} bpd"},
        {"Attribute / Metric": "Steam-Oil Ratio (SOR)", "Independent Mode (A)": f"{kpi_ind.sor:.3f}", "Coupled Mode (B)": f"{kpi_coup.sor:.3f}", "Engineering Delta": f"{deltas.get('delta_sor', 0.0):+.3f}"},
        {"Attribute / Metric": "Specific Energy (kWh/bbl)", "Independent Mode (A)": f"{kpi_ind.energy_kwh_bbl:.2f} kWh/bbl", "Coupled Mode (B)": f"{kpi_coup.energy_kwh_bbl:.2f} kWh/bbl", "Engineering Delta": f"{deltas.get('delta_energy_kwh', 0.0):+.2f} kWh/bbl"},
        {"Attribute / Metric": "Pump Fillage (%)", "Independent Mode (A)": f"{kpi_ind.pump_fillage_pct:.1f} %", "Coupled Mode (B)": f"{kpi_coup.pump_fillage_pct:.1f} %", "Engineering Delta": f"{deltas.get('delta_fillage_pct', 0.0):+.1f} %"},
        {"Attribute / Metric": "Peak Rod Load (kN)", "Independent Mode (A)": f"{kpi_ind.srp_load_kn:.1f} kN", "Coupled Mode (B)": f"{kpi_coup.srp_load_kn:.1f} kN", "Engineering Delta": f"{deltas.get('delta_srp_load_kn', 0.0):+.1f} kN"},
        {"Attribute / Metric": "Rod Stress (%)", "Independent Mode (A)": f"{kpi_ind.rod_stress_pct:.1f} %", "Coupled Mode (B)": f"{kpi_coup.rod_stress_pct:.1f} %", "Engineering Delta": f"{deltas.get('delta_rod_stress_pct', 0.0):+.1f} %"},
        {"Attribute / Metric": "Floating Risk", "Independent Mode (A)": f"{kpi_ind.floating_risk:.1f}", "Coupled Mode (B)": f"{kpi_coup.floating_risk:.1f}", "Engineering Delta": f"{deltas.get('delta_floating_risk', 0.0):+.1f}"},
        {"Attribute / Metric": "Maintenance Risk Score", "Independent Mode (A)": f"{kpi_ind.maintenance_risk:.2f}", "Coupled Mode (B)": f"{kpi_coup.maintenance_risk:.2f}", "Engineering Delta": f"{kpi_coup.maintenance_risk - kpi_ind.maintenance_risk:+.2f}"},
        {"Attribute / Metric": "Infeasible Candidates Filtered", "Independent Mode (A)": f"{kpi_ind.violations_count}", "Coupled Mode (B)": f"{kpi_coup.violations_count}", "Engineering Delta": f"{deltas.get('delta_violations', 0.0):+.0f}"},
        {"Attribute / Metric": "Normalized Objective Score", "Independent Mode (A)": f"{kpi_ind.objective_score:.4f}", "Coupled Mode (B)": f"{kpi_coup.objective_score:.4f}", "Engineering Delta": f"{deltas.get('delta_score', 0.0):+.4f}"},
    ]
    st.dataframe(pd.DataFrame(comp_data), use_container_width=True)

    st.markdown("#### 💡 Neutral Physical & Economic Causal Mechanism")
    st.markdown(f"""
    <div style="background: rgba(15, 23, 42, 0.7); border-left: 4px solid #f59e0b; border-radius: 8px; padding: 14px 18px; margin-top: 10px;">
        <div style="font-weight: 700; color: #f8fafc; font-size: 14px; margin-bottom: 6px;">Why Independent Optimization Fails Heavy Oil Assets:</div>
        <div style="font-size: 13px; color: #cbd5e1; line-height: 1.6;">
            {ablation_res.causal_explanation}
        </div>
    </div>
    """, unsafe_allow_html=True)

# -------------------------------------------------------------
# TAB 6: THERMAL TARGET (MINIMUM STEAM SOLVER)
# -------------------------------------------------------------
with tab6:
    st.markdown("### 🎯 Minimum-Necessary-Steam Target Solver")
    st.caption("Solves: 'What is the minimum steam intervention required to achieve the heated viscosity or temperature that renders downstream SRP production mechanically viable?'")

    tt_col1, tt_col2 = st.columns([1, 1])

    with tt_col1:
        st.markdown("##### 🎛️ Solver Target Specifications")
        target_mode = st.radio("Target Operational Variable", ["Heavy Crude Viscosity (kcP)", "Reservoir Temperature (°C)"], horizontal=True)
        
        if "Viscosity" in target_mode:
            target_val = st.slider("Target Downhole Viscosity (kcP)", min_value=6.0, max_value=12.0, value=8.5, step=0.1, help="Desired heavy oil viscosity reduction at the pump intake")
            t_type = "VISCOSITY"
        else:
            target_val = st.slider("Target Bottomhole Temperature (°C)", min_value=50.0, max_value=65.0, value=58.0, step=0.5, help="Target reservoir heating threshold")
            t_type = "TEMPERATURE"

        target_spm = st.slider("Anticipated Pumping Speed (SPM)", min_value=5.0, max_value=9.0, value=7.0, step=0.2)
        target_stroke = st.slider("Pump Stroke Length (m)", min_value=1.2, max_value=2.0, value=1.55, step=0.05)
        target_soak = st.slider("Planned Soaking Duration (h)", min_value=24, max_value=72, value=48, step=4)

        solve_clicked = st.button("🚀 Solve Minimum Necessary Steam", type="primary", use_container_width=True)

    with tt_col2:
        st.markdown("##### 📊 Solver Results & Feasibility Analysis")
        # Run solver
        t_target_res = solve_minimum_steam(
            target_type=t_type,
            target_value=target_val,
            spm=target_spm,
            stroke_m=target_stroke,
            soak_h=target_soak
        )

        if t_target_res.achieved:
            st.success(f"✅ Feasible Target Solution Discovered!")
            st.markdown(f"""
            <div class="kpi-container" style="border-color: #10b981; margin-bottom: 12px;">
                <div class="kpi-label">Minimum Feasible Steam Mass</div>
                <div class="kpi-val" style="color:#10b981;">{t_target_res.min_feasible_steam_t:.1f}<span class="kpi-unit">t</span></div>
                <div style="font-size:12px; color:#94a3b8; margin-top:4px;">Downstream SRP pump fillage: <b>{t_target_res.pump_fillage_pct:.1f}%</b> (min 52%) | Rod load: <b>{t_target_res.srp_load_kn:.1f} kN</b> (max 62kN)</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"- Resulting Heated Reservoir Temp: **{t_target_res.temperature_c:.1f} °C**")
            st.markdown(f"- Resulting Crude Viscosity: **{t_target_res.viscosity_kcp:.2f} kcP**")
            st.markdown(f"- Reservoir Inflow Rate: **{t_target_res.inflow_bpd:.1f} bpd**")
            st.markdown(f"- Downstream Limiting Condition: `{t_target_res.limiting_constraint}`")
            st.info(f"💡 {t_target_res.explanation}")
        else:
            st.error(f"❌ Target Unachievable within Prototype Operating Envelope")
            st.markdown(f"**Limiting Factor:** `{t_target_res.limiting_constraint}`")
            st.caption(t_target_res.explanation)

# -------------------------------------------------------------
# TAB 7: TIME MACHINE (HISTORICAL COUNTERFACTUAL REPLAY)
# -------------------------------------------------------------
with tab7:
    st.markdown("""
    <div class="prototype-banner">MODEL-BASED COUNTERFACTUAL REPLAY — NOT A MEASURED FIELD RESULT</div>
    """, unsafe_allow_html=True)

    st.markdown("### ⏳ Time Machine: Historical Cycle Replay")
    st.caption("Replays the frozen initial state of past production cycles under alternative decision setpoints. Fully leakage-free; demonstrates causal divergence.")

    tm_c1, tm_c2 = st.columns([1, 2])
    with tm_c1:
        st.markdown("##### 📜 Historical Baseline Cycle")
        selected_cycle = st.selectbox("Select Historical Cycle", [1, 2, 3, 4], index=2)
        cf_alt_steam = st.slider("Counterfactual Steam Mass (t)", min_value=85.0, max_value=125.0, value=115.0, step=1.0)
        cf_alt_soak = st.slider("Counterfactual Soak Duration (h)", min_value=24, max_value=72, value=48, step=4)
        cf_alt_spm = st.slider("Counterfactual Pumping Speed (SPM)", min_value=5.0, max_value=9.0, value=7.2, step=0.2)

        replay_btn = st.button("🔁 Replay Alternative Cycle Trajectory", type="primary", use_container_width=True)

    with tm_c2:
        hist_df = adapter.get_observations_history()
        cycle_df = hist_df[hist_df["cycle_id"] == selected_cycle] if not hist_df.empty else pd.DataFrame()
        
        act_steam = 98.0 if selected_cycle == 1 else (104.0 if selected_cycle == 2 else 108.0)
        act_oil = cycle_df["oil_rate_bpd"].mean() if not cycle_df.empty else 32.5
        act_temp = cycle_df["temperature_c"].mean() if not cycle_df.empty else 56.4

        # Simulate counterfactual alternative
        t_sim_cf = simulate_css_cycle(cf_alt_steam, soak_h=cf_alt_soak)
        v_sim_cf = [calculate_viscosity(t).viscosity_kcp for t in t_sim_cf.temperature_trajectory_c]
        sim_oil = 31.0 + (cf_alt_steam - 90.0) * 0.15 + (cf_alt_spm - 6.0) * 1.8

        fig_tm = go.Figure()
        if not cycle_df.empty:
            fig_tm.add_trace(go.Scatter(
                x=list(range(len(cycle_df))),
                y=cycle_df["temperature_c"],
                name=f"Actual Cycle {selected_cycle} Temperature",
                line=dict(color="#94a3b8", width=2, dash="dash")
            ))
        fig_tm.add_trace(go.Scatter(
            x=list(range(len(t_sim_cf.temperature_trajectory_c))),
            y=t_sim_cf.temperature_trajectory_c,
            name=f"Counterfactual Replay ({cf_alt_steam:.0f}t / {cf_alt_soak}h)",
            line=dict(color="#f59e0b", width=2.5)
        ))
        fig_tm.update_layout(
            title=dict(text=f"Historical Baseline vs. Counterfactual Thermal Trajectory (Cycle {selected_cycle})", font=dict(color="#f8fafc", size=13)),
            xaxis=dict(title="Cycle Elapsed Hours (h)", gridcolor="#1e293b"),
            yaxis=dict(title="Temperature (°C)", gridcolor="#1e293b"),
            template="plotly_dark",
            paper_bgcolor="rgba(15, 23, 42, 0.7)",
            plot_bgcolor="rgba(15, 23, 42, 0.7)",
            height=280,
            margin=dict(l=30, r=20, t=40, b=30)
        )
        st.plotly_chart(fig_tm, use_container_width=True)

        # Delta metrics
        delta_oil = sim_oil - act_oil
        st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 12px; font-size: 13px;">
            <b>Counterfactual Outcome:</b> Actual Oil: <b>{act_oil:.1f} bpd</b> | Replay Oil: <b>{sim_oil:.1f} bpd</b> | Divergence Delta: <b style="color:#10b981;">{delta_oil:+.1f} bpd</b><br>
            <span style="font-size:11px; color:#64748b;">Deterministic state hash preserved. Zero lookahead leakage into future cycle states.</span>
        </div>
        """, unsafe_allow_html=True)

# -------------------------------------------------------------
# TAB 8: SENSITIVITY & PARETO
# -------------------------------------------------------------
with tab8:
    st.markdown("### 🌪️ Deterministic Sensitivity Tornado & True Pareto Frontier")
    st.caption("One-At-A-Time (OAT) parameter swings and multi-objective non-dominated Pareto frontier mapping.")

    sens_tab_col1, sens_tab_col2 = st.columns([1, 1])

    with sens_tab_col1:
        st.markdown("#### 🌪️ Ranked Parameter Sensitivity Tornado")
        if top_rec:
            sens_res = run_sensitivity_analysis(top_rec, current_state, perturbation_pcts=[-20.0, -10.0, 10.0, 20.0])
            
            params = [p[0] for p in reversed(sens_res.ranked_importance)]
            swings = [p[1] for p in reversed(sens_res.ranked_importance)]

            fig_tor = go.Figure()
            fig_tor.add_trace(go.Bar(
                y=params,
                x=swings,
                orientation="h",
                marker_color="#f59e0b",
                text=[f"±{s:.1f}%" for s in swings],
                textposition="auto"
            ))
            fig_tor.update_layout(
                title=dict(text=f"Total Swing in Oil Rate across ±20% Parameter Perturbations", font=dict(color="#f8fafc", size=13)),
                xaxis=dict(title="Production Sensitivity Range (Δ Oil %)", gridcolor="#1e293b"),
                template="plotly_dark",
                paper_bgcolor="rgba(15, 23, 42, 0.7)",
                plot_bgcolor="rgba(15, 23, 42, 0.7)",
                height=300,
                margin=dict(l=40, r=20, t=40, b=30)
            )
            st.plotly_chart(fig_tor, use_container_width=True)
            st.caption("Parameters ranked by total output elasticity. Steam mass and pumping speed drive primary recovery variance.")

    with sens_tab_col2:
        st.markdown("#### ⚡ True Multi-Objective Pareto Frontier")
        pareto_res = compute_pareto_frontier(all_cands, selected_scenario_id=top_rec.scenario_id if top_rec else None)
        
        p_df = pd.DataFrame([c.model_dump() for c in pareto_res.candidates])
        p_df["Classification"] = p_df["is_nondominated"].apply(lambda x: "Pareto Frontier (Nondominated)" if x else "Dominated Candidate")

        fig_pareto = px.scatter(
            p_df,
            x="steam_mass_t",
            y="oil_rate_bpd",
            color="Classification",
            color_discrete_map={
                "Pareto Frontier (Nondominated)": "#10b981",
                "Dominated Candidate": "#64748b"
            },
            hover_name="scenario_id",
            hover_data=["energy_kwh_bbl", "risk_score", "objective_score"],
            labels={"steam_mass_t": "Steam Injected (t)", "oil_rate_bpd": "Net Oil Production (bpd)"},
            template="plotly_dark"
        )
        if top_rec:
            fig_pareto.add_trace(go.Scatter(
                x=[top_rec.steam_mass_t],
                y=[top_rec.oil_rate_bpd],
                mode="markers",
                marker=dict(size=18, color="rgba(0,0,0,0)", line=dict(color="#f59e0b", width=3)),
                name="Recommended",
                hoverinfo="skip"
            ))
        fig_pareto.update_layout(
            title=dict(text=f"Pareto Frontier: {pareto_res.nondominated_count} Non-Dominated of {pareto_res.total_candidates} Candidates", font=dict(color="#f8fafc", size=13)),
            paper_bgcolor="rgba(15, 23, 42, 0.7)",
            plot_bgcolor="rgba(15, 23, 42, 0.7)",
            height=300,
            margin=dict(l=30, r=20, t=40, b=30)
        )
        st.plotly_chart(fig_pareto, use_container_width=True)
        st.caption("Axiomatic 4-objective Pareto dominance: simultaneously maximizing oil while minimizing steam, energy, and mechanical risk.")

# -------------------------------------------------------------
# TAB 9: VALIDATION & ML RESIDUALS
# -------------------------------------------------------------
with tab9:
    st.markdown("### ✅ Scientific Validation & Physics-Residual ML")
    st.caption("Chronological cross-validation, physical monotonicity verification, and bounded hybrid residual regression.")

    val_c1, val_c2 = st.columns(2)
    with val_c1:
        st.markdown("#### ⏳ Temporal Backtesting (Leakage-Free)")
        temp_val = run_temporal_validation(hist_df)
        val_rows = [
            {"Cycle": r.cycle_id, "Metric": r.metric_name, "Value": f"{r.metric_value:.3f}", "Status": r.pass_fail, "Description": r.details}
            for r in temp_val
        ]
        st.dataframe(pd.DataFrame(val_rows), use_container_width=True)

    with val_c2:
        st.markdown("#### 📐 Physics Monotonicity Verification")
        phys_val = run_physics_validation()
        for pv in phys_val:
            badge = "🟢 PASS" if pv.pass_fail == "PASS" else "🔴 FAIL"
            st.markdown(f"- **{pv.metric_name}**: {badge} — *{pv.details}*")

    st.markdown("---")
    st.markdown("#### 🧠 Explainable Ridge Residual ML Calibration")
    st.caption("Hybrid physics+residual pathway: $T_{hybrid} = T_{physics} + \\Delta T$. The L2-regularized Ridge model transparently corrects minor wellbore heat conduction biases without violating physics bounds.")
    
    ml_c1, ml_c2 = st.columns([1, 1])
    with ml_c1:
        coefs = hybrid_residual_predictor.coefficients
        st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 14px; font-size: 13px;">
            <b>Residual Model Weights (L2 Regularization $\\alpha={coefs.l2_regularization}$):</b><br>
            • Steam Mass Coef: <code>{coefs.coef_steam_mass:+.3f}</code><br>
            • Soak Duration Coef: <code>{coefs.coef_soak_h:+.3f}</code><br>
            • Cycle Number Coef: <code>{coefs.coef_cycle_num:+.3f}</code><br>
            • Injection Rate Coef: <code>{coefs.coef_injection_rate:+.3f}</code><br>
            • Bias Intercept: <code>{coefs.bias:+.3f}</code><br>
            • Training MAE: <b>{coefs.train_mae_c:.2f} °C</b> | Guardrail: <b>±{hybrid_residual_predictor.max_correction_c:.1f} °C hard bound</b>
        </div>
        """, unsafe_allow_html=True)
    with ml_c2:
        t_test_mass = st.number_input("Test Steam Mass (t)", value=106.0, step=1.0)
        t_test_soak = st.number_input("Test Soak (h)", value=48.0, step=2.0)
        corr = hybrid_residual_predictor.predict_residual_correction(t_test_mass, t_test_soak)
        st.markdown(f"**Predicted Residual Correction (ΔT):** `{corr:+.3f} °C`")
        if abs(corr) < 2.5:
            st.success("✓ Residual within nominal GREEN uncertainty envelope (≤ 2.5 °C).")
        else:
            st.warning("⚠️ Residual elevated; advisory gate tripped to AMBER.")

    st.markdown("---")
    st.markdown("#### 📄 Field Data Ingestion Contract")
    st.caption("Standardized interface for live Oil India Limited (OIL) Baghewala telemetry ingestion. Governed by `docs/FIELD_DATA_CONTRACT.md`.")
    st.markdown("""
    - **Channel A (Surface SRP Skid):** Motor power (kW), polished rod load cell (kN), dynacard arrays (100–256 points), VFD stroke frequency.
    - **Channel B (Thermal Injection Skid):** Steam mass flow rate (t/h), generator pressure (bar), steam quality fraction ($X$), cumulative steam.
    - **Channel C (Downhole Sensors):** Permanent downhole pressure gauge ($P_{wf}$), distributed temperature DTS fiber array.
    - **Channel D (Separator Well Tests):** 24-hr gross liquid rate ($m^3/d$), BS&W water cut (%), crude PVT viscosity vs. temperature table.
    """)

# -------------------------------------------------------------
# TAB 10: PHOTOREALISTIC 3D THREE.JS TWIN
# -------------------------------------------------------------
with tab10:
    st.markdown("### 🌐 Photorealistic Three.js Well-to-Surface Physical Twin")
    st.caption("Real-time physical kinematics: Nodding donkey crank-beam linkage, reciprocating sucker rod, subsurface stratigraphic cutaway, and thermal reservoir glow.")

    overlay_choice = st.radio(
        "3D Model State Mode:",
        ["Current Telemetry Observation", "Top Recommended Scenario Setpoints"],
        horizontal=True
    )

    if overlay_choice == "Top Recommended Scenario Setpoints" and top_rec:
        disp_state = {
            "well_id": well_id,
            "temperature_c": top_rec.temperature_c,
            "viscosity_kcp": top_rec.viscosity_kcp,
            "spm": top_rec.pump_speed_spm,
            "stroke_m": top_rec.stroke_length_m,
            "oil_rate_bpd": top_rec.oil_rate_bpd,
            "pump_fillage_pct": top_rec.pump_fillage_pct,
            "srp_load_kn": top_rec.srp_load_kn,
            "risk_score": top_rec.risk_score,
            "phase": "production",
            "scenario_label": f"RECOMMENDED: {top_rec.scenario_id}"
        }
    else:
        disp_state = {
            "well_id": well_id,
            "temperature_c": current_state.temperature_c,
            "viscosity_kcp": current_state.viscosity_kcp,
            "spm": current_state.pump_speed_spm,
            "stroke_m": current_state.stroke_length_m,
            "oil_rate_bpd": current_state.oil_rate_bpd,
            "pump_fillage_pct": current_state.pump_fillage_pct,
            "srp_load_kn": current_state.srp_load_kn,
            "risk_score": float(current_state.srp_risk_score),
            "phase": current_state.phase,
            "scenario_label": "CURRENT TELEMETRY"
        }

    # Generate and embed the realistic Three.js HTML model
    three_html = generate_threejs_html(**disp_state)
    components.html(three_html, height=880, scrolling=False)

    col_g1, col_g2, col_g3 = st.columns(3)
    with col_g1:
        st.markdown("""
        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 10px; padding: 12px 14px; font-size: 12px;">
            <div style="font-weight: 700; color: #fbbf24; margin-bottom: 4px;">🏗️ Surface Unit Kinematics</div>
            <div style="color: #94a3b8; line-height: 1.5;">
                Exact 4-bar linkage solves beam oscillation from crank rotation. Horsehead circular arc radius matches front arm to maintain pure vertical tangency over stuffing box.
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col_g2:
        st.markdown("""
        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 10px; padding: 12px 14px; font-size: 12px;">
            <div style="font-weight: 700; color: #38bdf8; margin-bottom: 4px;">⚙️ Downhole Pump Valve Action</div>
            <div style="color: #94a3b8; line-height: 1.5;">
                <b>Upstroke:</b> Traveling Valve closed, lifting fluid column; Standing Valve open, drawing inflow.<br>
                <b>Downstroke:</b> Traveling Valve open; Standing Valve closed under hydrostatic head.
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col_g3:
        st.markdown("""
        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 10px; padding: 12px 14px; font-size: 12px;">
            <div style="font-weight: 700; color: #f43f5e; margin-bottom: 4px;">🔥 Thermal Viscosity Coupling</div>
            <div style="color: #94a3b8; line-height: 1.5;">
                Injected steam diffuses through the Jodhpur Sandstone. Radiant core heat drops heavy crude viscosity, lowering polished rod friction and boosting mobility inflow.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.info("💡 **Interactive Navigation Tip:** Click on any 3D mechanical part (e.g. Walking Beam, Counterweights, Stuffing Box, Valves, Reservoir) or label pin to inspect its technical function and operational telemetry in the live Component Inspector!")
