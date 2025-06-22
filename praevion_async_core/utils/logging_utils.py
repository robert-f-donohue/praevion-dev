import os
import shutil
import zipfile
import json
import pandas as pd

from datetime import datetime, timezone
from praevion_async_core.paths import LOG_DIR, RUN_LOGS_DIR, RESULTS_DIR, RESULTS_ARCHIVE


def archive_logs(run_label: str):
    """
    Archives previous logs and results into a timestamped subdirectory under archive/.

    The archive folder is suffixed with '__before' to distinguish it from the current run ID.
    """
    archive_dir = os.path.join(RESULTS_ARCHIVE, "old_result_files", f"{run_label}__before")
    os.makedirs(archive_dir, exist_ok=True)

    # Archive logs
    targets = {
        "run_logs": RUN_LOGS_DIR,
        "kpi_logs": LOG_DIR
    }

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
        result_files = [f for f in os.listdir(RESULTS_DIR) if f.startswith("results_") and f.endswith(".csv")]
        for f in result_files:
            full_path = os.path.join(RESULTS_DIR, f)
            dest = os.path.join(archive_dir, f)
            try:
                shutil.move(full_path, dest)
                print(f"📦 Archived {f} → {dest}")
            except Exception as e:
                print(f"⚠️ Failed to archive {f}: {e}")

    # Recreate fresh log directories
    os.makedirs(RUN_LOGS_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

def archive_osws(osw_dir: str, archive_base: str):
    """
    Compresses all .osw files and *_run folders in the given directory into a ZIP archive,
    then deletes the originals. Archive is stored inside `archive_base`.

    Parameters:
        osw_dir (str): Path to the directory containing .osw files and *_run folders.
        archive_base (str): Base directory to store the archive (e.g., 'praevion_async_core/archive/old_osw_files').
    """
    # Create archive name and path
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
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
    reduction_pct = 100 * (1 - compressed_size / total_uncompressed_size) if total_uncompressed_size else 0

    # 📦 Summary log
    print(f"📦 Archived OSWs and _run folders to {archive_path}")
    print(f"📉 Compression: {total_uncompressed_size / 1e6:.2f} MB → {compressed_size / 1e6:.2f} MB "
          f"({reduction_pct:.1f}% smaller)")

    # 📝 Log metadata
    stats_log_path = os.path.join(archive_base, "compression_stats.jsonl")
    with open(stats_log_path, "a") as f:
        f.write(json.dumps({
            "timestamp": timestamp,
            "archive_filename": archive_name,
            "uncompressed_size_mb": round(total_uncompressed_size / 1e6, 2),
            "compressed_size_mb": round(compressed_size / 1e6, 2),
            "percent_saved": round(reduction_pct, 1)
        }) + "\n")

    return archive_path

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
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        os.makedirs(LOG_DIR, exist_ok=True)
        df = pd.DataFrame(best_log)
        out_path = os.path.join(LOG_DIR, f"best_log_{ts}_{acq_func}.csv")
        df.to_csv(out_path, index=False)
        print(f"📈 Best objective history saved to {out_path}")

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

def delete_heavy_outputs(run_dir):
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
        "data_point.zip", "data_point_out.json", "eplusout.audit", "eplusout.bnd",
        "eplusout.eio", "eplusout.end", "eplusout.err", "eplusout.eso", "eplusout.mdd",
        "eplusout.mtd", "eplusout.rdd", "eplusout.shd", "eplusout.sql", "eplusspsz.csv",
        "eplustbl.htm", "finished.job", "in.idf", "in.osm", "measure_attributes.json",
        "pre-preprocess.idf", "results.json", "run.log", "sqlite.err", "started.job",
        "stdout-energyplus.txt"
    ]

    # delete all files in delete_targets:
    for filename in delete_targets:
        path = os.path.join(run_dir, filename)
        if os.path.exists(path):
            os.remove(path)

def clean_output_dir(run_dir):
    """
    Deletes large or unnecessary files in the OpenStudio run output directory,
    preserving only essentials like eplustbl.csv and model.osm.

    Parameters:
        run_dir (str): Path to the OpenStudio run folder (e.g., 7-run_logs/test001)
    """
    delete_heavy_outputs(run_dir)

def clean_batch_folders(project_root):
    """
    Cleans and resets key batch directories to prepare for a new optimization run.

    This function performs the following actions:
    - Clears all contents from the `5-osws`, `7-run_logs`, and `8-kpi_logs` folders.
    - Archives the main KPI log file (`kpi_log.jsonl`) in `8-kpi_logs` by timestamping it
      before deletion, ensuring previous logs are preserved.
    - Skips any previously archived KPI log files during cleanup.

    Parameters:
        project_root (str): The root directory of the project where batch folders are located.

    Returns:
        None
    """
    osw_dir = os.path.join(project_root, "5-osws")

    for path in [osw_dir, RUN_LOGS_DIR, LOG_DIR]:
        if not os.path.exists(path):
            continue

        # Archive main KPI log if it exists
        if path == LOG_DIR:
            log_file = os.path.join(LOG_DIR, "kpi_log.jsonl")
            if os.path.exists(log_file):
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
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

def clean_and_prepare_osw_paths(osw_path, run_dir):
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