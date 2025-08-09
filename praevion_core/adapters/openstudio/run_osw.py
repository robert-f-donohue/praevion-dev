import os
import shutil
import subprocess


def run_osw_and_organize_logs(osw_path, run_logs_dir):
    """
    Runs an OpenStudio workflow (.osw) in a clean subdirectory and moves its output logs.

    This function automates the execution of a given .osw file using the OpenStudio CLI.
    It isolates each run in a dedicated folder, captures stdout/stderr, and moves completed
    run logs into a central directory (`run_logs_dir`) for easier analysis.

    Process overview:
    - Extracts a test name from the .osw filename
    - Creates a clean run directory in `05_osws/`
    - Executes the workflow using OpenStudio CLI
    - Captures and returns stdout/stderr
    - Moves successful run outputs to `7-run_logs/`

    Parameters:
        osw_path (str): Path to the OpenStudio Workflow (.osw) file to execute.
        run_logs_dir (str): Destination folder for organized run outputs (e.g., "7-run_logs/").

    Returns:
        dict: A result summary with the following fields:
            - test_name (str): Identifier for this run, derived from the .osw filename.
            - success (bool): Whether the simulation ran without errors.
            - stderr (bytes or str): Captured stderr output, if available.
            - stdout (bytes or str): Captured stdout output, if available.
            - log_path (str or None): Path to moved run logs, or None if the run failed.
    """
    # Extract test name from file
    test_name = os.path.splitext(os.path.basename(osw_path))[0]

    # Create isolated run directory: 05_osws/test_name_run/
    osw_dir = os.path.join(os.path.dirname(osw_path), f"{test_name}_run")
    os.makedirs(osw_dir, exist_ok=True)

    # Copy the OSW into that directory and redefine the path
    new_osw_path = os.path.join(osw_dir, os.path.basename(osw_path))
    shutil.copy(osw_path, new_osw_path)

    # attempt to run the OpenStudio Ruby Measure
    try:
        openstudio_exe = os.getenv("OPENSTUDIO_EXE", "C:/openstudio-3.9.0/bin/openstudio.exe")
        result = subprocess.run(
            [openstudio_exe, "run", "-w", new_osw_path],
            cwd=osw_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        success = True

    except subprocess.CalledProcessError as e:
        result = e
        success = False

    except Exception as e:
        result = e
        success = False

    # Move results to run_logs_dir
    run_dir = os.path.join(osw_dir, "run")
    destination = os.path.join(run_logs_dir, test_name)
    if success and os.path.exists(run_dir):
        if os.path.exists(destination):
            shutil.rmtree(destination)
        shutil.move(run_dir, destination)

    # Default empty values
    stderr = stdout = "(not available)"

    # Extract stdout/stderr if result is a subprocess result or exception
    if isinstance(result, subprocess.CalledProcessError) or isinstance(
        result, subprocess.CompletedProcess
    ):
        stderr = result.stderr.encode() if isinstance(result.stderr, str) else result.stderr
        stdout = result.stdout.encode() if isinstance(result.stdout, str) else result.stdout
    elif isinstance(result, Exception):
        stderr = str(result)
        stdout = "(no stdout captured)"

    return {
        "test_name": test_name,
        "success": success,
        "stderr": stderr,
        "stdout": stdout,
        "log_path": destination if success else None,
    }
