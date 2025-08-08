import numpy as np
from scipy.stats import qmc
from ConfigSpace import Configuration
from deephyper.hpo import HpProblem
from praevion_async_core.utils.search_utils import is_valid_config

def generate_filtered_sobol_samples(
        problem: HpProblem,
        n_samples: int = 256,
        seed: int = 42,
        verbose: bool = True,
        debug: bool = False,
    ) -> list[dict]:
    """
    Generate Sobol samples from the full design space and filter out invalid configurations
    based on ConfigSpace constraints, preserving Sobol ordering

    Args:
        problem (HpProblem): The HpProblem object containing the search space.
        n_samples (int): Number of Sobol points to generate.
        seed (int): Random seed for reproducibility.
        verbose (bool): Whether to print summary information.
        debug (bool): If True, print detailed failure reasons.

    Returns:
        list[dict]: Valid configurations in Sobol sequence order.
    """
    # Model search space and dimensionality
    cs = problem.space
    hyperparameters = cs.get_hyperparameters()
    n_dims = len(hyperparameters)

    if debug:
        print(f"🧠 Total hyperparameters (input dimensions): {n_dims}")
        print("📋 Hyperparameter names:")
        for hp in hyperparameters:
            print(f"  - {hp.name} ({hp.__class__.__name__}): {getattr(hp, 'choices', 'continuous')}")

    # Initialize our quasi-random configuration generator
    sobol = qmc.Sobol(d=n_dims, scramble=True, seed=seed)
    sobol_vectors = sobol.random(n=n_samples)

    valid_configs = []
    for i in range(n_samples):
        try:
            config_dict = decode_sobol_vector(sobol_vectors[i], cs)

            # Now validate via ConfigSpace itself (checks conditions/forbidden)
            config_obj = Configuration(cs, values=config_dict)

            # Optional: check any domain-specific rules
            if is_valid_config(config_dict):
                valid_configs.append(config_dict)
            else:
                if debug:
                    print(f"❌ Sample {i} rejected by `is_valid_config`:\n{config_dict}\n")

        except Exception as e:
            if debug:
                print(f"⚠️ Sample {i} failed ConfigSpace decoding: {e}")

    if verbose:
        print(f"🧪 Generated {n_samples} Sobol samples.")
        print(f"✅ {len(valid_configs)} passed all constraints ({len(valid_configs) / n_samples:.1%})")

    return valid_configs

def decode_sobol_vector(vector: np.ndarray, cs) -> dict:
    config_dict = {}

    for i, hp in enumerate(cs.get_hyperparameters()):
        val = vector[i]

        if hp.__class__.__name__ == "CategoricalHyperparameter":
            idx = int(val * len(hp.choices))
            idx = min(idx, len(hp.choices) - 1)  # Clip upper bound
            config_dict[hp.name] = hp.choices[idx]

        elif hp.__class__.__name__ == "OrdinalHyperparameter":
            idx = int(val * len(hp.sequence))
            idx = min(idx, len(hp.sequence) - 1)
            config_dict[hp.name] = hp.sequence[idx]

        elif hp.__class__.__name__ == "UniformIntegerHyperparameter":
            lower, upper = hp.lower, hp.upper
            mapped_val = int(np.floor(val * (upper - lower + 1))) + lower
            mapped_val = min(mapped_val, upper)
            config_dict[hp.name] = mapped_val

        elif hp.__class__.__name__ == "UniformFloatHyperparameter":
            lower, upper = hp.lower, hp.upper
            config_dict[hp.name] = val * (upper - lower) + lower

        elif hp.__class__.__name__ == "Constant":
            config_dict[hp.name] = hp.value

        else:
            raise NotImplementedError(f"Unsupported hyperparameter type: {hp}")

    return config_dict