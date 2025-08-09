import ast
import json
import os
import shutil
import zipfile
from datetime import UTC, datetime

import numpy as np
import pandas as pd

from praevion_core.config.paths import LOG_DIR, RESULTS_ARCHIVE, RESULTS_DIR, RUN_LOGS_DIR


def archive_logs(run_label: str):
    """
    Archives KPI logs and result CSVs into a timestamped subdirectory under archive/.

    Run logs are now compressed and archived at the end of the simulation run,
    so this function no longer moves the run_logs directory.
    """
    archive_dir = os.path.join(RESULTS_ARCHIVE, "old_result_files", f"{run_label}__before")
    os.makedirs(archive_dir, exist_ok=True)

    # Archive logs
    targets = {"kpi_logs": LOG_DIR}

    for name, path in targets.items():
        if os.path.exists(path):
            dest = os.path.join(archive_dir, name)
            try:
                shutil.move(path, dest)
                print(f"📦 Archived {name} → {dest}")
            except Exception as e:
                print(f"⚠️ Failed to archive {name}: {e}")

    # Archive latest results_*.csv file if it exists
    if os.path.exists(RESULTS_DIR):
        result_files = [
            f for f in os.listdir(RESULTS_DIR) if f.startswith("results_") and f.endswith(".csv")
        ]
        for f in result_files:
            full_path = os.path.join(RESULTS_DIR, f)
            dest = os.path.join(archive_dir, f)
            try:
                shutil.move(full_path, dest)
                print(f"📦 Archived {f} → {dest}")
            except Exception as e:
                print(f"⚠️ Failed to archive {f}: {e}")

    # Recreate fresh log directories
    os.makedirs(LOG_DIR, exist_ok=True)
    print("🗃️ Note: Run logs are now archived at the end of the simulation in compressed form.")


def archive_osws(osw_dir: str, archive_base: str):
    """
    Compresses all .osw files and *_run folders in the given directory into a ZIP archive,
    then deletes the originals. Archive is stored inside `archive_base`.

    Parameters:
        osw_dir (str): Path to the directory containing .osw files and *_run folders.
        archive_base (str): Base directory to store the archive.
    """
    # Create archive name and path
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    archive_name = f"osw_backup_{timestamp}.zip"
    archive_path = os.path.join(archive_base, archive_name)

    # Ensure the archive directory exists
    os.makedirs(archive_base, exist_ok=True)

    total_uncompressed_size = 0

    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Archive all .osw files
        for filename in os.listdir(osw_dir):
            if filename.endswith(".osw"):
                full_path = os.path.join(osw_dir, filename)
                arcname = os.path.relpath(full_path, osw_dir)
                zipf.write(full_path, arcname)
                total_uncompressed_size += os.path.getsize(full_path)
                os.remove(full_path)

        # Archive all *_run directories
        for filename in os.listdir(osw_dir):
            if filename.endswith("_run"):
                dir_path = os.path.join(osw_dir, filename)
                for root, _, files in os.walk(dir_path):
                    for f in files:
                        full_path = os.path.join(root, f)
                        arcname = os.path.relpath(full_path, osw_dir)
                        zipf.write(full_path, arcname)
                        total_uncompressed_size += os.path.getsize(full_path)
                shutil.rmtree(dir_path)

    # Calculate compression savings
    compressed_size = os.path.getsize(archive_path)
    reduction_pct = (
        100 * (1 - compressed_size / total_uncompressed_size) if total_uncompressed_size else 0
    )

    # 📦 Summary log
    print(f"📦 Archived OSWs and _run folders to {archive_path}")
    print(
        f"📉 Compression: {total_uncompressed_size / 1e6:.2f} MB → {compressed_size / 1e6:.2f} MB"
        f" ({reduction_pct:.1f}% smaller)"
    )

    # 📝 Log metadata
    stats_log_path = os.path.join(archive_base, "compression_stats.jsonl")
    with open(stats_log_path, "a") as f:
        f.write(
            json.dumps(
                {
                    "timestamp": timestamp,
                    "archive_filename": archive_name,
                    "uncompressed_size_mb": round(total_uncompressed_size / 1e6, 2),
                    "compressed_size_mb": round(compressed_size / 1e6, 2),
                    "percent_saved": round(reduction_pct, 1),
                }
            )
            + "\n"
        )

    return archive_path


