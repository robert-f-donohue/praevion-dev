import os
import json
import ConfigSpace as cs
from deephyper.hpo import HpProblem

# Resolve the absolute path to the ECM options JSON file
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ecm_options_path = os.path.join(project_root, "3-ecm_definitions", "ecm_options_complex.json")

# Load the ECM search space from the JSON file
with open(ecm_options_path, "r") as f:
    ecm_options = json.load(f)

# Instantiate the search problem
problem = HpProblem()

# Define each of the hyperparameters
wall_hp = problem.add_hyperparameter(
    value=["R-7.5", "R-10", "R-15", "R-20", "R-25"], name="upgrade_wall_insulation"
)
roof_hp = problem.add_hyperparameter(
    value=["R-15", "R-20", "R-30", "R-40"], name="upgrade_roof_insulation"
)
window_u_value_hp = problem.add_hyperparameter(
    value=["None", "0.32", "0.28", "0.22", "0.18"], name="upgrade_window_u_value"
)
window_shgc_value_hp = problem.add_hyperparameter(
    value=["None", "0.25", "0.35", "0.40"], name="upgrade_window_shgc"
)
inf_rate_hp = problem.add_hyperparameter(
    value=["1.00","0.90", "0.80", "0.75", "0.70"], name="adjust_infiltration_rates"
)
hvac_hp = problem.add_hyperparameter(
    value=["Baseline", "Condensing Boiler","Mini-Split", "Packaged HP"], name="upgrade_hvac_system_choice"
)
dhw_hp = problem.add_hyperparameter(
    value=["Baseline", "Upgrade"], name="upgrade_dhw_to_hpwh"
)

# Condition 1: U-value & SHGC Pairing
window_condition_1 = cs.InCondition(
    child=window_shgc_value_hp, parent=window_u_value_hp, values=["0.32", "0.28", "0.22", "0.18"]
)
window_condition_2 = cs.InCondition(
    child=window_u_value_hp, parent=window_shgc_value_hp, values=["0.25", "0.35", "0.40"]
)
problem.add_conditions([window_condition_1, window_condition_2])

# Condition 2: Infiltration Rate = 0.40
forbidden_clause_wall_1 = cs.ForbiddenAndConjunction(
    cs.ForbiddenEqualsClause(inf_rate_hp, "0.40"),
    cs.ForbiddenInClause(wall_hp, ["R-7.5", "R-10", "R-15", "R-20"])
)
forbidden_clause_window_1 = cs.ForbiddenAndConjunction(
    cs.ForbiddenEqualsClause(inf_rate_hp, "0.40"),
    cs.ForbiddenEqualsClause(window_u_value_hp, "None")
)
problem.add_forbidden_clause(forbidden_clause_wall_1)
problem.add_forbidden_clause(forbidden_clause_window_1)

# Condition 3: Infiltration Rate = 0.60
forbidden_clause_wall_2 = cs.ForbiddenAndConjunction(
    cs.ForbiddenEqualsClause(inf_rate_hp, "0.60"),
    cs.ForbiddenInClause(wall_hp, ["R-7.5", "R-10"])
)
forbidden_clause_window_2 = cs.ForbiddenAndConjunction(
    cs.ForbiddenEqualsClause(inf_rate_hp, "0.60"),
    cs.ForbiddenEqualsClause(window_u_value_hp, "None")
)
problem.add_forbidden_clause(forbidden_clause_wall_2)
problem.add_forbidden_clause(forbidden_clause_window_2)

# Condition 4: Infiltration Rate = 0.75
forbidden_clause_wall_3 = cs.ForbiddenAndConjunction(
    cs.ForbiddenEqualsClause(inf_rate_hp, "0.75"),
    cs.ForbiddenInClause(wall_hp, ["R-7.5", "R-10"])
)
problem.add_forbidden_clause(forbidden_clause_wall_3)

# Initialize the MOO with 4 variables
problem.num_objectives = 4

# Print the search space if run as a script (for debugging or CLI use)
if __name__ == "__main__":
    print(problem)