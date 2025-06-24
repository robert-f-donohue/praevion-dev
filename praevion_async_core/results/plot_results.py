import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Theoretical maximums for normalization
min_oc = 1_508_000
max_oc = 5_552_000
max_ec = 464_000
max_fine = 487_000

# Load results
df = pd.read_csv("results_ucb_function_search_20250623-192330.csv")

# Extract normalized objective values
oc_norm = -df["objective_0"]
ec_norm = -df["objective_1"]
fine_norm = -df["objective_2"]

# Unscale values
df["OC"] = oc_norm * (max_oc - min_oc) + min_oc
df["EC"] = ec_norm * max_ec
df["Fine"] = fine_norm * max_fine

# Get pareto efficient
df["pareto"] = df["pareto_efficient"]

# Plotting
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# 1. Operational Carbon vs. Embodied Carbon
axes[0].scatter(df[~df.pareto]["OC"], df[~df.pareto]["EC"], alpha=0.5, label="Other configs")
axes[0].scatter(df[df.pareto]["OC"], df[df.pareto]["EC"], color="red", label="Pareto front")
axes[0].set_xlabel("Operational Carbon (kgCO₂)")
axes[0].set_ylabel("Embodied Carbon (kgCO₂)")
axes[0].set_xlim([1_500_000, 5_600_000])
axes[0].set_ylim([0, 475_000])
axes[0].set_title("Operational vs. Embodied Carbon (kg CO2e)")
axes[0].legend()

# 2. Operational Carbon vs. BERDO Fine
axes[1].scatter(df[~df.pareto]["OC"], df[~df.pareto]["Fine"], alpha=0.5)
axes[1].scatter(df[df.pareto]["OC"], df[df.pareto]["Fine"], color="red")
axes[1].set_xlabel("Operational Carbon (kgCO₂)")
axes[1].set_ylabel("BERDO Fine ($)")
axes[1].set_xlim([1_500_000, 5_600_000])
axes[1].set_ylim([0, 500_000])
axes[1].set_title("Operational Carbon vs. Fine")

# 3. Embodied Carbon vs. BERDO Fine
axes[2].scatter(df[~df.pareto]["EC"], df[~df.pareto]["Fine"], alpha=0.5)
axes[2].scatter(df[df.pareto]["EC"], df[df.pareto]["Fine"], color="red")
axes[2].set_xlabel("Embodied Carbon (kgCO₂)")
axes[2].set_ylabel("BERDO Fine ($)")
axes[2].set_xlim([0, 475_000])
axes[2].set_ylim([0, 500_000])
axes[2].set_title("EC vs. Fine")

plt.tight_layout()
plt.show()