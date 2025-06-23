import os
import uuid
import pandas as pd
import json
from datetime import datetime, timezone

from src.workflow import extract_measure_selections
from src.parser import extract_total_energy, extract_zone_area, extract_construction_areas
from src.embodied import calculate_embodied_carbon_from_df
from src.operational import calculate_operational_emissions
from src.cost_berdo import calculate_berdo_fine_from_factors
from src.run_simulation import run_osw_and_get_csv_path
from src.generate_osw import generate_osw_from_config

from praevion_async_core.paths import RUN_LOGS_DIR
from praevion_async_core.utils.logging_utils import clean_output_dir

def evaluate_kpis_from_osw_and_csv(osw_path, csv_path, ec_input_path, oc_input_path, threshold_input_path):
    """
    Evaluates key performance indicators (KPIs) for a completed OpenStudio simulation run.

    This function parses the measure selections from a .osw file, extracts relevant
    surface and zone metrics from the associated eplustbl.csv report, and computes both
    embodied and operational carbon values using provided emissions factor tables.

    Parameters:
        osw_path (str): Path to the OpenStudio Workflow (.osw) file used for the run.
        csv_path (str): Path to the corresponding EnergyPlus eplustbl.csv output file.
        ec_input_path (str): Path to the embodied carbon data CSV (e.g. component GWP).
        oc_input_path (str): Path to the operational emissions factor CSV (per fuel type).
        threshold_input_path (str): Path to multifamily BERDO CEI thresholds CSV.

    Returns:
        dict: Flattened dictionary containing:
            - Full paths to the .osw and .csv
            - Selected ECM arguments (measure.argument: value)
            - Embodied carbon metrics (wall_ec_kg, hvac_ec_kg, total_ec_kg, etc.)
            - Operational emissions (electricity_emissions_kg, natural_gas_emissions_kg, total_emissions_kg)
    """

    # Load dataframes
    df_ec = pd.read_csv(ec_input_path)
    df_oc = pd.read_csv(oc_input_path)
    df_thresholds = pd.read_csv(threshold_input_path)

    # Ensure consistent naming for embodied carbon calculations by enforcing all measures be lower case
    df_ec["measure_name"] = df_ec["measure_name"].str.strip().str.lower()
    df_ec["argument_value"] = df_ec["argument_value"].astype(str).str.strip().str.lower()

    # Parse .osw for selections
    selections = extract_measure_selections(osw_path)

    # Extract surface and zone metrics
    surface_areas = extract_construction_areas(csv_path)
    zone_data = extract_zone_area(csv_path)
    total_floor_area_m2 = zone_data['total_floor_area_m2']
    total_floor_area_ft2 = total_floor_area_m2 * 10.7639
    apartment_floor_area_m2 = zone_data['apartment_floor_area_m2']
    apartment_count = zone_data['apartment_count']

    # Extract energy usage by fuel type
    energy = extract_total_energy(csv_path)

    # Compute KPI metrics (Operational, Embodied Carbon, and BERDO fines)
    ec = calculate_embodied_carbon_from_df(
        selections=selections,
        surface_areas=surface_areas,
        total_floor_area=total_floor_area_m2,
        apartment_floor_area=apartment_floor_area_m2,
        apartment_count=apartment_count,
        df_ec=df_ec
    )

    oc = calculate_operational_emissions(
        electricity_mmbtu=energy['electricity_mmbtu'],
        natural_gas_mmbtu=energy['natural_gas_mmbtu'],
        df_factors=df_oc
    )

    fine_usd = calculate_berdo_fine_from_factors(
        electricity_mmbtu=energy['electricity_mmbtu'],
        natural_gas_mmbtu=energy['natural_gas_mmbtu'],
        gsf=total_floor_area_ft2,
        df_factors=df_oc,
        df_thresholds=df_thresholds
    )

    # Combine everything into one dictionary
    return {
        "osw_path": os.path.abspath(osw_path),
        "csv_path": os.path.abspath(csv_path),
        **selections,
        **ec,
        **oc,
        **fine_usd
    }

def evaluate_kpis_from_config(config, df_factors, df_embodied, df_thresholds):
    """
    Run a full simulation + KPI evaluation pipeline from a single ECM config dictionary.

    Parameters:
        config (dict): ECM measure selections.
        df_factors (str): Path to operational carbon inputs CSV.
        df_embodied (str): Path to embodied carbon inputs CSV.
        df_thresholds (str): Path to BERDO threshold CSV.

    Returns:
        dict: Contains both total and component-level metrics for EC, OC, and Cost, as well as file paths and selections.
    """

    # Setup input file paths
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    ecm_options_path = os.path.join(project_root, "3-ecm_definitions", "ecm_options.json")
    seed_file = os.path.join(project_root, "1-openstudio-models", "cluster4-existing-condition.osm")
    weather_file = os.path.join(project_root, "1-openstudio-models", "USA_MA_Boston-Logan.Intl.AP.725090_TMY3.epw")

    # Set label for individual DeepHyper optimization runs
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_id = f"deephyper_{timestamp}_{uuid.uuid4().hex[:8]}"

    # Establish output file paths
    osw_path = os.path.join(project_root, "5-osws", f"{run_id}.osw")
    run_logs_dir = os.path.join(RUN_LOGS_DIR, run_id)

    # Generate OSW
    generate_osw_from_config(
        config=config,
        ecm_options_path=ecm_options_path,
        output_path=osw_path,
        seed_file=seed_file,
        weather_file=weather_file
    )

    try:
        # Run simulation
        csv_path, run_dir = run_osw_and_get_csv_path(osw_path, run_logs_dir)

        # clean directory AFTER parsing context
        clean_output_dir(run_dir)

    except RuntimeError as e:
        if "EnergyPlus Terminated with a Fatal Error" in str(e):
            print("❌ OpenStudio simulation failed due to E+ fatal error. Skipping...")
            return {
                "osw_path": os.path.abspath(osw_path),
                "csv_path": None,
                "total_emissions_kg": float("inf"),
                "total_ec_kg": float("inf"),
                "berdo_fine_usd": float("inf")
            }
        else:
            raise

    return evaluate_kpis_from_osw_and_csv(
        osw_path=osw_path,
        csv_path=csv_path,
        ec_input_path=df_embodied,
        oc_input_path=df_factors,
        threshold_input_path=df_thresholds
    )
