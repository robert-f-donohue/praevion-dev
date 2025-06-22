# UpgradeDHWtoHPWH

This OpenStudio Measure replaces a central gas water heater (`WaterHeaterMixed`) with a central all-electric heat pump water heater (`WaterHeaterHeatPump`) connected to a stratified tank (`WaterHeaterStratified`). This measure is intended to support all-electric retrofit scenarios for domestic hot water systems in multifamily buildings.

## Purpose

The goal of this measure is to decarbonize the domestic hot water (DHW) system by removing fossil fuel-based heating and replacing it with an efficient heat pump water heater. This enables building-wide electrification and supports emissions reduction targets.

## Key Features

- Removes the existing `WaterHeaterMixed` from the DHW loop.
- Adds a stratified tank with a 250-gallon capacity (~0.95 m³).
- Adds a heat pump water heater unit and links it to the new stratified tank.
- Sets the rated COP of the system's DX coil to 2.0 as a conservative estimate.

## Notes

- **Performance curves for the heat pump water heater are not included** in this measure. Default OpenStudio behavior is used for seasonal variation. Custom curves for temperature-dependent performance are planned for future implementation.
- The original DHW loop's setpoint temperature schedule is preserved and applied to the new system.

## Intended Use

This measure is suitable for parametric studies, electrification scenarios, and optimization workflows evaluating carbon-reduction retrofit strategies.

## Tags

`DHW`, `Electrification`, `Retrofit`, `Heat Pump`, `Multifamily`, `All-Electric Ready`