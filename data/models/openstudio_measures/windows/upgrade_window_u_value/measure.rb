# -----------------------------------------------------------------------------------------------
# UpgradeWindowUValue
#
# Author:  Robert Donohue, enviENERGY Studio LLC
# Version: 0.1.0
# Date:    2025-06-13
# -----------------------------------------------------------------------------------------------

class UpgradeWindowUValue < OpenStudio::Measure::ModelMeasure

    def name
        return 'Upgrade Window U Value'
    end

    def arguments(model)
        args = OpenStudio::Measure::OSArgumentVector.new

        # dropdown with options for window U-values
        choices = OpenStudio::StringVector.new
        choices << 'None'
        choices << '0.32'
        choices << '0.28'
        choices << '0.22'
        choices << '0.18'

        # set your selection default to None
        u_value_option = OpenStudio::Measure::OSArgument.makeChoiceArgument('u_value_option', choices, true)
        u_value_option.setDisplayName('Select Target Window U-Value')
        u_value_option.setDefaultValue('None')
        args << u_value_option

        # return argument vector
        return args
    end

    def run(model, runner, user_arguments)
        super(model, runner, user_arguments)

        # validate the user arguments
        return false unless runner.validateUserArguments(arguments(model), user_arguments)

        # get selected U-value option
        u_value_option = runner.getStringArgumentValue('u_value_option', user_arguments)

        # return early if None is selected
        if u_value_option == 'None'
            runner.registerInfo('No change made to window U-value.')
            return true
        end

        # convert IP U-values to SI using OpenStudio.convert
        target_u_ip = u_value_option.to_f
        conversion = OpenStudio.convert(target_u_ip, 'Btu/h*ft^2*R', 'W/m^2*K')

        unless conversion.is_initialized
            runner.registerError("Failed to convert U-#{target_u_ip} from IP to SI.")
            return false
        end

        # select all window surfaces
        windows = model.getSubSurfaces.select do |s|
            ['FixedWindow', 'OperableWindow'].include?(s.subSurfaceType)
        end

        # check if any windows were found
        if windows.empty?
            runner.registerError('No windows found in the model.')
            return true
        end

        # get the converted U-value in SI
        target_u_si = conversion.get

        # set value to track updated windows
        windows_updated = 0

        # loop through each window and update the U-value
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
                        glazing.setUFactor(target_u_si)
                        runner.registerInfo("Updated U-value for window #{window.name} to #{target_u_si}.")
                        windows_updated += 1
                        has_simple_glazing = true
                    end
                end
            end

            next if has_simple_glazing

            # fallback to creating a new glazing material if the existing one is not a SimpleGlazing
            simple_glass = OpenStudio::Model::SimpleGlazing.new(model)
            simple_glass.setUFactor(target_u_si)
            simple_glass.setSolarHeatGainCoefficient(0.35) # set a default SHGC value, to be overridden later
            simple_glass.setName("Glazing U-#{target_u_ip}")

            # create new window construction
            window_construction = OpenStudio::Model::Construction.new(model)
            window_construction.setName("Window U-#{target_u_ip}")
            window_construction.insertLayer(0, simple_glass)

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
UpgradeWindowUValue.new.registerWithApplication
