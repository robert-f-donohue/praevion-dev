# DeepHyper Multi-Objective Optimization Workflow

## 🏗 Project Summary

This project performs **multi-objective optimization** on building retrofit configurations using:
- 📦 OpenStudio for energy simulations
- 🧠 DeepHyper for intelligent, Pareto-efficient search
- 🧮 Operational Carbon + Embodied Carbon as the dual objectives

The goal is to identify retrofit configurations that minimize both OC and EC while avoiding exhaustive search across 1000+ possible configurations.

---

## ✅ Current Status (Pre-Run)

### 🎯 Optimization Engine

- **Search Algorithm**: Centralized Bayesian Optimization (`CBO`)
- **Acquisition Function**: `UCB` (Upper Confidence Bound) with decaying `kappa`
- **Surrogate Model**: Extremely Randomized Trees (`ET`)
- **Batch Strategy**: `qUCBd` for efficient multi-point exploration
- **Initial Sampling**: Sobol generator for well-distributed starting points

### ⚙️ Execution Settings

| Setting                     | Value                      |
|----------------------------|----------------------------|
| Parallel Evaluations       | 10 (based on `num_cpus`)   |
| `n_points` (candidate pool)| 300                        |
| Initial Points             | Default (2n + 1)           |
| Kappa Decay                | Every 40 evals to 1.5      |
| Objective Scaler           | `minmax`                   |
| Failed Config Handling     | `filter_failures = ignore` |

### 🧪 Evaluation Function

- Robust validation of measure compatibility via `is_valid_config()`
- Invalid or failed runs return `[inf, inf]` with metadata
- Metadata and KPI logs stored in `8-kpi_logs/kpi_log.jsonl`

---

## 📁 Directory Structure

| Folder         | Purpose                                 |
|----------------|------------------------------------------|
| `4-input_data/`| ECM configuration options (JSON)        |
| `5-osws/`      | Input .osw files and temp run folders   |
| `6-deephyper/` | Search controller (`run_search.py`)     |
| `7-run_logs/`  | Archived run folders (post-run)         |
| `8-kpi_logs/`  | Final KPI logs (`kpi_log.jsonl`, archive) |

---

## 🧹 Pre-Run Cleanup

The following utilities reset your workspace before execution:

- `clean_batch_folders(project_root)`  
  - Clears `5-osws/`, `7-run_logs/`, and `8-kpi_logs/`  
  - Archives previous KPI logs with timestamp

- `delete_heavy_outputs(run_dir)`  
  - Deletes large/unneeded OpenStudio output files post-run  
  - Retains `eplustbl.csv`, `model.osm`, etc.

---

## 🔁 Execution

To begin the search:

```bash
python run_search.py