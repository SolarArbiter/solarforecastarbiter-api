/*
 *  Creates inputs for defining observation, forecast pairs for a report.
 */
$(document).ready(function() {
    function registerDatetimeValidator(input_name){
        /*
         * Applies a regex validator to ensure ISO8601 compliance. This is however, very strict. We
         * will need a better solution.
         */
        $(`[name="${input_name}"]`).keyup(function (){
            if($(`[name="${input_name}"]`).val().match(
                  /(\d{4})-(\d{2})-(\d{2})T(\d{2})\:(\d{2})\Z/
            )) {
                  $(`[name="${input_name}"]`)[0].setCustomValidity("");
            } else {
                  $(`[name="${input_name}"]`)[0].setCustomValidity('Please enter a datetime in the format "YYYY-MM-DDTHH:MMZ');
            }
        });
    }


    function createVariableSelect(){
        /*
         * Returns a JQuery object containing a select list of variable options.
         */
        var_names = {
            'air_temperature': 'Air Temperature',
            'wind_speed': 'Wind Speed',
            'ghi': 'GHI',
            'dni': 'DNI',
            'dhi': 'DHI',
            'poa_global': 'Plane of Array Irradiance',
            'relative_humidity': 'Relative Humidty',
            'ac_power': 'AC Power',
            'dc_power': 'DC Power',
            'availability': 'Availability',
            'curtailment': 'Curtailment'
        }
        variables = new Set();
        for (fx in page_data['forecasts']){
            variables.add(page_data['forecasts'][fx].variable);
        }
        variable_select = $('<select id="variable-select" class="form-control half-width"><option selected value>All Variables</option></select>');
        variables.forEach(function(variable){
            variable_select.append(
                $('<option></option>')
                    .html(var_names[variable])
                    .val(variable));
        });
        return variable_select
    }

    function searchSelect(inputSelector, selectSelector, offset=0){
        /*
         * Retrieves the value the <input> element identified by inputSelector and
         * returns a jquery list of the <option> elements inside the element
         * identified by selectSelector that do not contain the value.
         * Passing an offset ignores the first offset items.
         */
        var searchTerm = $(inputSelector).val();
        var searchSplit = searchTerm.replace(/ /g, "'):containsi('");
        return $(selectSelector + " option").slice(offset).not(":containsi('" + searchSplit + "')");
    }

    function addPair(truthType, truthName, truthId, fxName, fxId){
        /*
         * Returns a Jquery object containing 5 input elements representing a forecast,
         * observation pair:
         *  forecast-name-<index>
         *  forecast-id-<index>
         *  truth-name-<indeX>
         *  truth-id-<indeX>
         *  truth-type-<index>
         *  where index associates the pairs with eachother for easier parsing when the form
         *  is submitted.
         */
        var new_object_pair = $(`<div class="object-pair object-pair-${pair_index}">
                <div class="input-wrapper">
                  <div class="col-md-6">
                    <input type="text" class="form-control forecast-field" name="forecast-name-${pair_index}" required disabled value="${fxName}"/>
                    <input type="hidden" class="form-control forecast-field" name="forecast-id-${pair_index}" required value="${fxId}"/>
                  </div>
                  <div class="col-md-6">
                    <input type="text" class="form-control truth-field" name="truth-name-${pair_index}"  required disabled value="${truthName}"/>
                    <input type="hidden" class="form-control truth-field" name="truth-id-${pair_index}" required value="${truthId}"/>
                    <input type="hidden" class="form-control truth-field" name="truth-type-${pair_index}" required value="${truthType}"/>
                  </div>
                 </div>
                 <a role="button" class="object-pair-delete-button">x</a>
               </div>`);
        var remove_button = new_object_pair.find(".object-pair-delete-button");
        remove_button.click(function(){
            new_object_pair.remove();
            if ($('.object-pair-list .object-pair').length == 0){
                $('.empty-reports-list')[0].hidden = false;
            }
        });
        return new_object_pair;
    }


    function newSelector(field_type, depends_on=null){
        /*
         * Returns a JQuery object containing labels and select elements for appending options to.
         * Initializes with one default and one optional select option:
         *     Always adds an option containing "No matching <field_Type>s
         *     If depends_on is provided, inserts a "Please select a <depends_on> option>
         */
        return $(`<div class="form-element full-width ${field_type}-select-wrapper">
                    <label>Select a ${field_type}</label>
                      <div class="report-field-filters"><input id="${field_type}-option-search" class="form-control half-width" placeholder="Search by ${field_type} name"/></div><br>
                    <div class="input-wrapper">
                      <select id="${field_type}-select" class="form-control ${field_type}-field" name="${field_type}-select" size="5">
                      ${depends_on ? `<option id="no-${field_type}-${depends_on}-selection" disabled> Please select a ${depends_on}.</option>` : ""}
                      <option id="no-${field_type}s" disabled hidden>No matching ${field_type}s</option>
                    </select>
                    </div>
                  </div>`);
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
            sites = siteSelector.find('option').slice(1);
            sites.removeAttr('hidden');

            toHide = searchSelect('#site-option-search', '#site-select', 1);
            if (toHide.length == sites.length){
                $('#no-sites').removeAttr('hidden');
            } else {
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
            compareTo = $(`[name=observation-aggregate-radio]:checked`).val();
            if (compareTo == 'observation'){
                // hide aggregates
                // show sites & observations
                $('.aggregate-select-wrapper').attr('hidden', true);
                $('.site-select-wrapper').removeAttr('hidden');
                $('.observation-select-wrapper').removeAttr('hidden');
                $('#aggregate-select').val('');
                $("#add-obs-object-pair").removeAttr('hidden');
                $("#add-agg-object-pair").attr('hidden', true);
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
            forecasts = $('#forecast-select option').slice(2);
            forecasts.removeAttr('hidden');

            toHide = searchSelect('#forecast-option-search', '#forecast-select', 2);
            variable_select = $('#variable-select');
            variable = variable_select.val();
            if (variable){
                toHide = toHide.add(forecasts.not(`[data-variable=${variable}]`));
            }
            // Determine if we need to filter by site or aggregate
            compareTo = $(`[name=observation-aggregate-radio]:checked`).val();
            if (compareTo == 'observation'){
                selectedSite = $('#site-select :selected');
                site_id = selectedSite.data('site-id');
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
                //
                if ($('#no-forecast-site-selection').attr('hidden') || compareTo == 'aggregate'){
                    $('#no-forecasts').removeAttr('hidden');
                }
            } else {
                $('#no-forecasts').attr('hidden', true);
            }
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
            aggregates = aggregateSelector.find('option').slice(2);
            aggregates.removeAttr('hidden');
            selectedForecast = $('#forecast-select :selected');
            if (selectedForecast.length){
                aggregate_id = selectedForecast.data('aggregate-id');
                toHide = searchSelect('#aggregate-option-search', '#aggregate-select', 1);
                toHide = toHide.add(aggregates.not(`[data-aggregate-id=${aggregate_id}]`));
                current_interval = selectedForecast.data('interval-length');
                toHide = toHide.add(aggregates.filter(function(){
                    return parseInt(this.dataset['intervalLength']) > current_interval;
                }));
                if ((toHide.length == aggregates.length) && aggregate_id){
                    $('#no-aggregates').removeAttr('hidden');
                } else {
                    $('#no-aggregates').attr('hidden', true);
                }
                $('#no-aggregate-forecast-selection').attr('hidden', true);
            } else {
                toHide = aggregates;
                $('#no-aggregate-forecast-selection').removeAttr('hidden');
            }
            toHide.attr('hidden', true);
        }

        function filterObservations(){
            observations = $('#observation-select option').slice(2);
            // get the attributes of the currently selected forecast
            selectedForecast = $('#forecast-select :selected');
            if (selectedForecast.length){
                // Show all of the observations
                observations.removeAttr('hidden');
                // retrieve the current site id and variable from the selected forecast
                site_id = selectedForecast.data('site-id');
                variable = selectedForecast.data('variable');
                $('#no-observation-forecast-selection').attr('hidden', true);

                // Build the list of optiosn to hide by creating a set from
                // the lists of elements to hide from search, site id and variable
                var toHide = searchSelect('#observation-option-search', '#observation-select', 2);
                toHide = toHide.add(observations.not(`[data-site-id=${site_id}]`));
                toHide = toHide.add(observations.not(`[data-variable=${variable}]`));
                current_interval = selectedForecast.data('interval-length');
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
                }
            } else {
                observations.attr('hidden', true);
                $('#no-observation-forecast-selection').removeAttr('hidden');
            }
        }

        // Declare handles to each field's input widgets, and insert a variable select
        // widget for Forecast filtering.
        var widgetContainer = $('<div class="pair-selector-wrapper collapse"></div>');
        var aggregateSelector = newSelector("aggregate", "forecast");
        var siteSelector = newSelector("site");
        var obsSelector = newSelector("observation", "forecast");
        var fxSelector = newSelector("forecast", "site");
        var fxVariableSelector = createVariableSelect();
        fxSelector.find('.report-field-filters').append(fxVariableSelector);
        var addObsButton = $('<a role="button" class="btn btn-primary" id="add-obs-object-pair" style="padding-left: 1em">Add a Forecast, Observation pair</a>');
        var addAggButton = $('<a role="button" class="btn btn-primary" id="add-agg-object-pair" style="padding-left: 1em">Add a Forecast, Aggregate pair</a>');


        // Radio button for selecting between an aggregate or site
        var obsAggRadio = $(`<div><b>Compare Forecast to&colon;</b>
                             <input type="radio" name="observation-aggregate-radio" value="observation" checked> Observation
                             <input type="radio" name="observation-aggregate-radio" value="aggregate">Aggregate<br/></div>`);
        widgetContainer.append(obsAggRadio);
        radio_inputs = obsAggRadio.find('input[type=radio]');
        radio_inputs.change(determineWidgets);

        // Add the elements to the widget Container, so that the single container may
        // be inserted into the DOM
        widgetContainer.append(siteSelector);
        widgetContainer.append(fxSelector);
        widgetContainer.append(obsSelector);
        widgetContainer.append(aggregateSelector);
        widgetContainer.append(addObsButton);
        widgetContainer.append(addAggButton);

        // hide aggregate controls by default
        addAggButton.attr('hidden', true);
        aggregateSelector.attr('hidden', true);

        // Register callback functions
        siteSelector.find('#site-option-search').keyup(filterSites);
        obsSelector.find('#observation-option-search').keyup(filterObservations);
        fxSelector.find('#forecast-option-search').keyup(filterForecasts);
        aggregateSelector.find('#aggregate-option-search').keyup(filterAggregates);

        // create variables pointing to the specific select elements
        var observation_select = obsSelector.find('#observation-select');
        var forecast_select = fxSelector.find('#forecast-select');
        var site_select = siteSelector.find('#site-select');
        var aggregate_select = aggregateSelector.find('#aggregate-select');
        
        site_select.change(filterForecasts);
        variable_select.change(filterForecasts);
        forecast_select.change(filterObservations);
        forecast_select.change(filterAggregates);

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
            forecast_select.append(
                $('<option></option>')
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
                pair = addPair('observation',
                               selected_observation.text,
                               selected_observation.value,
                               selected_forecast.text,
                               selected_forecast.value);

                pair_container.append(pair);
                pair_index++;
                $(".empty-reports-list")[0].hidden = true;
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
        addAggButton.click(function(){
            /*
             * Add a forecast, aggregate pair
             */
            if (aggregate_select.val() && forecast_select.val()){
                var selected_aggregate = aggregate_select.find('option:selected')[0];
                var selected_forecast = forecast_select.find('option:selected')[0];
                pair = addPair('aggregate',
                               selected_aggregate.text,
                               selected_aggregate.value,
                               selected_forecast.text,
                               selected_forecast.value);
                pair_container.append(pair);
                pair_index++;
                $(".empty-reports-list")[0].hidden = true;
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
    pair_control_container.append($('<a role="button" class="full-width object-pair-button collapsed" data-toggle="collapse" data-target=".pair-selector-wrapper">Create Forecast Evaluation pairs</a>'));
    pair_control_container.append(pair_selector);
    registerDatetimeValidator('period-start');
    registerDatetimeValidator('period-end')
});
