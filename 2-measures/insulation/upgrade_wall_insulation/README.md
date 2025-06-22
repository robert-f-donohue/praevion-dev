# Upgrade Wall Insulation

This measure upgrades above-grade exterior walls by assigning new constructions with increased insulation.

## Inputs
- Choice argument: `'None'`, `'R-10'`, `'R-15'`, `'R-20'`, `'R-25'`

## Behavior
- Applies a `SimpleMassless` material to wall constructions representing selected R-value.
- Targets all `Wall` surface types with `Outdoors` boundary condition.

## Notes
- Does not distinguish between façade orientations or window-to-wall ratios.
- Additional refinement could include selecting assemblies from material libraries.