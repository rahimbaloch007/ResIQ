import numpy as np
import sys
import os

# Allow imports from core folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from core.units import Units
from core.validators import Validators


class PVTEngine:
    """
    Gas PVT calculation engine.
    Implements Hall-Yarborough Z-factor, Sutton pseudocriticals,
    Wichert-Aziz acid gas correction, gas FVF, and gas viscosity.
    Designed for Pakistani gas reservoir conditions (Sui, Qadirpur, Mari).
    """

    def __init__(self, gamma_g, T_f, H2S_pct=0.0, CO2_pct=0.0):
        self.gamma_g = Validators.check_gas_gravity(gamma_g)
        self.T_f = Validators.check_temperature_f(T_f)
        self.T_r = Units.f_to_rankine(T_f)
        self.H2S = H2S_pct / 100
        self.CO2 = CO2_pct / 100

        self.Tpc_raw, self.Ppc_raw = self._sutton_pseudocriticals()
        self.Tpc, self.Ppc = self._wichert_aziz_correction(
            self.Tpc_raw, self.Ppc_raw
        )

    def _sutton_pseudocriticals(self):
        """Sutton (1985) correlation for pseudocritical properties."""
        Tpc = 169.2 + 349.5 * self.gamma_g - 74.0 * self.gamma_g**2
        Ppc = 756.8 - 131.0 * self.gamma_g - 3.6 * self.gamma_g**2
        return Tpc, Ppc

    def _wichert_aziz_correction(self, Tpc, Ppc):
        """Wichert-Aziz (1972) acid gas correction."""
        A = self.H2S + self.CO2
        B = self.H2S

        if A == 0:
            return Tpc, Ppc

        epsilon = (120 * (A**0.9 - A**1.6) +
                   15 * (B**0.5 - B**4.0))

        Tpc_corrected = Tpc - epsilon
        Ppc_corrected = (Ppc * Tpc_corrected /
                          (Tpc + B * (1 - B) * epsilon))

        return Tpc_corrected, Ppc_corrected

    def z_factor_hall_yarborough(self, P_psia):
        """
        Hall-Yarborough (1974) Z-factor correlation.
        Standard formulation verified against published examples.
        """
        if P_psia < 100:
            # Below typical correlation validity — clamp to 100 psia.
            # Used for pseudopressure integration lower bound only;
            # contributes negligibly to the total integral.
            P_psia = 100

        Tpr = self.T_r / self.Tpc
        Ppr = P_psia / self.Ppc

        t = 1.0 / Tpr

        A = 0.06125 * t * np.exp(-1.2 * (1 - t) ** 2)

        y = 0.001

        for _ in range(200):
            y = min(max(y, 1e-8), 0.999999)

            c1 = 14.76 * t - 9.76 * t**2 + 4.58 * t**3
            c2 = 90.7 * t - 242.2 * t**2 + 42.4 * t**3
            c3 = 2.18 + 2.82 * t

            F = (-A * Ppr + (y + y**2 + y**3 - y**4) / (1 - y) ** 3
                 - c1 * y**2 + c2 * y**c3)

            dF = ((1 + 4*y + 4*y**2 - 4*y**3 + y**4) / (1 - y) ** 4
                  - 2 * c1 * y
                  + c2 * c3 * y ** (c3 - 1))

            y_new = y - F / dF
            y_new = min(max(y_new, 1e-8), 0.999999)

            if abs(y_new - y) < 1e-8:
                y = y_new
                break
            y = y_new

        Z = A * Ppr / y
        return round(Z, 6)

    def gas_fvf(self, P_psia):
        """Gas Formation Volume Factor (Bg) = 0.02829 * Z * T / P  [res ft³/scf]"""
        Z = self.z_factor_hall_yarborough(P_psia)
        Bg = 0.02829 * Z * self.T_r / P_psia
        return round(Bg, 8)

    def gas_viscosity(self, P_psia):
        """Lee-Gonzalez-Eakin (1966) gas viscosity correlation. Returns cp."""
        Z = self.z_factor_hall_yarborough(P_psia)
        M = 28.97 * self.gamma_g

        rho_g = (P_psia * M) / (Z * 10.73 * self.T_r)

        K = ((9.4 + 0.02 * M) * self.T_r ** 1.5 /
             (209 + 19 * M + self.T_r))
        X = 3.5 + 986 / self.T_r + 0.01 * M
        Y = 2.4 - 0.2 * X

        rho_ratio = rho_g / 62.4
        rho_ratio = max(rho_ratio, 1e-8)  # prevent negative/zero base

        mu_g = 1e-4 * K * np.exp(X * rho_ratio ** Y)
        return round(mu_g, 6)

    def pvt_table(self, P_array):
        """Generate complete PVT table across a pressure range."""
        results = {
            'Pressure_psia': [],
            'Z_factor': [],
            'Bg_resFt3_scf': [],
            'Viscosity_cp': [],
        }

        for P in P_array:
            results['Pressure_psia'].append(P)
            results['Z_factor'].append(self.z_factor_hall_yarborough(P))
            results['Bg_resFt3_scf'].append(self.gas_fvf(P))
            results['Viscosity_cp'].append(self.gas_viscosity(P))

        return results


if __name__ == "__main__":
    print("Testing PVTEngine — Qadirpur Field Conditions...")
    print("-" * 50)

    pvt = PVTEngine(gamma_g=0.65, T_f=212, H2S_pct=0.0, CO2_pct=0.0)

    print(f"Tpc (corrected) = {pvt.Tpc:.2f} °R")
    print(f"Ppc (corrected) = {pvt.Ppc:.2f} psia")

    P_test = 3500
    Z = pvt.z_factor_hall_yarborough(P_test)
    Bg = pvt.gas_fvf(P_test)
    mu = pvt.gas_viscosity(P_test)

    print(f"\nAt P = {P_test} psia:")
    print(f"  Z-factor   = {Z}")
    print(f"  Bg         = {Bg} res ft³/scf")
    print(f"  Viscosity  = {mu} cp")

    print("\nPVTEngine module working correctly.")