def archive_run_logs(run_logs_dir: str, archive_base: str):
    """
    Archives the run logs directory into a timestamped ZIP file and deletes the original directory.

    Parameters:
        run_logs_dir (str): Path to the run logs directory to archive.
        archive_base (str): Base directory to store the archive.
    """
    if not os.path.exists(run_logs_dir):
        print(f"⚠️ Run logs directory {run_logs_dir} does not exist. Skipping archiving.")
        return

    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    archive_name = f"run_logs_{timestamp}.zip"
    archive_path = os.path.join(archive_base, archive_name)

    os.makedirs(archive_base, exist_ok=True)

    total_uncompressed_size = 0
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(run_logs_dir):
            for f in files:
                full_path = os.path.join(root, f)
                arcname = os.path.relpath(full_path, run_logs_dir)
                zipf.write(full_path, arcname)
                total_uncompressed_size += os.path.getsize(full_path)

    shutil.rmtree(run_logs_dir)
    os.makedirs(run_logs_dir, exist_ok=True)

    compressed_size = os.path.getsize(archive_path)
    reduction_pct = (
        100 * (1 - compressed_size / total_uncompressed_size) if total_uncompressed_size else 0
    )

    print(f"📦 Archived run logs → {archive_path}")
    print(
        f"📉 Compression: {total_uncompressed_size / 1e6:.2f} MB → {compressed_size / 1e6:.2f} MB"
        f" ({reduction_pct:.1f}% smaller)"
    )


def save_best_log(best_log: list, acq_func: str = "ucb"):
    """
    Saves a DataFrame of best-performing configs during the search to CSV.

    Parameters:
        best_log (list): List of best objective summaries during the run
        acq_func (str): Acquisition function label for the file naming

    Returns:
        None
    """
    if best_log:
        ts = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        os.makedirs(LOG_DIR, exist_ok=True)
        df = pd.DataFrame(best_log)
        out_path = os.path.join(LOG_DIR, f"best_log_{ts}_{acq_func}.csv")
        df.to_csv(out_path, index=False)
        print(f"📈 Best objective history saved to {out_path}")


def delete_heavy_outputs(run_dir: str):
    """
    Deletes large or unnecessary files from a completed OpenStudio simulation run directory.

    This function is used to minimize disk space usage after extracting all relevant data
    (e.g., from `eplustbl.csv`). It targets known heavy or redundant files produced by
    EnergyPlus and OpenStudio, while retaining essentials like the main summary CSV and model files.

    Parameters:
        run_dir (str): Path to the run directory containing OpenStudio simulation outputs.

    Returns:
        None
    """

    # create list of unneeded files after parsing
    delete_targets = [
        "data_point.zip",
        "data_point_out.json",
        "eplusout.audit",
        "eplusout.bnd",
        "eplusout.eio",
        "eplusout.end",
        "eplusout.err",
        "eplusout.eso",
        "eplusout.mdd",
        "eplusout.mtd",
        "eplusout.rdd",
        "eplusout.shd",
        "eplusout.sql",
        "eplusspsz.csv",
        "eplustbl.htm",
        "finished.job",
        "in.idf",
        "in.osm",
        "measure_attributes.json",
        "pre-preprocess.idf",
        "results.json",
        "run.log",
        "sqlite.err",
        "started.job",
        "stdout-energyplus.txt",
    ]

    # delete all files in delete_targets:
    for filename in delete_targets:
        path = os.path.join(run_dir, filename)
        if os.path.exists(path):
            os.remove(path)


def clean_output_dir(run_dir: str):
    """
    Deletes large or unnecessary files in the OpenStudio run output directory,
    preserving only essentials like eplustbl.csv and model.osm.

    Parameters:
        run_dir (str): Path to the OpenStudio run folder (e.g., 7-run_logs/test001)
    """
    delete_heavy_outputs(run_dir)


