# -----------------------------------------------------------------------------------------------
# UpgradeHVACSystemChoice
#
# Author:  Robert Donohue, enviENERGY Studio LLC
# Version: 0.2.0
# Date:    2025-06-22
# -----------------------------------------------------------------------------------------------

class UpgradeHVACSystemChoice < OpenStudio::Measure::ModelMeasure

    def name
        return 'Upgrade HVAC System Choice'
    end

    def arguments(model)
        args = OpenStudio::Measure::OSArgumentVector.new

        # dropdown with options for whether or not to add a packaged heat pump to the zone
        choices = OpenStudio::StringVector.new
        choices << 'Baseline'          # Baseline - radiant heating, window AC
        choices << 'Condensing Boiler' # Condensing Boiler with Radiant Heating
        choices << 'Mini-Split'        # Mini-Split Ductless Heat Pump
        choices << 'Packaged HP'       # Packaged Terminal Heat Pump

        # set your selection default to None
        hvac_option = OpenStudio::Measure::OSArgument.makeChoiceArgument('hvac_option', choices, true)
        hvac_option.setDisplayName('Select HVAC System Option')
        hvac_option.setDefaultValue('Baseline')
        args << hvac_option 

        # return argument vector
        return args
    end

    def run(model, runner, user_arguments)
        super(model, runner, user_arguments)
        return false unless runner.validateUserArguments(arguments(model), user_arguments)

        hvac_option  = runner.getStringArgumentValue('hvac_option', user_arguments)
        return runner.registerInfo('No updated HVAC system selected.') && true if hvac_option == 'Baseline'

        # Update the boiler efficiency if Condensing Boiler is selected
        if hvac_option == 'Condensing Boiler'
            boilers = model.getBoilerHotWaters

            if boilers.empty?
                runner.registerInfo('No BoilerHotWater objects found in the model.')
                return false
            else
                boilers.each do |boiler|
                    boiler.setNominalThermalEfficiency(0.92)
                    runner.registerInfo("Updated boiler '#{boiler.name}' efficiency to 0.92.")
                end
                runner.registerFinalCondition("Updated #{boilers.size} boiler(s) to 92% efficiency.")
                return true
            end



        # Choose performance curves based on the selected option
        case hvac_option
        when 'Mini-Split'
            # DX cooling capacity as a function of EWB and OAT
            cool_cap_ft = OpenStudio::Model::CurveBiquadratic.new(model)
            cool_cap_ft.setName('MiniSplit-Cool-Cap-fEWB&OAT')
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
            cool_eir_ft.setName('MiniSplit-Cool-EIR-fEWB&OAT')
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
            cool_plr.setName('MiniSplit-Cool-EIR-fPLR')
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
            heat_plr.setName('MiniSplit-Heat-EIR-fPLR')
            heat_plr.setCoefficient1Constant(0.08565216)
            heat_plr.setCoefficient2x(0.93881381)
            heat_plr.setCoefficient3xPOW2(-0.18343613)
            heat_plr.setCoefficient4xPOW3(0.15897022)
        when 'Packaged HP'
            # DX cooling capacity as a function of EWB and OAT
            cool_cap_ft = OpenStudio::Model::CurveBiquadratic.new(model)
            cool_cap_ft.setName('PTHP-Cool-Cap-fEWB&OAT')
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
            cool_eir_ft.setName('PTHP-Cool-EIR-fEWB&OAT')
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
            cool_plr.setName('PTHP-Cool-EIR-fPLR')
            cool_plr.setCoefficient1Constant(0.20123008)
            cool_plr.setCoefficient2x(-0.0312175)
            cool_plr.setCoefficient3xPOW2(1.95049798)
            cool_plr.setCoefficient4xPOW3(-1.12051034)

            # Heating Capacity as a Function of EDB and OAT
            heat_cap_ft = OpenStudio::Model::CurveBiquadratic.new(model)
            heat_cap_ft.setName('PTHP-Heat-Cap-fT')
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
            heat_eir_ft.setName('PTHP-Heat-EIR-fT')
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
            heat_plr.setName('PTHP-Heat-EIR-fPLR')
            heat_plr.setCoefficient1Constant(0.08565216)
            heat_plr.setCoefficient2x(0.93881381)
            heat_plr.setCoefficient3xPOW2(-0.18343613)
            heat_plr.setCoefficient4xPOW3(0.15897022)
        end

        # initialize a counter for modified zones
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


            # create heating coil and set performance curves
            heating_coil = OpenStudio::Model::CoilHeatingDXSingleSpeed.new(model)
            heating_coil.setName("Heating Coil - #{zone.name}")
            heating_coil.setTotalHeatingCapacityFunctionofTemperatureCurve(heat_cap_ft)
            heating_coil.setEnergyInputRatioFunctionofTemperatureCurve(heat_eir_ft)
            heating_coil.setEnergyInputRatioFunctionofFlowFractionCurve(heat_plr)

            # add supplemental heating coil
            supplemental_heating_coil = OpenStudio::Model::CoilHeatingElectric.new(model)
            supplemental_heating_coil.setName("Supplemental Heating Coil - #{zone.name}")

            # create an always-on availability schedule
            availability = OpenStudio::Model::ScheduleConstant.new(model)
            availability.setValue(1.0)

            case hvac_option
            when 'Mini-Split'
                # set rated COPs for Mini-Split
                cooling_coil.setRatedCOP(5.667) # SEER2 21
                heating_coil.setRatedCOP(3.516) # HSPF2 10.2
            when 'Packaged HP'
                # set rated COPs for Packaged Terminal Heat Pump
                cooling_coil.setRatedCOP(3.645) # SEER2 13.65
                heating_coil.setRatedCOP(2.445) # HSPF2 7.1
            end

            # create a new packaged heat pump
            ptac = OpenStudio::Model::ZoneHVACPackagedTerminalHeatPump.new(
                model, availability, fan, heating_coil, cooling_coil, supplemental_heating_coil
            )
            ptac.setName("#{hvac_option} HP - #{zone.name}")
            ptac.addToThermalZone(zone)

            # increment the zone counter
            zones_modified += 1
        end

        if ['Mini-Split', 'Packaged HP'].include?(hvac_option)
            # set an always-on schedule for the ERV
            always_on = model.alwaysOnDiscreteSchedule

            # airflow in m³/s (75 CFM)
            erv_flow = OpenStudio.convert(75, 'cfm', 'm^3/s').get

            # ERV fan configuration
            fan_efficiency = 0.5
            target_power_watts = 75 * 0.5   # 0.5 W/CFM per fan
            pressure_rise = target_power_watts * fan_efficiency / erv_flow  # ~535.7 Pa

            # add ERV to each apartment zone
            model.getThermalZones.each do |zone|
                next unless zone.name.get.downcase.include?('apartment')
                next if zone.equipment.any? { |eq| eq.to_ZoneHVACEnergyRecoveryVentilator.is_initialized }

                # supply fan
                supply_fan = OpenStudio::Model::FanConstantVolume.new(model)
                supply_fan.setName("ERV Supply Fan - #{zone.nameString}")
                supply_fan.setFanEfficiency(fan_efficiency)
                supply_fan.setPressureRise(pressure_rise)
                supply_fan.setAvailabilitySchedule(always_on)

                # exhaust fan
                exhaust_fan = OpenStudio::Model::FanConstantVolume.new(model)
                exhaust_fan.setName("ERV Exhaust Fan - #{zone.nameString}")
                exhaust_fan.setFanEfficiency(fan_efficiency)
                exhaust_fan.setPressureRise(pressure_rise)
                exhaust_fan.setAvailabilitySchedule(always_on)

                # heat exchanger
                hx = OpenStudio::Model::HeatExchangerAirToAirSensibleAndLatent.new(model)
                hx.setSensibleEffectivenessat100HeatingAirFlow(0.75)
                hx.setSensibleEffectivenessat100CoolingAirFlow(0.75)
                hx.setLatentEffectivenessat100HeatingAirFlow(0.50)
                hx.setLatentEffectivenessat100CoolingAirFlow(0.50)

                # ERV unit
                erv = OpenStudio::Model::ZoneHVACEnergyRecoveryVentilator.new(model)
                erv.setName("ERV - #{zone.nameString}")
                erv.setAvailabilitySchedule(always_on)
                erv.setSupplyAirFlowRate(erv_flow)
                erv.setExhaustAirFlowRate(erv_flow)
                erv.setHeatExchanger(hx)
                erv.addToThermalZone(zone)
            end

        end

        runner.registerFinalCondition("Installed #{hvac_option} systems in #{zones_modified} zones.")



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
UpgradeHVACSystemChoice.new.registerWithApplication