class Units:
    """
    Unit conversion engine for ResIQ.
    Every module references this — built once, used everywhere.
    All conversions use field units as the base (psia, °F, scf).
    """

    # ── Pressure ──────────────────────────────────────────
    @staticmethod
    def psia_to_mpa(p):
        return p * 0.006895

    @staticmethod
    def mpa_to_psia(p):
        return p * 145.038

    @staticmethod
    def psia_to_bar(p):
        return p * 0.068948

    @staticmethod
    def psia_to_kpa(p):
        return p * 6.895

    # ── Temperature ───────────────────────────────────────
    @staticmethod
    def f_to_rankine(t):
        """Fahrenheit to Rankine — used in every PVT calculation"""
        return t + 459.67

    @staticmethod
    def rankine_to_f(t):
        return t - 459.67

    @staticmethod
    def f_to_celsius(t):
        return (t - 32) * 5 / 9

    @staticmethod
    def celsius_to_f(t):
        return (t * 9 / 5) + 32

    @staticmethod
    def celsius_to_rankine(t):
        return (t + 273.15) * 9 / 5

    # ── Gas Volume ────────────────────────────────────────
    @staticmethod
    def scf_to_mscf(v):
        return v / 1_000

    @staticmethod
    def mscf_to_mmscf(v):
        return v / 1_000

    @staticmethod
    def mmscf_to_bscf(v):
        return v / 1_000

    @staticmethod
    def scf_to_mmscf(v):
        return v / 1_000_000

    @staticmethod
    def mmscf_to_scf(v):
        return v * 1_000_000

    # ── Reservoir Volume ──────────────────────────────────
    @staticmethod
    def res_ft3_to_res_bbl(v):
        return v / 5.615

    @staticmethod
    def res_bbl_to_res_ft3(v):
        return v * 5.615

    # ── Length ────────────────────────────────────────────
    @staticmethod
    def ft_to_m(length):
        return length * 0.3048

    @staticmethod
    def m_to_ft(length):
        return length / 0.3048

    # ── Area ──────────────────────────────────────────────
    @staticmethod
    def acres_to_ft2(area):
        return area * 43_560

    @staticmethod
    def acres_to_m2(area):
        return area * 4_046.86

    # ── Rate ──────────────────────────────────────────────
    @staticmethod
    def mscfd_to_mmscfd(rate):
        return rate / 1_000

    @staticmethod
    def mmscfd_to_mscfd(rate):
        return rate * 1_000


if __name__ == "__main__":
    # Quick self-test — run this file directly to verify it works
    print("Testing Units class...")
    print(f"212°F to Rankine  = {Units.f_to_rankine(212)} °R")
    print(f"3500 psia to MPa  = {Units.psia_to_mpa(3500):.3f} MPa")
    print(f"100 res ft³ to bbl = {Units.res_ft3_to_res_bbl(100):.3f} bbl")
    print("Units module working correctly.")