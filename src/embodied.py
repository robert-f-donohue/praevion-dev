import pandas as pd

def calculate_embodied_carbon_from_df(selections, surface_areas, apartment_floor_area, apartment_count, df_ec):
    """
    Calculates total embodied carbon (kg CO2e) using ECM selection data, surface areas,
    apartment count, and a DataFrame of embodied carbon intensities by measure.

    Parameters:
        selections (dict): Keys like 'measure.argument', values like 'R-10' or 'Upgrade'
        surface_areas (dict): wall_area_m2, roof_area_m2, window_area_m2
        apartment_floor_area (int): total floor area of apartment units
        apartment_count (int): number of apartments in the model
        df_ec (pd.DataFrame): loaded EC data with measure_name, argument_value, GWP, etc.

    Returns:
        dict: kg CO2e by component and total
    """

    # Initialize embodied carbon result dictionary
    result = {
        "wall_ec_kg": 0.0,
        "roof_ec_kg": 0.0,
        "window_ec_kg": 0.0,
        "hvac_ec_kg": 0.0,
        "erv_ec_kg": 0.0,
        "dhw_ec_kg": 0.0,
        "other_ec_kg": 0.0,
        "total_ec_kg": 0.0
    }

    # Measures with no EC impact
    skip_measures = {"upgrade_window_shgc"}

    # Loop through each selected ECM from the workflow (.osw)
    for key, selected_value in selections.items():
        measure, _ = key.split('.')
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

        matched_rows = df_ec[
            (df_ec['measure_name'].str.strip().str.lower() == measure.strip().lower()) &
            (df_ec['argument_value'].apply(normalize_val) == normalize_val(selected_value))
        ]

        # If no match is found, skip to next selection
        if matched_rows.empty:
            print(f"[WARNING] No EC match found for: measure_id='{measure}', option_id='{selected_value}'")
            continue

        # Handle all rows (in case more than one entry exists for same measure/option)
        for _, row in matched_rows.iterrows():
            gwp = row['GWP (kg per unit)']
            unit_type = row['unit_mapping']

            # Decide how to normalize the GWP value
            if unit_type == "wall_area":
                quantity = surface_areas.get("wall_area_m2", 0)
            elif unit_type == "roof_area":
                quantity = surface_areas.get("roof_area_m2", 0)
            elif unit_type == "window_area":
                quantity = surface_areas.get("window_area_m2", 0)
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
                gwp *= thickness

            # Calculate subtotal embodied carbon for this line item
            subtotal = gwp * quantity

            # Categorize the subtotal based on the type of measure
            if 'wall' in measure:
                result['wall_ec_kg'] += subtotal
            elif 'roof' in measure:
                result['roof_ec_kg'] += subtotal
            elif 'window' in measure:
                result['window_ec_kg'] += subtotal
            elif 'hvac' in measure:
                result['hvac_ec_kg'] += subtotal
            elif 'erv' in measure:
                result['erv_ec_kg'] += subtotal
            elif 'dhw' in measure:
                result['dhw_ec_kg'] += subtotal
            else:
                result['other_ec_kg'] += subtotal

    # Sum all categories into the total
    result["total_ec_kg"] = sum([
        result["wall_ec_kg"],
        result["roof_ec_kg"],
        result["window_ec_kg"],
        result["hvac_ec_kg"],
        result["dhw_ec_kg"],
        result["other_ec_kg"]
    ])

    return result
