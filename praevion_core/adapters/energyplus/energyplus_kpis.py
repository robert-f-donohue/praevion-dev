import pandas as pd

from praevion_core.adapters.energyplus.energyplus_tables import (
    clean_table_with_headers,
    extract_named_table,
)


def extract_total_energy(filepath):
    """
    Extracts total site energy usage for each major end use from an EnergyPlus eplustbl.csv file.
    This function identifies the 'End Uses' table and parses electricity and natural gas values.

    Parameters:
        filepath (string): Path to the EnergyPlus simulation output CSV file (eplustbl.csv)

    Returns:
        dict: {
            "electricity_mmbtu": float,
            "natural_gas_mmbtu": float,
            "site_energy_mmbtu": float
        }
    """

    # STEP 1: Extract End Uses Table and clean
    df = extract_named_table(filepath, "End Uses", "End Uses By Subcategory")
    df = clean_table_with_headers(df)

    # STEP 2: Only keep relevant rows and convert to numeric
    df["Electricity [GJ]"] = pd.to_numeric(df["Electricity [GJ]"], errors="coerce")
    df["Natural Gas [GJ]"] = pd.to_numeric(df["Natural Gas [GJ]"], errors="coerce")
    df["Total Energy Usage [GJ]"] = df["Electricity [GJ]"] + df["Natural Gas [GJ]"]

    GJ_TO_MMBTU = 0.947817

    return {
        "electricity_mmbtu": df["Electricity [GJ]"].sum() * GJ_TO_MMBTU,
        "natural_gas_mmbtu": df["Natural Gas [GJ]"].sum() * GJ_TO_MMBTU,
        "site_energy_mmbtu": df["Total Energy Usage [GJ]"].sum() * GJ_TO_MMBTU,
    }


def extract_zone_area(filepath):
    """
    Parses the 'Zone Summary' section of eplustbl.csv to calculate floor areas of
    apartment and non-apartment zones. Used to normalize embodied carbon and distinguish
    residential vs. circulation area.

    Parameters:
        filepath (string): Path to the EnergyPlus simulation output CSV file (eplustbl.csv)

    Returns:
        dict: {
            "apartment_floor_area_m2": float,
            "non_apartment_floor_area_m2": float,
            "total_floor_area_m2": float,
            "apartment_count": int
        }
    """
    # STEP 1: Extract and clean Zone Summary Table
    df = extract_named_table(filepath, "Zone Summary", "Space Summary")
    df = clean_table_with_headers(df)

    df["Area [m2]"] = pd.to_numeric(df["Area [m2]"], errors="coerce")

    # STEP 2: Classify zones based on name
    apartment_zones = df[df["Zone"].str.contains("Apartment", case=False, na=False)]
    non_apartment_zones = df[~df["Zone"].str.contains("Apartment", case=False, na=False)]

    return {
        "apartment_floor_area_m2": apartment_zones["Area [m2]"].sum(),
        "non_apartment_floor_area_m2": non_apartment_zones["Area [m2]"].sum(),
        "total_floor_area_m2": df["Area [m2]"].sum(),
        "apartment_count": len(apartment_zones),
    }


def extract_construction_areas(filepath):
    """
    Parses the 'Zone Summary' and 'Skylight-Roof-Ratio' sections of eplustbl.csv to extract
    the total exterior wall area, window area, and roof area. These are used to normalize
    embodied carbon values for envelope-related measures.

    Parameters:
        filepath (string): Path to the EnergyPlus simulation output CSV file (eplustbl.csv)

    Returns:
        dict: {
            "wall_area_m2": float,
            "window_area_m2": float,
            "roof_area_m2": float
        }
    """

    # STEP 1: Extract and clean Zone Summary Table
    zone_df = extract_named_table(filepath, "Zone Summary", "Space Summary")
    zone_df = clean_table_with_headers(zone_df)

    zone_df["Wall Area [m2]"] = pd.to_numeric(
        zone_df["Above Ground Gross Wall Area [m2]"], errors="coerce"
    )
    zone_df["Window Area [m2]"] = pd.to_numeric(zone_df["Window Glass Area [m2]"], errors="coerce")

    # Step 2: Extract relevant metrics from table
    wall_area = zone_df["Wall Area [m2]"].sum()
    window_area = zone_df["Window Area [m2]"].sum()

    # Step 3: Extract and clean Skylight-Roof Ratio Table
    roof_df = extract_named_table(filepath, "Skylight-Roof Ratio", "PERFORMANCE")
    roof_df = clean_table_with_headers(roof_df)

    # Transpose because this table is vertical (row keys)
    roof_df_t = roof_df.set_index(roof_df.columns[0]).T

    # Step 4: Extract relevant metrics from table
    try:
        roof_area = pd.to_numeric(roof_df_t["Gross Roof Area [m2]"].iloc[0], errors="coerce")
    except Exception:
        roof_area = 0.0

    return {"wall_area_m2": wall_area, "window_area_m2": window_area, "roof_area_m2": roof_area}
