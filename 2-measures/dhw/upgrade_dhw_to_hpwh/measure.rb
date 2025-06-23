# -----------------------------------------------------------------------------------------------
# UpgradeDHWToHPWH 
#
# Author:  Robert Donohue, enviENERGY Studio LLC
# Version: 0.1.0
# Date:    2025-06-14
# -----------------------------------------------------------------------------------------------

require 'openstudio-standards'

class UpgradeDHWToHPWH < OpenStudio::Measure::ModelMeasure

    def name
        return 'Upgrade DHW to HPWH'
    end

    def arguments(model)
        args = OpenStudio::Measure::OSArgumentVector.new

        # dropdown with options for whether or not to add a mini split ductless heat pump to the zones
        choices = OpenStudio::StringVector.new
        choices << 'Baseline'
        choices << 'Upgrade'

        # set your selection default to None
        upgrade_option = OpenStudio::Measure::OSArgument.makeChoiceArgument('dhw_hpwh_option', choices, true)
        upgrade_option.setDisplayName('Select DHW Upgrade Option')
        upgrade_option.setDefaultValue('Baseline') # Default to Baseline
        args << upgrade_option 

        # return argument vector
        return args
    end

    def run(model, runner, user_arguments)
        super(model, runner, user_arguments)

        # validate the user arguments
        return false unless runner.validateUserArguments(arguments(model), user_arguments)

        # get selected usage option
        upgrade_option  = runner.getStringArgumentValue('dhw_hpwh_option', user_arguments)

        # return early if None is selected
        if upgrade_option == 'Baseline'
            runner.registerInfo('No heat pump water heater added.')
            return true
        end

        # Load openstudio-standards and instantiate the Standard object
        require 'openstudio-standards'
        standard = Standard.build('NREL ZNE Ready 2017')

        # ---------------------------------------------------------------------
        # ----------------- Find and Remove Existing DHW Loop -----------------
        # ---------------------------------------------------------------------

        # find existing DHW loop
        dhw_loop = model.getPlantLoops.find { |loop| loop.name.to_s.include?('DHW') }
        unless dhw_loop
            runner.registerError('No existing DHW loop found.')
            return false
        end

        old_setpoint_schedule = nil

        dhw_loop.supplyComponents.each do |comp|
        if comp.to_WaterHeaterMixed.is_initialized
            wh = comp.to_WaterHeaterMixed.get
            if wh.setpointTemperatureSchedule.is_initialized
                old_setpoint_schedule = wh.setpointTemperatureSchedule.get
                runner.registerInfo("Captured setpoint schedule from WaterHeaterMixed.")
            end
            wh.remove
            runner.registerInfo("Removed WaterHeaterMixed.")
        elsif comp.to_WaterHeaterHeatPump.is_initialized
            wh_hp = comp.to_WaterHeaterHeatPump.get
            wh_hp.remove
            runner.registerInfo("Removed WaterHeaterHeatPump.")
        end
        end

        # ---------------------------------------------------------------------
        # ----------------- Configure New HPWH --------------------------------
        # ---------------------------------------------------------------------

        # Get inlet node
        inlet_node = dhw_loop.supplyInletNode

        # # Use the first thermal zone as placeholder (or ideally set based on where DHW tank is located)
        # zone = model.getThermalZones.first
        # unless zone
        #     runner.registerError("No thermal zones available in model.")
        #     return false
        # end

        # -------------------------------------------------------------------------
        # -------------------------------------------------------------------------

        # use corridor zone as placeholder and lower its setpoint to mitigate heating penalty
        corridor_zone = model.getThermalZones.find { |z| z.name.to_s.downcase.include?('corridor') }
        unless corridor_zone
            runner.registerError('No corridor zone found.')
            return false
        end

        low_heat_schedule = OpenStudio::Model::ScheduleRuleset.new(model)
        low_heat_schedule.defaultDaySchedule.addValue(OpenStudio::Time.new(0, 24, 0, 0), 15.6) # 60°F in °C

        # Create a high cooling setpoint schedule (85°F)
        high_cool_schedule = OpenStudio::Model::ScheduleRuleset.new(model)
        high_cool_schedule.defaultDaySchedule.addValue(OpenStudio::Time.new(0, 24, 0, 0), 23.0) # 72°F in °C

        thermostat = OpenStudio::Model::ThermostatSetpointDualSetpoint.new(model)
        thermostat.setHeatingSetpointTemperatureSchedule(low_heat_schedule)
        thermostat.setCoolingSetpointTemperatureSchedule(high_cool_schedule)
        corridor_zone.setThermostatSetpointDualSetpoint(thermostat)

        # -------------------------------------------------------------------------
        # -------------------------------------------------------------------------


        # HPWH specs
        type = 'WrappedCondenser'
        cap_kw = 40
        cop = 2.2
        backup_kw = 5
        volume_gal = 250.0
        sched = old_setpoint_schedule || OpenStudio::Model::ScheduleRuleset.new(model)

        hpwh = OpenstudioStandards::ServiceWaterHeating.create_heatpump_water_heater(
        model,
            heat_pump_type: type,
            water_heater_capacity: (cap_kw * 1000 / cop),
            electric_backup_capacity: (backup_kw * 1000),
            water_heater_volume: OpenStudio.convert(volume_gal, 'gal', 'm^3').get,
            service_water_temperature: OpenStudio.convert(125.0, 'F', 'C').get,
            on_cycle_parasitic_fuel_consumption_rate: 3.0,
            off_cycle_parasitic_fuel_consumption_rate: 3.0,
            service_water_temperature_schedule: sched,
            coefficient_of_performance: cop,
            set_peak_use_flowrate: false,
            peak_flowrate: 0.0,
            flowrate_schedule: nil,
            water_heater_thermal_zone: corridor_zone
        )

        if hpwh.nil?
            runner.registerError('Failed to create heat pump water heater.')
            return false
        end

        hpwh.tank.addToNode(inlet_node)
        runner.registerInfo("Added HPWH: #{hpwh.tank.name} to DHW loop: #{dhw_loop.name}")

        sim_control = model.getSimulationControl
        sim_control.setDoZoneSizingCalculation(true)
        sim_control.setDoSystemSizingCalculation(true)
        sim_control.setDoPlantSizingCalculation(true)
        sim_control.setRunSimulationforSizingPeriods(true)

        runner.registerFinalCondition("Installed heat pump water heater with #{volume_gal} gal tank and COP of #{cop}.")
        return true
    end

end
# register the measure to be used by the application
UpgradeDHWToHPWH.new.registerWithApplication