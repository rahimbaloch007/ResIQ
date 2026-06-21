import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from modules.well_test.wt_engine import WellTestEngine


def render_wt_module():
    """Well Test Interpretation UI for ResIQ."""

    st.markdown("## 🔬 Well Test Interpretation")
    st.markdown("*Horner plot analysis — permeability, skin factor, reservoir pressure*")
    st.divider()

    # ── RESERVOIR & FLUID PROPERTIES ────────────────────────
    st.markdown("### Reservoir & Fluid Properties")
    col1, col2, col3 = st.columns(3)
    with col1:
        gamma_g = st.number_input(
            "Gas Specific Gravity", min_value=0.55, max_value=0.90,
            value=0.65, step=0.01, key="wt_gamma"
        )
        T_res = st.number_input(
            "Reservoir Temperature (°F)", min_value=80, max_value=400,
            value=212, key="wt_temp"
        )
    with col2:
        phi = st.number_input(
            "Porosity (fraction)", min_value=0.01, max_value=0.40,
            value=0.18, step=0.01, key="wt_phi"
        )
        h_ft = st.number_input(
            "Net Pay Thickness (ft)", min_value=1.0,
            value=45.0, key="wt_h"
        )
    with col3:
        rw_ft = st.number_input(
            "Wellbore Radius (ft)", min_value=0.1, max_value=2.0,
            value=0.354, step=0.01, key="wt_rw"
        )
        ct = st.number_input(
            "Total Compressibility (1/psi)", min_value=0.00001,
            value=0.00015, format="%.5f", key="wt_ct"
        )

    st.divider()

    # ── TEST PARAMETERS ──────────────────────────────────────
    st.markdown("### Test Parameters")
    col4, col5 = st.columns(2)
    with col4:
        q_rate = st.number_input(
            "Production Rate Before Shut-in (Mscf/d)",
            min_value=1.0, value=5000.0, key="wt_q"
        )
    with col5:
        tp_hr = st.number_input(
            "Producing Time Before Shut-in (hours)",
            min_value=1.0, value=720.0, key="wt_tp"
        )

    st.divider()

    # ── PRESSURE BUILDUP DATA ────────────────────────────────
    st.markdown("### Pressure Buildup Data")
    input_method = st.radio(
        "Input Method", ["Manual Entry", "Upload CSV"], horizontal=True
    )

    dt_array = []
    pws_array = []

    if input_method == "Manual Entry":
        default_data = pd.DataFrame({
            "Delta_t_hours": [1, 2, 4, 6, 8, 10, 15, 20, 24],
            "Pws_psia": [2950, 3120, 3290, 3390, 3460, 3510, 3600, 3650, 3680],
        })
        edited_df = st.data_editor(
            default_data, num_rows="dynamic", use_container_width=True
        )
        dt_array = edited_df["Delta_t_hours"].dropna().tolist()
        pws_array = edited_df["Pws_psia"].dropna().tolist()
    else:
        st.markdown("""
        **CSV Format Required:**

Delta_t_hours, Pws_psia
    1, 2950
    2, 3120
    4, 3290

""")
        uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
        if uploaded_file is not None:
            df_upload = pd.read_csv(uploaded_file)
            dt_array = df_upload.iloc[:, 0].tolist()
            pws_array = df_upload.iloc[:, 1].tolist()
            st.dataframe(df_upload, use_container_width=True)

    st.divider()

    # ── CALCULATE ─────────────────────────────────────────
    if st.button("⚡ Run Horner Analysis",
                  type="primary", use_container_width=True):

        if len(dt_array) < 3:
            st.error("Need at least 3 valid pressure points for analysis.")
            return

        with st.spinner("Calculating pseudopressure and running Horner regression..."):
            wt = WellTestEngine(
                q_Mscfd=q_rate, rw_ft=rw_ft, phi=phi, h_ft=h_ft,
                ct_psi_inv=ct, gamma_g=gamma_g, T_f=T_res
            )
            result = wt.horner_analysis(tp_hr, dt_array, pws_array)

        assessment = wt.classify_skin(result['skin_factor'])

        # ── METRICS ──────────────────────────────────────
        st.markdown("### Results")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Permeability (k)", f"{result['permeability_md']} md")
        m2.metric("Skin Factor", f"{result['skin_factor']}")
        m3.metric("P* (Avg Pressure)", f"{result['P_star_psia']} psia")
        m4.metric("kh", f"{result['kh_md_ft']} md·ft")

        if result['skin_factor'] is not None and result['skin_factor'] > 5:
            st.error(f"**Assessment:** {assessment}")
        elif result['skin_factor'] is not None and result['skin_factor'] > 0:
            st.warning(f"**Assessment:** {assessment}")
        else:
            st.success(f"**Assessment:** {assessment}")

        # ── HORNER PLOT ────────────────────────────────────
        log_htr = result['log_htr']
        pws_obs = result['pws_observed']

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=log_htr, y=pws_obs,
            mode='markers', name='Observed Pws',
            marker=dict(size=10, color='#00D4AA')
        ))
        fig.update_layout(
            title="Horner Plot — Pws vs log[(tp+Δt)/Δt]",
            xaxis=dict(title="log10[(tp+Δt)/Δt]", autorange="reversed"),
            yaxis_title="Shut-in Pressure, Pws (psia)",
            template="plotly_dark",
            height=450,
        )
        st.plotly_chart(fig, use_container_width=True)

        # ── DATA TABLE ───────────────────────────────────
        st.markdown("### Test Data")
        df_results = pd.DataFrame({
            "Delta_t_hours": dt_array,
            "Pws_psia": pws_array,
        })
        st.dataframe(df_results, use_container_width=True)

        # ── EXPORT ───────────────────────────────────────
        csv = df_results.to_csv(index=False)
        st.download_button(
            label="📥 Download Test Data (CSV)",
            data=csv,
            file_name="ResIQ_WellTest_Results.csv",
            mime="text/csv",
            use_container_width=True
        )