import pandas as pd

def calculate_material_cost_from_df(selections, surface_areas, total_floor_area, apartment_floor_area, apartment_count, df_material):
    """
    Calculates total material cost (USD) using ECM selection data, surface areas,
    apartment count, and a DataFrame of embodied carbon intensities by measure.

    Parameters:
        selections (dict): Keys like 'measure.argument', values like 'R-10' or 'Upgrade'
        surface_areas (dict): wall_area_m2, roof_area_m2, window_area_m2
        total_floor_area (int): total floor area of all residential and non-residential areas
        apartment_floor_area (int): total floor area of apartment units
        apartment_count (int): number of apartments in the model
        df_material (pd.DataFrame): loaded material cost data with measure_name, argument_value, $/unit, etc.

    Returns:
        dict: kg CO2e by component and total
    """

    # Initialize embodied carbon result dictionary
    result = {
        "wall_mat_cost": 0.0,
        "roof_mat_cost": 0.0,
        "window_mat_cost": 0.0,
        "hvac_mat_cost": 0.0,
        "erv_mat_cost": 0.0,
        "dhw_mat_cost": 0.0,
        "other_mat_cost": 0.0,
        "total_mat_cost": 0.0
    }

    # Measures with no EC impact
    skip_measures = {"upgrade_window_shgc"}

    # Loop through each selected ECM from the workflow (.osw)
    for key, selected_value in selections.items():
        measure, _ = key.split(".")
        measure = measure.lower()  # Normalize casing for match

        # Skip non-embodied carbon measures
        if measure in skip_measures:
            continue

        # Normalize values for comparison
        def normalize_val(val):
            try:
                return str(float(val))
            except (ValueError, TypeError):
                return str(val).strip().lower()

        matched_rows = df_material[
            (df_material["measure_name"].str.strip().str.lower() == measure.strip().lower()) &
            (df_material["argument_value"].apply(normalize_val) == normalize_val(selected_value))
        ]

        if matched_rows.empty:
            if normalize_val(selected_value) in {
                "baseline", "r-7.5", "r-15", "1.00", "condensing boiler"
            }:
                continue  # Silently skip baseline
            print(f"[WARNING] No cost match found for: measure_id='{measure}', option_id='{selected_value}'")
            continue

        # Handle all rows (in case more than one entry exists for same measure/option)
        for _, row in matched_rows.iterrows():
            unit_cost = row["Cost ($/unit)"]
            unit_type = row["unit_mapping"]

            # Decide how to normalize the unit_cost value
            if unit_type == "wall_area":
                quantity = surface_areas.get("wall_area_m2", 0)
            elif unit_type == "roof_area":
                quantity = surface_areas.get("roof_area_m2", 0)
            elif unit_type == "window_area":
                quantity = surface_areas.get("window_area_m2", 0)
            elif unit_type == "total_floor_area":
                quantity = total_floor_area
            elif unit_type == "apartment_floor_area":
                quantity = apartment_floor_area
            elif unit_type == "per_unit":
                quantity = apartment_count
            else:
                # Default to 1 if no matching unit type is found (e.g., per building)
                quantity = 1

            # If insulation, apply thickness scaling (e.g., 1.2 kg CO2e per inch x 6 inches
            thickness = row.get("insulation_thickness", 1)
            if pd.notna(thickness):
                unit_cost *= thickness

            # Calculate subtotal embodied carbon for this line item
            subtotal = unit_cost * quantity

            # Categorize the subtotal based on the type of measure
            if 'wall' in measure:
                result['wall_mat_cost'] += subtotal
            elif 'roof' in measure:
                result['roof_mat_cost'] += subtotal
            elif 'window' in measure:
                result['window_mat_cost'] += subtotal
            elif 'hvac' in measure:
                result['hvac_mat_cost'] += subtotal
            elif 'erv' in measure:
                result['erv_mat_cost'] += subtotal
            elif 'dhw' in measure:
                result['dhw_mat_cost'] += subtotal
            else:
                result['other_mat_cost'] += subtotal

    # Sum all categories into the total
    result["material_cost_usd"] = sum([
        result["wall_mat_cost"],
        result["roof_mat_cost"],
        result["window_mat_cost"],
        result["erv_mat_cost"],
        result["hvac_mat_cost"],
        result["dhw_mat_cost"],
        result["other_mat_cost"]
    ])

    return result