def clean_batch_folders(project_root: str):
    """
    Cleans and resets key batch directories to prepare for a new optimization run.

    This function performs the following actions:
    - Clears all contents from the `05_osws`, `7-run_logs`, and `8-kpi_logs` folders.
    - Archives the main KPI log file (`kpi_log.jsonl`) in `8-kpi_logs` by timestamping it
      before deletion, ensuring previous logs are preserved.
    - Skips any previously archived KPI log files during cleanup.

    Parameters:
        project_root (str): The root directory of the project where batch folders are located.

    Returns:
        None
    """
    osw_dir = os.path.join(project_root, "05_osws")

    for path in [osw_dir, RUN_LOGS_DIR, LOG_DIR]:
        if not os.path.exists(path):
            continue

        # Archive main KPI log if it exists
        if path == LOG_DIR:
            log_file = os.getenv("KPI_LOG_PATH", os.path.join(LOG_DIR, "kpi_log_fallback.jsonl"))
            if os.path.exists(log_file):
                timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
                archive_path = os.path.join(LOG_DIR, f"kpi_log_{timestamp}.jsonl")
                shutil.move(log_file, archive_path)

        for item in os.listdir(path):
            item_path = os.path.join(path, item)

            # Skip archived KPI logs and results
            if path == LOG_DIR and item.startswith("kpi_log_") and item.endswith(".jsonl"):
                continue
            if path == LOG_DIR and item.startswith("results") and item.endswith(".csv"):
                continue

            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            except Exception as e:
                print(f"⚠️ Failed to clean {item_path}: {e}")


def clean_and_prepare_osw_paths(osw_path: str, run_dir: str):
    """
    Safely clears old .osw files and run directories before launching a new simulation.

    This function ensures that stale output files and folders from prior runs are
    removed to avoid conflicts or reused data. It operates silently unless an
    error occurs, making it ideal for high-volume batch workflows.

    Parameters:
        osw_path (str): Path to the OpenStudio Workflow (.osw) file.
        run_dir (str): Path to the directory where the simulation results will be written.

    Returns:
        Tuple[str, str]: The validated (now clean) osw_path and run_dir.
    """
    # Ensure the run directory is clean and no .osw filename clash
    try:
        if os.path.exists(osw_path):
            os.remove(osw_path)
        if os.path.exists(run_dir):
            shutil.rmtree(run_dir)
    except Exception as e:
        print(f"⚠️ Failed to clean paths for {osw_path} or {run_dir}: {e}")
    return osw_path, run_dir


def save_results_csv(search, run_label: str):
    """
    Saves all search history (configs + objective values) to a CSV file.
    """
    if hasattr(search, "history"):
        df = search.history.to_dataframe()
        os.makedirs(RESULTS_DIR, exist_ok=True)
        path = os.path.join(RESULTS_DIR, f"results_{run_label}.csv")
        df.to_csv(path, index=False)
        print(f"📊 Results written to {path}")


def expand_objectives_column(csv_path: str):
    """
    Loads a results CSV, expands the 'm:objectives' dictionary column into separate columns,
    and saves the updated CSV in-place.

    Parameters:
        csv_path (str): Path to the results_*.csv file.
    """
    # Ensure results file exists
    if not os.path.exists(csv_path):
        print(f"⚠️ Could not find results file at {csv_path}")
        return
    # Load to csv and check column exists
    df = pd.read_csv(csv_path)
    if "m:objectives" not in df.columns:
        print(f"⚠️ Column 'm:objectives' not found in {csv_path}")
        return

    try:
        # Unpack KPI values from the dict
        objectives_expanded = df["m:objectives"].apply(ast.literal_eval).apply(pd.Series)
        kpi_cols = [
            "operational_carbon_kg",
            "embodied_carbon_kg",
            "berdo_fine_usd",
            "utility_cost_usd",
            "longrun_cost_usd",
            "material_cost_usd",
        ]
        for col in kpi_cols:
            df[col] = objectives_expanded.get(col, float("nan"))

        # Dedup based on objective_* values, preferring pareto_efficient=True if present
        obj_cols = ["objective_0", "objective_1", "objective_2", "objective_3"]
        if all(col in df.columns for col in obj_cols):
            original_len = len(df)

            # Mark duplicates
            df["_dup_key"] = df[obj_cols].apply(lambda row: tuple(row), axis=1)
            grouped = df.groupby("_dup_key", sort=False)

            to_keep = []
            for _, group in grouped:
                if len(group) == 1:
                    to_keep.append(group.index[0])
                else:
                    pareto = group[group["pareto_efficient"]]
                    if not pareto.empty:
                        to_keep.append(pareto.index[0])  # Keep any one Pareto-efficient entry
                    else:
                        to_keep.append(group.index[0])  # Fallback to first

            df = df.loc[to_keep].drop(columns=["_dup_key"]).reset_index(drop=True)
            removed = original_len - len(df)
            if removed > 0:
                print(f"🧹 Removed {removed} duplicate rows based on objective_* values.")

        # Save the cleaned and expanded CSV
        df.to_csv(csv_path, index=False)
        print(f"📂 Cleaned and unpacked results saved → {csv_path}")

    except Exception as e:
        print(f"❌ Failed to unpack KPIs from 'm:objectives': {e}")


