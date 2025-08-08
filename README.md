# DeepHyper Multi-Objective Optimization Workflow

## 🏗 Project Summary

This project performs **multi-objective optimization** on building retrofit configurations using:
- 📦 OpenStudio for energy simulations
- 🧠 DeepHyper for intelligent, Pareto-efficient search
- 📊 Evaluation of three objectives: **Operational Carbon**, **Embodied Carbon**, and **BERDO fine (cost)**

The goal is to identify retrofit configurations that minimize lifecycle carbon and policy fines while avoiding exhaustive enumeration of 1000+ combinations.

---

## ✅ Current Status (Asynchronous Run)

### 🎯 Optimization Engine

- **Search Algorithm**: Centralized Bayesian Optimization (`CBO`)
- **Acquisition Functions**: `UCB` or `EI` (select via `ACQUISITION_FUNCTION` env var)
- **Surrogate Model**: Extremely Randomized Trees (`ET`)
- **Search Strategy**: Fully asynchronous evaluation with candidate deduplication
- **Initial Sampling**: Seed configurations from JSON file (`seed_configs.json`)

### ⚙️ Execution Settings

| Setting                     | Value                          |
|----------------------------|----------------------------------|
| Parallel Evaluations       | 10 (via `num_cpu_workers`)      |
| Max Evaluations (`max_evals`) | 300                          |
| Kappa Decay (if using UCB) | Every 40 evals to min 1.5       |
| Seed Config Source         | `4-input_data/seed_configs/`    |
| Objective Scaler           | Manual normalization (max values) |
| Failed Config Handling     | Skipped with `[inf, inf, inf]`  |

---

## 🧠 Evaluation Pipeline

### Step-by-Step Breakdown

Each configuration undergoes:
1. **Constraint validation** (window/infiltration logic enforced if `is_valid_config` is active)
2. **.osw Generation** from ECM config + `cluster4-existing-condition.osm` seed model
3. **OpenStudio Simulation** to get `eplustbl.csv` metrics
4. **KPI Parsing**: 
   - **Embodied Carbon** (wall, roof, windows, HVAC, DHW)
   - **Operational Carbon** (fuel-type emissions)
   - **BERDO Fine Estimate** (based on EUI thresholds)
5. **Normalization + Objective Return** for optimization

> DeepHyper minimizes by default, so each objective is multiplied by `-1` to convert our maximization goals (OC/EC/Fine reduction) into minimization.

Normalized objective values:
- `[-OC_normalized, -EC_normalized, -Fine_normalized]`

---

## 📁 Directory Structure

| Path                     | Description                                                  |
|--------------------------|--------------------------------------------------------------|
| `1-openstudio-models/`   | Seed `.osm` model and weather file (`.epw`)                  |
| `2-measures/`            | Custom OpenStudio Measures for ECM upgrades                  |
| ├─ `insulation/`         | Wall, roof, wall+infiltration upgrade measures               |
| ├─ `windows/`            | U-value, SHGC, and window construction upgrades              |
| ├─ `hvac/`               | Mini-split, Packaged HP, and system selection measures       |
| ├─ `dhw/`                | DHW-to-HPWH conversion measure                               |
| ├─ `ventilation/`        | In-unit ERV addition                                         |
| └─ `air-sealing/`        | Infiltration rate adjustment                                 |
| `3-ecm_definitions/`     | ECM config file (`ecm_options.json`)                         |
| `4-input_data/`          | Emissions factors, thresholds, and `seed_configs.json`       |
| └─ `seed_configs/`       | Pre-defined starting configs (incl. `individual_configs/`)   |
| `5-osws/`                | Generated `.osw` files and matching `_run/` folders          |
| `praevion_async_core/`   | Main driver: async optimizer, run orchestration, logging     |
| ├─ `config/`             | Hyperparameter search settings (e.g., `config_ucb.py`)       |
| ├─ `utils/`              | Logging, filtering, cleanup, search helpers                  |
| ├─ `kpi_logs/`           | Live `.jsonl` logs and best config summaries                 |
| ├─ `results/`            | Full search results from DeepHyper                          |
| ├─ `run_logs/`           | Organized folders of OpenStudio simulation outputs           |
| └─ `archive/`            | Compressed logs, results, and `.osw` files from past runs    |
| `src/`                   | Simulation core: OSW generation, parsing, KPI computation    |
| `test_files/`            | Unit tests for core modules and ECM logic                    |

