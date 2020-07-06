/*
 *  Creates inputs for defining observation, forecast pairs for a report.
 */

// globals for tracking the previous constant value and units. Need to keep
// track of both to ensure we're not persisting values across different units.
var previous_constant = null;
var previous_units = null;


function pairWrapper(truth_type, truth_id, truth_name, fx_id, fx_name,
                     ref_fx_name, db_label, db_value, distribution_id){
    /*  Creates a wrapper container that groups forecast, observation pairs by
     *  observation and probabilistic forecast group as well as uncertainty.
     *  The wrapper will have the data attributes:
     *      truth-id - The observation or aggregate's UUID.
     *      fx-id    - The probabilistic forecast group's forecast id.
     *      deadband-value - The uncertainty value.
     *  The container will also have a "remove button" that removes it and all
     *  nested object pairs.
     *
     */
    if (truth_type == 'observation'){
        var truth_label = 'Observation';
    } else {
        var truth_label = 'Aggregate';
    }
    // create a container for the pair
    var container = $(`
      <div class="object-pair pair-container" data-truth-id="${truth_id}" data-fx-id="${distribution_id}" data-deadband-value="${db_value}">
        <div class="col-md-12 pair-metadata">
        </div>
        <hr>
        <ul class="col-md-12 pair-constant-values">
        </ul>
      </div>`);

    // Insert the forecast, observation or aggregate name and the uncertainty
    // into the container
    var meta_block = container.find('.pair-metadata');
    meta_block.append($('<div></div>')
        .addClass('object-pair-label')
        .addClass('forecast-name')
        .html(`<b>Forecast: </b>${fx_name}`));
    meta_block.append($('<div></div>')
        .addClass('object-pair-label')
        .addClass('truth-name')
        .html(`<b>${truth_label}: </b> ${truth_name}`));

    meta_block.append($('<div></div>')
        .addClass('object-pair-label')
        .addClass('deadband-label')
        .html(`<b>Uncertainty: </b> ${db_label}`));

    // Add a 'remove' button that removes the container and all of its
    // children. Children are made up of constant value, reference forecast
    // pairs.
    container.append('<a role="button" class="object-pair-delete-button">remove</a>')
    var remove_button = container.find(".object-pair-delete-button");
    remove_button.click(function(){
        container.remove();
        if ($('.object-pair-list .object-pair').length == 0){
            // If the last pairs were removed, unset the unit constraint
            $('.empty-reports-list')[0].hidden = false;
            report_utils.unset_units(x => $('#site-select').change());
        }
        report_utils.toggle_reference_dependent_metrics();
    });
    return container;
}


