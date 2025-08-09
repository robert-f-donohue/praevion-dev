# Upgrade Window U-Value

This measure replaces the window glazing material in exterior window constructions with one that meets a target U-value.

## Inputs
- Choice argument: `'None'`, `'0.32'`, `'0.28'`, `'0.22'`, `'0.18'`

## Behavior
- Creates a `SimpleGlazing` object with specified U-value and a fixed SHGC of 0.35.
- Assigns a new construction using this glazing material to all windows in the model.

## Notes
- U-value and SHGC upgrades are decoupled across separate measures for compatibility with multi-objective optimization.
