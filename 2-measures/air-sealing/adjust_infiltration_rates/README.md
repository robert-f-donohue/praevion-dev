# Adjust Infiltration Rates

This measure modifies infiltration rates for perimeter thermal zones to reflect improved air sealing measures in existing multifamily buildings.

## Inputs
- Choice argument: `'None'`, `'0.80'`, `''0.60'`, `''0.40'`

## Behavior
- Applies a reduced infiltration flow rate per exterior surface area to perimeter zones only.
- Core zones are excluded to better match retrofit implementation patterns.

## Notes
- Infiltration schedules and stack effects are not currently modified.
- Future versions may accept numeric input or import blower door results