import os
import json
import pandas as pd
from datetime import datetime, timezone

from deephyper.evaluator import Evaluator
from deephyper.hpo import CBO
from praevion_async_core.paths import RESULTS_ARCHIVE
from praevion_async_core.problem import problem
# from praevion_async_core.utils.constraint_aware_cbo import ConstraintAwareCBO
from praevion_async_core.utils.run_function_async import run_function, run_function_deduplicated, best_log
from praevion_async_core.utils.logging_utils import (
    clean_batch_folders,
    save_results_csv,
    save_best_log,
    archive_logs,
    archive_osws
)
from paths import BASE_DIR, INPUT_DIR, LOG_DIR, OSW_DIR

# Select which acquisition function is to be used in simulation (supports EI and UCB)
desired_acquisition_function = "ucb"
ACQUISITION_FUNCTION = os.getenv("ACQUISITION_FUNCTION", desired_acquisition_function)

# Load correct configuration
if ACQUISITION_FUNCTION == "ucb":
    from praevion_async_core.config.config_ucb import UCB_CONFIG as CONFIG
elif ACQUISITION_FUNCTION == "ei":
    from praevion_async_core.config.config_ei import EI_CONFIG as CONFIG
else:
    raise ValueError(f"Unsupported acquisition function: {ACQUISITION_FUNCTION}")


def main():
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_label = f"{ACQUISITION_FUNCTION}_function_search_{timestamp}"
    os.environ["RUN_LABEL"] = run_label

    print(f"🚀 Starting async optimization run: {run_label}")

    # 🗂 Archive previous results, logs, and kpi outputs before this run
    archive_logs(run_label)

    # 🧼 Clean up working directories to prepare for this run
    clean_batch_folders(project_root=".")

    # Add seed config files
    seed_path = os.path.join(INPUT_DIR, "seed_configs", "seed_configs.json")
    with open(seed_path, 'r') as f:
        seed_configs = json.load(f)

    # ⚙️ Launch DeepHyper evaluation context
    num_cpu_workers = 10
    with Evaluator.create(run_function=run_function_deduplicated, method="process",
                          method_kwargs={"num_workers": num_cpu_workers}) as evaluator:

        # 🧠 Instantiate search strategy (CBO)
        search = CBO(
            problem=problem,
            evaluator=evaluator,
            random_state=42,
            initial_points = seed_configs,
            n_initial_points=64,  # Sobol requires number of samples to be a power of 2
            **CONFIG
        )



        # Prevent DeepHyper from auto-saving results
        if hasattr(search, "save_results"):
            search.save_results = False

        # 🔍 Start the search
        MAX_EVALS = 600
        print(f"🔍 Starting search with max_evals = {MAX_EVALS}")
        search.search(max_evals=MAX_EVALS)

        # 📊 Log search ask history if available
        if hasattr(search, "ask_log"):
            ask_log_path = os.path.join(LOG_DIR, f"ask_log_{run_label}.csv")
            pd.DataFrame(search.ask_log).to_csv(ask_log_path, index=False)

        # 💾 Save search results + best log
        save_results_csv(search, run_label)
        save_best_log(best_log, acq_func=ACQUISITION_FUNCTION)

        # 📦 Archive old OSWs + _run folders
        archive_osws(OSW_DIR, os.path.join(RESULTS_ARCHIVE, "old_osw_files"))

        # 🧹 Remove internal DeepHyper results.csv
        internal_csv = os.path.join('..', BASE_DIR, "results.csv")
        if os.path.exists(internal_csv):
            os.remove(internal_csv)
            print("🧹 Removed internal DeepHyper results.csv file to avoid clutter.")

        print("\n🎉 Optimization run completed successfully!")
        print("📈 Results saved, logs archived, and OSW files compressed.")
        print("🚀 Ready for next mission — onwards to smarter retrofits with Praevion!")

if __name__ == "__main__":
    main()