# -----------------------------------------------------------------------------------------------
# AddInUnitERV
#
# Author:  Robert Donohue, enviENERGY Studio LLC
# Version: 0.1.0
# Date:    2025-06-13
# -----------------------------------------------------------------------------------------------

class AddInUnitERV < OpenStudio::Measure::ModelMeasure

    def name
        return 'Add In Unit ERV'
    end

    def arguments(model)
        args = OpenStudio::Measure::OSArgumentVector.new

        # dropdown with options for whether or not to add an ERV
        choices = OpenStudio::StringVector.new
        choices << 'No ERV'  # default option
        choices << 'Add ERV'

        # set your selection default to None
        erv_option = OpenStudio::Measure::OSArgument.makeChoiceArgument('erv_option', choices, true)
        erv_option.setDisplayName('Select ERV Option')
        erv_option.setDefaultValue('No ERV')
        args << erv_option 

        # return argument vector
        return args
    end

    def run(model, runner, user_arguments)
        super(model, runner, user_arguments)

        # validate the user arguments
        return false unless runner.validateUserArguments(arguments(model), user_arguments)

        # get selected ERV option
        erv_option  = runner.getStringArgumentValue('erv_option', user_arguments)

        if erv_option.empty?
            runner.registerError("ERV option not provided or unrecognized.")
            return false
        end

        # return early if None is selected
        if erv_option == 'No ERV'
            runner.registerInfo('No ERVs added.')
            return true
        end

        # DEBUG:
        runner.registerInfo("=== STARTING AddInUnitERV MEASURE ===")

        # set an always-on schedule for the ERV
        always_on = model.alwaysOnDiscreteSchedule
        erv_count = 0

        # airflow in m³/s (75 CFM)
        erv_flow = OpenStudio.convert(75, 'cfm', 'm^3/s').get

        # ERV fan configuration
        fan_efficiency = 0.5
        target_power_watts = 75 * 0.5   # 0.5 W/CFM per fan
        pressure_rise = target_power_watts * fan_efficiency / erv_flow  # ~535.7 Pa

        # add ERV to each apartment zone
        model.getThermalZones.each do |zone|
            # check if the zone already has an ERV
            next unless zone.name.get.downcase.include?('apartment')
            next if zone.equipment.any? { |eq| eq.to_ZoneHVACEnergyRecoveryVentilator.is_initialized }

            # create supply and exhaust fans
            supply_fan = OpenStudio::Model::FanConstantVolume.new(model)
            supply_fan.setName("ERV Supply Fan - #{zone.nameString}")
            supply_fan.setFanEfficiency(fan_efficiency)
            supply_fan.setPressureRise(pressure_rise)
            supply_fan.setAvailabilitySchedule(always_on)

            exhaust_fan = OpenStudio::Model::FanConstantVolume.new(model)
            exhaust_fan.setName("ERV Exhaust Fan - #{zone.nameString}")
            exhaust_fan.setFanEfficiency(fan_efficiency)
            exhaust_fan.setPressureRise(pressure_rise)
            exhaust_fan.setAvailabilitySchedule(always_on)

            # create a new ERV
            erv = OpenStudio::Model::ZoneHVACEnergyRecoveryVentilator.new(model)
            erv.setName("ERV - #{zone.nameString}")
            erv.setAvailabilitySchedule(always_on)
            # set ERV flow rates
            erv.setSupplyAirFlowRate(erv_flow)
            erv.setExhaustAirFlowRate(erv_flow)

            # create a heat exchanger
            hx = OpenStudio::Model::HeatExchangerAirToAirSensibleAndLatent.new(model)
            hx.setSensibleEffectivenessat100HeatingAirFlow(0.75)
            hx.setSensibleEffectivenessat100CoolingAirFlow(0.75)
            hx.setLatentEffectivenessat100HeatingAirFlow(0.50)
            hx.setLatentEffectivenessat100CoolingAirFlow(0.50)
            # add the heat exchanger to the ERV
            erv.setHeatExchanger(hx)

            # add the ERV to the thermal zone
            erv.addToThermalZone(zone)

            #  increment the ERV count
            erv_count += 1
        end

        # check if any ERVs were added
        if erv_count == 0
            runner.registerAsNotApplicable('No apartment zones found or ERVs already present.')
        else
            runner.registerInfo("Installed #{erv_count} in-unit ERV(s) at 75 CFM each with total fan power of 1 W/CFM.")
        end

        # set the simulation control to run sizing calculations
        sim_control = model.getSimulationControl
        sim_control.setDoZoneSizingCalculation(true)
        sim_control.setDoSystemSizingCalculation(true)
        sim_control.setDoPlantSizingCalculation(true)
        sim_control.setRunSimulationforSizingPeriods(true)

        return true
    end

end
# register the measure to be used by the application
AddInUnitERV.new.registerWithApplication