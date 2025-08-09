# -----------------------------------------------------------------------------------------------
# UpgradeWindowShgc
#
# Author:  Robert Donohue, enviENERGY Studio LLC
# Version: 0.1.0
# Date:    2025-06-13
# -----------------------------------------------------------------------------------------------

class UpgradeWindowShgc < OpenStudio::Measure::ModelMeasure

    def name
        return 'Upgrade Window SHGC'
    end

    def arguments(model)
        args = OpenStudio::Measure::OSArgumentVector.new

        # dropdown with options for window U-values
        choices = OpenStudio::StringVector.new
        choices << 'None'
        choices << '0.25'
        choices << '0.35'
        choices << '0.40'

        # set your selection default to None
        shgc_value_option = OpenStudio::Measure::OSArgument.makeChoiceArgument('shgc_value_option', choices, true)
        shgc_value_option.setDisplayName('Select Target Window SHGC')
        shgc_value_option.setDefaultValue('None')
        args << shgc_value_option

        # return argument vector
        return args
    end

    def run(model, runner, user_arguments)
        super(model, runner, user_arguments)

        # validate the user arguments
        return false unless runner.validateUserArguments(arguments(model), user_arguments)

        # get selected SHGC option
        shgc_value_option = runner.getStringArgumentValue('shgc_value_option', user_arguments)

        # return early if None is selected
        if shgc_value_option == 'None'
            runner.registerInfo('No change made to window SHGC.')
            return true
        end


        # convert SHGC to a numeric value
        target_shgc = shgc_value_option.to_f

        # select all window surfaces
        windows = model.getSubSurfaces.select do |s|
            ['FixedWindow', 'OperableWindow'].include?(s.subSurfaceType)
        end

        # check if any windows were found
        if windows.empty?
            runner.registerError('No windows found in the model.')
            return true
        end

        # set value to track updated windows
        windows_updated = 0

        # loop through each window and update the SHGC
        windows.each do |window|
            has_simple_glazing = false

            if window.construction.is_initialized
                construction_base = window.construction.get
                if construction_base.to_Construction.is_initialized
                    construction = construction_base.to_Construction.get
                    layers = construction.layers

                    # check if the first layer is a SimpleGlazing
                    if layers.size == 1 && layers[0].to_SimpleGlazing.is_initialized
                        glazing = layers[0].to_SimpleGlazing.get
                        glazing.setSolarHeatGainCoefficient(target_shgc)
                        runner.registerInfo("Updated SHGC for window #{window.name} to #{target_shgc}.")
                        windows_updated += 1
                        has_simple_glazing = true
                    end
                end
            end

            next if has_simple_glazing

            # fallback to creating a new glazing material if the existing one is not a SimpleGlazing
            simple_glass = OpenStudio::Model::SimpleGlazing.new(model)
            simple_glass.setName("Glazing SHGC-#{target_shgc}")
            simple_glass.setUFactor(1.8)  # Dummy U-value, overwritten by U-value measure (U-0.32)
            simple_glass.setSolarHeatGainCoefficient(target_shgc)

            # create construction with this glazing
            window_construction = OpenStudio::Model::Construction.new(model)
            window_construction.setName("Window SHGC-#{target_shgc}")
            window_construction.insertLayer(0, simple_glass)

            window.setConstruction(window_construction)
            windows_updated += 1
        end

        # report final condition of model
        runner.registerFinalCondition("Updated #{windows_updated} windows to SHGC of #{target_shgc}.")

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
UpgradeWindowShgc.new.registerWithApplication
