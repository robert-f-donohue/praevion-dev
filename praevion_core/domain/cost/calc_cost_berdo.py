import pandas as pd


def calculate_berdo_fine_from_factors(
    electricity_mmbtu: float,
    natural_gas_mmbtu: float,
    gsf: float,
    df_factors: pd.DataFrame,
    df_thresholds: pd.DataFrame,
    discount_rate: float = 0.03,  # 3% real discount rate
) -> dict:
    """
    Calculates the discounted total BERDO fine over a 25-year period.

    Parameters:
        electricity_mmbtu (float): Annual electricity usage (MMBtu)
        natural_gas_mmbtu (float): Annual natural gas usage (MMBtu)
        gsf (float): Gross floor area in square feet
        df_factors (pd.DataFrame): Emissions factors by year (kg CO2e/MMBtu)
        df_thresholds (pd.DataFrame): BERDO CEI thresholds by year (kg CO2e/ft²/yr)
        discount_rate (float): Real discount rate (e.g., 0.03 for 3%)

    Returns:
        dict: {"berdo_fine_usd": float}, total discounted fine over 25 years (min $1)
    """
    total_fine_usd = 0.0

    try:
        # Calculate fine year-by-year
        for i in range(min(25, len(df_factors))):
            elec_factor = df_factors.loc[i, "Electricity"]
            gas_factor = df_factors.loc[i, "Natural Gas"]
            threshold = df_thresholds.loc[i, "Emissions Threshold (kg CO2e/ft2/yr)"]

            # Calculate total emissions and CEI
            emissions_kg = electricity_mmbtu * elec_factor + natural_gas_mmbtu * gas_factor
            cei_kg_per_ft2 = emissions_kg / gsf

            # Apply fine only if above threshold
            if cei_kg_per_ft2 > threshold:  # type: ignore
                excess = cei_kg_per_ft2 - threshold
                fine_tons = (excess * gsf) / 1000  # kg to metric tons
                annual_fine = fine_tons * 234  # $234/ton CO2e

                # Apply present value discount
                discounted_fine = annual_fine / ((1 + discount_rate) ** i)
                total_fine_usd += discounted_fine  # type: ignore

        return {"berdo_fine_usd": max(total_fine_usd, 1)}  # type: ignore

    except Exception:
        print("🚨 Exception in calculate_berdo_fine_from_factors")
        print("electricity_mmbtu:", electricity_mmbtu, type(electricity_mmbtu))
        print("natural_gas_mmbtu:", natural_gas_mmbtu, type(natural_gas_mmbtu))
        print("gsf:", gsf, type(gsf))
        print("df_factors columns:", df_factors.columns)
        print("df_thresholds columns:", df_thresholds.columns)
        raise
