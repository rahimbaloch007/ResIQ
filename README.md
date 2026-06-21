# ResIQ — Reservoir Intelligence Platform

**An independently developed reservoir engineering workbench for gas reservoir analysis, built in Python.**

🔗 **Live App:** [resiq-rahim.streamlit.app](https://resiq-rahim.streamlit.app) *(password protected — contact for demo access)*

Built by **Rahim Ullah** — Petroleum & Gas Engineer (BS, BUITEMS, 2020)

---

## Overview

ResIQ implements industry-standard analytical workflows used by practicing reservoir engineers — covering PVT analysis, material balance, decline curve analysis, well test interpretation, gas deliverability, volumetric reserves estimation, and bottomhole pressure calculation. It was built to demonstrate the application of core reservoir engineering principles through software, using correlations and equations published in standard SPE literature and reservoir engineering textbooks.

The platform is designed around gas reservoirs, with default sample values reflecting typical Pakistani gas field conditions (pressure, temperature, and gas gravity ranges consistent with fields such as Qadirpur and Sui).

---

## Modules

| Module | Description |
|---|---|
| **PVT Analysis** | Z-factor (Hall-Yarborough), gas formation volume factor (Bg), gas viscosity (Lee-Gonzalez-Eakin), pseudocritical properties (Sutton correlation with Wichert-Aziz acid gas correction) |
| **P/Z & Material Balance** | OGIP estimation via P/Z straight-line extrapolation, drive mechanism screening from linearity (R²) |
| **Decline Curve Analysis** | Arps decline curve fitting (exponential, hyperbolic, harmonic), EUR forecasting, production rate projection to economic limit |
| **Well Test Interpretation** | Pseudopressure-based Horner plot analysis, permeability, skin factor (van Everdingen-Hurst), average reservoir pressure (P*) |
| **IPR & Deliverability** | LIT (Laminar-Inertial-Turbulent) method using pseudopressure, AOF (Absolute Open Flow) calculation, deliverability curve generation |
| **Volumetric Reserves** | Deterministic and probabilistic (Monte Carlo) OGIP estimation, P10/P50/P90 uncertainty quantification per SPE-PRMS classification |
| **BHP Calculator** | Static and flowing bottomhole pressure via the average temperature-Z method |
| **Well Report Generator** | Consolidates results from multiple modules into a single professional PDF report |

---

## Technical Approach

All calculations use field-unit, industry-standard correlations:

- **Z-factor:** Hall-Yarborough (1974) iterative correlation, solved via Newton-Raphson
- **Pseudocriticals:** Sutton (1985) correlation with Wichert-Aziz (1972) acid gas correction
- **Pseudopressure m(p):** Numerical integration (Al-Hussainy, Ramey & Crawford, 1966) — used for well test and IPR analysis to maintain accuracy across the full reservoir pressure range, rather than relying on the simplified pressure-squared approximation
- **Decline curves:** Arps (1945) equations, fit via nonlinear least squares with b-factor constrained to physically realistic bounds for conventional gas reservoirs
- **Material balance:** P/Z straight-line method

A key engineering decision made during development: well test and deliverability calculations use **pseudopressure (m(p))** rather than raw pressure. At typical Pakistani reservoir pressures (3,000–5,000 psia), gas viscosity and Z-factor vary enough across the pressure range that a raw-pressure Horner analysis introduces meaningful error. Using m(p) keeps the underlying flow equations linear and accurate regardless of pressure level — this is standard practice in rigorous gas well test analysis.

---

## Tech Stack

- **Backend:** Python (NumPy, SciPy for numerical methods)
- **Frontend:** Streamlit
- **Visualization:** Plotly
- **PDF Reports:** ReportLab
- **Deployment:** Streamlit Community Cloud

---

## Project Structure

```
ResIQ/
├── app.py                      # Main application entry point
├── core/
│   ├── units.py                 # Unit conversion utilities
│   ├── validators.py            # Input validation
│   └── auth.py                  # Authentication
├── modules/
│   ├── pvt/                     # PVT analysis engine + UI
│   ├── material_balance/        # P/Z and material balance
│   ├── decline_curve/           # Arps DCA
│   ├── well_test/               # Horner plot analysis
│   ├── ipr/                     # Gas deliverability (LIT method)
│   ├── volumetric/              # OGIP and Monte Carlo reserves
│   └── bhp/                     # Bottomhole pressure calculator
└── reports/
    └── pdf_generator.py         # PDF report generation
```

---

## Background

This project was built as an independent, self-directed exercise to apply petroleum engineering fundamentals through software — combining a BS in Petroleum & Gas Engineering with practical Python development. It is not intended as a replacement for commercial reservoir engineering software (such as Petrel, Eclipse, or Harmony), nor for professional engineering judgment. Rather, it demonstrates the ability to translate engineering theory into a working, validated analytical tool.

---

## Disclaimer

ResIQ is an independent educational and portfolio project. Calculations are based on published, peer-reviewed correlations, but results should be validated against established commercial software and professional judgment before use in any operational decision-making context.

---

## Contact

**Rahim Ullah**
Petroleum & Gas Engineer
📧 khanrahim706@gmail.com
📍 Islamabad, Pakistan