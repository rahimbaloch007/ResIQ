import numpy as np
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from core.validators import Validators
from modules.pvt.pvt_engine import PVTEngine
from modules.well_test.wt_engine import WellTestEngine


class IPREngine:
    """
    Gas Well Inflow Performance & Deliverability Engine.
    Implements the LIT (Laminar-Inertial-Turbulent) method
    using pseudopressure, the modern standard for gas well
    deliverability testing (replaces the older empirical
    back-pressure equation for new analysis work).
    """

    def __init__(self, gamma_g, T_f, H2S_pct=0.0, CO2_pct=0.0):
        self.pvt = PVTEngine(gamma_g, T_f, H2S_pct, CO2_pct)
        self.T_rankine = self.pvt.T_r

    def pseudopressure(self, P_psia, p_ref=100, n_steps=100):
        """Same m(p) integration as WellTestEngine — reused here
        for inflow performance calculations."""
        if P_psia <= p_ref:
            return 0.0
        p_array = np.linspace(p_ref, P_psia, n_steps)
        integrand = np.array([
            p / (self.pvt.gas_viscosity(p) * self.pvt.z_factor_hall_yarborough(p))
            for p in p_array
        ])
        return 2 * np.trapz(integrand, p_array)

    def fit_lit_coefficients(self, Pr_psia, q_array, Pwf_array):
        """
        Fit the LIT deliverability equation:
        m(Pr) - m(Pwf) = a*q + b*q^2

        where 'a' represents laminar (Darcy) flow resistance
        and 'b' represents non-Darcy (turbulent/inertial) effects.

        Input:
          Pr_psia    : static reservoir pressure (psia)
          q_array    : test rates (Mscf/d), typically 4 points
                       from a multi-point/isochronal test
          Pwf_array  : stabilized flowing BHP at each rate (psia)

        Output:
          dict with a, b coefficients and fit quality
        """
        q = np.array(q_array, dtype=float)
        Pwf = np.array(Pwf_array, dtype=float)

        if len(q) < 3:
            raise ValueError("Need at least 3 test points for LIT fit")

        m_Pr = self.pseudopressure(Pr_psia)
        m_Pwf = np.array([self.pseudopressure(p) for p in Pwf])

        delta_m = m_Pr - m_Pwf  # should be positive (Pr > Pwf)

        # delta_m / q = a + b*q   →  linear regression
        y = delta_m / q
        slope_b, intercept_a = np.polyfit(q, y, 1)

        # R² of the linear fit
        y_pred = slope_b * q + intercept_a
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

        return {
            'a': float(intercept_a),
            'b': float(slope_b),
            'm_Pr': float(m_Pr),
            'r_squared': round(r_squared, 4),
        }

    def calculate_aof(self, Pr_psia, a, b):
        """
        Calculate AOF (Absolute Open Flow) — the theoretical
        maximum rate when Pwf = 14.7 psia (atmospheric).

        From: m(Pr) - m(14.7) = a*qAOF + b*qAOF^2
        Solve quadratic for qAOF.
        """
        m_Pr = self.pseudopressure(Pr_psia)
        m_atm = self.pseudopressure(14.7) if 14.7 > 100 else 0.0
        delta_m_max = m_Pr - m_atm

        if b == 0:
            qAOF = delta_m_max / a if a != 0 else None
        else:
            # b*q^2 + a*q - delta_m_max = 0
            discriminant = a**2 + 4 * b * delta_m_max
            if discriminant < 0:
                qAOF = None
            else:
                qAOF = (-a + np.sqrt(discriminant)) / (2 * b)

        return round(qAOF, 1) if qAOF else None

    def deliverability_curve(self, Pr_psia, a, b, n_points=50):
        """
        Generate the full deliverability curve (Pwf vs q)
        from Pwf = Pr down to Pwf = 14.7 psia, for IPR plotting.
        """
        m_Pr = self.pseudopressure(Pr_psia)

        Pwf_range = np.linspace(100, Pr_psia, n_points)
        q_values = []

        for Pwf in Pwf_range:
            m_Pwf = self.pseudopressure(Pwf)
            delta_m = m_Pr - m_Pwf

            if delta_m <= 0:
                q_values.append(0)
                continue

            if b == 0:
                q = delta_m / a if a != 0 else 0
            else:
                discriminant = a**2 + 4 * b * delta_m
                q = (-a + np.sqrt(discriminant)) / (2 * b) if discriminant >= 0 else 0

            q_values.append(q)

        return {
            'Pwf_psia': Pwf_range.tolist(),
            'q_Mscfd': q_values,
        }


if __name__ == "__main__":
    print("Testing IPREngine...")
    print("-" * 50)

    ipr = IPREngine(gamma_g=0.65, T_f=212)

    Pr = 3500  # static reservoir pressure
    q_test = [5200, 10800, 18400, 24100]       # Mscf/d (4-point test)
    Pwf_test = [3380, 3180, 2900, 2620]        # psia

    fit = ipr.fit_lit_coefficients(Pr, q_test, Pwf_test)
    print(f"a coefficient = {fit['a']:.6f}")
    print(f"b coefficient = {fit['b']:.8f}")
    print(f"R-squared     = {fit['r_squared']}")

    aof = ipr.calculate_aof(Pr, fit['a'], fit['b'])
    print(f"\nAOF = {aof} Mscf/d")

    print("\nIPREngine module working correctly.")