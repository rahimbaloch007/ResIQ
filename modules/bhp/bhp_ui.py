import streamlit as st
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from modules.bhp.bhp_engine import BHPEngine


def render_bhp_module():
    """BHP Calculator UI for ResIQ."""

    st.markdown("## ⚡ BHP Calculator")
    st.markdown("*Static and flowing bottomhole pressure from wellhead data*")
    st.divider()

    # ── FLUID & TEMPERATURE PROPERTIES ──────────────────────
    st.markdown("### Fluid & Temperature Properties")
    col1, col2, col3 = st.columns(3)
    with col1:
        gamma_g = st.number_input(
            "Gas Specific Gravity", min_value=0.55, max_value=0.90,
            value=0.65, step=0.01, key="bhp_gamma"
        )
    with col2:
        T_surface = st.number_input(
            "Surface Temperature (°F)", min_value=40, max_value=150,
            value=90, key="bhp_tsurf"
        )
    with col3:
        T_reservoir = st.number_input(
            "Reservoir Temperature (°F)", min_value=80, max_value=400,
            value=212, key="bhp_tres"
        )

    st.divider()

    # ── WELL GEOMETRY ──────────────────────────────────────
    st.markdown("### Well Geometry")
    depth_ft = st.number_input(
        "True Vertical Depth to Mid-Perforations (ft)",
        min_value=100.0, value=8500.0, key="bhp_depth"
    )

    st.divider()

    # ── TABS FOR STATIC VS FLOWING ──────────────────────────
    tab1, tab2 = st.tabs(["📍 Static BHP", "💨 Flowing BHP"])

    with tab1:
        st.markdown("### Static Bottomhole Pressure")
        Pwh_static = st.number_input(
            "Wellhead Shut-in Pressure (psia)",
            min_value=14.7, value=2800.0, key="bhp_pwh_static"
        )

        if st.button("⚡ Calculate Static BHP",
                      type="primary", use_container_width=True, key="btn_static"):
            bhp = BHPEngine(gamma_g, T_surface, T_reservoir)
            result = bhp.static_bhp(Pwh_static, depth_ft)

            m1, m2, m3 = st.columns(3)
            m1.metric("Static BHP", f"{result['BHP_static_psia']} psia")
            m2.metric("Avg Z-factor", f"{result['Z_avg']}")
            m3.metric("Gradient", f"{result['gradient_psi_per_ft']} psi/ft")

            st.info(
                f"At a wellhead pressure of {Pwh_static} psia and "
                f"depth of {depth_ft:.0f} ft, the static bottomhole "
                f"pressure is **{result['BHP_static_psia']} psia** — "
                f"using the average temperature-Z method."
            )

    with tab2:
        st.markdown("### Flowing Bottomhole Pressure")
        col4, col5 = st.columns(2)
        with col4:
            Pwh_flowing = st.number_input(
                "Flowing Wellhead Pressure (psia)",
                min_value=14.7, value=2200.0, key="bhp_pwh_flowing"
            )
            q_rate = st.number_input(
                "Gas Flow Rate (Mscf/d)",
                min_value=1.0, value=15000.0, key="bhp_q"
            )
        with col5:
            tubing_id = st.number_input(
                "Tubing Inner Diameter (inches)",
                min_value=1.0, value=2.992, step=0.001, key="bhp_tubing"
            )

        if st.button("⚡ Calculate Flowing BHP",
                      type="primary", use_container_width=True, key="btn_flowing"):
            bhp = BHPEngine(gamma_g, T_surface, T_reservoir)
            result = bhp.flowing_bhp(Pwh_flowing, depth_ft, q_rate, tubing_id)

            m1, m2, m3 = st.columns(3)
            m1.metric("Flowing BHP", f"{result['BHP_flowing_psia']} psia")
            m2.metric("Avg Z-factor", f"{result['Z_avg']}")
            m3.metric("Pressure Drop", f"{result['pressure_drop_psia']} psia")

            st.info(
                f"At a flowing wellhead pressure of {Pwh_flowing} psia, "
                f"flowing at {q_rate:,.0f} Mscf/d through "
                f"{tubing_id}\" tubing, the flowing bottomhole pressure "
                f"is **{result['BHP_flowing_psia']} psia** — combining "
                f"gas column weight and frictional pressure drop."
            )

            st.caption(
                "Note: This uses a simplified average T-Z method with "
                "friction correction, suitable for dry gas wells without "
                "significant liquid loading. For complex multiphase flow "
                "scenarios, dedicated nodal analysis software is recommended."
            )