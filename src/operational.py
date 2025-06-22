def calculate_operational_emissions(electricity_mmbtu, natural_gas_mmbtu, df_factors):
    """
    Calculates 25-year operational emissions using annual average emissions factors
    for electricity and natural gas from a DataFrame.

    Parameters:
        electricity_mmbtu (float): Total electricity usage over 1 year (MMBtu)
        natural_gas_mmbtu (float): Total natural gas usage over 1 year (MMBtu)
        df_factors (pd.DataFrame): Emission factors per year (kg CO2e/MMBtu)

    Returns:
        dict: {
            "electricity_emissions_kg": float,
            "natural_gas_emissions_kg": float,
            "total_emissions_kg": float
        }
    """

    # Average the 25-year emissions factors (assume 2025-2049 rows are present)
    avg_elec_factor = df_factors['Electricity'].iloc[:25].mean()
    avg_gas_factor = df_factors['Natural Gas'].iloc[:25].mean()

    # Calculate emissions
    elec_emissions = electricity_mmbtu * avg_elec_factor * 25
    gas_emissions = natural_gas_mmbtu * avg_gas_factor * 25
    total_emissions = elec_emissions + gas_emissions

    return {
        "electricity_emissions_kg": elec_emissions,
        "natural_gas_emissions_kg": gas_emissions,
        "total_emissions_kg": total_emissions
    }