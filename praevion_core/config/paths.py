from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Input file paths
DATA_DIR = REPO_ROOT / "data"

INPUT_DIR = DATA_DIR / "inputs"
MODEL_DIR = DATA_DIR / "models"
OS_DIR = MODEL_DIR / "openstudio_models"
MEASURES_DIR = MODEL_DIR / "openstudio_measures"
ECM_DIR = DATA_DIR / "ecm_definitions"
OSW_DIR = DATA_DIR / "osws"

# Output file paths
RESULTS_DIR = REPO_ROOT / "results"

# Logging file paths
LOG_DIR = REPO_ROOT / "logs"
KPI_LOG_DIR = LOG_DIR / "kpi_logs"
RUN_LOGS_DIR = LOG_DIR / "run_logs"
SUMMARY_DIR = LOG_DIR / "summary_stats"
RESULTS_ARCHIVE = LOG_DIR / "archive"
