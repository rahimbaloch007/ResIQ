import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from modules.pvt.pvt_engine import PVTEngine


def render_pvt_module():
    """Complete PVT Analysis UI for ResIQ."""

    st.markdown("## 📊 PVT Analysis")
    st.markdown("*Gas PVT properties using Hall-Yarborough Z-factor correlation*")
    st.divider()

    # ── INPUT SECTION ─────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Reservoir Properties")
        gamma_g = st.number_input(
            "Gas Specific Gravity (air=1.0)",
            min_value=0.55, max_value=0.90,
            value=0.65, step=0.01,
            help="From wellhead gas chromatograph"
        )
        T_res = st.number_input(
            "Reservoir Temperature (°F)",
            min_value=80, max_value=400,
            value=212,
            help="From MDT/DST measurement"
        )

    with col2:
        st.markdown("### Acid Gas Content")
        H2S = st.number_input(
            "H2S Content (%)",
            min_value=0.0, max_value=30.0,
            value=0.0, step=0.1,
            help="Critical for Sui gas field"
        )
        CO2 = st.number_input(
            "CO2 Content (%)",
            min_value=0.0, max_value=30.0,
            value=0.0, step=0.1
        )

    st.divider()

    st.markdown("### Pressure Range")
    col3, col4 = st.columns(2)
    with col3:
        P_min = st.number_input("Minimum Pressure (psia)",
                                 value=500, min_value=100)
    with col4:
        P_max = st.number_input("Maximum Pressure (psia)",
                                 value=5000, min_value=500)

    if st.button("⚡ Calculate PVT Properties",
                  type="primary", use_container_width=True):

        pvt = PVTEngine(gamma_g, T_res, H2S, CO2)
        P_array = np.linspace(P_min, P_max, 50)
        results = pvt.pvt_table(P_array)
        df = pd.DataFrame(results)
    # Save to session state for PDF report —
        # use Maximum Pressure as the representative
        # reservoir condition (typically set to Pi)
        st.session_state['pvt_results'] = {
            'Z_factor': results['Z_factor'][-1],
            'Bg': results['Bg_resFt3_scf'][-1],
            'viscosity': results['Viscosity_cp'][-1],
            'Tpc': round(pvt.Tpc, 2),
            'Ppc': round(pvt.Ppc, 2),
            'reference_pressure': P_max,
        }

        st.markdown("### Results at Maximum Pressure")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Z-Factor", f"{results['Z_factor'][-1]:.4f}")
        m2.metric("Bg (res ft³/scf)", f"{results['Bg_resFt3_scf'][-1]:.6f}")
        m3.metric("Viscosity (cp)", f"{results['Viscosity_cp'][-1]:.5f}")
        m4.metric("Tpc (°R)", f"{pvt.Tpc:.1f}")

        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=results['Pressure_psia'], y=results['Z_factor'],
            mode='lines+markers', name='Z-Factor',
            line=dict(color='#00D4AA', width=2.5), marker=dict(size=4)
        ))
        fig1.update_layout(
            title="Z-Factor vs Pressure",
            xaxis_title="Pressure (psia)", yaxis_title="Z-Factor",
            template="plotly_dark", height=400,
        )
        st.plotly_chart(fig1, use_container_width=True)

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=results['Pressure_psia'], y=results['Bg_resFt3_scf'],
            mode='lines+markers', name='Bg',
            line=dict(color='#F59E0B', width=2.5), marker=dict(size=4)
        ))
        fig2.update_layout(
            title="Gas FVF (Bg) vs Pressure",
            xaxis_title="Pressure (psia)", yaxis_title="Bg (res ft³/scf)",
            template="plotly_dark", height=400,
        )
        st.plotly_chart(fig2, use_container_width=True)

        st.markdown("### Complete PVT Table")
        st.dataframe(
            df.style.format({
                'Pressure_psia': '{:.0f}',
                'Z_factor': '{:.4f}',
                'Bg_resFt3_scf': '{:.6f}',
                'Viscosity_cp': '{:.5f}',
            }),
            use_container_width=True
        )

        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download PVT Table (CSV)",
            data=csv,
            file_name="ResIQ_PVT_Results.csv",
            mime="text/csv",
            use_container_width=True
        )