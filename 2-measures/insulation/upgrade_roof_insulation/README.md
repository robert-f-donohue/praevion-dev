# Upgrade Roof Insulation

This measure replaces the existing roof construction with an assembly representing improved insulation levels.

## Inputs
- Choice argument: `'None'`, `'R-20'`, `'R-30'`, `'R-40'`

## Behavior
- Creates a `Construction` object with a single `SimpleMassless` material representing the target R-value.
- Applies the new construction to all surfaces with `surfaceType = RoofCeiling` and `outsideBoundaryCondition = Outdoors`.

## Notes
- The measure does not currently account for layered assemblies or radiant barriers.
- Intended as a simplified prototype input for energy optimization workflows.