---

## 🧹 Pre-Run Cleanup

Utility functions manage workspace hygiene:
- `clean_batch_folders()` — wipes `5-osws/`, `praevion_async_core/run_logs/`, `praevion_async_core/kpi_logs/` before a new run
- `archive_logs()` — saves old KPI logs and results to `praevion_async_core/archive/`
- `archive_osws()` — zips `.osw` + `_run` folders, deletes originals
- `delete_heavy_outputs()` — removes large OpenStudio files post-parsing

---

## 🔧 Current Configuration

Configuration is loaded dynamically from `config_ucb.py` or `config_ei.py` depending on `ACQUISITION_FUNCTION`. The default is:

| Parameter                    | Value                          |
|-----------------------------|----------------------------------|
| `initial_point_generator`   | `sobol`                         |
| `n_initial_points`          | 32                              |
| `acq_func`                  | `UCB`                           |
| `kappa (start)`             | 2.5                             |
| `kappa (final)`             | 1.25                            |
| `decay schedule`            | every 35 evals                  |
| `acq_optimizer`             | `mixedga` (for discrete space)  |
| `n_points` (for scoring)    | 500                             |
| `multi_point_strategy`      | `qUCBd`                         |
| `moo_scalarization_strategy`| `AugChebyshev`                  |
| `objective_scaler`          | `minmax`                        |
| `filter_duplicated`         | True                            |
| `filter_failures`           | `ignore`                        |
| `max_failures`              | 200                             |

---

## 🔁 Launching an Optimization Run

To start an asynchronous optimization with your preferred acquisition function:

```bash
# Set acquisition function to either 'ucb' or 'ei'
export ACQUISITION_FUNCTION=ucb

# Run the search engine
python praevion_async_core/run_async.py
```

---

## ⚠️ Current Limitations

- **Conditional Logic Not Yet Incorporated into Search Space**  
  ECM constraints (e.g., infiltration depending on wall insulation) are not yet enforced via ConfigSpace conditions. This logic is planned but currently missing from the active optimization layer.

- **No Cost Constraints or Budget Optimization Yet**  
  Total retrofit implementation cost is not yet a constraint or optimization variable.

- **No User-Tunable Preference Weighting**  
  Scalarization is randomized. User-defined priorities across OC, EC, and Fine are not yet supported.

- **Single-Algorithm Backend (CBO)**  
  Current backend uses only CBO. No hybrid or dynamic algorithm switching yet.

---

## 🌱 Future Expansions

- 🔄 **Hybrid Algorithms**  
  Combine CBO with:
  - Genetic Algorithms (e.g., NSGA-II) for better exploration
  - Reinforcement Learning for adaptive search over time
  - Constraint-aware filtering within `ask()` for real-time validation and duplicates exclusion

- 🧠 **Conditional ConfigSpace Definitions**  
  Integrate `EqualsCondition` / `InCondition` from ConfigSpace to enforce valid ECM hierarchies during sampling.

- 💸 **Cost-Effectiveness Modeling**  
  Add total retrofit cost, marginal abatement cost, and simple payback period as KPIs.

- 🧪 **User-Controlled Exploration/Exploitation Settings**  
  Allow interface-level control over `kappa`, `max_evals`, and category freezing to guide the search.

- 📈 **Pareto-Aware Recommendations Engine + Interface**  
  Train a supervised ML model on search results to offer real-time retrofit suggestions, delivered via an interactive frontend interface that connects to the backend inference engine.


> Built with ❤️ by Praevion — unlocking smarter retrofit strategies with optimization.