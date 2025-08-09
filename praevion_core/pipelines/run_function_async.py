import os
import sys
import uuid
import json
import hashlib
from datetime import UTC, datetime
from deephyper.evaluator import RunningJob
from praevion_core.config.paths import INPUT_DIR, LOG_DIR
from praevion_core.config.objective_constants import CONSTANTS
from praevion_core.domain.kpis.evaluate_kpis import evaluate_kpis_from_config

# Directory for KPI logs and results
os.makedirs(LOG_DIR, exist_ok=True)

def hash_config(config: dict) -> str:
    """Create a consistent hash for a config dictionary."""
    return hashlib.md5(
        json.dumps(config, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

def compute_objectives_from_kpis(kpis: dict, constants: dict) -> tuple[list[float], dict]:
    oc = kpis["total_emissions_kg"]
    ec = kpis["total_ec_kg"] if kpis["total_ec_kg"] > 0 else 1.0
    fine = kpis["berdo_fine_usd"]
    mat_cost = kpis["material_cost_usd"] if kpis["material_cost_usd"] > 0 else 1.0
    util = kpis["discounted_utility_cost_usd"]

    # --- unpack constants ---
    min_oc = constants["min_oc"]
    max_oc = constants["max_oc"]

    max_ec = constants["max_ec"]

    max_mat = constants["max_mat_cost"]

    util_base = constants["utility_cost_baseline"]
    util_min = constants["utility_cost_min"]
    util_max = constants["utility_cost_max"]

    berdo_min = constants["net_berdo_min"]

    net_util = util - util_base
    net_util_min = util_min - util_base
    net_util_max = util_max - util_base
    net_longrun = net_util + fine

    net_longrun_min = net_util_min + berdo_min
    net_longrun_max = net_util_max

    oc_n = (oc - min_oc) / (max_oc - min_oc)
    ec_n = ec / max_ec
    lr_n = (net_longrun - net_longrun_min) / (net_longrun_max - net_longrun_min)
    mat_n = mat_cost / max_mat

    objectives = [-oc_n, -ec_n, -lr_n, -mat_n]
    extras = {
        "operational_carbon_kg": oc,
        "embodied_carbon_kg": ec,
        "berdo_fine_usd": fine,
        "utility_cost_usd": util,
        "longrun_cost_usd": net_longrun,
        "normalized_objective_values": objectives,
        "material_cost_usd": mat_cost,
    }
    return objectives, extras



def run_function(config: dict):
    """
    Evaluates a configuration during DeepHyper's async search process.

    Args:
        config (dict): A dictionary of selected ECM options.

    Returns:
        Returns the 4D objective vector (negated for minimization) and a metadata log entry
    """
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    run_id = f"opt_{timestamp}_{uuid.uuid4().hex[:8]}"
    kpi_log_path = os.getenv("KPI_LOG_PATH", os.path.join(LOG_DIR, "kpi_log_fallback.jsonl"))
    os.makedirs(LOG_DIR, exist_ok=True)

    # Unpack RunningJob object
    if isinstance(config, RunningJob):
        config = config.parameters
    if not isinstance(config, dict):
        raise RuntimeError("❌ Config is not a dict after unwrapping!")

    print(f"🔁 Starting config {run_id}")

    try:
        # Evaluate KPIs based on the currently evaluated ECM configuration
        kpis = evaluate_kpis_from_config(
            config,
            df_factors=os.path.join(INPUT_DIR, "operational-carbon-inputs.csv"),
            df_embodied=os.path.join(INPUT_DIR, "embodied-carbon-inputs.csv"),
            df_thresholds=os.path.join(INPUT_DIR, "berdo-thresholds-multifamily.csv"),
            df_material=os.path.join(INPUT_DIR, "material-cost-inputs.csv"),
            df_rates=os.path.join(INPUT_DIR, "utility-cost-inputs.csv"),
        )

        # Get objective values and extra information for logging
        objectives, extras = compute_objectives_from_kpis(kpis, CONSTANTS)

        # Structure successful kpi_log entry
        log_entry = {
            "timestamp": timestamp,
            "run_id": run_id,
            "config": config,
            "success": True,
            "objectives": extras,
        }

        with open(kpi_log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        print(f"✅ Completed config {run_id} with objectives: {objectives}")
        return {"objective": objectives, "metadata": log_entry}

    except Exception as e:
        print(f"❌ Failed config {run_id}: {e}")
        log_entry = {
            "timestamp": timestamp,
            "run_id": run_id,
            "config": config,
            "success": False,
            "error": str(e),
        }
        with open(kpi_log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        return {"objective": [sys.float_info.max] * 4, "metadata": log_entry}
