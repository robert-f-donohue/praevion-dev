import io
import pandas as pd

def extract_named_table(filepath, start_marker, end_marker):
    """
    Extracts a tabular section from a messy EnergyPlus CSV report.

    Parameters:
        filepath (str): Path to the .csv file
        start_marker (str): Line of text that signals the start of the table
        end_marker (str): Line of text that signals the end of the table

    Returns:
        pd.DataFrame: DataFrame parsed from that section
    """

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Find start and end of desired table
    start = None
    end = None
    for i, line in enumerate(lines):
        if start is None and start_marker.lower() in line.lower():
            start = i
        elif start is not None and end_marker.lower() in line.lower():
            end = i
            break

    if start is None or end is None:
        raise ValueError(f"Could not locate section: {start_marker} to {end_marker}")

    # Extract and join into a CSV-compatible string
    section_lines = lines[start + 1:end]
    section_lines = [l for l in section_lines if l.strip() != ""]

    csv_content = "".join(section_lines)
    return pd.read_csv(io.StringIO(csv_content), header=None)

def clean_table_with_headers(df_raw):
    """
    Cleans and standardizes a raw table extracted from an EnergyPlus CSV output.

    This function is used when EnergyPlus tables (e.g., eplustbl.csv) are read without
    proper headers or include messy formatting. It performs the following steps:
    - Removes the first column if it's entirely null (common in many EnergyPlus tables).
    - Uses the first row as the column header.
    - Replaces the first column name with "Zone" if it's blank or contains "nan".
    - Strips leading/trailing whitespace from all header strings.
    - Drops the original header row from the data.

    Parameters:
        df_raw (pd.DataFrame): A raw DataFrame extracted from an EnergyPlus table.

    Returns:
        pd.DataFrame: A cleaned DataFrame with proper headers and ready for analysis.
    """
    # Drop all-null leading column (seen in most tables)
    if df_raw.shape[1] > 1 and df_raw.iloc[:, 0].isnull().all():
        df_raw = df_raw.iloc[:, 1:]

    # Pull header row and strip whitespace
    new_header = df_raw.iloc[0].astype(str).str.strip().tolist()

    # Replace first column name if blank or nan
    if not new_header[0] or new_header[0].lower() in ("nan", ""):
        new_header[0] = "Zone"

    # Apply new headers and remove original header row
    df_cleaned = df_raw[1:].copy()
    df_cleaned.columns = new_header
    df_cleaned = df_cleaned.reset_index(drop=True)

    return df_cleaned