function addPair(
    truth_type, truth_name, truth_id, fx_name, fx_id, ref_fx_name, ref_fx_id,
    db_label, db_value, forecast_type='probabilistic_forecast',
    constant_value, distribution_id){
	/*  Inserts a new probabilistic forecast object pair.
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
	 *  @param {string} constant_value
     *      The constant value of the forecast. Pass "Distribution" For
     *      probabilistic forecast groups.
     *  @param {string} distribution_id
     *      The UUID of the probabilistic forecast group of the forecast. For
     *      probabilistic forecast groups, this is just the forecast_id. For
     *      probabilistic forecast constant values, this is the parent field.
     */
    var new_container = false;

    if (forecast_type=='probabilistic_forecast'){
        $('[name="metrics"][value="crps"]').attr('checked', true);
    }

    // Check for the parent pair container that groups object_pairs
    // with similar observations, forecasts and uncertainties
    var pair_container = $(`
        .pair-container[data-truth-id=${truth_id}][data-fx-id=${distribution_id}][data-deadband-value="${db_value}"]`);
    if (pair_container.length == 0){
        pair_container = pairWrapper(
            truth_type, truth_id, truth_name, fx_id, fx_name, ref_fx_name,
            db_label, db_value, distribution_id);
        new_container = true;
    }

    // Get a handle to the list where we will append constant value pairs
    var constant_values = pair_container.find('.pair-constant-values');

    var constant_value_pair = $(`<li class="object-pair object-pair-${pair_index}">
        <div class="constant-value-label">${constant_value}</div>
        <div class="object-pair-label reference-forecast-name"><b>Reference Forecast: </b> ${ref_fx_name}</div>
        <input type="hidden" class="forecast-value" name="forecast-id-${pair_index}" required value="${fx_id}"/>
        <input type="hidden" class="truth-value" name="truth-id-${pair_index}" required value="${truth_id}"/>
        <input type="hidden" class="truth-type-value" name="truth-type-${pair_index}" required value="${truth_type}"/>
        <input type="hidden" class="reference-forecast-value" name="reference-forecast-${pair_index}" required value="${ref_fx_id}"/>
        <input type="hidden" class="deadband-value" name="deadband-value-${pair_index}" required value="${db_value}"/>
        <input type="hidden" class="forecast-type-value" name="forecast-type-${pair_index}" required value="${forecast_type}"/>
    </li>`);

    // Add a 'remove' button for the constant value pair
    constant_value_pair.append('<a role="button" class="object-pair-delete-button">remove</a>')
    var remove_button = constant_value_pair.find(".object-pair-delete-button");
    remove_button.click(function(){
        constant_value_pair.remove();
        if (constant_values.find('li').length == 0){
            // removing the last pair, remove the parent container
            pair_container.remove();
        }
        if ($('.object-pair-list .object-pair').length == 0){
            // if the last pairs were removed, remove the units constraint
            $('.empty-reports-list')[0].hidden = false;
            report_utils.unset_units(x => $('#site-select').change());
        }
        report_utils.toggle_reference_dependent_metrics();
    });

    // add the constant value pair to the parent container
    constant_values.append(constant_value_pair);

    // If the parent container was just created, add it to the dom.
    if (new_container){
        $('.object-pair-list').append(pair_container);
    }
    pair_index++;
}


function populateReferenceForecasts(){
    /* Filter the list of reference forecasts based on the current
     * forecast.
     */
    // Remove all the reference forecasts.
    var reference_forecasts = $('#reference-forecast-select option').slice(2);
    reference_forecasts.remove();

    // get the current distribution's forecast id
    var forecast = $('#distribution-select').val();
    var selected_constant_value = $('#constant-value-select').find(":selected").first();
    var compareTo = $('[name=observation-aggregate-radio]:checked').val();

    // Determine the attribute to use when comparing locations
    if (compareTo == 'observation'){
        var location_key = 'site_id';
    } else {
        var location_key = 'aggregate_id';
    }

    // If no constant value was selected, hide all reference forecasts,
    // display a message and return.
    if (selected_constant_value.length == 0){
        $('#no-reference-forecast-forecast-selection').removeAttr('hidden');
        $('#no-reference-forecasts').attr('hidden', true);
        return;
    }

    var constant_value_forecast_id = selected_constant_value.val();
    if (constant_value_forecast_id == 'full-cdf-group'){
        // No support for reference forecasts for full distributions
        $('#no-reference-forecast-forecast-selection').removeAttr('hidden');
        $('#no-reference-forecasts').attr('hidden', true);
        return;
    } else {
        // Get the metadata of the selected constant value. Metadata fields
        // will be used for filtering reference forecasts.
        var constant_value_metadata = report_utils.searchObjects(
            'forecasts', forecast);
        var constant_value = selected_constant_value.data().measurement;
        var axis = constant_value_metadata['axis'];
        var variable = constant_value_metadata['variable'];
        var interval_length = constant_value_metadata['interval_length'];
        var interval_label = constant_value_metadata['interval_label'];
        var loc = constant_value_metadata[location_key];

        // Create a filter function for removing reference forecasts that
        // dont share constant value, axis, variable, site or agg, and
        // interval length.
        var cv_filter = function(e){
            constant_values = e['constant_values'].map(function(c){
                if(c['forecast_id'] == constant_value_forecast_id){
                    return [];
                } else {
                    return c['constant_value'];
                }
            });
            return e['forecast_id'] != selected_constant_value.val()
                && e['axis'] == axis
                && e['variable'] == variable
                && e[location_key] == loc
                && e['interval_length'] == interval_length
                && e['interval_label'] == interval_label
                && constant_values.includes(constant_value);
        };
        var ref_fx = page_data['forecasts'].filter(cv_filter);
    }

    if (ref_fx.length != 0){
        // If there are matching reference forecast, insert them into the
        // reference forecast <select> element.
        reference_selector = $('#reference-forecast-select');
        ref_fx.forEach(function(fx){
            var matching_constant = fx['constant_values'].find(
                x => x['constant_value'] == constant_value);
            var forecast_id = matching_constant['forecast_id'];
            reference_selector.append(
                $('<option></option>')
                    .html(fx['name'])
                    .val(forecast_id)
                    .attr('data-site-id', fx['site_id'])
                    .attr('data-aggregate-id', fx['aggregate_id'])
                    .attr('data-interval-length', fx['interval_length'])
                    .attr('data-variable', fx['variable']));
        });
        $('#no-reference-forecasts').attr('hidden', true);
        $('#no-reference-forecast-forecast-selection').attr('hidden', true);

    } else {
        $('#no-reference-forecasts').removeAttr('hidden');
        $('#no-reference-forecast-forecast-selection').attr('hidden', true);
    }
}

