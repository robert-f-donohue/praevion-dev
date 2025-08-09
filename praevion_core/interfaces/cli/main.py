import os
import pandas as pd
from datetime import UTC, datetime
from pathlib import Path
from deephyper.hpo import CBO
from deephyper.evaluator import Evaluator

from praevion_core.config.problem import problem
from praevion_core.pipelines.run_function_async import run_function
from praevion_core.pipelines.sobol_sampler import generate_filtered_sobol_samples
from praevion_core.config.paths import (
    REPO_ROOT,
    LOG_DIR,
    OSW_DIR,
    RESULTS_ARCHIVE,
    RESULTS_DIR,
    RUN_LOGS_DIR,
    SUMMARY_DIR,
)
from praevion_core.pipelines.logging_utils import (
    archive_logs,
    archive_osws,
    archive_run_logs,
    clean_batch_folders,
    expand_objectives_column,
    log_optimization_summary_to_csv,
    save_results_csv,
)

# Select which acquisition function is to be used in simulation (supports EI and UCB)
desired_acquisition_function = "ucb"
ACQUISITION_FUNCTION = os.getenv("ACQUISITION_FUNCTION", desired_acquisition_function)

# Load correct configuration
if ACQUISITION_FUNCTION == "ucb":
    from praevion_core.config.config_ucb import UCB_CONFIG as CONFIG
elif ACQUISITION_FUNCTION == "ei":
    from praevion_core.config.config_ei import EI_CONFIG as CONFIG
else:
    raise ValueError(f"Unsupported acquisition function: {ACQUISITION_FUNCTION}")


def main():
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    run_label = f"{ACQUISITION_FUNCTION}_function_search_{timestamp}"
    os.environ["RUN_LABEL"] = run_label
    os.environ["KPI_LOG_PATH"] = os.path.join(LOG_DIR, f"kpi_log_{run_label}.jsonl")

    print(f"🚀 Starting async optimization run: {run_label}")

    # 🗂 Archive previous results, logs, and kpi outputs before this run
    archive_logs(run_label)

    # 🧼 Clean up working directories to prepare for this run
    clean_batch_folders(project_root=".")

    # ✅ Generate filtered Sobol seed configs
    seed_configs = generate_filtered_sobol_samples(
        problem=problem, n_samples=256, seed=42, verbose=True
    )
    print(f"📦 Loaded {len(seed_configs)} valid Sobol seeds for initial_points.")

    # ⚙️ Launch DeepHyper evaluation context
    num_cpu_workers = 8
    with Evaluator.create(
        run_function=run_function,
        method="process",
        method_kwargs={"num_workers": num_cpu_workers},
    ) as evaluator:
        # 🧠 Instantiate search strategy (CBO)
        search = CBO(
            problem=problem,
            evaluator=evaluator,
            initial_points=seed_configs,
            random_state=42,
            **CONFIG,
        )

        # print(f"📊 Initial configs seeded: {len(seed_configs)}")
        print(f"🧠 Starting with kappa = {CONFIG['acq_func_kwargs']['kappa']}")
        print(
            f"🔁 Decaying kappa every {CONFIG['acq_func_kwargs']['scheduler']['period']} runs "
            f"to {CONFIG['acq_func_kwargs']['scheduler']['kappa_final']}"
        )

        # Prevent DeepHyper from auto-saving results
        if hasattr(search, "save_results"):
            search.save_results = False

        # 🔍 Start the search
        MAX_EVALS = 640
        print(f"🔍 Starting search with max_evals = {MAX_EVALS}")
        search.search(max_evals=MAX_EVALS)

        # 📊 Log search ask history if available
        if hasattr(search, "ask_log"):
            ask_log_path = os.path.join(LOG_DIR, f"ask_log_{run_label}.csv")
            pd.DataFrame(search.ask_log).to_csv(ask_log_path, index=False)

        # 💾 Save search results and best log
        save_results_csv(search, run_label)
        expand_objectives_column(os.path.join(RESULTS_DIR, f"results_{run_label}.csv"))

        # Save summary stats log
        summary_log_path = os.path.join(SUMMARY_DIR, "optimization_runs_summary.csv")
        log_optimization_summary_to_csv(
            csv_path=os.path.join(RESULTS_DIR, f"results_{run_label}.csv"),
            run_label=run_label,
            max_evals=MAX_EVALS,
            output_csv_path=summary_log_path,
        )

        # 📦 Archive old OSWs + run folders
        archive_osws(OSW_DIR, os.path.join(RESULTS_ARCHIVE, "old_osw_files"))
        archive_run_logs(
            run_logs_dir=RUN_LOGS_DIR, archive_base=os.path.join(RESULTS_ARCHIVE, "old_run_logs")
        )

        # 🧹 Remove internal DeepHyper results.csv
        for p in [Path.cwd() / "results.csv", REPO_ROOT / "results.csv"]:
            # Don’t touch your curated results folder
            if p.exists() and RESULTS_DIR not in p.parents:
                p.unlink()
                print(f"🧹 Removed internal DeepHyper results.csv at {p}")

        print("\n🎉 Optimization run completed successfully!")
        print("📈 Results saved, logs archived, and OSW/result files compressed.")
        print("🚀 Ready for next mission — onwards to smarter retrofits with Praevion!")


if __name__ == "__main__":
    main()
