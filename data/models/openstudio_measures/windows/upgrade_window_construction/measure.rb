# -----------------------------------------------------------------------------------------------
# UpgradeWindowConstruction
#
# Author:  Robert Donohue, enviENERGY Studio LLC
# Version: 0.1.0
# Date:    2025-06-22
# -----------------------------------------------------------------------------------------------

class UpgradeWindowConstruction < OpenStudio::Measure::ModelMeasure

    def name
        return 'Upgrade Window Construction'
    end

    def arguments(model)
        args = OpenStudio::Measure::OSArgumentVector.new

        # dropdown with options for window U-values
        choices = OpenStudio::StringVector.new
        choices << 'baseline (U-0.59, SHGC-0.40)'  # Baseline
        choices << 'double_clear_lowE (U-0.32, SHGC-0.40)'
        choices << 'double_tinted_lowE (U-0.30, SHGC-0.30)'
        choices << 'triple_lowE (U-0.20, SHGC-0.25)'

        # set your selection default to None
        glazing_choice = OpenStudio::Measure::OSArgument.makeChoiceArgument('glazing_choice', choices, true)
        glazing_choice.setDisplayName('Select Target Window Construction')
        glazing_choice.setDefaultValue('baseline (U-0.59, SHGC-0.40)')
        args << glazing_choice

        # return argument vector
        return args
    end

    def run(model, runner, user_arguments)
        super(model, runner, user_arguments)

        # validate the user arguments
        return false unless runner.validateUserArguments(arguments(model), user_arguments)

        # get selected U-value option
        glazing_choice = runner.getStringArgumentValue('glazing_choice', user_arguments)

        # define the glazing specifications with U-values and SHGC
        glazing_specs = {
            'double_clear_lowE (U-0.32, SHGC-0.40)' => { u_value_ip: 0.32, shgc: 0.40 },
            'double_tinted_lowE (U-0.30, SHGC-0.30)' => { u_value_ip: 0.30, shgc: 0.30 },
            'triple_lowE (U-0.20, SHGC-0.25)' => { u_value_ip: 0.20, shgc: 0.25 }
        }

        # return early if None is selected
        if glazing_choice == 'baseline (U-0.59, SHGC-0.40)'
            runner.registerInfo('No change made to window U-value.')
            return true
        end

        unless glazing_specs.key?(glazing_choice)
            runner.registerError("Invalid glazing option selected: #{glazing_choice}")
            return false
        end

        # get the target U-value and SHGC from the selected option
        target_u_ip = glazing_specs[glazing_choice][:u_value_ip]
        target_shgc = glazing_specs[glazing_choice][:shgc]

        # convert IP U-values to SI using OpenStudio.convert
        u_si_opt = OpenStudio.convert(target_u_ip, 'Btu/h*ft^2*R', 'W/m^2*K')
        unless u_si_opt.is_initialized
            runner.registerError("Failed to convert U-value #{target_u_ip} to SI.")
            return false
        end

        windows = model.getSubSurfaces.select { |s| ['FixedWindow', 'OperableWindow'].include?(s.subSurfaceType) }
        if windows.empty?
            runner.registerInfo('No windows found in the model.')
            return true
        end
        u_si = u_si_opt.get

        # set value to track updated windows
        windows_updated = 0

        # loop through each window and update the U-value
        windows.each do |window|
             # Create new SimpleGlazing material with correct U and SHGC
            simple_glass = OpenStudio::Model::SimpleGlazing.new(model)
            simple_glass.setUFactor(u_si)
            simple_glass.setSolarHeatGainCoefficient(target_shgc) # parsed from the selected option
            simple_glass.setName("Glazing U-#{u_si}_SHGC-#{target_shgc}")

            # create new window construction
            window_construction = OpenStudio::Model::Construction.new(model)
            window_construction.setName("Window U-#{u_si}_SHGC-#{target_shgc}")
            window_construction.insertLayer(0, simple_glass)

            # Assign to window
            window.setConstruction(window_construction)
            windows_updated += 1
        end

        # report final condition of model
        runner.registerFinalCondition("Updated #{windows_updated} windows to U-#{target_u_ip}.")

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
UpgradeWindowConstruction.new.registerWithApplication
