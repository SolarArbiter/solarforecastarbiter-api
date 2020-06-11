/*
 *  Creates inputs for defining observation, forecast pairs for a report.
 */
$(document).ready(function() {
    function searchObjects(object_type, object_id){
        /* Get a json object from the page_data object.
         *
         * @param {string} object_type - The type of the object to search for.
         *     One of 'forecasts', 'sites', 'observations' 
         *
         * @param {string} object_id - UUID of the object to search for
         *
         * @returns {Object} An object containing the SFA object's metadata.
         */
        try{
            var objects = page_data[object_type];
            var id_prop = object_type.slice(0, -1) + '_id';
            var metadata = objects.find(e => e[id_prop] == object_id);
        }catch(error){
            return null;
        }
        return metadata;
    }

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

    function applyFxDependentFilters(){
        filterObservations();
    }

    function addPair(
        truthType, truthName, truthId, fxName, fxId, db_label, db_value,
        forecast_type='event_forecast'){
        /*
         * Returns a Jquery object containing 5 input elements representing a forecast,
         * observation pair:
         *  forecast-name-<index>
         *  forecast-id-<index>
         *  truth-name-<indeX>
         *  truth-id-<indeX>
         *  truth-type-<index>
         *  db_label,
         *  db_value,
         *  where index associates the pairs with eachother for easier parsing when the form
         *  is submitted.
         */
        var new_object_pair = $(`<div class="object-pair pair-container object-pair-${pair_index}">
                <div class="input-wrapper">
                  <div class="col-md-12">
                    <div class="object-pair-label forecast-name-${pair_index}"><b>Forecast: </b>${fxName}</div>
                    <input type="hidden" class="form-control forecast-value" name="forecast-id-${pair_index}" required value="${fxId}"/>
                    <div class="object-pair-label truth-name-${pair_index}"><b>Observation: </b> ${truthName}</div>
                    <input type="hidden" class="form-control truth-value" name="truth-id-${pair_index}" required value="${truthId}"/>
                    <input type="hidden" class="form-control truth-type-value" name="truth-type-${pair_index}" required value="${truthType}"/>
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
        return new_object_pair;
    }


    function newSelector(field_name, depends_on=null, required=true){
        /*
         * Returns a JQuery object containing labels and select elements for appending options to.
         * Initializes with one default and one optional select option:
         *     Always adds an option containing "No matching <field_Type>s
         *     If depends_on is provided, inserts a "Please select a <depends_on> option>
         */
        var field_type = field_name.toLowerCase().replace(' ', '-');
        return $(`<div class="form-element full-width ${field_type}-select-wrapper">
                    <label>Select a ${field_name} ${required ? "" : "(Optional)"}</label>
                      <div class="report-field-filters"><input id="${field_type}-option-search" class="form-control half-width" placeholder="Search by ${field_name} name"/></div><br>
                    <div class="input-wrapper">
                      <select id="${field_type}-select" class="form-control ${field_type}-field" name="${field_type}-select" size="5">
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

        function filterForecasts(){
            /*
             * Hide options in the forecast selector based on the currently selected
             * site and variable.
             */
            // Show all Forecasts
            forecasts = $('#forecast-select option').slice(2);
            forecasts.removeAttr('hidden');

            toHide = searchSelect('#forecast-option-search', '#forecast-select', 2);
            variable = "event";
            toHide = toHide.add(forecasts.not(`[data-variable=${variable}]`));
            selectedSite = $('#site-select :selected');
            site_id = selectedSite.data('site-id');
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
            observations = $('#observation-select option').slice(2);
            // get the attributes of the currently selected forecast
            selectedForecast = $('#forecast-select :selected');
            if (selectedForecast.length){
                // Show all of the observations
                observations.removeAttr('hidden');
                // retrieve the current site id and variable from the selected forecast
                site_id = selectedForecast.data('site-id');
                variable = "event";
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

        /*
         * Create select widgets for creating an observatio/forecast pair, 
         */
        var siteSelector = newSelector("site");
        var obsSelector = newSelector("observation", "forecast");
        var fxSelector = newSelector("forecast", "site");

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
                pair = addPair('observation',
                               selected_observation.text,
                               selected_observation.value,
                               selected_forecast.text,
                               selected_forecast.value,
                );
                pair_container.append(pair);
                pair_index++;
                var variable = "event";
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
    registerDatetimeValidator('period-start');
    registerDatetimeValidator('period-end')
});


function insertErrorMessage(title, msg){
    $('#form-errors').append(`<li class="alert alert-danger"><p><b>${title}: </b>${msg}</p></li>`);
}
function validateReport(){
    /*
     * Callback before the report form is submitted. Any js validation should
     * occur here.
     */
    // remove any existing errors
    $('#form-errors').empty();
    var errors = 0;
    // assert at least one pair was selected.
    if($('.object-pair').length == 0){
        insertErrorMessage(
            "Analysis Pairs",
            "Must specify at least one Observation, Forecast pair.");
        errors++;
    }
    if (errors){
       return false;
    }
}
