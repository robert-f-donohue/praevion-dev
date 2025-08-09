import os

from praevion_core.adapters.openstudio.run_osw import run_osw_and_organize_logs


def run_osw_and_get_csv_path(osw_path, run_logs_dir):
    """
    Runs the OpenStudio simulation using the provided .osw file.
    Organizes the log output into run_logs_dir and returns the path to eplustbl.csv.

    Parameters:
        osw_path (str): Path to the .osw file
        run_logs_dir (str): Root directory to store simulation outputs

    Returns:
        tuple:
            - csv_path (str): Path to the resulting eplustbl.csv file
            - run_dir (str): Directory where simulation output was moved
    """
    # Run OpenStudio simulation using provided .osw configuration
    result = run_osw_and_organize_logs(osw_path, run_logs_dir)

    # Raise RuntimeError if the model fails to run
    if not result["success"]:
        stderr = result.get("stderr", b"").decode("utf-8")
        stdout = result.get("stdout", b"").decode("utf-8")
        raise RuntimeError(f"OpenStudio simulation failed:\nSTDERR:\n{stderr}\n\nSTDOUT:\n{stdout}")

    # Establish paths to run logs and output .csv
    run_dir = result["log_path"]
    csv_path = os.path.join(run_dir, "eplustbl.csv")

    # Ensure the .csv is where it should be
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"eplustbl.csv not found in {run_dir}")

    return csv_path, run_dir
