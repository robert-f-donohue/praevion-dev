# Praevion Phase I – Monte Carlo Bayesian Optimization Engine

## 🏗 Project Summary

This project executes **multi-objective optimization** for building retrofit strategies using:
- 📦 **OpenStudio/EnergyPlus** for full-building simulation
- 🧠 **DeepHyper CBO** with tree-based surrogates for constrained, categorical search
- 📊 **Four objectives**: Operational Carbon, Embodied Carbon, Material Cost, and Long-run Cost (Material + Utility)
- 🎯 **Goal**: Identify Pareto-optimal retrofit configurations that minimize lifecycle emissions and costs under policy constraints like BERDO.

---

## ✅ Phase I Optimization Engine

- **Surrogate Model**: Extremely Randomized Trees (ET) – handles categorical, mixed-type inputs
- **Acquisition Function**: `qUCBd` (Monte Carlo-estimated, decaying κ)
- **Scalarization**: Augmented Chebyshev (robust for non-convex Pareto fronts)
- **Initialization**: Filtered Sobol sequence – removes invalid configs via ConfigSpace + `is_valid_config()`
- **Constraints**: All hard constraints encoded in ConfigSpace (`problem.py`) + domain-specific filters
- **Execution**: Fully parallel, 10 CPU workers by default
- **Deduplication**: Hash-based duplicate check across async jobs

## ⚙️ Execution Defaults


| Setting                     | Value                           |
|-----------------------------|---------------------------------|
| Parallel Evaluations        | 10 CPU workers                  |
| Max Evaluations             | user-set (e.g., 300–700)        |
| Initial Sobol Samples       | 256                             |
| Acquisition Function        | qUCBd                           |
| κ Start → Final             | 3.0 → 0.25 (periodic decay)     |
| Scalarization               | AugChebyshev                    |
| Objective Sign              | Negative (DeepHyper minimizes)  |
| Fail Handling               | `[inf, inf, inf, inf]` returned |

---


## 🧠 Evaluation Pipeline

Each configuration goes through:

1. **Validation** – ConfigSpace + `is_valid_config()` rules
2. **OSW Generation** – ECM config + baseline `.osm`
3. **Simulation** – OpenStudio runs, producing `eplustbl.csv`
4. **KPI Extraction**:
   - Operational Carbon (OC)
   - Embodied Carbon (EC)
   - Material Cost (USD)
   - BERDO Fine (25 years, 3% discount rate)
   - Discounted Utility Cost (25 years, 3% discount rate)
5. **Objective Normalization** – fixed-theoretical max/min scaling
6. **Return to Optimizer** – 4D normalized, negated objective vector

---

## 📁 Directory Structure

| Path                                   | Description |
|----------------------------------------|-------------|
| `data/ecm_definitions/`               | ECM option definitions (JSON) |
| `data/inputs/`                         | Factor tables, thresholds, material costs, utility rates, seed configs |
| `data/models/openstudio_measures/`     | OpenStudio measures grouped by category (e.g., hvac, insulation, windows) |
| `data/models/openstudio_models/`       | Baseline `.osm` + `.epw` files |
| `data/models/seed_configs/`            | Example ECM configuration seeds |
| `data/osws/`                           | Generated OSWs and `_run/` outputs |
| `logs/kpi_logs/`                        | KPI JSONL logs per configuration |
| `logs/run_logs/`                        | Runtime logs from optimization loop |
| `logs/summary_stats/`                   | Aggregated run summaries (Pareto size, crowding distance, etc.) |
| `logs/archive/`                         | Old run logs and OSWs |
| `praevion_core/config/`                 | Path constants, optimization constants |
| `praevion_core/domain/`                 | KPI computation, carbon and cost modules |
| `praevion_core/adapters/`               | OpenStudio/EnergyPlus execution and parsing |
| `praevion_core/interfaces/cli/`         | CLI entry points (e.g., `main.py`) |
| `praevion_core/pipelines/`              | Orchestrated run loops and search workflows |
| `results/`                              | Output CSV of completed optimization runs |
| `tests/`                                | Unit and integration tests |


---

## 🧹 Pre-Run Cleanup & Archiving

- `clean_batch_folders()` – wipes `05_osws/`, `run_logs/`, `kpi_logs/`
- `archive_logs()` – moves prior run logs/results to `07_archive/`
- `archive_osws()` – zips OSWs + `_run` folders
- `expand_objectives_column()` – unpacks KPI dicts into flat CSV columns
- `log_optimization_summary_to_csv()` – logs Pareto size, crowding stats, objective ranges

---

## 🔁 Launching an Optimization Run

```bash
# Example run
python -m praevion_core.interfaces.cli.main
```

```bash
# Optional: choose acquisition function
export ACQUISITION_FUNCTION=ucb
```

---

## 📊 Performance Metrics

After each run:
- Pareto front coverage
- Crowding distance mean/std
- Objective min/max
- Duplicate removal count

These support **runtime sensitivity analysis** to find the "good enough" budget.

---

## 🌱 Next Steps (Beyond Phase I)

- Multi-cluster testing for generalization
- `RunDataset` abstraction for re-seeding and meta-modeling
- User-driven scalarization in interactive sandbox
- Test new surrogate models (e.g., MLP + Dropout)
- Soft constraint modeling for stochastic failures

> Built with ❤️ by Praevion — unlocking smarter retrofit strategies with optimization.
