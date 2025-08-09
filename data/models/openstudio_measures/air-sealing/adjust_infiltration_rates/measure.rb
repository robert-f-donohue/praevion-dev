# -----------------------------------------------------------------------------------------------
# AdjustInfiltrationRates
#
# Author:  Robert Donohue, enviENERGY Studio LLC
# Version: 0.2.0
# Date:    2025-06-22
# -----------------------------------------------------------------------------------------------

class AdjustInfiltrationRates < OpenStudio::Measure::ModelMeasure

    def name
        return 'Adjust Infiltration Rates'
    end

    def arguments(model)
        args = OpenStudio::Measure::OSArgumentVector.new

        # dropdown with options for air leakage rates (cfm/sf envelope area)
        choices = OpenStudio::StringVector.new
        choices << '1.00'
        choices << '0.90'
        choices << '0.75'
        choices << '0.60'
        choices << '0.40'

        # set your selection default to None
        infiltration_option  = OpenStudio::Measure::OSArgument.makeChoiceArgument('infiltration_option', choices, true)
        infiltration_option .setDisplayName('Select Target Air Leakage Rate (cfm/sf envelope area)')
        infiltration_option .setDefaultValue('1.00') # default to 1.00 cfm/sf
        args << infiltration_option

        # return argument vector
        return args
    end

    def run(model, runner, user_arguments)
        super(model, runner, user_arguments)

        # validate the user arguments
        return false unless runner.validateUserArguments(arguments(model), user_arguments)

        # get selected air leakage option
        infiltration_option  = runner.getStringArgumentValue('infiltration_option', user_arguments)

        # return early if None is selected
        if infiltration_option == '1.00'
            runner.registerInfo('No change made to air leakage rate.')
            return true
        end

        # convert IP air leakage to SI using OpenStudio.convert (cfm/ft² to m³/s·m²)
        target_ip = infiltration_option.to_f
        conversion  = OpenStudio.convert(target_ip, 'ft^3/min', 'm^3/s')

        unless conversion.is_initialized
            runner.registerError("Failed to convert U-#{target_ip} from IP to SI.")
            return false
        end

        target_si = conversion.get

        # Loop through spaces with exterior exposure
        perimeter_spaces = model.getSpaces.select do |space|
            space.surfaces.any? { |s| s.outsideBoundaryCondition.downcase == 'outdoors' }
        end

        if perimeter_spaces.empty?
            runner.registerAsNotApplicable('No perimeter (exterior) spaces found in the model.')
            return true
        end

        updated_count = 0



        # select each perimeter space's air leakage rate
        perimeter_spaces.each do |space|
            # set air leakage rate to the target value
            space.spaceInfiltrationDesignFlowRates.each do |infiltration|
                infiltration.setFlowperExteriorSurfaceArea(target_si)
                updated_count += 1
            end
        end

        if updated_count == 0
            runner.registerWarning('No SpaceInfiltrationDesignFlowRate objects found. Consider adding infiltration objects to spaces.')
        else
            runner.registerFinalCondition("Updated infiltration rate to #{infiltration_option} cfm/ft² for #{updated_count} perimeter zones.")
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
AdjustInfiltrationRates.new.registerWithApplication
