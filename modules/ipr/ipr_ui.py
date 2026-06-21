import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from modules.ipr.ipr_engine import IPREngine


def render_ipr_module():
    """IPR & Gas Deliverability UI for ResIQ."""

    st.markdown("## 🌊 IPR & Gas Deliverability")
    st.markdown("*LIT method — deliverability curve and AOF calculation*")
    st.divider()

    # ── RESERVOIR & FLUID PROPERTIES ────────────────────────
    st.markdown("### Reservoir & Fluid Properties")
    col1, col2, col3 = st.columns(3)
    with col1:
        gamma_g = st.number_input(
            "Gas Specific Gravity", min_value=0.55, max_value=0.90,
            value=0.65, step=0.01, key="ipr_gamma"
        )
    with col2:
        T_res = st.number_input(
            "Reservoir Temperature (°F)", min_value=80, max_value=400,
            value=212, key="ipr_temp"
        )
    with col3:
        Pr = st.number_input(
            "Static Reservoir Pressure, Pr (psia)",
            min_value=100.0, value=3500.0, key="ipr_pr"
        )

    st.divider()

    # ── MULTI-RATE TEST DATA ─────────────────────────────────
    st.markdown("### Multi-Rate Test Data")
    st.markdown("*Typically a 4-point or isochronal test*")

    input_method = st.radio(
        "Input Method", ["Manual Entry", "Upload CSV"], horizontal=True
    )

    q_array = []
    pwf_array = []

    if input_method == "Manual Entry":
        default_data = pd.DataFrame({
            "Rate_Mscfd": [5200, 10800, 18400, 24100],
            "FBHP_psia": [3380, 3180, 2900, 2620],
        })
        edited_df = st.data_editor(
            default_data, num_rows="dynamic", use_container_width=True
        )
        q_array = edited_df["Rate_Mscfd"].dropna().tolist()
        pwf_array = edited_df["FBHP_psia"].dropna().tolist()
    else:
        st.markdown("""
        **CSV Format Required:**

Rate_Mscfd, FBHP_psia
    5200, 3380
    10800, 3180
    18400, 2900

""")
        uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
        if uploaded_file is not None:
            df_upload = pd.read_csv(uploaded_file)
            q_array = df_upload.iloc[:, 0].tolist()
            pwf_array = df_upload.iloc[:, 1].tolist()
            st.dataframe(df_upload, use_container_width=True)

    st.divider()

    # ── CALCULATE ─────────────────────────────────────────
    if st.button("⚡ Run Deliverability Analysis",
                  type="primary", use_container_width=True):

        if len(q_array) < 3:
            st.error("Need at least 3 valid test points for analysis.")
            return

        with st.spinner("Calculating pseudopressure and fitting LIT coefficients..."):
            ipr = IPREngine(gamma_g, T_res)
            fit = ipr.fit_lit_coefficients(Pr, q_array, pwf_array)
            aof = ipr.calculate_aof(Pr, fit['a'], fit['b'])
            curve = ipr.deliverability_curve(Pr, fit['a'], fit['b'])

        # ── METRICS ──────────────────────────────────────
        st.markdown("### Results")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("AOF", f"{aof:,.0f} Mscf/d" if aof else "N/A")
        m2.metric("AOF (MMscf/d)", f"{aof/1000:.2f}" if aof else "N/A")
        m3.metric("R²", f"{fit['r_squared']}")
        m4.metric("Max Tested Rate", f"{max(q_array):,.0f} Mscf/d")

        if aof and max(q_array) > 0:
            ratio = aof / max(q_array)
            st.info(f"**AOF is {ratio:.2f}x the highest tested rate** "
                    f"— typical range is 1.5x to 3x for a well with "
                    f"reasonable deliverability.")

        # ── DELIVERABILITY PLOT ───────────────────────────
        fig = go.Figure()

        # Theoretical curve
        fig.add_trace(go.Scatter(
            x=curve['q_Mscfd'], y=curve['Pwf_psia'],
            mode='lines', name='Deliverability Curve',
            line=dict(color='#F59E0B', width=2.5)
        ))

        # Actual test points
        fig.add_trace(go.Scatter(
            x=q_array, y=pwf_array,
            mode='markers', name='Test Data',
            marker=dict(size=10, color='#00D4AA')
        ))

        # AOF point
        if aof:
            fig.add_trace(go.Scatter(
                x=[aof], y=[14.7],
                mode='markers', name='AOF (Pwf=14.7 psia)',
                marker=dict(size=12, color='red', symbol='star')
            ))

        fig.update_layout(
            title="Gas Well Deliverability Curve (IPR)",
            xaxis_title="Gas Rate, q (Mscf/d)",
            yaxis_title="Flowing Bottomhole Pressure, Pwf (psia)",
            template="plotly_dark",
            height=450,
        )
        st.plotly_chart(fig, use_container_width=True)

        # ── DATA TABLE ───────────────────────────────────
        st.markdown("### Test Data")
        df_results = pd.DataFrame({
            "Rate_Mscfd": q_array,
            "FBHP_psia": pwf_array,
        })
        st.dataframe(df_results, use_container_width=True)

        # ── EXPORT ───────────────────────────────────────
        csv = df_results.to_csv(index=False)
        st.download_button(
            label="📥 Download Test Data (CSV)",
            data=csv,
            file_name="ResIQ_IPR_Results.csv",
            mime="text/csv",
            use_container_width=True
        )