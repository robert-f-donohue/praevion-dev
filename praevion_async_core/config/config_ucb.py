UCB_CONFIG = {
    # "initial_point_generator": "sobol",     # Feasibility modeling of sobol sampling offloaded to custom function
    # "n_initial_points": 128,
    "surrogate_model": "ET",
    "surrogate_model_kwargs": {
        "n_estimators": 100,
        "min_impurity_decrease": 0.001,
        "max_features": "sqrt",
        "splitter": "random",
        "random_state": 42,
    },
    "acq_func": "UCBd",
    "acq_func_kwargs": {
        "kappa": 3.0,                       # Start with strong exploration
        "xi": 0.1,                          # Placeholder in case scheduler is changed
        "scheduler": {                      # Add scheduler to taper exploration
            "type": "periodic-exp-decay",
            "period": 40,                   # Every 40 evaluations, apply decay
            "kappa_final": 0.25             # Don't decay all the way to greediness (0.25 is too aggressive)
        }
    },
    "acq_optimizer": "mixedga",         # Handles discrete + continuous search spaces well
    "acq_optimizer_kwargs": {
        "n_points": 80,                 # Wide sampling pool for surrogate scoring
        "n_jobs": 10,                   # Matches your CPU core count for fast batch eval
        "filter_duplicated": True,      # Avoid scoring duplicate configs
        "filter_failures": "ignore",    # Failures get immediately removed
        "max_failures": 200,            # Cap the retry window to prevent stalls
        "acq_optimizer_freq": 5
    },
    # Then here this is all wrong
    "multi_point_strategy": "qUCBd",                # Vectorized + decayed UCB for smart parallel batch selection
    "moo_scalarization_strategy": "AugChebyshev",   # Adds a 1-norm penalty Pareto front edge discovery
    "moo_scalarization_weight": None,               # Randomized weights for full Pareto front coverage
    "objective_scaler": "auto",                   # Normalize for equal importance across KPIs
    "verbose": 1
}