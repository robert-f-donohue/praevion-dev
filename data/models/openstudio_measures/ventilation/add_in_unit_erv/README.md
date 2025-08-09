# Add In-Unit ERV

Adds in-unit Energy Recovery Ventilators (ERVs) to each apartment zone in the model to comply with ventilation code requirements and improve indoor air quality.

## Inputs
- Choice argument: `'None'` or `'Add ERV'`

## Behavior
- Adds a `ZoneHVACEnergyRecoveryVentilator` to all thermal zones containing the word "apartment" in their name.
- Sets outdoor air supply airflow to **75 CFM** (per IMC 2021 ventilation requirements).
- Assigns **two constant volume fans** (supply and exhaust) to each ERV.
- Each fan is configured to operate at **0.5 W/CFM**, totaling **1 W/CFM** fan power per ERV.
- Fan parameters (efficiency = 0.5, pressure rise ≈ 535 Pa) are calculated to match the intended power draw.
- Sensible and latent effectiveness values are hardcoded:
  - Sensible: 0.75
  - Latent: 0.50
- Fans are set to run on an always-on schedule, assuming 24/7 ventilation.

## Notes
- Only zones with `"apartment"` in their name are considered.
- This implementation assumes simple in-unit ERVs with no central ventilation distribution.
- Future improvements may include CO₂ control or dynamic scheduling.
