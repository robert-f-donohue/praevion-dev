import os

BASE_DIR = os.path.dirname(__file__)

# Logging and Results
INPUT_DIR       = os.path.join(BASE_DIR, '..', '4-input_data')
LOG_DIR         = os.path.join(BASE_DIR, 'kpi_logs')
SUMMARY_DIR     = os.path.join(BASE_DIR, 'summary_stats')
OSW_DIR         = os.path.abspath(os.path.join(BASE_DIR, '..', '5-osws'))
RUN_LOGS_DIR    = os.path.join(BASE_DIR, 'run_logs')
RESULTS_DIR     = os.path.join(BASE_DIR, 'results')
RESULTS_ARCHIVE = os.path.join(BASE_DIR, 'archive')