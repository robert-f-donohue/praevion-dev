import os
import sys
import json
import uuid
from datetime import datetime, timezone
from deephyper.evaluator import RunningJob

# from praevion_async_core.utils.search_utils import is_valid_config
from src.evaluate_kpis import evaluate_kpis_from_config
from praevion_async_core.paths import LOG_DIR, INPUT_DIR

# Directory for KPI logs and results
os.makedirs(LOG_DIR, exist_ok=True)

# Internal cache of best configs
best_log = []
__all__ = ["run_function", "best_log"]  # THIS LINE EXPOSES best_log TO OTHER MODULES

import hashlib
# 🔐 Shared set to store seen config hashes
seen_config_hashes = set()
seen_config_results = {}  # Maps hash → objective

def hash_config(config: dict) -> str:
    """Create a consistent hash for a config dictionary."""
    return hashlib.md5(str(sorted(config.items())).encode()).hexdigest()

def run_function(config: dict):
    """
    Evaluates a configuration during DeepHyper's async search process.

    Args:
        config (dict): A dictionary of selected ECM options.

    Returns:
        list: Objective values [total_emissions_kg, total_ec_kg, berdo_fine_usd]
    """

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_id = f"opt_{timestamp}_{uuid.uuid4().hex[:8]}"
    kpi_log_path = os.path.join(LOG_DIR, f"results_{timestamp}.jsonl")
    os.makedirs(LOG_DIR, exist_ok=True)

    # Unpack RunningJob object
    if isinstance(config, RunningJob):
        config = config.parameters
    if not isinstance(config, dict):
        raise RuntimeError("❌ Config is not a dict after unwrapping!")

    print(f"🔁 Starting config {run_id}")

    # if not is_valid_config(config):
    #     error_msg = "Invalid configuration (violates constraints)."
    #     print(f"❌ Failed config {run_id}: {error_msg}")
    #     log_entry = {
    #         "timestamp": timestamp,
    #         "run_id": run_id,
    #         "config": config,
    #         "success": False,
    #         "error": error_msg
    #     }
    #     with open(kpi_log_path, "a") as f:
    #         f.write(json.dumps(log_entry) + "\n")
    #     return {"objective": [sys.float_info.max] * 2, "metadata": log_entry}

    try:

        # Evaluate KPIs based on currently evaluated ECM configuration
        kpis = evaluate_kpis_from_config(
            config,
            df_factors=os.path.join(INPUT_DIR, "operational-carbon-inputs.csv"),
            df_embodied=os.path.join(INPUT_DIR, "embodied-carbon-inputs.csv"),
            df_thresholds=os.path.join(INPUT_DIR, "berdo-thresholds-multifamily.csv"),
            df_material=os.path.join(INPUT_DIR, "material-costs.csv")
        )

        # Combine total embodied and operational carbon for engineered total carbon metric
        operational_carbon_kg = kpis["total_emissions_kg"]
        embodied_carbon_kg = kpis["total_ec_kg"] if kpis["total_ec_kg"] > 0 else 1.0
        berdo_fine_usd = kpis["berdo_fine_usd"]
        material_cost_usd = kpis["material_cost_usd"] if kpis["material_cost_usd"] > 0 else 1.0

        # Theoretical maximums for normalization
        max_oc = 5_552_000
        max_ec = 464_000
        max_fine = 487_000
        max_mat_cost = 630_000

        # Theoretical minimums for operational carbon emissions
        min_oc = 1_508_000

        # Normalize objective values
        OC_normalized = (operational_carbon_kg - min_oc) / (max_oc - min_oc)
        EC_normalized = embodied_carbon_kg / max_ec
        Fine_normalized = berdo_fine_usd / max_fine
        Material_normalized = material_cost_usd / max_mat_cost

        # Gather the objective values to be fed in the MOO engine
        objective_values = [
            -OC_normalized,
            -EC_normalized,
            -Fine_normalized
        ]

        # Structure successful kpi_log entry
        log_entry = {
            "timestamp": timestamp,
            "run_id": run_id,
            "config": config,
            "success": True,
            "objectives": {
                "operational_carbon_kg": operational_carbon_kg,
                "embodied_carbon_kg": embodied_carbon_kg,
                "berdo_fine_usd": berdo_fine_usd,
                "material_cost_usd": material_cost_usd
            }
        }

        # Append summary to best_log
        best_log.append({
            "timestamp": timestamp,
            "run_id": run_id,
            "oc_total": objective_values[0],
            "ec_total": objective_values[1],
            "cost_total": objective_values[2]
        })
        with open(kpi_log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        print(f"✅ Completed config {run_id} with objectives: {objective_values}")
        return {"objective": objective_values, "metadata": log_entry}

    except Exception as e:
        print(f"❌ Failed config {run_id}: {e}")
        log_entry = {
            "timestamp": timestamp,
            "run_id": run_id,
            "config": config,
            "success": False,
            "error": str(e)
        }
        with open(kpi_log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        return {"objective": [sys.float_info.max] * 3, "metadata": log_entry}

def run_function_deduplicated(config):
    config_hash = hash_config(config)

    if config_hash in seen_config_hashes:
        print(f"⚠️ Duplicate config — returning cached result for {config_hash}")
        return seen_config_results[config_hash]

    # Run simulation and compute objectives
    result = run_function(config)

    # Cache it
    seen_config_hashes.add(config_hash)
    seen_config_results[config_hash] = result

    return result