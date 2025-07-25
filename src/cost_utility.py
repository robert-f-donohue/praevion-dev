import pandas as pd

def calculate_discounted_utility_costs(
    electricity_mmbtu: float,
    natural_gas_mmbtu: float,
    df_rates: pd.DataFrame,
    discount_rate: float = 0.03
) -> dict:
    """
    Calculates the discounted total utility cost (electricity + gas) over 25 years.

    Parameters:
        electricity_mmbtu (float): Annual electricity usage (MMBtu)
        natural_gas_mmbtu (float): Annual natural gas usage (MMBtu)
        df_rates (pd.DataFrame): Utility rates by year, must include "Electricity $/MMBtu" and "Natural Gas $/MMBtu"
        discount_rate (float): Real discount rate (e.g., 0.03 for 3%)

    Returns:
        dict: {"discounted_utility_cost_usd": float}
    """
    total_cost_usd = 0.0
    
    # Ensure DataFrame columns are numeric
    df_rates["Electricity $/MMBtu"] = pd.to_numeric(df_rates["Electricity $/MMBtu"], errors="raise")
    df_rates["Natural Gas $/MMBtu"] = pd.to_numeric(df_rates["Natural Gas $/MMBtu"], errors="raise")

    try:
        for i in range(min(25, len(df_rates))):
            elec_rate = df_rates.loc[i, "Electricity $/MMBtu"]
            gas_rate = df_rates.loc[i, "Natural Gas $/MMBtu"]

            annual_cost = electricity_mmbtu * elec_rate + natural_gas_mmbtu * gas_rate
            discounted_cost = annual_cost / ((1 + discount_rate) ** i)
            total_cost_usd += discounted_cost # type: ignore

        return {"discounted_utility_cost_usd": total_cost_usd}

    except Exception as e:
        print("🚨 Exception in calculate_discounted_utility_costs")
        print("electricity_mmbtu:", electricity_mmbtu, type(electricity_mmbtu))
        print("natural_gas_mmbtu:", natural_gas_mmbtu, type(natural_gas_mmbtu))
        print("df_rates columns:", df_rates.columns)
        raise