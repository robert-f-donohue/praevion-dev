import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


# Load results
df = pd.read_csv("results_ucb_function_search_20250624-041706.csv")

# Constants for reversing normalization
min_oc = 1_508_000
max_oc = 5_552_000
max_ec = 464_000
max_fine = 487_000
max_mat_cost = 1_167_000

# Reverse normalization
df["OC"] = -df["objective_0"] * (max_oc - min_oc) + min_oc
df["EC"] = -df["objective_1"] * max_ec
df["Fine"] = np.exp(-df["objective_2"] * np.log(max_fine + 100)) - 100
df["Material"] = -df["objective_3"] * max_mat_cost
df["pareto"] = df["pareto_efficient"]

# Compute totals
df["Total_Carbon"] = df["OC"] + df["EC"]
df["Total_Cost"] = df["Fine"] + df["Material"]

# Piecewise custom axis transformation
x_min = df["Total_Carbon"].min()
x_q25 = 2_000_000
x_q50 = 3_500_000
x_max = df["Total_Carbon"].max()

def piecewise_stretch(x):
    if x <= x_q25:
        return 0.5 * (x - x_min) / (x_q25 - x_min)
    elif x <= x_q50:
        return 0.5 + 0.25 * (x - x_q25) / (x_q50 - x_q25)
    else:
        return 0.75 + 0.25 * (x - x_q50) / (x_max - x_q50)

df["Total_Carbon_stretched"] = df["Total_Carbon"].apply(piecewise_stretch)

# HVAC system (color) and DHW system (shape)
df["HVAC"] = df["p:upgrade_hvac_system_choice"].fillna("Unknown")
df["DHW"] = df["p:upgrade_dhw_to_hpwh"].map({
    "Upgrade": "HPWH",
    "Baseline": "Gas DHW"
}).fillna("Unknown")


# Normalize material cost to [0, 1] for shading scale
df["Capex_Normalized"] = (df["Material"] - df["Material"].min()) / (df["Material"].max() - df["Material"].min())

# Seaborn theme
sns.set_theme(style="whitegrid", context="notebook", font_scale=1.1)

# Capex tiers for point sizing
df["Capex_Tier"] = pd.qcut(df["Material"], q=3, labels=["Low", "Medium", "High"])
df["Capex_Alpha"] = df["Capex_Tier"].map({
    "Low": 0.98,  # Most visible
    "Medium": 0.65,
    "High": 0.4
})

plt.figure(figsize=(10, 6))

# Background (non-Pareto)
sns.scatterplot(
    data=df[~df["pareto"]],
    x="Total_Carbon_stretched", y="Total_Cost",
    color="lightgray", alpha=0.4
)

# HVAC colors
hvac_palette = {
    "Condensing Boiler": "#AF2E2E",
    "Mini-Split": "#018DDF",
    "Packaged HP": "#11C020",
    "Baseline": "#5A5A5A"
}

hvac_legend = [
    Line2D([0], [0], marker='o', color='w', label=hvac,
           markerfacecolor=color, markeredgecolor='black', markersize=10)
    for hvac, color in hvac_palette.items()
]

# DHW shapes
dhw_legend = [
    Line2D([0], [0], marker='o', color='w', label='HPWH (Full Electric)',
           markerfacecolor='gray', markeredgecolor='black', markersize=10),
    Line2D([0], [0], marker='X', color='w', label='Gas DHW',
           markerfacecolor='gray', markeredgecolor='black', markersize=10)
]

# Capex Alpha Legend (Upfront Cost)
capex_legend = [
    Line2D([0], [0], marker='o', color='black', label='Low', alpha=1.0, markersize=8),
    Line2D([0], [0], marker='o', color='black', label='Medium', alpha=0.7, markersize=8),
    Line2D([0], [0], marker='o', color='black', label='High', alpha=0.4, markersize=8)
]

# Plot Pareto configurations by Capex_Alpha group
for alpha_level in df["Capex_Alpha"].unique():
    subset = df[(df["pareto"]) & (df["Capex_Alpha"] == alpha_level)]
    sns.scatterplot(
        data=subset,
        x="Total_Carbon_stretched", y="Total_Cost",
        hue="HVAC", style="DHW",
        markers={"HPWH": "o", "Gas DHW": "X"},
        s=120,
        palette=hvac_palette,
        alpha=alpha_level,
        edgecolor="black",
        legend=False
    )


