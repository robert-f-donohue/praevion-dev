# -----------------------------------------------------------------------------------------------
# UpgradeWallInsulation 
#
# Author:  Robert Donohue, enviENERGY Studio LLC
# Version: 0.1.0
# Date:    2025-06-13
# -----------------------------------------------------------------------------------------------


class UpgradeWallInsulation < OpenStudio::Measure::ModelMeasure

    def name
        return 'Upgrade Wall Insulation'
    end

    def arguments(model)
        args = OpenStudio::Measure::OSArgumentVector.new

        # dropdown with options for wall R-value
        choices = OpenStudio::StringVector.new
        choices << 'None'
        choices << 'R-10'
        choices << 'R-15'
        choices << 'R-20'
        choices << 'R-25'

        # set your selection default to None
        r_value_option = OpenStudio::Measure::OSArgument.makeChoiceArgument('r_value_option', choices, true)
        r_value_option.setDisplayName('Select Target Wall Insulation R-Value')
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
            runner.registerInfo('No change made to exterior wall insulation.')
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

        # select all exterior wall surfaces
        ext_walls = model.getSurfaces.select do |s|
            s.surfaceType.downcase == 'wall' && 
            s.outsideBoundaryCondition.downcase == 'outdoors'
        end

        # check if any exterior walls were found
        if ext_walls.empty?
            runner.registerError('No exterior walls found in the model.')
            return true
        end

        # create new insulation material
        new_insulation = OpenStudio::Model::MasslessOpaqueMaterial.new(model)
        new_insulation.setName("Wall Insulation R-#{target_r_ip} (#{target_r_si.round(2)} SI)")
        new_insulation.setThermalResistance(target_r_si)

        # create new construction with insulation layer
        new_construction = OpenStudio::Model::Construction.new(model)
        new_construction.setName("Upgraded Wall R-#{target_r_ip}")
        new_construction.insertLayer(0, new_insulation)

        # apply new construction to all exterior walls
        ext_walls.each do |wall|
            wall.setConstruction(new_construction)
        end

        # report final condition
        runner.registerFinalCondition("Applied R-#{target_r_ip} insulation (#{target_r_si.round(2)} SI) to #{ext_walls.size} exterior walls.")

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
UpgradeWallInsulation.new.registerWithApplication