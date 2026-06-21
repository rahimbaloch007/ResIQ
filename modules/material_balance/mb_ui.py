import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from modules.material_balance.mb_engine import MaterialBalanceEngine


def render_mb_module():
    """Material Balance & P/Z Analysis UI for ResIQ."""

    st.markdown("## 📉 Material Balance & P/Z Analysis")
    st.markdown("*OGIP estimation from pressure-production history*")
    st.divider()

    # ── RESERVOIR PROPERTIES ───────────────────────────────
    st.markdown("### Reservoir Fluid Properties")
    col1, col2, col3 = st.columns(3)
    with col1:
        gamma_g = st.number_input(
            "Gas Specific Gravity", min_value=0.55, max_value=0.90,
            value=0.65, step=0.01, key="mb_gamma"
        )
    with col2:
        T_res = st.number_input(
            "Reservoir Temperature (°F)", min_value=80, max_value=400,
            value=212, key="mb_temp"
        )
    with col3:
        H2S = st.number_input(
            "H2S Content (%)", min_value=0.0, max_value=30.0,
            value=0.0, step=0.1, key="mb_h2s"
        )

    st.divider()

    # ── DATA INPUT METHOD ───────────────────────────────────
    st.markdown("### Pressure-Production History")
    input_method = st.radio(
        "Input Method",
        ["Manual Entry", "Upload CSV"],
        horizontal=True
    )

    pressures = []
    cum_prod = []

    if input_method == "Manual Entry":
        st.markdown("*Enter at least 3 data points for reliable trend analysis*")
        default_data = pd.DataFrame({
            "Avg_Pressure_psia": [3500, 3350, 3200, 3000, 2800],
            "Cum_Production_MMscf": [0, 850, 1800, 3100, 4500],
        })
        edited_df = st.data_editor(
            default_data, num_rows="dynamic", use_container_width=True
        )
        pressures = edited_df["Avg_Pressure_psia"].dropna().tolist()
        cum_prod = edited_df["Cum_Production_MMscf"].dropna().tolist()

    else:
        st.markdown("""
        **CSV Format Required:**
                    
Avg_Pressure_psia, Cum_Production_MMscf
    3500, 0
    3350, 850
    3200, 1800
                    
""")
        uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
        if uploaded_file is not None:
            df_upload = pd.read_csv(uploaded_file)
            pressures = df_upload.iloc[:, 0].tolist()
            cum_prod = df_upload.iloc[:, 1].tolist()
            st.dataframe(df_upload, use_container_width=True)

    st.divider()

    # ── CALCULATE ─────────────────────────────────────────
    if st.button("⚡ Run Material Balance Analysis",
                  type="primary", use_container_width=True):

        if len(pressures) < 2:
            st.error("Need at least 2 valid data points to run analysis.")
            return

        mb = MaterialBalanceEngine(gamma_g, T_res, H2S)
        result = mb.ogip_from_pz_plot(pressures, cum_prod)
        drive = mb.detect_drive_mechanism(result['r_squared'])
        rf = mb.recovery_factor(cum_prod[-1], result['OGIP_MMscf'])

    # Save to session state for PDF report
        st.session_state['mb_results'] = {
            'OGIP_Bscf': result['OGIP_Bscf'],
            'r_squared': result['r_squared'],
            'drive': drive,
        }

        # ── METRICS ──────────────────────────────────────
        st.markdown("### Results")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("OGIP", f"{result['OGIP_Bscf']} Bscf")
        m2.metric("R²", f"{result['r_squared']}")
        m3.metric("Current Recovery", f"{rf}%")
        m4.metric("Data Points", f"{len(pressures)}")

        st.info(f"**Drive Mechanism Assessment:** {drive}")

        # ── P/Z PLOT ─────────────────────────────────────
        Gp_array = np.array(cum_prod)
        pz_array = np.array(result['p_over_z_values'])

        # Extended trend line to x-intercept (OGIP)
        Gp_line = np.linspace(0, result['OGIP_MMscf'], 50)
        pz_line = result['slope'] * Gp_line + result['intercept']

        fig = go.Figure()

        # Actual data points
        fig.add_trace(go.Scatter(
            x=Gp_array, y=pz_array,
            mode='markers', name='Field Data',
            marker=dict(size=10, color='#00D4AA')
        ))

        # Trend line extrapolated to OGIP
        fig.add_trace(go.Scatter(
            x=Gp_line, y=pz_line,
            mode='lines', name='Trend Line (extrapolated)',
            line=dict(color='#F59E0B', width=2, dash='dash')
        ))

        fig.update_layout(
            title="P/Z Plot — OGIP Estimation",
            xaxis_title="Cumulative Gas Production, Gp (MMscf)",
            yaxis_title="P/Z (psia)",
            template="plotly_dark",
            height=450,
        )
        st.plotly_chart(fig, use_container_width=True)

        # ── DATA TABLE ───────────────────────────────────
        st.markdown("### P/Z Calculation Table")
        df_results = pd.DataFrame({
            "Pressure_psia": pressures,
            "Cum_Production_MMscf": cum_prod,
            "P_over_Z": pz_array,
        })
        st.dataframe(df_results, use_container_width=True)

        # ── EXPORT ───────────────────────────────────────
        csv = df_results.to_csv(index=False)
        st.download_button(
            label="📥 Download Results (CSV)",
            data=csv,
            file_name="ResIQ_MaterialBalance_Results.csv",
            mime="text/csv",
            use_container_width=True
        )