plt.legend(
    handles=(
        [Line2D([], [], linestyle='none', label='HVAC')] + hvac_legend +
        [Line2D([], [], linestyle='none', label='DHW')] + dhw_legend +
        [Line2D([], [], linestyle='none', label='Upfront Cost')] + capex_legend
    ),
    loc="upper right", frameon=True, facecolor="white", framealpha=0.9
)

for v in [0.5, 0.75]:
    plt.axvline(x=v, color="black", linestyle="--", linewidth=1)

plt.xlabel("Custom-Stretched Total Carbon")
plt.ylabel("Total Cost ($)")
plt.title("Pareto Configurations by HVAC & DHW\nLow-Cost Solutions Pop Visually via Alpha")
plt.tight_layout()


# ----------------------------------------------------------------
# OC vs EC Scatter Plot
# ----------------------------------------------------------------

# Custom-stretch Operational Carbon for X-axis
x_min = df["OC"].min()
x_q25 = 2_000_000
x_q50 = 3_500_000
x_max = df["OC"].max()

def piecewise_stretch_oc(x):
    if x <= x_q25:
        return 0.5 * (x - x_min) / (x_q25 - x_min)
    elif x <= x_q50:
        return 0.5 + 0.25 * (x - x_q25) / (x_q50 - x_q25)
    else:
        return 0.75 + 0.25 * (x - x_q50) / (x_max - x_q50)

df["OC_stretched"] = df["OC"].apply(piecewise_stretch_oc)

# HVAC and DHW formatting
df["HVAC"] = df["p:upgrade_hvac_system_choice"].fillna("Unknown")
df["DHW"] = df["p:upgrade_dhw_to_hpwh"].map({
    "Upgrade": "HPWH",
    "Baseline": "Gas DHW"
}).fillna("Unknown")

# Normalize material cost for alpha mapping
df["Capex_Tier"] = pd.qcut(df["Material"], q=3, labels=["Low", "Medium", "High"])
df["Capex_Alpha"] = df["Capex_Tier"].map({
    "Low": 0.98,  # Most visible
    "Medium": 0.65,
    "High": 0.4
})

# Seaborn theme
sns.set_theme(style="whitegrid", context="notebook", font_scale=1.1)

# Define HVAC palette
hvac_palette = {
    "Condensing Boiler": "#AF2E2E",
    "Mini-Split": "#018DDF",
    "Packaged HP": "#11C020",
    "Baseline": "#5A5A5A"
}

# HVAC legend
hvac_legend = [
    Line2D([0], [0], marker='o', color='w', label=hvac,
           markerfacecolor=color, markeredgecolor='black', markersize=10)
    for hvac, color in hvac_palette.items()
]

# DHW legend
dhw_legend = [
    Line2D([0], [0], marker='o', color='w', label='HPWH (Full Electric)',
           markerfacecolor='gray', markeredgecolor='black', markersize=10),
    Line2D([0], [0], marker='X', color='w', label='Gas DHW',
           markerfacecolor='gray', markeredgecolor='black', markersize=10)
]

# Capex alpha legend
capex_legend = [
    Line2D([0], [0], marker='o', color='black', label='Low', alpha=1.0, markersize=8),
    Line2D([0], [0], marker='o', color='black', label='Medium', alpha=0.7, markersize=8),
    Line2D([0], [0], marker='o', color='black', label='High', alpha=0.4, markersize=8)
]

# Begin plot
plt.figure(figsize=(10, 6))

# Background (non-Pareto)
sns.scatterplot(
    data=df[~df["pareto"]],
    x="OC_stretched", y="EC",
    color="lightgray", alpha=0.4
)

# Pareto configurations with Capex alpha
for alpha_level in df["Capex_Alpha"].unique():
    subset = df[(df["pareto"]) & (df["Capex_Alpha"] == alpha_level)]
    sns.scatterplot(
        data=subset,
        x="OC_stretched", y="EC",
        hue="HVAC", style="DHW",
        markers={"HPWH": "o", "Gas DHW": "X"},
        s=120,
        palette=hvac_palette,
        alpha=alpha_level,
        edgecolor="black",
        legend=False
    )

