from praevion_core.config import paths


def test_paths_exist():
    # Test all paths exist
    assert paths.DATA_DIR.exists()
    assert paths.INPUT_DIR.exists()
    assert paths.MODEL_DIR.exists()
    assert paths.ECM_DIR.exists()
    assert paths.OSW_DIR.exists()
    assert paths.RESULTS_DIR.exists()
    assert paths.LOG_DIR.exists()
    assert paths.KPI_LOG_DIR.exists()
    assert paths.RUN_LOGS_DIR.exists()
    assert paths.SUMMARY_DIR.exists()
    assert paths.RESULTS_ARCHIVE.exists()
