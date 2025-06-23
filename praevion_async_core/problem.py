import os
import json
from deephyper.hpo import HpProblem


# Resolve the absolute path to the ECM options JSON file
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ecm_options_path = os.path.join(project_root, "3-ecm_definitions", "ecm_options.json")

# Load the ECM search space from the JSON file
with open(ecm_options_path, "r") as f:
    ecm_options = json.load(f)

# Instantiate the search problem
problem = HpProblem()

# Add each ECM upgrade measure as a categorical hyperparameter
for measure, data in ecm_options.items():
    options = data["options"]
    problem.add_hyperparameter(options, measure)

# Initialize the MOO with 3 variables
problem.num_objectives = 3

# Print the search space if run as a script (for debugging or CLI use)
if __name__ == "__main__":
    print(problem)