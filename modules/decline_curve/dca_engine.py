import numpy as np
from scipy.optimize import curve_fit
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from core.validators import Validators


class DeclineCurveEngine:
    """
    Arps Decline Curve Analysis Engine.
    Implements exponential, hyperbolic, and harmonic decline
    with automated curve fitting and EUR forecasting.
    """

    @staticmethod
    def arps_rate(t, qi, Di, b):
        """
        General Arps decline equation.
        q(t) = qi / (1 + b*Di*t)^(1/b)     for b > 0
        q(t) = qi * exp(-Di*t)             for b = 0
        """
        if b == 0:
            return qi * np.exp(-Di * t)
        else:
            return qi / np.power(1 + b * Di * t, 1 / b)

    def fit_decline_curve(self, time_array, rate_array, b_fixed=None):
        """
        Fit Arps decline parameters to production history
        using nonlinear least squares.
        """
        t = np.array(time_array, dtype=float)
        q = np.array(rate_array, dtype=float)

        if len(t) < 3:
            raise ValueError("Need at least 3 data points to fit decline curve")

        qi_guess = q[0]
        Di_guess = 0.05

        if b_fixed is not None:
            def model(t, qi, Di):
                return self.arps_rate(t, qi, Di, b_fixed)

            popt, _ = curve_fit(
                model, t, q,
                p0=[qi_guess, Di_guess],
                bounds=([0, 0], [np.inf, 1]),
                maxfev=5000
            )
            qi = popt[0]
            Di = popt[1]
            b = b_fixed
        else:
            def model(t, qi, Di, b):
                return self.arps_rate(t, qi, Di, b)

            popt, _ = curve_fit(
                model, t, q,
                p0=[qi_guess, Di_guess, 0.5],
                bounds=([0, 0, 0], [np.inf, 1, 1.0]),
                maxfev=5000
            )
            qi = popt[0]
            Di = popt[1]
            b = popt[2]
            qi = popt[0]
            Di = popt[1]
            b = popt[2]
            
        q_predicted = self.arps_rate(t, qi, Di, b)
        ss_res = np.sum((q - q_predicted) ** 2)
        ss_tot = np.sum((q - np.mean(q)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

        decline_type = self._classify_decline(b)

        return {
            'qi': round(float(qi), 3),
            'Di_monthly': round(float(Di), 5),
            'Di_annual_pct': round((1 - (1 - Di) ** 12) * 100, 2)
                              if Di < 1 else round(Di * 12 * 100, 2),
            'b': round(float(b), 3),
            'decline_type': decline_type,
            'r_squared': round(float(r_squared), 4),
        }

    def _classify_decline(self, b):
        if b < 0.05:
            return "Exponential"
        elif b > 0.95:
            return "Harmonic"
        else:
            return "Hyperbolic"

    def forecast_production(self, qi, Di, b, time_array):
        t = np.array(time_array, dtype=float)
        return self.arps_rate(t, qi, Di, b).tolist()

    def cumulative_production(self, qi, Di, b, t_months):
        t = np.array(t_months, dtype=float)

        if b == 0:
            Gp = (qi / Di) * (1 - np.exp(-Di * t))
        elif b == 1:
            Gp = (qi / Di) * np.log(1 + Di * t)
        else:
            Gp = (qi / ((1 - b) * Di)) * (
                1 - np.power(1 + b * Di * t, 1 - 1 / b)
            )
        return Gp.tolist()

    def calculate_eur(self, qi, Di, b, q_economic_limit, max_months=600):
        Validators.check_positive(q_economic_limit, "Economic limit rate")

        if q_economic_limit >= qi:
            t_abandon = 0
        elif b == 0:
            t_abandon = -np.log(q_economic_limit / qi) / Di
        else:
            t_abandon = ((qi / q_economic_limit) ** b - 1) / (b * Di)

        t_abandon = min(t_abandon, max_months)

        eur = self.cumulative_production(qi, Di, b, [t_abandon])[0]

        return {
            'time_to_abandonment_months': round(t_abandon, 1),
            'time_to_abandonment_years': round(t_abandon / 12, 1),
            'EUR': round(eur, 2),
        }


if __name__ == "__main__":
    print("Testing DeclineCurveEngine...")
    print("-" * 50)

    dca = DeclineCurveEngine()

    months = [0, 6, 12, 18, 24, 36, 48, 60, 72]
    rates = [45.0, 32.0, 25.5, 21.5, 18.8, 15.5, 13.5, 12.1, 11.0]

    result = dca.fit_decline_curve(months, rates, b_fixed=0.5)

    print(f"qi             = {result['qi']} MMscfd")
    print(f"Di (monthly)   = {result['Di_monthly']}")
    print(f"Di (annual %)  = {result['Di_annual_pct']}%")
    print(f"b-factor       = {result['b']}")
    print(f"Decline type   = {result['decline_type']}")
    print(f"R-squared      = {result['r_squared']}")

    eur_result = dca.calculate_eur(
        result['qi'], result['Di_monthly'], result['b'],
        q_economic_limit=2.0
    )
    print(f"\nTime to abandonment = {eur_result['time_to_abandonment_years']} years")
    print(f"EUR                  = {eur_result['EUR']} MMscf-months equivalent")

    print("\nDeclineCurveEngine module working correctly.")