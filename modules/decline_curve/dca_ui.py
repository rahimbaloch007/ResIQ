import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from modules.decline_curve.dca_engine import DeclineCurveEngine


def render_dca_module():
    """Decline Curve Analysis UI for ResIQ."""

    st.markdown("## 📈 Decline Curve Analysis")
    st.markdown("*Arps decline curve fitting, EUR forecasting*")
    st.divider()

    # ── B-FACTOR SELECTION ──────────────────────────────────
    st.markdown("### Decline Model Settings")
    col1, col2 = st.columns(2)
    with col1:
        fit_mode = st.radio(
            "B-Factor Method",
            ["Fix b (recommended for sparse data)", "Auto-fit b (all 3 parameters)"],
            help="Fixing b based on reservoir analogy is standard "
                 "practice when production history is limited"
        )
    with col2:
        if fit_mode == "Fix b (recommended for sparse data)":
            b_value = st.slider(
                "B-Factor", min_value=0.0, max_value=1.0,
                value=0.5, step=0.05,
                help="0 = Exponential, 0.3-0.6 = typical hyperbolic "
                     "for conventional gas, 1.0 = Harmonic"
            )
        else:
            b_value = None

    st.divider()

    # ── PRODUCTION HISTORY INPUT ────────────────────────────
    st.markdown("### Production History")
    input_method = st.radio(
        "Input Method", ["Manual Entry", "Upload CSV"], horizontal=True
    )

    months = []
    rates = []

    if input_method == "Manual Entry":
        default_data = pd.DataFrame({
            "Month": [0, 6, 12, 18, 24, 36, 48, 60, 72],
            "Rate_MMscfd": [45.0, 32.0, 25.5, 21.5, 18.8, 15.5, 13.5, 12.1, 11.0],
        })
        edited_df = st.data_editor(
            default_data, num_rows="dynamic", use_container_width=True
        )
        months = edited_df["Month"].dropna().tolist()
        rates = edited_df["Rate_MMscfd"].dropna().tolist()
    else:
        st.markdown("""
        **CSV Format Required:**

Month, Rate_MMscfd
    0, 45.0
    6, 32.0
    12, 25.5
""")
        uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
        if uploaded_file is not None:
            df_upload = pd.read_csv(uploaded_file)
            months = df_upload.iloc[:, 0].tolist()
            rates = df_upload.iloc[:, 1].tolist()
            st.dataframe(df_upload, use_container_width=True)

    st.divider()

    # ── ECONOMIC LIMIT ───────────────────────────────────────
    q_econ = st.number_input(
        "Economic Limit Rate (MMscfd)",
        min_value=0.1, value=2.0, step=0.1,
        help="Abandonment rate — well shuts in below this"
    )

    st.divider()

    # ── CALCULATE ─────────────────────────────────────────
    if st.button("⚡ Run Decline Curve Analysis",
                  type="primary", use_container_width=True):

        if len(months) < 3:
            st.error("Need at least 3 valid data points to fit decline curve.")
            return

        dca = DeclineCurveEngine()

        try:
            result = dca.fit_decline_curve(months, rates, b_fixed=b_value)
        except RuntimeError:
            st.error("Curve fitting failed to converge. Try adjusting "
                      "b-factor or check your data for irregularities.")
            return

        eur_result = dca.calculate_eur(
            result['qi'], result['Di_monthly'], result['b'],
            q_economic_limit=q_econ
        )

    # Save to session state for PDF report
        st.session_state['dca_results'] = {
            'qi': result['qi'],
            'decline_type': result['decline_type'],
            'b': result['b'],
            'Di_annual_pct': result['Di_annual_pct'],
            'EUR': eur_result['EUR'],
        }

        # ── METRICS ──────────────────────────────────────
        st.markdown("### Results")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Initial Rate (qi)", f"{result['qi']} MMscfd")
        m2.metric("Decline Type", result['decline_type'])
        m3.metric("R²", f"{result['r_squared']}")
        m4.metric("EUR", f"{eur_result['EUR']:.0f} MMscf")

        st.info(
            f"**Annual Decline Rate:** {result['Di_annual_pct']}%  |  "
            f"**b-factor:** {result['b']}  |  "
            f"**Time to Economic Limit:** {eur_result['time_to_abandonment_years']} years"
        )

        # ── FORECAST PLOT ──────────────────────────────────
        t_history = np.array(months)
        q_history = np.array(rates)

        t_forecast = np.linspace(
            0, eur_result['time_to_abandonment_months'], 100
        )
        q_forecast = dca.forecast_production(
            result['qi'], result['Di_monthly'], result['b'], t_forecast
        )

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=t_history, y=q_history,
            mode='markers', name='Actual Production',
            marker=dict(size=10, color='#00D4AA')
        ))

        fig.add_trace(go.Scatter(
            x=t_forecast, y=q_forecast,
            mode='lines', name='Arps Forecast',
            line=dict(color='#F59E0B', width=2)
        ))

        fig.add_hline(
            y=q_econ, line_dash="dot", line_color="red",
            annotation_text="Economic Limit"
        )

        fig.update_layout(
            title="Production Rate Forecast",
            xaxis_title="Time (months)",
            yaxis_title="Gas Rate (MMscfd)",
            template="plotly_dark",
            height=450,
        )
        st.plotly_chart(fig, use_container_width=True)

        # ── EXPORT ───────────────────────────────────────
        df_forecast = pd.DataFrame({
            "Month": t_forecast,
            "Forecast_Rate_MMscfd": q_forecast,
        })
        csv = df_forecast.to_csv(index=False)
        st.download_button(
            label="📥 Download Forecast (CSV)",
            data=csv,
            file_name="ResIQ_DCA_Forecast.csv",
            mime="text/csv",
            use_container_width=True
        )