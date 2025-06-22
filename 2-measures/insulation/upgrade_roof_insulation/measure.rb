# -----------------------------------------------------------------------------------------------
# UpgradeRoofInsulation 
#
# Author:  Robert Donohue, enviENERGY Studio LLC
# Version: 0.1.0
# Date:    2025-06-13
# -----------------------------------------------------------------------------------------------


class UpgradeRoofInsulation < OpenStudio::Measure::ModelMeasure

    def name
        return 'Upgrade Roof Insulation'
    end

    def arguments(model)
        args = OpenStudio::Measure::OSArgumentVector.new

        # dropdown with options for roof R-value
        choices = OpenStudio::StringVector.new
        choices << 'None'
        choices << 'R-20'
        choices << 'R-30'
        choices << 'R-40'

        # set your selection default to None
        r_value_option = OpenStudio::Measure::OSArgument.makeChoiceArgument('r_value_option', choices, true)
        r_value_option.setDisplayName('Select Target Roof R-Value')
        r_value_option.setDefaultValue('None')
        args << r_value_option

        # return argument vector
        return args
    end

    def run(model, runner, user_arguments)
        super(model, runner, user_arguments)

        # validate the user arguments
        return false unless runner.validateUserArguments(arguments(model), user_arguments)

        # get selected R-value option
        r_value_option = runner.getStringArgumentValue('r_value_option', user_arguments)

        # return early if None is selected
        if r_value_option == 'None'
            runner.registerInfo('No change made to roof insulation.')
            return true
        end

        # convert IP R-values to SI using OpenStudio.convert
        target_r_ip = r_value_option.gsub('R-', '').to_f
        conversion = OpenStudio.convert(target_r_ip, 'ft^2*h*R/Btu', 'm^2*K/W')

        unless conversion.is_initialized
            runner.registerError("Failed to convert R-#{target_r_ip} from IP to SI.")
            return false
        end

        target_r_si = conversion.get

        # select all roof surfaces
        ext_walls = model.getSurfaces.select do |s|
            s.surfaceType.downcase == 'roofceiling' && 
            s.outsideBoundaryCondition.downcase == 'outdoors'
        end

        # check if any roofs were found
        if ext_walls.empty?
            runner.registerError('No roofs found in the model.')
            return true
        end

        # create new insulation material
        new_insulation = OpenStudio::Model::MasslessOpaqueMaterial.new(model)
        new_insulation.setName("Roof Insulation R-#{target_r_ip} (#{target_r_si.round(2)} SI)")
        new_insulation.setThermalResistance(target_r_si)

        # create new construction with insulation layer
        new_construction = OpenStudio::Model::Construction.new(model)
        new_construction.setName("Upgraded Roof R-#{target_r_ip}")
        new_construction.insertLayer(0, new_insulation)

        # apply new construction to all roofs
        ext_walls.each do |wall|
            wall.setConstruction(new_construction)
        end

        # report final condition
        runner.registerFinalCondition("Applied R-#{target_r_ip} insulation (#{target_r_si.round(2)} SI) to #{ext_walls.size} roofs.")

        # set the simulation control to run sizing calculations
        sim_control = model.getSimulationControl
        sim_control.setDoZoneSizingCalculation(true)
        sim_control.setDoSystemSizingCalculation(true)
        sim_control.setDoPlantSizingCalculation(true)
        sim_control.setRunSimulationforSizingPeriods(true)
        
        # set the measure as successful
        return true
    end

end
# register the measure to be used by the application
UpgradeRoofInsulation.new.registerWithApplication