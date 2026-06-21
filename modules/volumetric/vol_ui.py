import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from modules.volumetric.vol_engine import VolumetricEngine


def render_vol_module():
    """Volumetric Reserves UI for ResIQ."""

    st.markdown("## 📦 Volumetric Reserves & OGIP")
    st.markdown("*OGIP estimation with P10/P50/P90 uncertainty analysis*")
    st.divider()

    # ── FLUID PROPERTIES ─────────────────────────────────────
    st.markdown("### Reservoir Fluid Properties")
    col1, col2, col3 = st.columns(3)
    with col1:
        gamma_g = st.number_input(
            "Gas Specific Gravity", min_value=0.55, max_value=0.90,
            value=0.65, step=0.01, key="vol_gamma"
        )
    with col2:
        T_res = st.number_input(
            "Reservoir Temperature (°F)", min_value=80, max_value=400,
            value=212, key="vol_temp"
        )
    with col3:
        Pi = st.number_input(
            "Initial Reservoir Pressure, Pi (psia)",
            min_value=100.0, value=3500.0, key="vol_pi"
        )

    st.divider()

    # ── DETERMINISTIC INPUTS ──────────────────────────────────
    st.markdown("### Reservoir Properties (Mid Case)")
    col4, col5, col6, col7 = st.columns(4)
    with col4:
        area = st.number_input("Drainage Area (acres)",
                                min_value=10.0, value=5000.0, key="vol_area")
    with col5:
        h = st.number_input("Net Pay Thickness (ft)",
                             min_value=1.0, value=45.0, key="vol_h")
    with col6:
        phi = st.number_input("Porosity (fraction)",
                               min_value=0.01, max_value=0.40,
                               value=0.18, step=0.01, key="vol_phi")
    with col7:
        Swi = st.number_input("Water Saturation (fraction)",
                               min_value=0.05, max_value=0.95,
                               value=0.25, step=0.01, key="vol_swi")

    st.divider()

    # ── UNCERTAINTY RANGES ─────────────────────────────────────
    st.markdown("### Uncertainty Ranges (for Monte Carlo)")
    st.markdown("*Set low and high bounds around each mid-case value*")

    col8, col9 = st.columns(2)
    with col8:
        area_low = st.number_input("Area — Low (acres)", value=area * 0.8, key="vol_area_lo")
        h_low = st.number_input("Thickness — Low (ft)", value=h * 0.8, key="vol_h_lo")
        phi_low = st.number_input("Porosity — Low", value=phi * 0.8, key="vol_phi_lo")
        Swi_low = st.number_input("Sw — Low", value=Swi * 0.8, key="vol_swi_lo")
    with col9:
        area_high = st.number_input("Area — High (acres)", value=area * 1.3, key="vol_area_hi")
        h_high = st.number_input("Thickness — High (ft)", value=h * 1.3, key="vol_h_hi")
        phi_high = st.number_input("Porosity — High", value=phi * 1.3, key="vol_phi_hi")
        Swi_high = st.number_input("Sw — High", value=Swi * 1.3, key="vol_swi_hi")

    st.divider()

    recovery_factor = st.slider(
        "Recovery Factor (%)", min_value=50, max_value=95,
        value=80, key="vol_rf"
    ) / 100

    st.divider()

    # ── CALCULATE ─────────────────────────────────────────
    if st.button("⚡ Run Volumetric Analysis",
                  type="primary", use_container_width=True):

        vol = VolumetricEngine(gamma_g, T_res, Pi)

        ogip = vol.calculate_ogip(area, h, phi, Swi)

        with st.spinner("Running Monte Carlo simulation (10,000 iterations)..."):
            mc = vol.monte_carlo_uncertainty(
                area_range=(area_low, area, area_high),
                h_range=(h_low, h, h_high),
                phi_range=(phi_low, phi, phi_high),
                Swi_range=(Swi_low, Swi, Swi_high),
            )

        rec = vol.reserves_classification(ogip['OGIP_Bscf'], recovery_factor)

        # ── METRICS ──────────────────────────────────────
        st.markdown("### Results")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("OGIP (Deterministic)", f"{ogip['OGIP_Bscf']} Bscf")
        m2.metric("P50 (Probabilistic)", f"{mc['P50_Bscf']} Bscf")
        m3.metric("Recoverable Reserves", f"{rec['recoverable_reserves_Bscf']} Bscf")
        m4.metric("Bgi", f"{ogip['Bgi']:.6f} res ft³/scf")

        st.info(
            f"**P10 (High Case):** {mc['P10_Bscf']} Bscf  |  "
            f"**P50 (Mid Case):** {mc['P50_Bscf']} Bscf  |  "
            f"**P90 (Low Case):** {mc['P90_Bscf']} Bscf"
        )

        # ── DISTRIBUTION HISTOGRAM ─────────────────────────
        fig1 = go.Figure()
        fig1.add_trace(go.Histogram(
            x=mc['distribution'], nbinsx=60,
            marker_color='#00D4AA', name='OGIP Distribution'
        ))
        fig1.add_vline(x=mc['P10_Bscf'], line_dash="dash", line_color="red",
                        annotation_text="P10")
        fig1.add_vline(x=mc['P50_Bscf'], line_dash="dash", line_color="orange",
                        annotation_text="P50")
        fig1.add_vline(x=mc['P90_Bscf'], line_dash="dash", line_color="yellow",
                        annotation_text="P90")
        fig1.update_layout(
            title="OGIP Probability Distribution (Monte Carlo, 10,000 runs)",
            xaxis_title="OGIP (Bscf)",
            yaxis_title="Frequency",
            template="plotly_dark",
            height=400,
        )
        st.plotly_chart(fig1, use_container_width=True)

        # ── TORNADO-STYLE SUMMARY TABLE ─────────────────────
        st.markdown("### Reserves Summary")
        df_summary = pd.DataFrame({
            "Case": ["P10 (High)", "P50 (Mid)", "P90 (Low)", "Deterministic"],
            "OGIP_Bscf": [mc['P10_Bscf'], mc['P50_Bscf'],
                          mc['P90_Bscf'], ogip['OGIP_Bscf']],
        })
        st.dataframe(df_summary, use_container_width=True)

        # ── EXPORT ───────────────────────────────────────
        csv = df_summary.to_csv(index=False)
        st.download_button(
            label="📥 Download Summary (CSV)",
            data=csv,
            file_name="ResIQ_Volumetric_Results.csv",
            mime="text/csv",
            use_container_width=True
        )