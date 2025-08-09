import json
import os
from pathlib import Path

from praevion_core.config.paths import MODEL_DIR
from praevion_core.pipelines.logging_utils import clean_and_prepare_osw_paths


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
    output_path = os.path.abspath(output_path)
    seed_file = os.path.abspath(seed_file)
    weather_file = os.path.abspath(weather_file)

    with open(ecm_options_path) as f:
        ecm_options = json.load(f)

    # OpenStudio/OSW skeleton
    osw = {
        "seed_file": seed_file.replace("\\", "/"),
        "weather_file": weather_file.replace("\\", "/"),
        "steps": [],
    }

    # Root where all measures live in your new layout
    measures_root = os.path.join(str(MODEL_DIR), "openstudio_measures")

    # Preferred ordering
    preferred_order_candidates = [
        # Envelope first
        "upgrade_wall_insulation",
        "upgrade_roof_insulation",
        # Windows
        "upgrade_window_u_value",
        "upgrade_window_shgc",
        # Infiltration next
        "adjust_infiltration_rates",
        # Systems
        "upgrade_hvac_system_choice",
        "upgrade_dhw_to_hpwh",
    ]
    preferred_order = [m for m in preferred_order_candidates if m in ecm_options and m in config]

    # Track already-applied measures to avoid duplicates
    applied_measures = set()
    measure_paths = set()  # unique parent directories of measure folders (OSW 'measure_paths')

    # Utility function to append a measure step
    def append_measure_step(measure_name):
        selection = str(config[measure_name]).strip()
        measure_info = ecm_options[measure_name]

        # Get folder structure from ECM options
        full_path = measure_info.get("measure_dir", "").strip()
        if not full_path:
            raise ValueError(f"Missing 'measure_dir' for {measure_name} in {ecm_options_path}")
        # 'measure_dir' is expected to be category/dir_name
        parent_dir, measure_dir_name = os.path.split(full_path)

        # Resolve absolute parent path under the measures root
        abs_parent_path = os.path.abspath(os.path.join(measures_root, parent_dir))
        measure_paths.add(abs_parent_path.replace("\\", "/"))

        # Build the step
        step = {"measure_dir_name": measure_dir_name}
        argument_key = measure_info.get("argument_key")
        if argument_key:
            step["arguments"] = {argument_key: selection}

        osw["steps"].append(step)
        applied_measures.add(measure_name)

    # 1) Add all measures in preferred order
    for m in preferred_order:
        append_measure_step(m)

    # 2) Add any remaining measures present in config & options (not already added)
    for m in config:
        if m not in applied_measures and m in ecm_options:
            append_measure_step(m)

    # 3) Attach measure paths (normalized, unique)
    osw["measure_paths"] = list(measure_paths)
    osw["measure_paths"] = [os.path.abspath(p).replace("\\", "/") for p in measure_paths]

    # 4) Clean previous OSW + run dir (derive run dir robustly)
    osw_dir = str(Path(output_path).with_suffix("")) + "_run"
    clean_and_prepare_osw_paths(output_path, osw_dir)

    # 5) Final validations and write
    assert os.path.isfile(seed_file), f"Seed file missing: {seed_file}"
    assert os.path.isfile(weather_file), f"Weather file missing: {weather_file}"

    with open(output_path, "w") as f:
        json.dump(osw, f, indent=2)

    return output_path
