import os
import sys
import json
import uuid
from datetime import datetime, timezone
from deephyper.evaluator import RunningJob

from praevion_async_core.utils.search_utils import is_valid_config
from src.evaluate_kpis import evaluate_kpis_from_config
from praevion_async_core.paths import LOG_DIR, INPUT_DIR

# Directory for KPI logs and results
os.makedirs(LOG_DIR, exist_ok=True)

# Internal cache of best configs
best_log = []
__all__ = ["run_function", "best_log"]  # THIS LINE EXPOSES best_log TO OTHER MODULES

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

    if not is_valid_config(config):
        error_msg = "Invalid configuration (violates constraints)."
        print(f"❌ Failed config {run_id}: {error_msg}")
        log_entry = {
            "timestamp": timestamp,
            "run_id": run_id,
            "config": config,
            "success": False,
            "error": error_msg
        }
        with open(kpi_log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        return {"objective": [sys.float_info.max] * 2, "metadata": log_entry}

    try:

        # Evaluate KPIs based on currently evaluated ECM configuration
        kpis = evaluate_kpis_from_config(
            config,
            df_factors=os.path.join(INPUT_DIR, "operational-carbon-inputs.csv"),
            df_embodied=os.path.join(INPUT_DIR, "embodied-carbon-inputs.csv"),
            df_thresholds=os.path.join(INPUT_DIR, "berdo-thresholds-multifamily.csv")
        )

        # Combine total embodied and operational carbon for engineered total carbon metric
        total_carbon_kg = kpis["total_emissions_kg"] + kpis["total_ec_kg"]
        berdo_fine_usd = kpis["berdo_fine_usd"]

        # Gather the objective values to be fed in the MOO engine
        objective_values = [total_carbon_kg, berdo_fine_usd]

        # Structure successful kpi_log entry
        log_entry = {
            "timestamp": timestamp,
            "run_id": run_id,
            "config": config,
            "success": True,
            "objectives": {
                "total_emissions_kg": total_carbon_kg,
                "berdo_fine_usd": berdo_fine_usd,
            }
        }

        # Append summary to best_log
        best_log.append({
            "timestamp": timestamp,
            "run_id": run_id,
            "oc_ec_total": objective_values[0],
            "cost": objective_values[1]
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

        return {"objective": [sys.float_info.max] * 2, "metadata": log_entry}