# Upgrade Window SHGC

This measure adjusts the solar heat gain coefficient (SHGC) of existing exterior windows.

## Inputs
- Choice argument: `'None'`, `'0.4'`, `'0.35'`, `'0.25'`

## Behavior
- Creates a new `SimpleGlazing` object with the selected SHGC.
- Duplicates and reassigns existing window constructions while preserving U-value.

## Notes
- This measure intentionally separates SHGC and U-value changes to avoid overwriting previous modifications in optimization workflows.