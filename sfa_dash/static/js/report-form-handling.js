/*
 *  Creates inputs for defining observation, forecast pairs for a report.
 */

function addPair(
    truth_type, truth_name, truth_id, fx_name, fx_id, ref_fx_name, ref_fx_id,
    db_label, db_value, forecast_type='forecast'){
    /*  Inserts a new deterministic forecast object pair.
     *
     *  @param {string} truth_type
     *      The type of object to compare the forecast against. Either
     *      'aggregate' or 'observation'.
     *  @param {string} truth_name
     *      Name of the observation or aggregate in the pair.
     *  @param {string} truth_id
     *      UUID of the observation or aggregate in the pair.
     *  @param {string} fx_name
     *      Name of the forecast in the pair.
     *  @param {string} fx_id
     *      UUID of the forecast in the pair
     *  @param {string} ref_fx_name
     *      Name of the reference forecast in the pair.
     *  @param {string} ref_fx_id
     *      UUID of the reference forecast in the pair
     *  @param {string} db_label
     *      The uncertainty (deadband) label to display.
     *  @param {float} db_value
     *      The uncertainty (deadband) value to forward to the API.
     *  @param {string} forecast_type
     *      The type of forecast in the pair.
     */

    var new_object_pair = $(`<div class="pair-container object-pair object-pair-${pair_index}">
            <div class="input-wrapper">
              <div class="col-md-12">
                <div class="object-pair-label forecast-name-${pair_index}"><b>Forecast: </b>${fx_name}</div>
                <input type="hidden" class="form-control forecast-value" name="forecast-id-${pair_index}" required value="${fx_id}"/>
                <div class="object-pair-label truth-name-${pair_index}"><b>Observation: </b> ${truth_name}</div>
                <input type="hidden" class="form-control truth-value" name="truth-id-${pair_index}" required value="${truth_id}"/>
                <input type="hidden" class="form-control truth-type-value" name="truth-type-${pair_index}" required value="${truth_type}"/>
                <div class="object-pair-label reference-forecast-name"><b>Reference Forecast: </b> ${ref_fx_name}</div>
                <input type="hidden" class="form-control reference-forecast-value" name="reference-forecast-${pair_index}" required value="${ref_fx_id}"/>
                <div class="object-pair-label deadband-label"><b>Uncertainty: </b> ${db_label}</div>
                <input type="hidden" class="form-control deadband-value" name="deadband-value-${pair_index}" required value="${db_value}"/>
                <input type="hidden" class="forecast-type-value" required name="forecast-type-${pair_index}" value="${forecast_type}"/>
              </div>
             </div>
             <a role="button" class="object-pair-delete-button">remove</a>
           </div>`);
    var remove_button = new_object_pair.find(".object-pair-delete-button");
    remove_button.click(function(){
        new_object_pair.remove();
        if ($('.object-pair-list .object-pair').length == 0){
            $('.empty-reports-list')[0].hidden = false;
            report_utils.unset_units();
        }
        report_utils.toggle_reference_dependent_metrics();
    });
    pair_container.append(new_object_pair);
    pair_index++;
}

