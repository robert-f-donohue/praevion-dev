import os
import sys
import json
import uuid
import numpy as np
from datetime import datetime, timezone
from deephyper.evaluator import RunningJob

from src.evaluate_kpis import evaluate_kpis_from_config
from praevion_async_core.paths import LOG_DIR, INPUT_DIR

# Directory for KPI logs and results
os.makedirs(LOG_DIR, exist_ok=True)

# Internal cache of best configs
best_log = []
__all__ = ["run_function", "best_log", "run_function_deduplicated"]  # THIS LINE EXPOSES best_log TO OTHER MODULES

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
    kpi_log_path = os.getenv("KPI_LOG_PATH", os.path.join(LOG_DIR, "kpi_log_fallback.jsonl"))
    os.makedirs(LOG_DIR, exist_ok=True)

    # Unpack RunningJob object
    if isinstance(config, RunningJob):
        config = config.parameters
    if not isinstance(config, dict):
        raise RuntimeError("❌ Config is not a dict after unwrapping!")

    print(f"🔁 Starting config {run_id}")

    try:

        # Evaluate KPIs based on currently evaluated ECM configuration
        kpis = evaluate_kpis_from_config(
            config,
            df_factors=os.path.join(INPUT_DIR, "operational-carbon-inputs.csv"),
            df_embodied=os.path.join(INPUT_DIR, "embodied-carbon-inputs.csv"),
            df_thresholds=os.path.join(INPUT_DIR, "berdo-thresholds-multifamily.csv"),
            df_material=os.path.join(INPUT_DIR, "material-cost-inputs.csv"),
            df_rates=os.path.join(INPUT_DIR, "utility-cost-inputs.csv")
        )

        # Combine total embodied and operational carbon for engineered total carbon metric
        operational_carbon_kg = kpis["total_emissions_kg"]
        embodied_carbon_kg = kpis["total_ec_kg"] if kpis["total_ec_kg"] > 0 else 1.0
        berdo_fine_usd = kpis["berdo_fine_usd"]
        material_cost_usd = kpis["material_cost_usd"] if kpis["material_cost_usd"] > 0 else 1.0
        utility_cost_usd = kpis["discounted_utility_cost_usd"] if kpis["discounted_utility_cost_usd"] > 0 else 1.0


        # BERDO fine at net utility min
        net_berdo_min = 74_620

        # Utility cost metrics
        utility_cost_baseline = 2_184_813
        utility_cost_max = 3_693_027
        utility_cost_min = 1_638_838

        # Net utility cost metrics
        net_utility_cost_max = utility_cost_max - utility_cost_baseline
        net_utility_cost_min = utility_cost_min - utility_cost_baseline
        net_utility_cost = utility_cost_usd - utility_cost_baseline

        # Long run cost metrics
        net_longrun_cost = net_utility_cost + berdo_fine_usd

        # Theoretical maximums for normalization
        max_oc = 5_515_869
        max_ec = 476_657
        max_mat_cost = 1_209_421
        net_longrun_cost_max = net_utility_cost_max + 1

        # Theoretical minimums for operational carbon emissions
        min_oc = 1_355_578
        net_longrun_cost_min = net_utility_cost_min + net_berdo_min

        # Normalize objective values
        oc_normalized = (operational_carbon_kg - min_oc) / (max_oc - min_oc)
        ec_normalized = embodied_carbon_kg / max_ec
        longrun_normalized = (net_longrun_cost - net_longrun_cost_min) / (net_longrun_cost_max - net_longrun_cost_min)
        material_normalized = material_cost_usd / max_mat_cost

        # Gather the objective values to be fed in the MOO engine
        objective_values = [
            -oc_normalized,
            -ec_normalized,
            -longrun_normalized,
            -material_normalized
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
                "utility_cost_usd": utility_cost_usd,
                "longrun_cost_usd": net_longrun_cost,
                "material_cost_usd": material_cost_usd,
                "normalized_objective_values": objective_values
            }
        }

        # Append summary to best_log
        best_log.append({
            "timestamp": timestamp,
            "run_id": run_id,
            "oc_total": objective_values[0],
            "ec_total": objective_values[1],
            "longrun_cost_total": objective_values[2],
            "mat_cost_total": objective_values[3],
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

        return {"objective": [sys.float_info.max] * 4, "metadata": log_entry}

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