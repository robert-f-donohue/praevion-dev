def is_valid_config(config: dict) -> bool:
    """
    Check if a given ECM configuration satisfies domain-specific constraints.

    Rules enforced:
    1. If either window U-value or SHGC is specified, both must be.
    2. Infiltration reduction options require corresponding envelope upgrades:
       - 0.75 requires wall R-10 or greater
       - 0.60 requires wall R-15 or greater and window upgrades
       - 0.40 requires wall R-20 or greater and window upgrades

    Parameters:
        config (dict): A dictionary of ECM options (e.g. from DeepHyper search).

    Returns:
        bool: True if the configuration is valid, False if it violates any constraints.
    """

    # Rule 1: If one of U-value or SHGC is upgraded, the other must be too
    u_value = config.get("upgrade_window_u_value", "None")
    shgc = config.get("upgrade_window_shgc", "None")
    if (u_value != "None" and shgc == "None") or (shgc != "None" and u_value == "None"):
        return False

    # Rule 2: Infiltration requires envelope support
    wall = config.get("upgrade_wall_insulation", "None")
    infiltration = config.get("adjust_infiltration_rates", "None")

    # Convert R-value string to number (e.g., "R-20" -> 20.0)
    def r_value_num(r_val):
        return float(r_val.split("-")[1]) if r_val.startswith("R") else 0.0

    wall_r = r_value_num(wall)

    if infiltration == "0.75":
        if wall_r < 10:
            return False
    if infiltration == "0.60":
        if wall_r < 15 or u_value == "None" or shgc == "None":
            return False
    if infiltration == "0.40":
        if wall_r < 20 or u_value == "None" or shgc == "None":
            return False

    return True
