# Upgrade HVAC Mini Split

This measure replaces existing HVAC systems in each thermal zone with ductless mini-split heat pumps, modeled using packaged terminal heat pump (PTHP) objects for simplicity.

## Inputs
- Choice argument: `'None'` or `'Upgrade'`

## Behavior
- Replaces existing zone HVAC equipment with a `ZoneHVACPackagedTerminalHeatPump`.
- COPs are derived from Daikin Oterra SEER2/HSPF2 values: 5.667 (cooling), 3.516 (heating).
- Includes detailed performance curves for temperature and part-load behavior.

## Notes
- Performance curves are based on eQuest PVVT and DX curve templates.
- Future updates may replace generic curves with manufacturer-specific data.