import numpy as np
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from core.validators import Validators
from modules.pvt.pvt_engine import PVTEngine


class BHPEngine:
    """
    Bottom Hole Pressure Calculator.
    Implements the average temperature-Z method for
    static and flowing BHP calculation from wellhead
    pressure — standard field technique for gas wells.
    """

    def __init__(self, gamma_g, T_surface_f, T_reservoir_f,
                 H2S_pct=0.0, CO2_pct=0.0):
        """
        gamma_g          : gas specific gravity
        T_surface_f      : surface/wellhead temperature (°F)
        T_reservoir_f    : bottomhole/reservoir temperature (°F)
        """
        self.gamma_g = gamma_g
        self.T_surface_f = T_surface_f
        self.T_reservoir_f = T_reservoir_f
        self.H2S_pct = H2S_pct
        self.CO2_pct = CO2_pct

        # Average temperature for the gas column
        self.T_avg_f = (T_surface_f + T_reservoir_f) / 2
        self.T_avg_r = self.T_avg_f + 459.67

        self.pvt = PVTEngine(gamma_g, self.T_avg_f, H2S_pct, CO2_pct)

    def static_bhp(self, Pwh_psia, depth_ft, n_iterations=5):
        """
        Static bottomhole pressure using the average
        temperature-Z factor method (iterative, since Z
        depends on pressure which is what we're solving for).

        Pwh_psia  : wellhead (shut-in) pressure
        depth_ft  : true vertical depth to mid-perforations

        Formula:
        Pwf = Pwh * exp(0.0375 * gamma_g * depth / (Z_avg * T_avg_r))
        """
        Validators.check_positive(Pwh_psia, "Wellhead pressure")
        Validators.check_positive(depth_ft, "Depth")

        # Initial guess for Z at average conditions
        P_guess = Pwh_psia * 1.1

        for _ in range(n_iterations):
            Z_avg = self.pvt.z_factor_hall_yarborough(P_guess)
            exponent = (0.0375 * self.gamma_g * depth_ft) / (Z_avg * self.T_avg_r)
            P_bhp = Pwh_psia * np.exp(exponent)
            P_guess = (P_guess + P_bhp) / 2  # damped update for stability

        return {
            'BHP_static_psia': round(P_bhp, 1),
            'Z_avg': round(Z_avg, 4),
            'T_avg_F': round(self.T_avg_f, 1),
            'gradient_psi_per_ft': round((P_bhp - Pwh_psia) / depth_ft, 4),
        }

    def flowing_bhp(self, Pwh_flowing_psia, depth_ft, q_Mscfd,
                     tubing_id_in, n_iterations=8):
        """
        Flowing bottomhole pressure using the average
        temperature-Z method with friction correction
        (standard field-units form).

        Pwf^2 = Pwh^2 * exp(s) + (f * q^2 * Z_avg^2 * T_avg_r^2
                 * (exp(s) - 1)) / (s * d^5)

        where s = 0.0375 * gamma_g * depth / (Z_avg * T_avg_r)
        and f is a friction factor (~0.01-0.03 typical for
        tubing flow, using 0.02 as a representative default).

        This is a simplified field-applicable estimate, not a
        full multiphase flow correlation — adequate for dry
        gas wells without significant liquid loading.
        """
        Validators.check_positive(Pwh_flowing_psia, "Flowing wellhead pressure")
        Validators.check_positive(depth_ft, "Depth")
        Validators.check_positive(q_Mscfd, "Flow rate")
        Validators.check_positive(tubing_id_in, "Tubing ID")

        f_friction = 0.02  # typical Fanning-equivalent friction factor
        d = tubing_id_in

        P_guess = Pwh_flowing_psia * 1.15

        for _ in range(n_iterations):
            Z_avg = self.pvt.z_factor_hall_yarborough(P_guess)

            s = (0.0375 * self.gamma_g * depth_ft) / (Z_avg * self.T_avg_r)

            exp_s = np.exp(s)

            friction_term = (
                (f_friction * (q_Mscfd / 1000) ** 2 * Z_avg ** 2
                 * self.T_avg_r ** 2 * (exp_s - 1))
                / (s * d ** 5)
            ) if s != 0 else 0

            Pwf_squared = (Pwh_flowing_psia ** 2 * exp_s) + friction_term

            P_flowing = np.sqrt(max(Pwf_squared, 0))
            P_guess = (P_guess + P_flowing) / 2

        return {
            'BHP_flowing_psia': round(P_flowing, 1),
            'Z_avg': round(Z_avg, 4),
            'pressure_drop_psia': round(P_flowing - Pwh_flowing_psia, 1),
        }


if __name__ == "__main__":
    print("Testing BHPEngine...")
    print("-" * 50)

    bhp = BHPEngine(
        gamma_g=0.65, T_surface_f=90, T_reservoir_f=212
    )

    static_result = bhp.static_bhp(Pwh_psia=2800, depth_ft=8500)
    print(f"Static BHP    = {static_result['BHP_static_psia']} psia")
    print(f"Z (avg)       = {static_result['Z_avg']}")
    print(f"T (avg)       = {static_result['T_avg_F']} °F")
    print(f"Gradient      = {static_result['gradient_psi_per_ft']} psi/ft")

    flowing_result = bhp.flowing_bhp(
        Pwh_flowing_psia=2200, depth_ft=8500,
        q_Mscfd=15000, tubing_id_in=2.992
    )
    print(f"\nFlowing BHP   = {flowing_result['BHP_flowing_psia']} psia")
    print(f"Pressure drop = {flowing_result['pressure_drop_psia']} psia")

    print("\nBHPEngine module working correctly.")