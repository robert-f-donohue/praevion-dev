# -----------------------------------------------------------------------------------------------
# UpgradeHVACPackagedHeatPump
#
# Author:  Robert Donohue, enviENERGY Studio LLC
# Version: 0.1.0
# Date:    2025-06-14
# -----------------------------------------------------------------------------------------------

class UpgradeHVACPackagedHeatPump < OpenStudio::Measure::ModelMeasure

    def name
        return 'Upgrade HVAC Packaged In-Unit Heat Pump'
    end

    def arguments(model)
        args = OpenStudio::Measure::OSArgumentVector.new

        # dropdown with options for whether or not to add a packaged heat pump to the zone
        choices = OpenStudio::StringVector.new
        choices << 'None'
        choices << 'Upgrade'

        # set your selection default to None
        pt_hp_option = OpenStudio::Measure::OSArgument.makeChoiceArgument('pt_hp_option', choices, true)
        pt_hp_option.setDisplayName('Select Packaged In-Unit Heat Pump Option')
        pt_hp_option.setDefaultValue('None')
        args << pt_hp_option 

        # return argument vector
        return args
    end

    def run(model, runner, user_arguments)
        super(model, runner, user_arguments)

        # validate the user arguments
        return false unless runner.validateUserArguments(arguments(model), user_arguments)

        # get selected usage option
        pt_hp_option  = runner.getStringArgumentValue('pt_hp_option', user_arguments)

        # return early if None is selected
        if pt_hp_option == 'None'
            runner.registerInfo('No packaged heat pump added.')
            return true
        end

        # DX cooling capacity as a function of EWB and OAT
        cool_cap_ft = OpenStudio::Model::CurveBiquadratic.new(model)
        cool_cap_ft.setName('DX-Cool-Cap-fEWB&OAT')
        cool_cap_ft.setCoefficient1Constant(0.87403017)
        cool_cap_ft.setCoefficient2x(-0.0011416)
        cool_cap_ft.setCoefficient3xPOW2(0.0001711)
        cool_cap_ft.setCoefficient4y(-0.002957)
        cool_cap_ft.setCoefficient5yPOW2(0.00001018)
        cool_cap_ft.setCoefficient6xTIMESY(-0.00005917)
        cool_cap_ft.setMinimumValueofx(19.4)    # EWB ~67 °F
        cool_cap_ft.setMaximumValueofx(23.9)    # EWB ~75 °F
        cool_cap_ft.setMinimumValueofy(21.1)    # OAT ~70 °F
        cool_cap_ft.setMaximumValueofy(40.6)    # OAT ~105 °F

        # DX Cooling EIR as a Function of EWB and OAT
        cool_eir_ft = OpenStudio::Model::CurveBiquadratic.new(model)
        cool_eir_ft.setName('DX-Cool-EIR-fEWB&OAT')
        cool_eir_ft.setCoefficient1Constant(0.9)
        cool_eir_ft.setCoefficient2x(0.005)
        cool_eir_ft.setCoefficient3xPOW2(-0.00005)
        cool_eir_ft.setCoefficient4y(0.002)
        cool_eir_ft.setCoefficient5yPOW2(0.00002)
        cool_eir_ft.setCoefficient6xTIMESY(-0.0001)
        cool_eir_ft.setMinimumValueofx(17.0)
        cool_eir_ft.setMaximumValueofx(25.0)
        cool_eir_ft.setMinimumValueofy(25.0)
        cool_eir_ft.setMaximumValueofy(40.0)

        # Cooling EIR as a function of PLR
        cool_plr = OpenStudio::Model::CurveCubic.new(model)
        cool_plr.setName('DX-Cool-EIR-fPLR')
        cool_plr.setCoefficient1Constant(0.20123008)
        cool_plr.setCoefficient2x(-0.0312175)
        cool_plr.setCoefficient3xPOW2(1.95049798)
        cool_plr.setCoefficient4xPOW3(-1.12051034)

        # Heating Capacity as a Function of EDB and OAT
        heat_cap_ft = OpenStudio::Model::CurveBiquadratic.new(model)
        heat_cap_ft.setName('MiniSplit-Heat-Cap-fT')
        heat_cap_ft.setCoefficient1Constant(0.70)
        heat_cap_ft.setCoefficient2x(0.0)
        heat_cap_ft.setCoefficient3xPOW2(0.0)
        heat_cap_ft.setCoefficient4y(0.025)
        heat_cap_ft.setCoefficient5yPOW2(-0.0001)
        heat_cap_ft.setCoefficient6xTIMESY(0.0)
        heat_cap_ft.setMinimumValueofx(15.6)   # Indoor temp
        heat_cap_ft.setMaximumValueofx(23.9)
        heat_cap_ft.setMinimumValueofy(-8.3)   # Outdoor temp
        heat_cap_ft.setMaximumValueofy(8.3)

        # Heating EIR as a Function of EDB and OAT
        heat_eir_ft = OpenStudio::Model::CurveBiquadratic.new(model)
        heat_eir_ft.setName('MiniSplit-Heat-EIR-fT')
        heat_eir_ft.setCoefficient1Constant(0.70)         # baseline EIR
        heat_eir_ft.setCoefficient2x(0.0)
        heat_eir_ft.setCoefficient3xPOW2(0.0)
        heat_eir_ft.setCoefficient4y(-0.040)              # linear decrease w/ OAT
        heat_eir_ft.setCoefficient5yPOW2(0.0010)           # quadratic curve for realism
        heat_eir_ft.setCoefficient6xTIMESY(0.0)
        heat_eir_ft.setMinimumValueofx(15.6)               # Indoor temp (EDB) range
        heat_eir_ft.setMaximumValueofx(23.9)
        heat_eir_ft.setMinimumValueofy(-8.3)               # Outdoor air temp (OAT)
        heat_eir_ft.setMaximumValueofy(8.3)

        # Heating EIR as a function of PLR
        heat_plr = OpenStudio::Model::CurveCubic.new(model)
        heat_plr.setName('PVVT-Heat-EIR-fPLR')
        heat_plr.setCoefficient1Constant(0.08565216)
        heat_plr.setCoefficient2x(0.93881381)
        heat_plr.setCoefficient3xPOW2(-0.18343613)
        heat_plr.setCoefficient4xPOW3(0.15897022)

        # set up zone counter
        zones_modified = 0

        # loop through all thermal zones
        model.getThermalZones.each do |zone|
            next if zone.spaces.empty?

            # remove existing HVAC equipment
            zone.equipment.each(&:remove)

            # create autosized fan
            fan = OpenStudio::Model::FanOnOff.new(model)
            fan.setName("Fan - #{zone.name}")
            # set airflow rates
            fan.setMaximumFlowRate(0.142)  # ~ 300 cfm per zone
            # set fan power (~0.4 W/cfm)
            fan.setMotorEfficiency(0.9)
            fan.setFanEfficiency(0.6)
            fan.setPressureRise(400.0)  # Pa

            # create cooling coil and set performance curves
            cooling_coil = OpenStudio::Model::CoilCoolingDXSingleSpeed.new(model)
            cooling_coil.setName("Cooling Coil - #{zone.name}")
            cooling_coil.setTotalCoolingCapacityFunctionOfTemperatureCurve(cool_cap_ft)
            cooling_coil.setEnergyInputRatioFunctionOfTemperatureCurve(cool_eir_ft)
            cooling_coil.setEnergyInputRatioFunctionOfFlowFractionCurve(cool_plr)
            cooling_coil.setRatedCOP(3.645) # SEER2 13.65

            # create heating coil and set performance curves
            heating_coil = OpenStudio::Model::CoilHeatingDXSingleSpeed.new(model)
            heating_coil.setName("Heating Coil - #{zone.name}")
            heating_coil.setTotalHeatingCapacityFunctionofTemperatureCurve(heat_cap_ft)
            heating_coil.setEnergyInputRatioFunctionofTemperatureCurve(heat_eir_ft)
            heating_coil.setEnergyInputRatioFunctionofFlowFractionCurve(heat_plr)
            heating_coil.setRatedCOP(2.445) # HSPF2 7.1

            # add supplemental heating coil
            supplemental_heating_coil = OpenStudio::Model::CoilHeatingElectric.new(model)
            supplemental_heating_coil.setName("Supplemental Heating Coil - #{zone.name}")

            # create an always-on availability schedule
            availability_schedule = OpenStudio::Model::ScheduleConstant.new(model)
            availability_schedule.setName("Availability Schedule - #{zone.name}")
            availability_schedule.setValue(1.0)

            # create a new packaged heat pump
            pt_hp = OpenStudio::Model::ZoneHVACPackagedTerminalHeatPump.new(
                model,
                availability_schedule,
                fan,
                heating_coil,
                cooling_coil,
                supplemental_heating_coil
            )
            pt_hp.setName("Packaged Heat Pump - #{zone.name}")

            # add the heat pump to the zone
            pt_hp.addToThermalZone(zone)

            # increment the zone counter
            zones_modified += 1
        end

        runner.registerFinalCondition("Installed packaged heat pumps in #{zones_modified} thermal zones.")

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
UpgradeHVACPackagedHeatPump.new.registerWithApplication