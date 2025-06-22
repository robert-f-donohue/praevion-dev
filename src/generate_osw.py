import os
import json
from praevion_async_core.utils.logging_utils import clean_and_prepare_osw_paths

def generate_osw_from_config(config, ecm_options_path, output_path, seed_file, weather_file):
    """
    Generates an OpenStudio Workflow (.osw) file from a configuration dictionary of ECMs.

    Parameters:
        config (dict): ECM configuration {measure_name: option}
        ecm_options_path (str): Path to the ecm_options.json file
        output_path (str): Path to save the generated .osw file
        seed_file (str): Path to the baseline .osm model
        weather_file (str): Path to the .epw weather file

    Returns:
        str: Absolute path to the generated .osw file
    """
    with open(ecm_options_path, 'r') as f:
        ecm_options = json.load(f)

    # OSW file template
    osw = {
        "seed_file": os.path.abspath(seed_file).replace("\\", "/"),
        "weather_file": os.path.abspath(weather_file).replace("\\", "/"),
        "steps": []
    }

    # collect unique parent folders for measure_path
    measure_paths = set()

    # Define preferred order of measures
    preferred_order = [
        "upgrade_wall_insulation",
        "upgrade_roof_insulation",
        "upgrade_window_u_value",
        "upgrade_window_shgc",
        "adjust_infiltration_rates",
        "upgrade_hvac_system_choice",
        "add_in_unit_erv",
        "upgrade_dhw_to_hpwh"
    ]

    # Track already-applied measures to avoid duplicates
    applied_measures = set()

    # Utility function to append a measure step
    def append_measure_step(measure_name):
        selection = config[measure_name]
        measure_info = ecm_options[measure_name]

        # Get folder structure from ECM options
        full_path = measure_info['measure_dir']
        parent_dir, measure_dir_name = os.path.split(full_path)

        # Resolve full measure path relative to ecm_options_path
        base_dir = os.path.abspath(os.path.join(os.path.dirname(ecm_options_path), ".."))

        abs_parent_path = os.path.abspath(os.path.join(base_dir, parent_dir))
        measure_paths.add(abs_parent_path.replace("\\", "/"))

        # Add step with arguments if defined
        step = {"measure_dir_name": measure_dir_name}

        if measure_info["argument_key"]:
            step["arguments"] = {measure_info["argument_key"]: selection}
        osw["steps"].append(step)
        applied_measures.add(measure_name)

    # Step 1: Add all measures in preferred order
    for measure_name in preferred_order:
        if measure_name in config and config[measure_name] != "None":
            append_measure_step(measure_name)

    # Step 2: Add any remaining measures that weren't in preferred_order
    for measure_name in config:
        if measure_name not in applied_measures and config[measure_name] != "None":
            append_measure_step(measure_name)

    # Add collected measure paths to the OSW
    osw["measure_paths"] = list(measure_paths)
    osw["measure_paths"] = [os.path.abspath(p).replace("\\", "/") for p in measure_paths]

    # Clean previous OSW and related run directory
    osw_dir = output_path.replace(".osw", "_run")
    clean_and_prepare_osw_paths(output_path, osw_dir)

    # Write the final OSW file
    with open(output_path, 'w') as f:
        assert os.path.isfile(seed_file), f"Seed file missing: {seed_file}"
        assert os.path.isfile(weather_file), f"Weather file missing: {weather_file}"
        json.dump(osw, f, indent=2)

    return output_path