class ValidationError(Exception):
    """Custom exception for ResIQ input validation failures"""
    pass


class Validators:
    """
    Input validation for ResIQ.
    Prevents bad data from breaking engineering calculations.
    Every module input passes through here before calculation.
    """

    @staticmethod
    def check_positive(value, name="Value"):
        """Ensures a value is greater than zero"""
        if value <= 0:
            raise ValidationError(f"{name} must be positive. Got: {value}")
        return value

    @staticmethod
    def check_range(value, min_val, max_val, name="Value"):
        """Ensures a value falls within an expected engineering range"""
        if not (min_val <= value <= max_val):
            raise ValidationError(
                f"{name} = {value} is outside valid range "
                f"[{min_val}, {max_val}]"
            )
        return value

    @staticmethod
    def check_gas_gravity(gamma_g):
        """
        Gas specific gravity check.
        Valid range for Sutton correlation: 0.55 - 0.90
        """
        return Validators.check_range(
            gamma_g, 0.55, 0.90, "Gas Specific Gravity"
        )

    @staticmethod
    def check_temperature_f(temp_f):
        """
        Reservoir temperature check (°F).
        Valid range for Pakistani gas reservoirs: 80 - 400°F
        """
        return Validators.check_range(
            temp_f, 80, 400, "Reservoir Temperature (°F)"
        )

    @staticmethod
    def check_pressure_psia(pressure):
        """
        Reservoir pressure check (psia).
        Valid range: 100 - 15000 psia
        """
        return Validators.check_range(
            pressure, 100, 15000, "Pressure (psia)"
        )

    @staticmethod
    def check_mole_fraction(value, name="Mole fraction"):
        """
        Ensures a mole fraction (like H2S%, CO2%) is between 0 and 1
        Input is expected as a fraction, not percentage
        """
        return Validators.check_range(value, 0.0, 1.0, name)

    @staticmethod
    def check_porosity(phi):
        """
        Porosity check.
        Valid range: 0.01 - 0.40 (1% to 40%)
        """
        return Validators.check_range(phi, 0.01, 0.40, "Porosity")

    @staticmethod
    def check_saturation(sw):
        """
        Water saturation check.
        Valid range: 0.05 - 0.95
        """
        return Validators.check_range(sw, 0.05, 0.95, "Water Saturation")


if __name__ == "__main__":
    # Quick self-test
    print("Testing Validators class...")

    print(f"Gas gravity 0.65 → {Validators.check_gas_gravity(0.65)}")
    print(f"Temperature 212°F → {Validators.check_temperature_f(212)}")
    print(f"Pressure 3500 psia → {Validators.check_pressure_psia(3500)}")

    try:
        Validators.check_gas_gravity(1.5)  # Should fail
    except ValidationError as e:
        print(f"Correctly caught bad input: {e}")

    print("Validators module working correctly.")