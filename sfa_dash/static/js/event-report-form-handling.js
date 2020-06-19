/*
 *  Creates inputs for defining observation, forecast pairs for a report.
 */
function addPair(
    truth_type, truth_name, truth_id, fx_name, fx_id, ref_fx_name, ref_fx_id,
    db_label, db_value, forecast_type='event_forecast'){
	/*  Inserts a new event forecast object pair.
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
     *  @param {string} ref_fx_name - Ignored.
     *  @param {string} ref_fx_id - Ignored.
     *  @param {string} db_label - Ignored.
     *  @param {float} db_value - Ignored.
     *  @param {string} forecast_type
     *      The type of forecast in the pair. Defaults to 'event_forecast'.
     */
    var new_object_pair = $(`<div class="object-pair pair-container object-pair-${pair_index}">
            <div class="input-wrapper">
              <div class="col-md-12">
                <div class="object-pair-label forecast-name-${pair_index}"><b>Forecast: </b>${fx_name}</div>
                <input type="hidden" class="form-control forecast-value" name="forecast-id-${pair_index}" required value="${fx_id}"/>
                <div class="object-pair-label truth-name-${pair_index}"><b>Observation: </b> ${truth_name}</div>
                <input type="hidden" class="form-control truth-value" name="truth-id-${pair_index}" required value="${truth_id}"/>
                <input type="hidden" class="form-control truth-type-value" name="truth-type-${pair_index}" required value="${truth_type}"/>
                <input type="hidden" class="form-control deadband-value" name="deadband-value-${pair_index}" required value="null"/>
                <input type="hidden" class="form-control reference-forecast-value" name="reference-forecast-${pair_index}" required value="null"/>
                <input type="hidden" class="forecast-type-value" name="forecast-type-${pair_index}" required value="${forecast_type}"/>
              </div>
             </div>
             <a role="button" class="object-pair-delete-button">remove</a>
           </div>`);
    var remove_button = new_object_pair.find(".object-pair-delete-button");
    remove_button.click(function(){
        new_object_pair.remove();
        if ($('.object-pair-list .object-pair').length == 0){
            $('.empty-reports-list')[0].hidden = false;
        }
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

        var toHide = report_utils.searchSelect(
            '#site-option-search', '#site-select', 1);

        if (toHide.length == sites.length){
            $('#no-sites').removeAttr('hidden');
        } else {
            $('#no-sites').attr('hidden', true);
        }
        toHide.attr('hidden', true);
    }

    function filterForecasts(){
        /*
         * Hide options in the forecast selector based on the currently selected
         * site and variable.
         */
        // Show all Forecasts
        var forecasts = $('#forecast-select option').slice(2);
        forecasts.removeAttr('hidden');

        var toHide = report_utils.searchSelect(
            '#forecast-option-search', '#forecast-select', 2);

        var variable = "event";
        toHide = toHide.add(forecasts.not(`[data-variable=${variable}]`));
        var selectedSite = $('#site-select :selected');
        var site_id = selectedSite.data('site-id');
        if (site_id){
            $('#no-forecast-site-selection').attr('hidden', true);
        } else {
            $('#no-forecast-site-selection').removeAttr('hidden');
        }

        // create a set of elements to hide from selected site, variable and search
        toHide = toHide.add(forecasts.not(`[data-site-id=${site_id}]`));

        // if current forecast selection is invalid, deselect
        if (toHide.filter(':selected').length){
            forecast_select.val('');
        }
        toHide.attr('hidden', 'true');

        // if all options are hidden, show "no matching forecasts"
        if (toHide.length == forecasts.length){
            forecast_select.val('');
            if ($('#no-forecast-site-selection').attr('hidden')){
                $('#no-forecasts').removeAttr('hidden');
            }
        } else {
            $('#no-forecasts').attr('hidden', true);
        }
        filterObservations();
    }

    function filterObservations(){
        /* Filter list of observations based on current site and variable.
         */
        var observations = $('#observation-select option').slice(2);
        var selectedForecast = $('#forecast-select :selected');

        if (selectedForecast.length){
            // Show all of the observations
            observations.removeAttr('hidden');

            // retrieve the current site id
            var site_id = selectedForecast.data('site-id');
            var variable = "event";
            $('#no-observation-forecast-selection').attr('hidden', true);

            // Build the list of optiosn to hide by creating a set from
            // the lists of elements to hide from search, site id and variable
            var toHide = report_utils.searchSelect(
                '#observation-option-search', '#observation-select', 2);

            // Hise any observations that don't match the forecasts site_id
            // or variable
            toHide = toHide.add(observations.not(`[data-site-id=${site_id}]`));
            toHide = toHide.add(observations.not(`[data-variable=${variable}]`));

            var current_interval = selectedForecast.data('interval-length');
            toHide = toHide.add(observations.filter(function(){
                return parseInt(this.dataset['intervalLength']) > current_interval
            }));
            toHide.attr('hidden', true);

            // if the current selection is hidden, deselect it
            if (toHide.filter(':selected').length){
                observation_select.val('');
            }

            if (toHide.length == observations.length){
                $('#no-observations').removeAttr('hidden');
            } else {
                $('#no-observations').attr('hidden', true);
                report_utils.restore_prev_value(previous_observation);
            }
        } else {
            observations.attr('hidden', true);
            $('#no-observation-forecast-selection').removeAttr('hidden');
        }
    }

    /*
     * Create select widgets for creating an observatio/forecast pair,
     */
    var siteSelector = report_utils.newSelector("site");
    var obsSelector = report_utils.newSelector("observation", "forecast");
    var fxSelector = report_utils.newSelector("forecast", "site");

    // Buttons for adding an obs/fx pair for observations
    var addObsButton = $('<a role="button" class="btn btn-primary" id="add-obs-object-pair" style="padding-left: 1em">Add a Forecast, Observation pair</a>');


    /*
     * Add all of the input elements to the widget container.
     */
    var widgetContainer = $('<div class="pair-selector-wrapper collapse"></div>');
    widgetContainer.append(siteSelector);
    widgetContainer.append(fxSelector);
    widgetContainer.append(obsSelector);
    widgetContainer.append(addObsButton);


    // Register callback functions
    siteSelector.find('#site-option-search').keyup(filterSites);
    obsSelector.find('#observation-option-search').keyup(filterObservations);
    fxSelector.find('#forecast-option-search').keyup(filterForecasts);

    // create variables pointing to the specific select elements
    var observation_select = obsSelector.find('#observation-select');
    var forecast_select = fxSelector.find('#forecast-select');
    var site_select = siteSelector.find('#site-select');

    // set callbacks for select inputs
    site_select.change(filterForecasts);
    forecast_select.change(filterObservations);

    // Store selected observation when the value changs for persistence.
    observation_select.change(report_utils.store_prev_observation);

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
    $.each(page_data['forecasts'], function(){
        forecast_select.append($('<option></option>')
                .html(this.name)
                .val(this.forecast_id)
                .attr('hidden', true)
                .attr('data-site-id', this.site_id)
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
            addPair('observation',
                    selected_observation.text,
                    selected_observation.value,
                    selected_forecast.text,
                    selected_forecast.value,
            );
            $(".empty-reports-list").attr('hidden', 'hidden');
            forecast_select.css('border', '');
            observation_select.css('border', '');
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
    pair_control_container.append($('<a role="button" class="full-width collapser-button collapsed" data-toggle="collapse" data-target=".pair-selector-wrapper">Create Forecast Evaluation pairs</a>'));
    pair_control_container.append(pair_selector);
    report_utils.registerDatetimeValidator('period-start');
    report_utils.registerDatetimeValidator('period-end')
    report_utils.fill_existing_pairs();
});
