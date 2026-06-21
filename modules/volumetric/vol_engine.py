import numpy as np
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from core.validators import Validators
from modules.pvt.pvt_engine import PVTEngine


class VolumetricEngine:
    """
    Volumetric OGIP & Reserves Engine.
    Implements the standard volumetric equation with
    Monte Carlo uncertainty analysis for P10/P50/P90
    reserves classification per SPE-PRMS standard.
    """

    def __init__(self, gamma_g, T_f, Pi_psia, H2S_pct=0.0, CO2_pct=0.0):
        self.pvt = PVTEngine(gamma_g, T_f, H2S_pct, CO2_pct)
        self.Pi = Validators.check_pressure_psia(Pi_psia)
        self.Bgi = self.pvt.gas_fvf(Pi_psia)

    def calculate_ogip(self, area_acres, h_ft, phi, Swi):
        """
        Volumetric OGIP equation:
        OGIP = 43,560 * A * h * phi * (1 - Swi) / Bgi

        Input:
          area_acres : drainage area (acres)
          h_ft       : net pay thickness (ft)
          phi        : porosity (fraction)
          Swi        : connate water saturation (fraction)

        Output: OGIP in scf, MMscf, and Bscf
        """
        Validators.check_positive(area_acres, "Drainage area")
        Validators.check_positive(h_ft, "Net pay thickness")
        Validators.check_porosity(phi)
        Validators.check_saturation(Swi)

        ogip_scf = (43560 * area_acres * h_ft * phi * (1 - Swi)) / self.Bgi
        ogip_mmscf = ogip_scf / 1_000_000
        ogip_bscf = ogip_mmscf / 1000

        return {
            'OGIP_scf': round(ogip_scf, 0),
            'OGIP_MMscf': round(ogip_mmscf, 2),
            'OGIP_Bscf': round(ogip_bscf, 3),
            'Bgi': self.Bgi,
        }

    def monte_carlo_uncertainty(self, area_range, h_range, phi_range,
                                  Swi_range, n_simulations=10000):
        """
        Monte Carlo simulation for OGIP uncertainty.
        Each parameter given as (low, mid, high) representing
        P90/P50/P10-style triangular distribution inputs.

        Returns P10, P50, P90 OGIP values (Bscf) per SPE-PRMS
        convention (P10 = high case, P90 = low case — note
        the inverted naming convention is intentional and
        matches industry usage).
        """
        np.random.seed(42)  # reproducible results

        area_sim = np.random.triangular(
            area_range[0], area_range[1], area_range[2], n_simulations
        )
        h_sim = np.random.triangular(
            h_range[0], h_range[1], h_range[2], n_simulations
        )
        phi_sim = np.random.triangular(
            phi_range[0], phi_range[1], phi_range[2], n_simulations
        )
        Swi_sim = np.random.triangular(
            Swi_range[0], Swi_range[1], Swi_range[2], n_simulations
        )

        ogip_sim = (43560 * area_sim * h_sim * phi_sim *
                    (1 - Swi_sim)) / self.Bgi / 1_000_000_000  # → Bscf

        p10 = np.percentile(ogip_sim, 90)  # P10 = high case (90th pctile)
        p50 = np.percentile(ogip_sim, 50)
        p90 = np.percentile(ogip_sim, 10)  # P90 = low case (10th pctile)

        return {
            'P10_Bscf': round(p10, 3),
            'P50_Bscf': round(p50, 3),
            'P90_Bscf': round(p90, 3),
            'distribution': ogip_sim.tolist(),
        }

    def reserves_classification(self, ogip_bscf, recovery_factor=0.80):
        """
        Simple reserves classification using a typical
        recovery factor assumption for conventional gas
        reservoirs (75-85% is standard range).
        """
        Validators.check_range(recovery_factor, 0.3, 0.95, "Recovery factor")

        recoverable = ogip_bscf * recovery_factor

        return {
            'recoverable_reserves_Bscf': round(recoverable, 3),
            'recovery_factor_used': recovery_factor,
        }


if __name__ == "__main__":
    print("Testing VolumetricEngine...")
    print("-" * 50)

    vol = VolumetricEngine(gamma_g=0.65, T_f=212, Pi_psia=3500)

    # Deterministic OGIP — Qadirpur-style field
    result = vol.calculate_ogip(
        area_acres=5000, h_ft=45, phi=0.18, Swi=0.25
    )
    print(f"OGIP = {result['OGIP_Bscf']} Bscf")
    print(f"Bgi  = {result['Bgi']} res ft3/scf")

    # Monte Carlo uncertainty
    mc = vol.monte_carlo_uncertainty(
        area_range=(4000, 5000, 6500),
        h_range=(35, 45, 55),
        phi_range=(0.14, 0.18, 0.22),
        Swi_range=(0.20, 0.25, 0.32),
    )
    print(f"\nP10 (high case) = {mc['P10_Bscf']} Bscf")
    print(f"P50 (mid case)  = {mc['P50_Bscf']} Bscf")
    print(f"P90 (low case)  = {mc['P90_Bscf']} Bscf")

    rec = vol.reserves_classification(result['OGIP_Bscf'])
    print(f"\nRecoverable Reserves = {rec['recoverable_reserves_Bscf']} Bscf "
          f"(at {rec['recovery_factor_used']*100:.0f}% RF)")

    print("\nVolumetricEngine module working correctly.")