UCB_CONFIG = {
    "initial_point_generator": "sobol",     # Quasi-random for good initial spread across space
    "n_initial_points": 16,
    "acq_func": "UCB",                      # Use UCB with decaying exploration for better convergence
    "acq_func_kwargs": {
        "kappa": 2.5,                       # Start with strong exploration
        "scheduler": {                      # Add scheduler to taper exploration
            "type": "periodic-exp-decay",
            "period": 80,                   # Every 80 evaluations, apply decay
            "kappa_final": 1.0              # Don't decay all the way to greediness (0.25 is too aggressive)
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
    "multi_point_strategy": "qUCBd",            # Vectorized + decayed UCB for smart parallel batch selection
    "moo_scalarization_strategy": "Chebyshev",  # Balances Pareto front edge discovery
    "moo_scalarization_weight": None,           # Randomized weights for full Pareto front coverage
    "objective_scaler": "minmax",               # Normalize for equal importance across KPIs
    "verbose": 1
}