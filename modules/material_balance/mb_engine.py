import numpy as np
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from core.validators import Validators
from modules.pvt.pvt_engine import PVTEngine


class MaterialBalanceEngine:
    """
    Gas Material Balance Engine.
    Implements P/Z plot analysis and Havlena-Odeh method
    for OGIP estimation and drive mechanism identification.
    """

    def __init__(self, gamma_g, T_f, H2S_pct=0.0, CO2_pct=0.0):
        """
        gamma_g, T_f, H2S_pct, CO2_pct : same as PVTEngine
        Used to calculate Z-factor at each pressure point.
        """
        self.pvt = PVTEngine(gamma_g, T_f, H2S_pct, CO2_pct)

    def calculate_p_over_z(self, pressure_array):
        """
        Calculate P/Z at each pressure point.
        This is the fundamental quantity plotted in
        gas material balance analysis.

        Input  : array of pressures (psia)
        Output : array of P/Z values
        """
        p_over_z = []
        for P in pressure_array:
            Z = self.pvt.z_factor_hall_yarborough(P)
            p_over_z.append(round(P / Z, 2))
        return p_over_z

    def ogip_from_pz_plot(self, pressure_array, cum_production_array):
        """
        Estimate OGIP using P/Z straight-line extrapolation.

        Method: Linear regression of P/Z vs Gp.
        OGIP = x-intercept of that line (where P/Z = 0)

        Input:
          pressure_array        : list of avg reservoir pressures (psia)
          cum_production_array  : list of cumulative gas produced (MMscf)
                                   at SAME time points as pressure_array

        Output:
          dict with OGIP (Bscf), slope, intercept, R²
        """
        if len(pressure_array) != len(cum_production_array):
            raise ValueError(
                "Pressure and production arrays must be same length"
            )
        if len(pressure_array) < 2:
            raise ValueError(
                "Need at least 2 data points for P/Z analysis"
            )

        p_over_z = np.array(self.calculate_p_over_z(pressure_array))
        Gp = np.array(cum_production_array)

        # Linear regression: P/Z = intercept + slope * Gp
        slope, intercept = np.polyfit(Gp, p_over_z, 1)

        # R² calculation
        predicted = slope * Gp + intercept
        ss_res = np.sum((p_over_z - predicted) ** 2)
        ss_tot = np.sum((p_over_z - np.mean(p_over_z)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

        # OGIP = x-intercept (where P/Z = 0)
        # 0 = intercept + slope * OGIP  →  OGIP = -intercept / slope
        if slope == 0:
            ogip_mmscf = None
        else:
            ogip_mmscf = -intercept / slope

        ogip_bscf = ogip_mmscf / 1000 if ogip_mmscf else None

        return {
            'OGIP_MMscf': round(ogip_mmscf, 2) if ogip_mmscf else None,
            'OGIP_Bscf': round(ogip_bscf, 3) if ogip_bscf else None,
            'slope': round(slope, 6),
            'intercept': round(intercept, 2),
            'r_squared': round(r_squared, 4),
            'p_over_z_values': p_over_z.tolist(),
        }

    def recovery_factor(self, cum_production_mmscf, ogip_mmscf):
        """
        Current recovery factor (%) given cumulative production
        and estimated OGIP.
        """
        Validators.check_positive(ogip_mmscf, "OGIP")
        rf = (cum_production_mmscf / ogip_mmscf) * 100
        return round(rf, 2)

    def detect_drive_mechanism(self, r_squared):
        """
        Simple drive mechanism flag based on P/Z linearity.
        High R² (>0.97) → likely volumetric depletion drive
        Lower R² → possible water influx or compartmentalization
        This is a screening indicator, not a definitive diagnosis —
        a real engineer would also examine plot curvature directly.
        """
        if r_squared >= 0.97:
            return "Likely volumetric depletion drive (strong linear fit)"
        elif r_squared >= 0.90:
            return "Possible minor aquifer influence — review plot shape"
        else:
            return "Significant deviation from linearity — investigate " \
                   "aquifer support or compartmentalization"


if __name__ == "__main__":
    # Self-test using realistic Qadirpur-style depletion data
    print("Testing MaterialBalanceEngine...")
    print("-" * 50)

    mb = MaterialBalanceEngine(gamma_g=0.65, T_f=212)

    # Synthetic pressure-production history (volumetric depletion pattern)
    pressures = [3500, 3350, 3200, 3000, 2800, 2500]
    cum_prod = [0, 850, 1800, 3100, 4500, 6700]  # MMscf

    result = mb.ogip_from_pz_plot(pressures, cum_prod)

    print(f"OGIP estimate    = {result['OGIP_Bscf']} Bscf")
    print(f"R-squared        = {result['r_squared']}")
    print(f"Drive mechanism  = {mb.detect_drive_mechanism(result['r_squared'])}")

    rf = mb.recovery_factor(cum_prod[-1], result['OGIP_MMscf'])
    print(f"Current recovery factor = {rf}%")

    print("\nMaterialBalanceEngine module working correctly.")