function createPairSelector(){
    /*
     * Returns a JQuery object containing Forecast, Observation pair widgets to insert into the DOM
     */

    /*
     *  Filtering Functions
     *      Callbacks for hidding/showing select list options based on the searchbars
     *      for each field and previously made selections
     */
    function filterSites(){
        /*
         * Filter the Site Options Via the text found in the #site-option-search input
         */
        var sites = siteSelector.find('option').slice(1);
        sites.removeAttr('hidden');

        var toHide = report_utils.searchSelect('#site-option-search', '#site-select', 1);
        if (toHide.length == sites.length){
            // No sites matched search query, display "no matching sites"
            $('#no-sites').removeAttr('hidden');
        } else {
            // Some sites matched, hide "no matching sites" message.
            $('#no-sites').attr('hidden', true);
        }
        toHide.attr('hidden', true);
    }

    function determineWidgets(){
        /*
         * Based on the value of the observation-aggregate-radio button,
         * display the correct select lists and set up the correct
         * parsing of values into object-pairs.
         */
        var compareTo = $(`[name=observation-aggregate-radio]:checked`).val();
        if (compareTo == 'observation'){
            // hide aggregates
            // show sites & observations
            $('.aggregate-select-wrapper').attr('hidden', true);
            $('.site-select-wrapper').removeAttr('hidden');
            $('.observation-select-wrapper').removeAttr('hidden');
            $('#aggregate-select').val('');
            $("#add-obs-object-pair").removeAttr('hidden');
            $("#add-agg-object-pair").attr('hidden', true);
            $('.deadband-select-wrapper').removeAttr('hidden');
            filterForecasts();
        } else {
            // hide sites & observations
            // show aggregates
            $('.site-select-wrapper').attr('hidden', true);
            $('.observation-select-wrapper').attr('hidden', true);
            $('.aggregate-select-wrapper').removeAttr('hidden');
            $('#site-select').val('');
            $("#add-agg-object-pair").removeAttr('hidden');
            $("#add-obs-object-pair").attr('hidden', true);
            $('.deadband-select-wrapper').attr('hidden', true);
            filterForecasts();
        }
        return compareTo

    }

    function filterForecasts(){
        /*
         * Hide options in the forecast selector based on the currently selected
         * site and variable.
         */
        // Show all Forecasts
        var forecasts = $('#forecast-select option').slice(2);
        forecasts.removeAttr('hidden');

        var toHide = report_utils.searchSelect('#forecast-option-search', '#forecast-select', 2);
        var variable_select = $('#variable-select');
        var variable = variable_select.val();
        if (variable){
            toHide = toHide.add(forecasts.not(`[data-variable=${variable}]`));
        }
        // Determine if we need to filter by site or aggregate
        var compareTo = $(`[name=observation-aggregate-radio]:checked`).val();
        if (compareTo == 'observation'){
            var selectedSite = $('#site-select :selected');
            var site_id = selectedSite.data('site-id');
            if (site_id){
                $('#no-forecast-site-selection').attr('hidden', true);
            } else {
                $('#no-forecast-site-selection').removeAttr('hidden');
            }
            // create a set of elements to hide from selected site, variable and search
            toHide = toHide.add(forecasts.not(`[data-site-id=${site_id}]`));
        } else {

            toHide = toHide.add(forecasts.not('[data-aggregate-id]'));
            $('#no-forecast-site-selection').attr('hidden', true);
        }
        // if current forecast selection is invalid, deselect
        if (toHide.filter(':selected').length){
            forecast_select.val('');
        }
        toHide.attr('hidden', 'true');
        // if all options are hidden, show "no matching forecasts"
        if (toHide.length == forecasts.length){
            forecast_select.val('');
            if ($('#no-forecast-site-selection').attr('hidden') || compareTo == 'aggregate'){
                $('#no-forecasts').removeAttr('hidden');
            }
        } else {
            $('#no-forecasts').attr('hidden', true);
        }
        filterReferenceForecasts(variable);
        if (compareTo == 'observation'){
            filterObservations();
        } else {
            filterAggregates();
        }
    }

    function filterReferenceForecasts(variable){
        /* Filter the list of reference forecasts based on the current
         * forecast.
         */
        var forecast = forecast_select.find(':selected').first();
        var reference_forecasts = $('#reference-forecast-select option').slice(2);
        var compareTo = $(`[name=observation-aggregate-radio]:checked`).val();
        reference_forecasts.removeAttr('hidden');
        if (forecast[0]){
            // collect the site or aggregate id, variable and interval_length
            // of the currently selected forecast.
            if(forecast.data.hasOwnProperty('siteId')){
                var site_id = forecast.data().siteId;
            }else{
                var aggregate_id = forecast.data().aggregateId;
            }
            var variable = forecast.data().variable;
            var interval_length = forecast.data().intervalLength;

            // hide the "please select forecast" prompt"
            $('#no-reference-forecast-forecast-selection').attr('hidden', true);
            var toHide = report_utils.searchSelect('#reference-forecast-option-search',
                              '#reference-forecast-select', 2);

            // if a variable is selected, hide all reference forecasts for
            // other variables.
            if (variable){
                toHide = toHide.add(reference_forecasts.not(
                    `[data-variable=${variable}]`));
            }

            // Determine if we need to filter by site or aggregate
            if (site_id){
                // create a set of elements to hide from selected site, variable and search
                toHide = toHide.add(reference_forecasts.not(
                    `[data-site-id=${site_id}]`));
            } else {
                toHide = toHide.add(
                    reference_forecasts.not(
                        `[data-aggregate-id=${aggregate_id}]`));
            }

            // Filter out reference forecasts that don't have the same
            // interval length
            mismatched_intervals = reference_forecasts.filter(function(){
                return $(this).data().intervalLength != interval_length ||
                    $(this).attr('value') == forecast_select.val();
            });
            toHide = toHide.add(mismatched_intervals);
        }else{
            // No forecast was selected, hide all reference forecasts
            // and display a message.
            var toHide = reference_forecasts;
            $('#no-reference-forecast-forecast-selection').removeAttr('hidden');
        }

        // if current forecast selection is invalid, deselect
        if (toHide.filter(':selected').length){
            ref_forecast_select.val('');
        }
        toHide.attr('hidden', 'true');
        // if all options are hidden, show "no matching forecasts"
        if (toHide.length == reference_forecasts.length){
            ref_forecast_select.val('');
            if ($('#no-reference-forecast-forecast-selection').attr('hidden') || compareTo == 'aggregate'){
                $('#no-reference-forecasts').removeAttr('hidden');
            }
        } else {
            $('#no-reference-forecasts').attr('hidden', true);
            report_utils.restore_prev_value(previous_reference_forecast);
        }
    }

    function filterAggregates(){
        /*
         * Filter aggregate options based on radio buttons
         */
        var aggregates = aggregateSelector.find('option').slice(2);
        aggregates.removeAttr('hidden');
        var selectedForecast = $('#forecast-select :selected');
        if (selectedForecast.length){
            var aggregate_id = selectedForecast.data('aggregate-id');
            var toHide = report_utils.searchSelect('#aggregate-option-search', '#aggregate-select', 1);
            // Hide aggregates that don't match the forecasts aggregate id
            toHide = toHide.add(aggregates.not(`[data-aggregate-id=${aggregate_id}]`));

            // Hide all aggregates with greater interval length than the
            // forecast.
            var current_interval = selectedForecast.data('interval-length');
            toHide = toHide.add(aggregates.filter(function(){
                return parseInt(this.dataset['intervalLength']) > current_interval;
            }));

            if ((toHide.length == aggregates.length) && aggregate_id){
                // No aggregates match, hide all and display a message.
                $('#no-aggregates').removeAttr('hidden');
            } else {
                // Some aggregates matched, hide the "no matching aggregates"
                // message
                $('#no-aggregates').attr('hidden', true);
            }

            // Hide the "please select a forecast" message.
            $('#no-aggregate-forecast-selection').attr('hidden', true);
        } else {
            // No forecast was selected, hide all aggregates and display a
            // message.
            var toHide = aggregates;
            $('#no-aggregate-forecast-selection').removeAttr('hidden');
        }
        toHide.attr('hidden', true);
    }

    function filterObservations(){
        /* Filter list of observations based on current site and variable.
         */
        var observations = $('#observation-select option').slice(2);
        // get the attributes of the currently selected forecast
        var selectedForecast = $('#forecast-select :selected');
        if (selectedForecast.length){
            // Show all of the observations
            observations.removeAttr('hidden');

            // retrieve the current site id and variable from the selected forecast
            var site_id = selectedForecast.data('site-id');
            var variable = selectedForecast.data('variable');
            $('#no-observation-forecast-selection').attr('hidden', true);

            // Build the list of options to hide by creating a set from
            // the lists of elements to hide from search, site id and variable
            var toHide = report_utils.searchSelect('#observation-option-search', '#observation-select', 2);
            // Hide observations that don't match the forecasts site id or
            // variable
            toHide = toHide.add(observations.not(`[data-site-id=${site_id}]`));
            toHide = toHide.add(observations.not(`[data-variable=${variable}]`));

            // Hide all observations with interval lengths greater than the
            // forecast
            var current_interval = selectedForecast.data('interval-length');
            toHide = toHide.add(observations.filter(function(){
                return parseInt(this.dataset['intervalLength']) > current_interval
            }));

            toHide.attr('hidden', true);

            // if the current selection is hidden, deselect it
            if (toHide.filter(':selected').length){
                observation_select.val('').change();
            }

            if (toHide.length == observations.length){
                // all observations are hidden, display "no observations"
                $('#no-observations').removeAttr('hidden');
            } else {
                // some observations matched, hide "no observations" message
                $('#no-observations').attr('hidden', true);
                report_utils.restore_prev_value(previous_observation);
            }
        } else {
            // No forecast selected, hide all observations and display
            // forecast selection message.
            observations.attr('hidden', true);
            $('#no-observation-forecast-selection').removeAttr('hidden');
            observation_select.val('').change();
        }
    }
    /*
     * Create select widgets for creating an observatio/forecast pair,
     */
    var aggregateSelector = report_utils.newSelector("aggregate", "forecast");
    var siteSelector = report_utils.newSelector("site");
    var obsSelector = report_utils.newSelector("observation", "forecast");
    var fxSelector = report_utils.newSelector("forecast", "site");
    var refFxSelector = report_utils.newSelector("reference forecast", "forecast", required=false);
    var fxVariableSelector = report_utils.createVariableSelect();
    var dbSelector = report_utils.deadbandSelector();
    fxSelector.find('.report-field-filters').append(fxVariableSelector);

    // Buttons for adding an obs/fx pair for observations or aggregates
    var addObsButton = $('<a role="button" class="btn btn-primary" id="add-obs-object-pair" style="padding-left: 1em">Add a Forecast, Observation pair</a>');
    var addAggButton = $('<a role="button" class="btn btn-primary" id="add-agg-object-pair" style="padding-left: 1em">Add a Forecast, Aggregate pair</a>');


    // Create a radio button for selecting between aggregate or observation
    var obsAggRadio = $(`<div><b>Compare Forecast to&colon;</b>
                         <input type="radio" name="observation-aggregate-radio" value="observation" checked> Observation
                         <input type="radio" name="observation-aggregate-radio" value="aggregate">Aggregate<br/></div>`);
    radio_inputs = obsAggRadio.find('input[type=radio]');
    radio_inputs.change(determineWidgets);

    /*
     * Add all of the input elements to the widget container.
     */
    var widgetContainer = $('<div class="pair-selector-wrapper collapse"></div>');
    widgetContainer.append(obsAggRadio);
    widgetContainer.append(siteSelector);
    widgetContainer.append(fxSelector);
    widgetContainer.append(refFxSelector);
    widgetContainer.append(obsSelector);
    widgetContainer.append(aggregateSelector);
    widgetContainer.append(dbSelector);
    widgetContainer.append(addObsButton);
    widgetContainer.append(addAggButton);

    // hide aggregate controls by default
    addAggButton.attr('hidden', true);
    aggregateSelector.attr('hidden', true);

    // Register callback functions
    siteSelector.find('#site-option-search').keyup(filterSites);
    obsSelector.find('#observation-option-search').keyup(filterObservations);
    fxSelector.find('#forecast-option-search').keyup(filterForecasts);
    fxSelector.find('#reference-forecast-option-search').keyup(filterForecasts);
    aggregateSelector.find('#aggregate-option-search').keyup(filterAggregates);

    // create variables pointing to the specific select elements
    var observation_select = obsSelector.find('#observation-select');
    var forecast_select = fxSelector.find('#forecast-select');
    var ref_forecast_select = refFxSelector.find('#reference-forecast-select');
    var site_select = siteSelector.find('#site-select');
    var aggregate_select = aggregateSelector.find('#aggregate-select');

    // set callbacks for select inputs
    site_select.change(filterForecasts);
    variable_select.change(filterForecasts);
    forecast_select.change(filterObservations);
    forecast_select.change(filterAggregates);
    forecast_select.change(filterReferenceForecasts);

    // Store the selected observation or reference forecast when the value
    // changes for persisting across different forecasts/sites etc.
    observation_select.change(report_utils.store_prev_observation);
    ref_forecast_select.change(report_utils.store_prev_reference_forecast);

    // insert options from page_data into the select elements
    $.each(page_data['sites'], function(){
        site_select.append(
            $('<option></option>')
                .html(this.name)
                .val(this.site_id)
                .attr('data-site-id', this.site_id));
    });
    $.each(page_data['observations'], function(){
        observation_select.append(
            $('<option></option>')
                .html(this.name)
                .val(this.observation_id)
                .attr('hidden', true)
                .attr('data-site-id', this.site_id)
                .attr('data-interval-length', this.interval_length)
                .attr('data-variable', this.variable));
    });
    var nonevent_forecasts = page_data['forecasts'].filter(
        f => f.variable != 'event');
    $.each(nonevent_forecasts, function(){
        forecast_select.append($('<option></option>')
                .html(this.name)
                .val(this.forecast_id)
                .attr('hidden', true)
                .attr('data-site-id', this.site_id)
                .attr('data-aggregate-id', this.aggregate_id)
                .attr('data-interval-length', this.interval_length)
                .attr('data-variable', this.variable));
    });
    $.each(nonevent_forecasts, function(){
        ref_forecast_select.append($('<option></option>')
                .html(this.name)
                .val(this.forecast_id)
                .attr('hidden', true)
                .attr('data-site-id', this.site_id)
                .attr('data-aggregate-id', this.aggregate_id)
                .attr('data-interval-length', this.interval_length)
                .attr('data-variable', this.variable));
    });
    $.each(page_data['aggregates'], function(){
        aggregate_select.append(
            $('<option></option>')
                .html(this.name)
                .val(this.aggregate_id)
                .attr('hidden', true)
                .attr('data-aggregate-id', this.aggregate_id)
                .attr('data-interval-length', this.interval_length)
                .attr('data-variable', this.variable));
    });

    addObsButton.click(function(){
        /*
         * 'Add a Forecast, Observation pair button on button click
         *
         * On click, appends a new pair of inputs inside the 'pair_container' div, initializes
         * their select options and increment the pair_index.
         */
        if (observation_select.val() && forecast_select.val()){
            // If both inputs contain valid data, create a pair and add it to the DOM
            var selected_observation = observation_select.find('option:selected')[0];
            var selected_forecast = forecast_select.find('option:selected')[0];
            var selected_reference_forecast = ref_forecast_select.find('option:selected')[0];
            if(!selected_reference_forecast){
                var ref_text = "Unset";
                var ref_id = null;
            }else{
                var ref_text = selected_reference_forecast.text;
                var ref_id = selected_reference_forecast.value;
            }
            // try to parse deadband values
            try{
                var deadband_values = report_utils.parseDeadband();
            }catch(error){
                return;
            }
            addPair('observation',
                    selected_observation.text,
                    selected_observation.value,
                    selected_forecast.text,
                    selected_forecast.value,
                    ref_text,
                    ref_id,
                    deadband_values[0],
                    deadband_values[1],
            );
            var variable = selected_forecast.dataset.variable;
            report_utils.set_units(variable);
            $(".empty-reports-list").attr('hidden', 'hidden');
            forecast_select.css('border', '');
            observation_select.css('border', '');
            report_utils.toggle_reference_dependent_metrics();
        } else {
            // Otherwise apply a red border to alert the user to need of input
            if (forecast_select.val() == null){
                forecast_select.css('border', '2px solid #F99');
            }
            if (observation_select.val() == null){
                observation_select.css('border', '2px solid #F99');
            }
        }
    });
    addAggButton.click(function(){
        /*
         * Add a forecast, aggregate pair
         */
        if (aggregate_select.val() && forecast_select.val()){
            var selected_aggregate = aggregate_select.find('option:selected')[0];
            var selected_forecast = forecast_select.find('option:selected')[0];
            var selected_reference_forecast = ref_forecast_select.find('option:selected')[0];
            if(!selected_reference_forecast){
                var ref_text = "Unset";
                var ref_id = null;
            }else{
                var ref_text = selected_reference_forecast.text;
                var ref_id = selected_reference_forecast.value;
            }
             addPair('aggregate',
                           selected_aggregate.text,
                           selected_aggregate.value,
                           selected_forecast.text,
                           selected_forecast.value,
                           ref_text,
                           ref_id,
                           "Unset",
                           null,
            );
            var variable = selected_forecast.dataset.variable;
            report_utils.set_units(variable);

            $(".empty-reports-list")[0].hidden = true;
            forecast_select.css('border', '');
            observation_select.css('border', '');
            report_utils.toggle_reference_dependent_metrics();
        } else {
            // Otherwise apply a red border to alert the user to need of input
            if (forecast_select.val() == null){
                forecast_select.css('border', '2px solid #F99');
            }
            if (observation_select.val() == null){
                observation_select.css('border', '2px solid #F99');
            }
        }
    });
    return widgetContainer;
}

$(document).ready(function() {
    /*
     * Initialize global variables
     * pair_index - used for labelling matching pairs of observations/forecasts
     * pair_container - JQuery handle for the ul to hold pair elements
     * pair_control_container - JQuery handle for div to hold the select widgets
     *     used to create new pairs
     */
    pair_container = $('.object-pair-list');
    pair_control_container = $('.object-pair-control')
    pair_index = 0;
    // call the function to initialize the pair creation widget and insert it into the DOM
    pair_selector = createPairSelector();
    pair_control_container.append($('<a role="button" class="full-width object-pair-button collapser-button collapsed" data-toggle="collapse" data-target=".pair-selector-wrapper">Create Forecast Evaluation pairs</a>'));
    pair_control_container.append(pair_selector);
    report_utils.registerDatetimeValidator('period-start');
    report_utils.registerDatetimeValidator('period-end')
    report_utils.fill_existing_pairs();
    report_utils.register_uncertainty_handler('#observation-select');
});
