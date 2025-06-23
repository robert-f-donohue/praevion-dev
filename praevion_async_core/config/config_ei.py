EI_CONFIG = {
    "initial_point_generator": "sobol",     # Quasi-random for good initial spread across space
    "n_initial_points": 32,                 # Sobol requires number of samples to be a power of 2
    "acq_func": "EI",                       # Use UCB with decaying exploration for better convergence
    "acq_func_kwargs": {
        "xi": 0.01,
        "scheduler": {
            "type": "periodic-exp-decay",
            "period": 25,
            "xi_final": 0.001           # Higher xi = more exploration. EI is greedy by default.
        }
    },
    "acq_optimizer": "mixedga",         # Handles discrete + continuous search spaces well
    "acq_optimizer_kwargs": {
        "n_points": 300,                # Wide sampling pool for surrogate scoring
        "n_jobs": 6,                    # Matches your CPU core count for fast batch eval
        "filter_duplicated": True,      # Avoid scoring duplicate configs
        "filter_failures": "ignore",    # Failures get immediately removed
        "max_failures": 200             # Cap the retry window to prevent stalls
    },
    "surrogate_model": "ET",
    "solution_selection": "argmax_obs",
    "multi_point_strategy": "cl_min",           # Enables parallel EI
    "moo_scalarization_strategy": "Chebyshev",  # Balances Pareto front edge discovery
    "moo_scalarization_weight": None,           # Randomized weights for full Pareto front coverage
    "objective_scaler": "minmax",               # Normalize for equal importance across KPIs
    "verbose": 1
}