# Upgrade HVAC Packaged Heat Pump

This measure installs lower-efficiency packaged in-unit heat pumps across all thermal zones, modeled using a `ZoneHVACPackagedTerminalHeatPump` object.

## Inputs
- Choice argument: `'None'` or `'Upgrade Packaged In-Unit Heat Pump'`

## Behavior
- Replaces existing HVAC equipment with a PTHP object.
- Applies COPs derived from SEER2 13.65 and HSPF2 7.1: Cooling COP = 3.645, Heating COP = 2.445.
- Performance curves are not included in this version.

## Notes
- This baseline upgrade is intended to reflect less efficient packaged heat pump systems.
- Future iterations will add seasonal performance curves for realism.