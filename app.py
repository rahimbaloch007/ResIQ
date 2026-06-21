import streamlit as st
import os

st.set_page_config(
    page_title="ResIQ — Reservoir Intelligence Platform",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stButton>button {
        background-color: #00D4AA;
        color: #0A1628;
        font-weight: bold;
        border-radius: 8px;
    }
    .sidebar-footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        padding: 12px 20px;
        font-size: 12px;
        color: #888888;
        background-color: inherit;
    }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    # ── TOP: Logo + Title ──────────────────────────
    st.markdown("# 🛢️ ResIQ")
    st.markdown("*Reservoir Intelligence Platform*")
    st.divider()

    module = st.selectbox("Select Module", [
        "📊 PVT Analysis",
        "📉 P/Z & Material Balance",
        "📈 Decline Curve Analysis",
        "🔬 Well Test Interpretation",
        "🌊 IPR & Deliverability",
        "📦 Volumetric Reserves",
        "⚡ BHP Calculator",
        "📄 Generate Well Report",
    ])

    # ── BOTTOM: Footer pinned to bottom of sidebar ──
    st.markdown("""
        <div class="sidebar-footer">
            Built by Rahim Ullah<br>
            Petroleum & Gas Engineer
        </div>
    """, unsafe_allow_html=True)

if module == "📊 PVT Analysis":
    from modules.pvt.pvt_ui import render_pvt_module
    render_pvt_module()

elif module == "📉 P/Z & Material Balance":
    from modules.material_balance.mb_ui import render_mb_module
    render_mb_module()

elif module == "📈 Decline Curve Analysis":
    from modules.decline_curve.dca_ui import render_dca_module
    render_dca_module()

elif module == "🔬 Well Test Interpretation":
    from modules.well_test.wt_ui import render_wt_module
    render_wt_module()

elif module == "🌊 IPR & Deliverability":
    from modules.ipr.ipr_ui import render_ipr_module
    render_ipr_module()

elif module == "📦 Volumetric Reserves":
    from modules.volumetric.vol_ui import render_vol_module
    render_vol_module()

elif module == "⚡ BHP Calculator":
    from modules.bhp.bhp_ui import render_bhp_module
    render_bhp_module()

elif module == "📄 Generate Well Report":
    import sys as _sys
    _sys.path.append(os.path.dirname(__file__))
    from reports.pdf_generator import generate_well_report

    st.markdown("## 📄 Generate Well Report")
    st.markdown("*Combines results from PVT, Material Balance, and "
                 "Decline Curve modules into one PDF*")
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        well_name = st.text_input("Well Name", value="Well-1")
    with col2:
        field_name = st.text_input("Field Name", value="Qadirpur Gas Field")

    st.divider()

    st.markdown("### Available Results")
    has_pvt = 'pvt_results' in st.session_state
    has_mb = 'mb_results' in st.session_state
    has_dca = 'dca_results' in st.session_state

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"PVT Analysis: {'✅ Ready' if has_pvt else '⚠️ Not run yet'}")
    c2.markdown(f"Material Balance: {'✅ Ready' if has_mb else '⚠️ Not run yet'}")
    c3.markdown(f"Decline Curve: {'✅ Ready' if has_dca else '⚠️ Not run yet'}")

    if not (has_pvt or has_mb or has_dca):
        st.warning("Run at least one module first (PVT, Material Balance, "
                    "or Decline Curve) to include results in the report.")
    else:
        if st.button("📄 Generate PDF Report",
                      type="primary", use_container_width=True):
            output_path = "ResIQ_Well_Report.pdf"
            generate_well_report(
                output_path,
                well_name=well_name,
                field_name=field_name,
                pvt_results=st.session_state.get('pvt_results'),
                mb_results=st.session_state.get('mb_results'),
                dca_results=st.session_state.get('dca_results'),
            )

            with open(output_path, "rb") as f:
                st.download_button(
                    label="📥 Download Well Report (PDF)",
                    data=f,
                    file_name=f"ResIQ_{well_name}_Report.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            st.success("Report generated successfully!")