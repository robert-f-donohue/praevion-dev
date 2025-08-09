CONSTANTS = {
    # BERDO + utility baselines
    "net_berdo_min": 74_620,
    "utility_cost_baseline": 2_184_813,
    "utility_cost_max": 3_693_027,
    "utility_cost_min": 1_638_838,

    # Normalization bounds
    "min_oc": 1_355_578,
    "max_oc": 5_515_869,
    "max_ec": 476_657,
    "max_mat_cost": 1_209_421,

# Guard for long-run normalization (was +1 to avoid zero denom)
    "longrun_guard": 1,
}
