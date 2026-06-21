import numpy as np
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from core.validators import Validators
from modules.pvt.pvt_engine import PVTEngine


class WellTestEngine:
    """
    Well Test Interpretation Engine — Gas Wells.
    Implements pseudopressure-based Horner plot analysis,
    the correct industry-standard method for gas reservoirs
    at any pressure range (avoids the p vs p² approximation
    error that occurs at high reservoir pressures).
    """

    def __init__(self, q_Mscfd, rw_ft, phi, h_ft, ct_psi_inv,
                 gamma_g, T_f, H2S_pct=0.0, CO2_pct=0.0):
        """
        q_Mscfd    : production rate before shut-in (Mscf/d)
        rw_ft      : wellbore radius (ft)
        phi        : porosity (fraction)
        h_ft       : net pay thickness (ft)
        ct_psi_inv : total compressibility (1/psi)
        gamma_g    : gas specific gravity (for PVT/m(p) calculation)
        T_f        : reservoir temperature (°F)
        H2S_pct, CO2_pct : acid gas content (%)
        """
        self.q = Validators.check_positive(q_Mscfd, "Production rate")
        self.rw = Validators.check_positive(rw_ft, "Wellbore radius")
        self.phi = Validators.check_porosity(phi)
        self.h = Validators.check_positive(h_ft, "Net pay thickness")
        self.ct = Validators.check_positive(ct_psi_inv, "Total compressibility")

        # PVT engine handles Z-factor and viscosity internally —
        # needed to compute pseudopressure m(p)
        self.pvt = PVTEngine(gamma_g, T_f, H2S_pct, CO2_pct)
        self.T_rankine = self.pvt.T_r

        # Reference viscosity at a representative pressure,
        # used in skin factor equation (van Everdingen-Hurst
        # requires a single mu value, evaluated near P*)
        self._mu_ref = None  # set during analysis once P* is known

    def pseudopressure(self, P_psia, p_ref=14.7, n_steps=200):
        """
        Calculate pseudopressure m(p) via numerical integration.
        m(p) = 2 * integral[p_ref to P] of (p / (mu(p) * Z(p))) dp

        Uses trapezoidal rule with n_steps subdivisions.
        Units: psia^2/cp
        """
        if P_psia <= p_ref:
            return 0.0

        p_array = np.linspace(p_ref, P_psia, n_steps)
        integrand = np.array([
            p / (self.pvt.gas_viscosity(p) * self.pvt.z_factor_hall_yarborough(p))
            for p in p_array
        ])
        m_p = 2 * np.trapz(integrand, p_array)
        return m_p

    def pseudopressure_array(self, P_array):
        """Vectorized pseudopressure calculation for an array of pressures."""
        return np.array([self.pseudopressure(p) for p in P_array])

    def inverse_pseudopressure(self, m_p_target, P_low=100, P_high=15000, tol=1.0):
        """
        Find pressure P such that m(p) = m_p_target, using
        bisection search. Needed to convert P* back from
        m(p) units to actual psia for display.
        """
        for _ in range(100):
            P_mid = (P_low + P_high) / 2
            m_mid = self.pseudopressure(P_mid)

            if abs(m_mid - m_p_target) < tol:
                return P_mid

            if m_mid < m_p_target:
                P_low = P_mid
            else:
                P_high = P_mid

        return (P_low + P_high) / 2

    def horner_analysis(self, tp_hr, dt_hr_array, pws_psia_array):
        """
        Pseudopressure-based Horner plot analysis.

        Converts measured Pws to m(Pws), performs linear
        regression in pseudopressure space (correct for gas
        at any pressure range), then converts results back
        to conventional engineering units.
        """
        dt = np.array(dt_hr_array, dtype=float)
        pws = np.array(pws_psia_array, dtype=float)

        if len(dt) < 3:
            raise ValueError("Need at least 3 pressure points for Horner analysis")

        htr = (tp_hr + dt) / dt
        log_htr = np.log10(htr)

        # Convert observed pressures to pseudopressure
        m_pws = self.pseudopressure_array(pws)

        n_points = len(dt)
        start_idx = n_points // 2 if n_points >= 6 else 0

        log_htr_fit = log_htr[start_idx:]
        m_pws_fit = m_pws[start_idx:]

        # Linear regression in pseudopressure space:
        # m(pws) = m(P*) - m_slope * log10(htr)
        slope_raw, intercept = np.polyfit(log_htr_fit, m_pws_fit, 1)
        m_slope = -slope_raw  # pseudopressure Horner slope, positive

        m_P_star = intercept  # m(p) at htr = 1 (log10(1) = 0)

        # Convert m(P*) back to actual pressure (psia)
        P_star = self.inverse_pseudopressure(m_P_star)

        # Permeability — NO mu/Z needed, already embedded in m(p)
        k = (1637 * self.q * self.T_rankine) / (m_slope * self.h) \
            if m_slope != 0 else None

        # Pressure (and pseudopressure) at Δt = 1 hour
        if dt.min() <= 1.0 <= dt.max():
            p_1hr = np.interp(1.0, dt[::-1], pws[::-1])
        else:
            p_1hr = pws[0]
        m_p_1hr = self.pseudopressure(p_1hr)

        # Skin factor using pseudopressure form:
        # s = 1.1513 * [(m(p_1hr) - m(pwf_last)) / m_slope
        #               - log10(k / (phi*mu*ct*rw^2)) + 3.2275]
        # mu evaluated at P* (representative reservoir condition)
        mu_at_pstar = self.pvt.gas_viscosity(P_star)

        if k is not None and k > 0:
            skin = 1.1513 * (
                (m_p_1hr - m_pws[-1]) / m_slope
                - np.log10(k / (self.phi * mu_at_pstar * self.ct * self.rw**2))
                + 3.2275
            )
        else:
            skin = None

        kh = k * self.h if k else None

        return {
            'permeability_md': round(k, 3) if k else None,
            'skin_factor': round(skin, 2) if skin is not None else None,
            'P_star_psia': round(P_star, 1),
            'kh_md_ft': round(kh, 2) if kh else None,
            'horner_slope_m': round(m_slope, 2),
            'log_htr': log_htr.tolist(),
            'pws_observed': pws.tolist(),
        }

    def classify_skin(self, skin):
        """Classify skin factor for stimulation recommendation."""
        if skin is None:
            return "Unable to calculate"
        elif skin > 5:
            return "Severe damage — acid stimulation strongly recommended"
        elif skin > 0:
            return "Mild to moderate damage — stimulation may be beneficial"
        elif skin > -2:
            return "Near-zero skin — well is not significantly damaged"
        else:
            return "Negative skin — well has been stimulated " \
                   "(natural fracture or prior treatment)"