# Legend: grouped and manually formatted
plt.legend(
    handles=(
        [Line2D([], [], linestyle='none', label='HVAC')] + hvac_legend +
        [Line2D([], [], linestyle='none', label='DHW')] + dhw_legend +
        [Line2D([], [], linestyle='none', label='Upfront Cost')] + capex_legend
    ),
    loc="upper right", frameon=True, facecolor="white", framealpha=0.9
)

# Optional regime lines for OC (stretched)
for v in [0.5, 0.75]:
    plt.axvline(x=v, color="black", linestyle="--", linewidth=1)

plt.xlabel("Custom-Stretched Operational Carbon (kgCO₂)")
plt.ylabel("Embodied Carbon (kgCO₂)")
plt.title("Pareto Configurations by HVAC & DHW\nVisualizing OC vs. EC with Alpha-Based Cost Visibility")
plt.tight_layout()
plt.show()


# ----------------------------------------------------------------
# Upfront vs Long Term Cost Scatter Plot
# ----------------------------------------------------------------

# Alpha based on total carbon emissions (low carbon = more visible)
df["Carbon_Tier"] = pd.qcut(df["Total_Carbon"], q=3, labels=["Low", "Medium", "High"])
df["Carbon_Alpha"] = df["Carbon_Tier"].map({
    "Low": 0.98,     # Best performers = dark
    "Medium": 0.65,
    "High": 0.4      # High-carbon = faint
})

plt.figure(figsize=(10, 6))

# Plot non-Pareto configs
sns.scatterplot(
    data=df[~df["pareto"]],
    x="Material", y="Fine",
    color="lightgray", alpha=0.4
)

# Plot Pareto configs grouped by carbon-driven alpha
for alpha_level in df["Carbon_Alpha"].unique():
    subset = df[(df["pareto"]) & (df["Carbon_Alpha"] == alpha_level)]
    sns.scatterplot(
        data=subset,
        x="Material", y="Fine",
        hue="HVAC", style="DHW",
        markers={"HPWH": "o", "Gas DHW": "X"},
        palette=hvac_palette,
        alpha=alpha_level,
        s=120,
        edgecolor="black",
        legend=False
    )

# Legend remains unchanged and well formatted
plt.legend(
    handles=(
        [Line2D([], [], linestyle='none', label='HVAC')] + hvac_legend +
        [Line2D([], [], linestyle='none', label='DHW')] + dhw_legend +
        [Line2D([], [], linestyle='none', label='Total Carbon')] + [
            Line2D([0], [0], marker='o', color='black', label='Low', alpha=0.98, markersize=8),
            Line2D([0], [0], marker='o', color='black', label='Medium', alpha=0.7, markersize=8),
            Line2D([0], [0], marker='o', color='black', label='High', alpha=0.5, markersize=8)
        ]
    ),
    loc="upper right", frameon=True, facecolor="white", framealpha=0.9
)

# Axis labels and title
plt.xlabel("Upfront Material Cost ($)")
plt.ylabel("Long-Term BERDO Fine ($)")
plt.title("Pareto Configurations by HVAC & DHW\nAlpha-Scaled by Total Carbon Emissions")
plt.tight_layout()
plt.show()

import plotly.express as px

# Filter to Pareto configs only
df_plot = df[df["pareto"]].copy()

# Interactive scatter plot
fig = px.scatter(
    df_plot,
    x="Total_Carbon_stretched", y="Total_Cost",
    color="HVAC",
    symbol="DHW",
    hover_data=["run_id", "HVAC", "DHW", "Material", "Fine", "Total_Carbon"],
    title="Interactive: Total Cost vs. Custom-Stretched Total Carbon",
    labels={
        "Total_Carbon_stretched": "Stretched Total Carbon",
        "Total_Cost": "Total Cost ($)"
    },
    opacity=0.85
)

# Improve styling
fig.update_traces(marker=dict(size=10, line=dict(width=1, color='black')))

fig.update_layout(
    legend_title="HVAC System",
    width=950,
    height=600
)

fig.show()