function populateConstantValues(){
    /*  Fills the constant value select element with the currently selected
     *  probabilistic forecast group (distribution).
     */
    var selected_forecast_id = $('#distribution-select').val();
    var constant_value_select = $('#constant-value-select');

    var non_static_constants = constant_value_select.find('option').slice(3);
    if (selected_forecast_id){
        $("#no-constant-value-distribution-selection").attr('hidden', 'hidden');
        non_static_constants.remove();

        var forecast = report_utils.searchObjects('forecasts', selected_forecast_id);
        var cv_label = x => report_utils.constant_value_label(forecast, x)
        var constant_values = forecast['constant_values'];
        constant_values.forEach(function(constant_value){
            let option = $('<option></option')
                .attr('value', constant_value['forecast_id'])
                .attr('data-measurement', constant_value['constant_value'])
                .html(cv_label(constant_value['constant_value']));
            if ((previous_constant == constant_value['constant_value'].toString()
                 && previous_units == current_units)){
                option.attr('selected', 'selected');
            }
            $('#full-cdf-group').removeAttr('hidden');
            $('#full-cdf-group').attr('selected', 'selected');
            constant_value_select.append(option);
        });

    } else {
        let selected = constant_value_select.find(':selected')[0];
        if (selected){
            previous_constant = selected.dataset['measurement'];
            previous_units = current_units;
        }
        non_static_constants.remove();
        $("#no-constant-value-distribution-selection").removeAttr('hidden');
        $('#full-cdf-group').attr('hidden', 'hidden');
        $('#full-cdf-group').removeAttr('selected');
    }
    populateReferenceForecasts();
}

function newConstantValueSelector(){
    /* Creates a Constant Value selector.
     */
    return $(
        `<div class="form-element full-width constant-value-select-wrapper">
             <label>Select a forecast</label>
            <div class="input-wrapper">
              <select id="constant-value-select" class="form-control contant-value-field name="constant-value-select" size="5">
              <option id="no-constant-value-distribution-selection" disabled> Please select a probabilistic forecast distribution.</option>
              <option id="no-constant-values" disabled hidden>No Constant Values</option>
              <option id="full-cdf-group" value ='full-cdf-group' data-measurement="full"hidden>Distribution (CRPS metric only)</option>
            </select>
            </div>
          </div>`);
}

function newSelector(field_name, depends_on=null, required=true, description="",classes=[]){
    /*
     * Returns a JQuery object containing labels and select elements for appending options to.
     * Initializes with one default and one optional select option:
     *     Always adds an option containing "No matching <field_Type>s
     *     If depends_on is provided, inserts a "Please select a <depends_on> option>
     */
    var field_type = field_name.toLowerCase().replace(/ /g, '-');
    return $(`<div class="form-element full-width ${field_type}-select-wrapper">
                <label>Select a ${field_name} ${required ? "" : "(Optional)"}</label>
                  <div class="report-field-filters"><input id="${field_type}-option-search" class="form-control half-width" placeholder="Search by ${field_name} name"/></div><br>
                <div class="selector-description">${description}</div>
                <div class="input-wrapper">
                  <select id="${field_type}-select" class="form-control ${field_type}-field ${classes.join(" ")}" name="${field_type}-select" size="5">
                  ${depends_on ? `<option id="no-${field_type}-${depends_on}-selection" disabled> Please select a ${depends_on}.</option>` : ""}
                  <option id="no-${field_type}s" disabled hidden>No matching ${field_name}s</option>
                </select>
                </div>
              </div>`);
}