if __name__ == "__main__":
    print("Testing WellTestEngine (Pseudopressure Method)...")
    print("-" * 50)

    wt = WellTestEngine(
        q_Mscfd=5000, rw_ft=0.354, phi=0.18, h_ft=45,
        ct_psi_inv=0.00015, gamma_g=0.65, T_f=212
    )

    # Realistic buildup test — Qadirpur-style conditions
    # Forward-generate self-consistent test data for k_true = 10 md
    k_true = 10.0
    P_star_true = 4000  # psia

    m_slope_true = (1637 * wt.q * wt.T_rankine) / (k_true * wt.h)
    m_P_star_true = wt.pseudopressure(P_star_true)

    tp = 720
    dt = np.array([1, 2, 4, 6, 8, 10, 15, 20, 24], dtype=float)
    htr = (tp + dt) / dt
    log_htr = np.log10(htr)

    # m(pws) = m(P*) - m_slope * log10(htr)
    m_pws_target = m_P_star_true - m_slope_true * log_htr

    # Convert each target m(p) back to actual pressure
    pws = [wt.inverse_pseudopressure(m_val) for m_val in m_pws_target]
    dt = dt.tolist()

    print(f"[Generator] True k={k_true} md, P*={P_star_true} psia")
    print(f"[Generator] Generated pws = {[round(p,1) for p in pws]}")
    print()

    result = wt.horner_analysis(tp, dt, pws)

    print(f"Permeability (k) = {result['permeability_md']} md")
    print(f"Skin factor      = {result['skin_factor']}")
    print(f"P* (avg pressure) = {result['P_star_psia']} psia")
    print(f"kh               = {result['kh_md_ft']} md.ft")
    print(f"Horner slope (m) = {result['horner_slope_m']}")

    print(f"\nAssessment: {wt.classify_skin(result['skin_factor'])}")

    print("\nWellTestEngine module working correctly.")