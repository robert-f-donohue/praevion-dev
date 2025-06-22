import json

def extract_measure_selections(osw_path):
    '''
    Parses an OpenStudio Workflow (.osw) file to extract selected arguments for each measure.
    Returns a dictionary mapping measure.argument to the selected value.

    This is used to determine which ECMs were applied in the simulation and
    to feed into embodied carbon calculations for each measure.

    Parameters:
        osw_path (str): Path to the .osw workflow file

    Returns:
        dict: {
            "measure_name.argument_name": value (str)
        }
    '''

    # STEP 1: Read workflow file (.osw)
    with open(osw_path, 'r') as f:
        osw = json.load(f)

    # STEP 2: Get dictionary of measure arguments (ECMs)
    selections = {}
    # iterate over each measure in the workflow file
    for step in osw.get('steps', []):
        # get the measure name
        measure = step['measure_dir_name']
        # get the name of the argument parameter
        args = step.get('arguments', {})

        # parse the value associated with the measure and argument
        for key, val in args.items():
            selections[f"{measure}.{key}"] = val

    return selections