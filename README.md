# Praevion Phase I – Monte Carlo Bayesian Optimization Engine

## 🏗 Project Summary

This project executes **multi-objective optimization** for building retrofit strategies using:
- 📦 **OpenStudio/EnergyPlus** for full-building simulation
- 🧠 **DeepHyper CBO** with tree-based surrogates for constrained, categorical search
- 📊 **Four objectives**: Operational Carbon, Embodied Carbon, Long-run Cost (Material + Utility), and Material Cost (standalone KPI)
- - 🎯 **Goal**: Identify Pareto-optimal retrofit configurations that minimize lifecycle emissions and costs under policy constraints like BERDO.

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
| κ Start → Final             | 3.0 → 0.1 (periodic decay)      |
| Scalarization               | AugChebyshev                    |
| Objective Sign              | Negative (DeepHyper minimizes)  |
| Fail Handling               | `[inf, inf, inf, inf]` returned |

---


## 🧠 Evaluation Pipeline

Each configuration goes through:

1. **Validation** – ConfigSpace + `is_valid_config()` rules
2. **OSW Generation** – from ECM config + `cluster4-existing-condition.osm`
3. **Simulation** – OpenStudio runs, producing `eplustbl.csv`
4. **KPI Extraction**:
   - Operational Carbon (OC)
   - Embodied Carbon (EC)
   - BERDO Fine (USD)
   - Material Cost (USD)
   - Discounted Utility Cost (25 years, 3% discount rate)
5. **Objective Normalization** – fixed-theoretical max/min scaling
6. **Return to Optimizer** – 4D normalized, negated objective vector

---

## 📁 Directory Structure

| Path                           | Description |
|--------------------------------|-------------|
| `01_models/`                   | Baseline `.osm` + `.epw` files |
| `02_measures/`                 | OpenStudio measures (ECMs) grouped by category |
| `03_ecm_search_spaces/`        | ECM option definitions (`ecm_options_complex.json`, etc.) |
| `04_input_data/`               | Factor tables, thresholds, material costs, utility rates, seed configs |
| `05_osws/`                     | Generated OSWs and `_run/` output folders |
| `06_tests/`                    | Unit and integration tests for pipeline components |
| `07_archive/`                  | Compressed logs, results, old OSWs, retired scripts/measures |
| `praevion_core/`               | Optimization engine core: configs, run orchestration, logging, Sobol sampling, constraint filters |
| `src/`                         | Simulation orchestration, KPI computation, OpenStudio interfacing |


---

## 🧹 Pre-Run Cleanup & Archiving

- `clean_batch_folders()` – wipes `05_osws/`, `run_logs/`, `kpi_logs/`
- `archive_logs()` – moves prior run logs/results to `07_archive/`
- `archive_osws()` – zips OSWs + `_run` folders
- `expand_objectives_column()` – unpacks KPI dicts into flat CSV columns
- `log_optimization_summary_to_csv()` – logs Pareto size, crowding stats, objective ranges

---

## 🔁 Launching an Optimization Run

To start an asynchronous optimization with your preferred acquisition function:

```bash
# Example run
python praevion_core/main.py
```

```bash
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