def log_optimization_summary_to_csv(
    csv_path: str, run_label: str, max_evals: int, output_csv_path: str
):
    """
    Logs a summary of optimization performance to a CSV file.

    Parameters:
        csv_path (str): Path to the results CSV after expansion and deduplication.
        run_label (str): Label for the current run (e.g. 'run_300e').
        max_evals (int): The number of total evaluations performed in the search.
        output_csv_path (str): Path to the summary log CSV (e.g., 'optimization_runs_summary.csv').
    """
    if not os.path.exists(csv_path):
        print(f"⚠️ Results file not found at {csv_path}")
        return

    df = pd.read_csv(csv_path)
    if df.empty:
        print(f"⚠️ Results file is empty: {csv_path}")
        return

    # Extract non-dominated points (Pareto front)
    pareto_df = df[df["pareto_efficient"]]
    num_pareto = len(pareto_df)

    # Define objective columns
    obj_cols = ["objective_0", "objective_1", "objective_2", "objective_3"]

    # Compute number of rows and deduplicates
    num_final = len(df)
    num_duplicates = max_evals - num_final

    # Compute objective ranges
    obj_ranges = {col: (df[col].min(), df[col].max()) for col in obj_cols if col in df.columns}

    # Compute crowding distance stats (only if pareto front exists)
    crowding_mean = np.nan
    crowding_std = np.nan
    if not pareto_df.empty:
        crowding = compute_crowding_distance(pareto_df, obj_cols)
        crowding_mean = round(crowding.replace(np.inf, np.nan).mean(), 4)
        crowding_std = round(crowding.replace(np.inf, np.nan).std(), 4)

    # Prepare summary row
    summary_row = {
        "timestamp": datetime.now().isoformat(),
        "run_label": run_label,
        "max_evals": max_evals,
        "final_configs": num_final,
        "duplicates_removed": num_duplicates,
        "pareto_size": num_pareto,
        "crowding_mean": crowding_mean,
        "crowding_std": crowding_std,
    }
    for col, (obj_min, obj_max) in obj_ranges.items():
        summary_row[f"{col}_min"] = round(obj_min, 4)
        summary_row[f"{col}_max"] = round(obj_max, 4)

    # Append to summary log
    summary_df = pd.DataFrame([summary_row])
    if os.path.exists(output_csv_path):
        summary_df.to_csv(output_csv_path, mode="a", header=False, index=False)
    else:
        summary_df.to_csv(output_csv_path, index=False)

    print(f"📈 Logged optimization summary → {output_csv_path}")


def compute_crowding_distance(df: pd.DataFrame, objective_cols: list) -> pd.Series:
    """
    Compute crowding distance for a set of non-dominated solutions
    with already scaled objective values (e.g., in [-1, 0]).

    Parameters:
        df (pd.DataFrame): DataFrame of non-dominated points.
        objective_cols (list): List of objective column names (e.g. ['objective_0', ...]).

    Returns:
        pd.Series: Crowding distance values (same index as df).
    """
    n = len(df)
    if n == 0:
        return pd.Series(dtype=float)
    if n == 1:
        return pd.Series([np.inf], index=df.index)

    distances = np.zeros(n)

    for col in objective_cols:
        sorted_idx = df[col].argsort()
        sorted_df = df.iloc[sorted_idx]

        # Assign infinite distance to boundary points
        distances[sorted_idx[0]] = distances[sorted_idx[-1]] = np.inf

        # Add crowding distance for interior points (objectives already scaled)
        for i in range(1, n - 1):
            prev_val = sorted_df.iloc[i + 1][col]
            next_val = sorted_df.iloc[i - 1][col]
            distances[sorted_idx[i]] += abs(prev_val - next_val)

    return pd.Series(distances, index=df.index)