function createPairSelector(){
    /*
     * Returns a JQuery object containing Forecast, Observation pair widgets to insert into the DOM
     */

    /**********************************************************************
     *
     *  Filtering Functions
     *      Callbacks for hidding/showing select list options based on the
     *      searchbars for each field and previously made selections
     *
     *********************************************************************/

    function filterSites(){
        /*
         * Filter the Site Options Via the text found in the
         * #site-option-search input.
         */
        var sites = siteSelector.find('option').slice(1);
        sites.removeAttr('hidden');

        var toHide = report_utils.searchSelect('#site-option-search', '#site-select', 1);
        if (toHide.length == sites.length){
            // No sites matched, display "no matching sites"
            $('#no-sites').removeAttr('hidden');
        } else {
            // some sites matched, hide "no matching sites" message
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
    function applyFxDependentFilters(){
        filterObservations();
        filterAggregates();
        populateConstantValues()
    }

    function filterForecasts(){
        /*
         * Hide options in the forecast selector based on the currently selected
         * site and variable.
         */
        // Show all Forecasts
        var forecasts = $('#distribution-select option').slice(2);
        forecasts.removeAttr('hidden');

        var toHide = report_utils.searchSelect(
            '#distribution-option-search',
            '#distribution-select', 2);
        variable_select = $('#variable-select');
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
                $('#no-distribution-site-selection').attr('hidden', true);
            } else {
                $('#no-distribution-site-selection').removeAttr('hidden');
            }
            toHide = toHide.add(forecasts.not(`[data-site-id=${site_id}]`));
        } else {
            // Forecasts are made for an aggregate directly, so we will use
            // the forecast to filter aggregates, instead of vice versa
            toHide = toHide.add(forecasts.not('[data-aggregate-id]'));
            $('#no-distribution-site-selection').attr('hidden', true);
        }

        // if current forecast selection is invalid, deselect
        if (toHide.filter(':selected').length){
            forecast_select.val('');
            populateConstantValues();
        }
        toHide.attr('hidden', 'true');

        // if all options are hidden, show "no matching forecasts"
        if (toHide.length == forecasts.length){
            forecast_select.val('');
            if ($('#no-distribution-site-selection').attr('hidden') || compareTo == 'aggregate'){
                $('#no-distributions').removeAttr('hidden');
            }
        } else {
            $('#no-distributions').attr('hidden', true);
            report_utils.restore_prev_value(previous_reference_forecast);
        }
        populateReferenceForecasts();
        if (compareTo == 'observation'){
            filterObservations();
        } else {
            filterAggregates();
        }
    }

    function filterAggregates(){
        /*
         * Filter aggregate options based on radio buttons
         */
        var aggregates = aggregateSelector.find('option').slice(2);
        aggregates.removeAttr('hidden');
        var selectedForecast = $('#distribution-select :selected');

        if (selectedForecast.length){
            var aggregate_id = selectedForecast.data('aggregate-id');
            //
            // hide aggregates based on search field
            var toHide = report_utils.searchSelect(
                '#aggregate-option-search', '#aggregate-select', 1);

            // hide aggregates that are not referenced by the forecast
            toHide = toHide.add(aggregates.not(`[data-aggregate-id=${aggregate_id}]`));

            // hide aggregates with longer interval_lengeth
            var current_interval = selectedForecast.data('interval-length');
            toHide = toHide.add(aggregates.filter(function(){
                return parseInt(this.dataset['intervalLength']) > current_interval;
            }));

            // if all aggregates are hidden, display "no matching aggregates,
            // else ensure the message is hidden
            if ((toHide.length == aggregates.length) && aggregate_id){
                $('#no-aggregates').removeAttr('hidden');
            } else {
                $('#no-aggregates').attr('hidden', true);
            }
            $('#no-aggregate-distribution-selection').attr('hidden', true);
        } else {
            // If no forecast is selected, hide all aggregates.
            var toHide = aggregates;
            $('#no-aggregate-distribution-selection').removeAttr('hidden');
        }
        toHide.attr('hidden', true);
    }

    function filterObservations(){
        /* Filter list of observations based on current site and variable.
         */
        var observations = $('#observation-select option').slice(2);
        // get the attributes of the currently selected forecast
        var selectedForecast = $('#distribution-select :selected');
        if (selectedForecast.length){
            // Show all of the observations
            observations.removeAttr('hidden');
            //
            // retrieve the current site id and variable from the selected forecast
            var site_id = selectedForecast.data('site-id');
            var variable = selectedForecast.data('variable');
            $('#no-observation-distribution-selection').attr('hidden', true);

            // Build the list of optiosn to hide by creating a set from
            // the lists of elements to hide from search, site id and variable
            var toHide = report_utils.searchSelect(
                '#observation-option-search', '#observation-select', 2);
            toHide = toHide.add(observations.not(`[data-site-id=${site_id}]`));
            toHide = toHide.add(observations.not(`[data-variable=${variable}]`));

            // Hide Observations with longer interval lengths
            var current_interval = selectedForecast.data('interval-length');
            toHide = toHide.add(observations.filter(function(){
                return parseInt(this.dataset['intervalLength']) > current_interval
            }));

            toHide.attr('hidden', true);

            // if the current selection is hidden, deselect it
            if (toHide.filter(':selected').length){
                observation_select.val('');
            }

            // if all observations are hidden, display a "no matching obs"
            // message, else ensure it is hidden.
            if (toHide.length == observations.length){
                $('#no-observations').removeAttr('hidden');
            } else {
                $('#no-observations').attr('hidden', true);
                report_utils.restore_prev_value(previous_observation);
            }
        } else {
            observations.attr('hidden', true);
            $('#no-observation-distribution-selection').removeAttr('hidden');
        }
    }

    /**********************************************************************
     *
     * Create the control elements for creating observation, forecast pairs
     *
     *********************************************************************/
    var siteSelector = newSelector("site");
    var aggregateSelector = newSelector("aggregate", "distribution",);
    var obsSelector = newSelector("observation", "distribution");
    var fxSelector = newSelector(
        "distribution", "site", required=true,
        description=`
            The Solar Forecast Arbiter supports the specification of
            probabilistic forecasts in terms of a cumulative distribution
            function (CDF). First select, the distribution of interest.
            Second, select the portion of the distribution to be evaluated.
            Select Distribution to calculate the
            <a href="https://solarforecastarbiter.org/metrics/#crps">CRPS</a>
            metric for the entire forecast distribution. Select a forecast
            for a portion of the distribution to calculate binary metrics
            for each forecast.`
    );

    var refFxSelector = newSelector(
        "reference forecast", "forecast", required=false,
        description='Skill metrics will be calculated for any binary forecasts matching the selection above.');
    refFxSelector.append(
        $('<a role="button" id="ref-clear">Clear reference forecast selection</a>').click(
            function(){$('#reference-forecast-select').val('')})
    );

    var dbSelector = report_utils.deadbandSelector();
    var constantValueSelector = newConstantValueSelector();
    var fxVariableSelector = report_utils.createVariableSelect();

    // Create a radio button for selecting between aggregate or observation
    var obsAggRadio = $(
      `<div><b>Compare Forecast to&colon;</b>
         <input type="radio" name="observation-aggregate-radio" value="observation" checked> Observation
         <input type="radio" name="observation-aggregate-radio" value="aggregate">Aggregate<br/></div>`);

    // Create two buttons that act on the set of observation or aggregate
    // fields independently, these should be shown/hidden when the obs
    var addObsButton = $('<a role="button" class="btn btn-primary" id="add-obs-object-pair" style="padding-left: 1em">Add a Forecast, Observation pair</a>');

    var addAggButton = $('<a role="button" class="btn btn-primary" id="add-agg-object-pair" style="padding-left: 1em">Add a Forecast, Aggregate pair</a>');


    /**********************************************************************
     *
     * Create a container for the html inputs, widgetContainer, and append
     * all of the inputs needed.
     *
     *********************************************************************/
    var widgetContainer = $('<div class="pair-selector-wrapper collapse"></div>');
    widgetContainer.append(obsAggRadio);
    widgetContainer.append(siteSelector);
    widgetContainer.append(fxSelector);
    widgetContainer.append(constantValueSelector);
    widgetContainer.append(refFxSelector);
    widgetContainer.append(obsSelector);
    widgetContainer.append(aggregateSelector);
    widgetContainer.append(dbSelector);
    widgetContainer.append(addObsButton);
    widgetContainer.append(addAggButton);

    fxSelector.find('.report-field-filters').append(fxVariableSelector);

    /**********************************************************************
     *
     * Hide all of the Aggregate controls by default because we default to
     * compare to: observation.
     *
     *********************************************************************/
    addAggButton.attr('hidden', true);
    aggregateSelector.attr('hidden', true);


    /**********************************************************************
     *
     * Register call backs for searching and filtering on user input. These
     * correspond with the "Search by <field>" input, and the variable
     * selector.
     *
     *********************************************************************/
    siteSelector.find('#site-option-search').keyup(filterSites);
    obsSelector.find('#observation-option-search').keyup(filterObservations);
    fxSelector.find('#distribution-option-search').keyup(filterForecasts);
    fxSelector.find('#reference-forecast-option-search').keyup(filterForecasts);
    aggregateSelector.find('#aggregate-option-search').keyup(filterAggregates);

    /**********************************************************************
     *
     * Create jquery handles to all of the inputs we've created pertaining
     * to observation, forecast pair creation.
     *
     *********************************************************************/
    var observation_select = obsSelector.find('#observation-select');
    var forecast_select = fxSelector.find('#distribution-select');
    var constant_value_select = constantValueSelector.find('#constant-value-select')
    var ref_forecast_select = refFxSelector.find('#reference-forecast-select');
    var site_select = siteSelector.find('#site-select');
    var aggregate_select = aggregateSelector.find('#aggregate-select');

    var radio_inputs = obsAggRadio.find('input[type=radio]');

    /**********************************************************************
     *
     * Register onchange callbacks for the pair selection widgets.
     *
     *********************************************************************/
    radio_inputs.change(determineWidgets);
    site_select.change(filterForecasts);
    variable_select.change(filterForecasts);
    forecast_select.change(applyFxDependentFilters);

    forecast_select.change(populateConstantValues);
    constant_value_select.change(populateReferenceForecasts);

    observation_select.change(report_utils.store_prev_observation);
    ref_forecast_select.change(report_utils.store_prev_reference_forecast);

    /**********************************************************************
     *
     * Populate options from the page_data variable
     *
     *********************************************************************/
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
        if (observation_select.val() && constant_value_select.val()){
            // If both inputs contain valid data, create a pair and add it to the DOM
            var selected_observation = observation_select.find(':selected')[0];
            var selected_forecast = forecast_select.find(':selected')[0];
            var selected_reference_forecast = ref_forecast_select.find(':selected')[0];
            if(!selected_reference_forecast){
                ref_text = "Unset";
                ref_id = null;
            }else{
                ref_text = selected_reference_forecast.text;
                ref_id = selected_reference_forecast.value;
            }
            // try to parse deadband values
            try{
                deadband_values = report_utils.parseDeadband();
            }catch(error){
                return;
            }
            constant_value_select.find('option:selected').each(function(){
                let forecast_id = $(this).val();
                let forecast = report_utils.searchObjects(
                    'forecasts', selected_forecast.value);
                let forecast_name = forecast['name'];
                let forecast_type = 'probabilistic_forecast';
                let constant_value_label = "Distribution";
                let distribution_id = selected_forecast.value;
                if (forecast_id == 'full-cdf-group'){
                    forecast_id = selected_forecast.value;
                } else {
                    let constant_value = $(this).data('measurement');
                    forecast_type = 'probabilistic_forecast_constant_value';
                    constant_value_label = report_utils.constant_value_label(
                        forecast, constant_value);
                    forecast_id = $(this).val();
                }
                addPair(
                    'observation',
                    selected_observation.text,
                    selected_observation.value,
                    forecast_name,
                    forecast_id,
                    ref_text,
                    ref_id,
                    deadband_values[0],
                    deadband_values[1],
                    forecast_type,
                    constant_value_label,
                    distribution_id,
                )
            });

            var variable = selected_forecast.dataset.variable;
            report_utils.set_units(variable, filterForecasts);
            $(".empty-reports-list").attr('hidden', 'hidden');
            forecast_select.css('border', '');
            observation_select.css('border', '');
            constant_value_select.css('border', '');
            report_utils.toggle_reference_dependent_metrics();
        } else {
            // Otherwise apply a red border to alert the user to need of input
            if (forecast_select.val() == null){
                forecast_select.css('border', '2px solid #F99');
            }
            if (constant_value_select.val() == null){
                constant_value_select.css('border', '2px solid #F99');
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
        if (aggregate_select.val() && constant_value_select.val()){
            var selected_aggregate = aggregate_select.find('option:selected')[0];
            var selected_forecast = forecast_select.find('option:selected')[0];
            var selected_reference_forecast = ref_forecast_select.find('option:selected')[0];
            if(!selected_reference_forecast){
                ref_text = "Unset";
                ref_id = null;
            }else{
                ref_text = selected_reference_forecast.text;
                ref_id = selected_reference_forecast.value;
            }
            constant_value_select.find('option:selected').each(function(){
                let forecast_id = $(this).val();
                let forecast = report_utils.searchObjects(
                    'forecasts', selected_forecast.value);
                let forecast_name = forecast['name'];
                let forecast_type = 'probabilistic_forecast_constant_value';
                let constant_value_label = "Distribution";
                let distribution_id = selected_forecast.value;
                if (forecast_id == 'full-cdf-group'){
                    forecast_id = selected_forecast;
                    forecast_type = 'probabilistic_forecast';
                } else {
                    let constant_value = $(this).data('measurement');
                    constant_value_label = report_utils.constant_value_label(
                        forecast, constant_value);
                    forecast_id = selected_forecast['forecast_id'];
                }
                addPair(
                    'aggregate',
                    selected_aggregate.text,
                    selected_aggregate.value,
                    forecast_name,
                    forecast_id,
                    ref_text,
                    ref_id,
                    "Unset",
                    null,
                    forecast_type,
                    constant_value_label,
                    distribution_id,
                );
            });
            var variable = selected_forecast.dataset.variable;
            report_utils.set_units(variable, filterForecasts);

            $(".empty-reports-list")[0].hidden = true;
            forecast_select.css('border', '');
            aggregate_select.css('border', '');
            constant_value_select.css('border', '');
            report_utils.toggle_reference_dependent_metrics();
        } else {
            // Otherwise apply a red border to alert the user to need of input
            if (forecast_select.val() == null){
                forecast_select.css('border', '2px solid #F99');
            }
            if (constant_value_select.val() == null){
                constant_value_select.css('border', '2px solid #F99');
            }
            if (aggregate_select.val() == null){
                aggregate_select.css('border', '2px solid #F99');
            }
        }

    });
    return widgetContainer;
}

function unpack_constant_values(){
    let constant_values = [];
    page_data['forecasts'].forEach(function(forecast){
        forecast['constant_values'].forEach(function(constant){
            let constant_metadata = Object.assign({}, forecast);
            constant_metadata['constant_value'] = constant['constant_value'];
            constant_metadata['parent'] = forecast['forecast_id']
            constant_metadata['forecast_id'] = constant['forecast_id'];
            delete constant_metadata.constant_values;
            constant_values.push(constant_metadata);
        });
    });
    page_data['constant_values'] = constant_values;
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
    report_utils.registerDatetimeValidator('period-end');
    unpack_constant_values();
    report_utils.fill_existing_pairs();
    report_utils.register_uncertainty_handler('#observation-select');
    report_utils.register_forecast_fill_method_validator('probabilistic');
});
