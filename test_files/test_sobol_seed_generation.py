import pytest
import numpy as np
import matplotlib.pyplot as plt
from praevion_async_core.problem import problem
from praevion_async_core.utils.search_utils import is_valid_config
from praevion_async_core.utils.sobol_sampler import generate_filtered_sobol_samples

def test_pass_rate():
    n_samples = 256
    seed = 42

    valid_configs = generate_filtered_sobol_samples(problem=problem, n_samples=n_samples, seed=seed)

    assert isinstance(valid_configs, list), "Output should be a list"
    assert all(isinstance(cfg, dict) for cfg in valid_configs), "Each config should be a dictionary"

    num_valid = len(valid_configs)
    pass_rate = num_valid / n_samples

    print(f"\n🧪 Pass rate: {num_valid}/{n_samples} ({pass_rate:.1%})")

    # Sanity check: expect at least 25% of samples to survive constraints
    assert pass_rate >= 0.25, "Too many configurations were filtered out — check constraints or ConfigSpace"

    # Bonus: check all configs satisfy domain rules
    for cfg in valid_configs:
        assert is_valid_config(cfg), f"Config failed custom constraint: {cfg}"

def test_reproducibility():
    configs1 = generate_filtered_sobol_samples(problem, n_samples=256, seed=42, verbose=False)
    configs2 = generate_filtered_sobol_samples(problem, n_samples=256, seed=42, verbose=False)
    assert configs1 == configs2, "Same seed should produce identical results"

@pytest.mark.parametrize("n_samples", [64, 128, 256, 512, 1024])
def test_pass_rate_scaling(n_samples):
    configs = generate_filtered_sobol_samples(problem, n_samples=n_samples, seed=42, verbose=False)
    pass_rate = len(configs) / n_samples
    print(f"📈 Pass rate @ n={n_samples}: {len(configs)} / {n_samples} ({pass_rate:.1%})")
    assert 0.2 <= pass_rate <= 0.8, "Unexpected pass rate — check constraint tightness"

def test_seed_sensitivity():
    seeds = list(range(10))
    rates = []
    for seed in seeds:
        configs = generate_filtered_sobol_samples(problem, n_samples=256, seed=seed, verbose=False)
        rate = len(configs) / 256
        rates.append(rate)
        print(f"🎲 Seed {seed}: Pass rate = {rate:.1%}")

    avg_rate = np.mean(rates)
    std_rate = np.std(rates)
    print(f"\n📊 Mean pass rate = {avg_rate:.1%}, Std dev = {std_rate:.1%}")
    assert 0.2 <= avg_rate <= 0.8, "Average pass rate out of expected range"
    assert std_rate < 0.2, "Too much variability — may need more stable constraint logic"

def test_sample_config_format():
    n_samples = 64
    seed = 123

    valid_configs = generate_filtered_sobol_samples(problem=problem, n_samples=n_samples, seed=seed)

    assert len(valid_configs) > 0, "No valid configurations found."

    print("\n🧾 Example valid configuration:")
    for k, v in valid_configs[0].items():
        print(f"  {k}: {v}")

    # Optional: check structure
    assert isinstance(valid_configs[0], dict), "Config should be a dictionary"
    assert all(isinstance(k, str) for k in valid_configs[0].keys()), "All keys should be strings"