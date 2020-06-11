/*
 *  Creates inputs for defining observation, forecast pairs for a report.
 */

var previous_constant = null;
$(document).ready(function() {
    function toggle_reference_dependent_metrics(){
        /*
         * Disables and de-selects the forecast skill metric if not all of the
         * object pairs have reference foreasts.
         */
        var nulls_exist = $('.reference-forecast-value').map(function(){return $(this).val()}).get().some(x=>x=='null');
        var skill = $('[name=metrics][value=s]'); 
        if(nulls_exist){
            // hide skill, insert warning
            skill.attr('disabled', true);
            if($('#reference-warning').length == 0){
                $(`<span id="reference-warning" class="warning-message">
                   (Requires reference forecast selection)</span>`
                 ).insertAfter(skill.next());
            }
            if(skill.is(':checked')){
                skill.removeAttr('checked');
            }
        }else{
            // show skill remove warning
            skill.removeAttr('disabled');
            $('#reference-warning').remove();
        }
    }
    function searchObjects(object_type, object_id){
        /* Get a json object from the page_data object.
         *
         * @param {string} object_type - The type of the object to search for.
         *     One of 'forecasts', 'sites', 'observations', 'aggregates'.
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
    
    var current_units = null;
    
    function unset_units(){
        /* Set units to null when the last pair is removed */
        current_units = null;
        setVariables()
    }

    function set_units(variable){
        units = sfa_dash_config.VARIABLE_UNIT_MAP[variable];
        if(units){
            current_units = units;
        }
        setVariables();
    }


    function setVariables(){
        variable_options = $('#variable-select option');
        variable_options.removeAttr('hidden');
        variable_options.removeAttr('disabled');
        if (current_units){
            variable_options.each(function(){
                units = sfa_dash_config.VARIABLE_UNIT_MAP[$(this).attr('value')]
                if(units != current_units){
                    $(this).attr('hidden', true);
                    $(this).attr('disabled', true);
                }
            });
        }
        $('#variable-select').val(variable_options.filter(":not([hidden])").val());
    }
    function changeVariable(){
        setVariables(); 
        filterForecasts();
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


    function createVariableSelect(){
        /*
         * Returns a JQuery object containing a select list of variable options.
         */
        variables = new Set();
        for (fx in page_data['forecasts']){
            var new_var = page_data['forecasts'][fx].variable;
            if (!current_units ||
                sfa_dash_config.VARIABLE_UNIT_MAP[new_var] == current_units ||
                !sfa_dash_config.VARIABLE_UNIT_MAP[new_var]){
                variables.add(page_data['forecasts'][fx].variable);
            }
        }
        variable_select = $('<select id="variable-select" class="form-control half-width"><option selected value>All Variables</option></select>');
        variables.forEach(function(variable){
            variable_select.append(
                $('<option></option>')
                    .html(sfa_dash_config.VARIABLE_NAMES[variable])
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

    

    function pairWrapper(truthType, truthId, truthName, fxId, fxName,
                         ref_fxName, db_label, db_value, distribution_id){
        if (truthType == 'observation'){
            truth_label = 'Observation';
        } else {
            truth_label = 'Aggregate';
        }
        // create a container for the pair
        container = $(`
          <div class="object-pair pair-container" data-truth-id="${truthId}" data-fx-id="${distribution_id}" data-deadband-value="${db_value}">
            <div class="col-md-12 pair-metadata">
            </div>
            <hr>
            <ul class="col-md-12 pair-constant-values">
            </ul>
          </div>`);
        // <div class="input-wrapper"></div>?
        meta_block = container.find('.pair-metadata');
        meta_block.append($('<div></div>')
            .addClass('object-pair-label')
            .addClass('forecast-name')
            .html(`<b>Forecast: </b>${fxName}`));
        meta_block.append($('<div></div>')
            .addClass('object-pair-label')
            .addClass('truth-name')
            .html(`<b>${truth_label}: </b> ${truthName}`));

        meta_block.append($('<div></div>')
            .addClass('object-pair-label')
            .addClass('deadband-label')
            .html(`<b>Uncertainty: </b> ${db_label}`));

        container.append('<a role="button" class="object-pair-delete-button">remove</a>')
        var remove_button = container.find(".object-pair-delete-button");
        remove_button.click(function(){
            container.remove();
            if ($('.object-pair-list .object-pair').length == 0){
                $('.empty-reports-list')[0].hidden = false;
                unset_units();
            }
            toggle_reference_dependent_metrics();
        });
        return container;
    }

    function addPair(
        truthType, truthName, truthId, fxName, fxId, ref_fxName, ref_fxId,
        db_label, db_value, constant_value, distribution_id,
        forecast_type='probabilistic_forecast'){
        /*
         * Returns a Jquery object containing 5 input elements representing a forecast,
         * observation pair:
         *  forecast-name-<index>
         *  forecast-id-<index>
         *  truth-name-<indeX>
         *  truth-id-<indeX>
         *  truth-type-<index>
         *  ref_fxName,
         *  ref_fxId,
         *  db_label,
         *  db_value,
         *  where index associates the pairs with eachother for easier parsing when the form
         *  is submitted.
         */
        new_container = false;

        if (forecast_type=='probabilistic_forecast'){
            $('[name="metrics"][value="crps"]').attr('checked', true);
        }
        // Check for the parent pair container that groups object_pairs
        // with similar observations, forecasts and uncertainties
        var pair_container = $(`
            .pair-container[data-truth-id=${truthId}][data-fx-id=${distribution_id}][data-deadband-value="${db_value}"]`);
        if (pair_container.length == 0){
            pair_container = pairWrapper(
                truthType, truthId, truthName, fxId, fxName, ref_fxName,
                db_label, db_value, distribution_id);
            new_container = true;
        }
        var constant_values = pair_container.find('.pair-constant-values');
        if (constant_value){
            fxName = `${fxName} (${constant_value})`
        }

        var constant_value_pair = $(`<li class="object-pair object-pair-${pair_index}">
            <div class="constant-value-label">${constant_value}</div>
            <div class="object-pair-label reference-forecast-name"><b>Reference Forecast: </b> ${ref_fxName}</div>
            <input type="hidden" class="forecast-value" name="forecast-id-${pair_index}" required value="${fxId}"/>
            <input type="hidden" class="truth-value" name="truth-id-${pair_index}" required value="${truthId}"/>
            <input type="hidden" class="truth-type-value" name="truth-type-${pair_index}" required value="${truthType}"/>
            <input type="hidden" class="reference-forecast-value" name="reference-forecast-${pair_index}" required value="${ref_fxId}"/>
            <input type="hidden" class="deadband-value" name="deadband-value-${pair_index}" required value="${db_value}"/>
            <input type="hidden" class="forecast-type-value" name="forecast-type-${pair_index}" required value="${forecast_type}"/>
        </li>`);

        constant_value_pair.append('<a role="button" class="object-pair-delete-button">remove</a>')
        var remove_button = constant_value_pair.find(".object-pair-delete-button");
        remove_button.click(function(){
            constant_value_pair.remove();
            if (constant_values.find('li').length == 0){
                pair_container.remove();
            }
            if ($('.object-pair-list .object-pair').length == 0){
                $('.empty-reports-list')[0].hidden = false;
                unset_units();
            }
            toggle_reference_dependent_metrics();
        });
        constant_values.append(constant_value_pair);
        if (new_container){
            $('.object-pair-list').append(pair_container);
        }
        pair_index++;
    }
    function determine_forecast_units(forecast){
        /*
         * Determine the proper units for the cdf forecast's associated data.
         */
        var units = '%';
        if (forecast['axis'] == 'y'){
            units = sfa_dash_config.VARIABLE_UNIT_MAP[forecast['variable']];
        }
        return units;
    }

    function populateReferenceForecasts(){
        /* Filter the list of reference forecasts based on the current
         * forecast.
         */
        // Remove all the reference forecasts.
        reference_forecasts = $('#reference-forecast-select option').slice(2);
        reference_forecasts.remove();

        forecast = $('#distribution-select').val();
        selected_constant_value = $('#constant-value-select').find(":selected").first();
        compareTo = $('[name=observation-aggregate-radio]:checked').val();
        if (compareTo == 'observation'){
            location_key = 'site_id';
        } else {
            location_key = 'aggregate_id';
        }
        if (selected_constant_value.length == 0){
            $('#no-reference-forecast-forecast-selection').removeAttr('hidden');
            $('#no-reference-forecasts').attr('hidden', true);
            return;
        }
        constant_value_forecast_id = selected_constant_value.val();
        if (constant_value_forecast_id == 'full-cdf-group'){
            $('#no-reference-forecast-forecast-selection').removeAttr('hidden');
            $('#no-reference-forecasts').attr('hidden', true);
            return;
        } else {
            constant_value_metadata = searchObjects('forecasts', forecast);
            constant_value = selected_constant_value.data().measurement;
            axis = constant_value_metadata['axis'];
            variable = constant_value_metadata['variable'];
            interval_length = constant_value_metadata['interval_length'];
            loc = constant_value_metadata[location_key];

            cv_filter = function(e){
                constant_values = e['constant_values'].map(function(c){
                    if(c['forecast_id'] == constant_value_forecast_id){
                        return [];
                    } else {
                        return c['constant_value'];
                    }
                });
                return e['forecast_id'] != selected_constant_value.val() &&
                e['axis'] == axis &&
                e['variable'] == variable &&
                e[location_key] == loc &&
                e['interval_length'] == interval_length &&
                constant_values.includes(constant_value);
            };
            ref_fx = page_data['forecasts'].filter(cv_filter);
        }
        
        if (ref_fx.length != 0){
            reference_selector = $('#reference-forecast-select');
            ref_fx.forEach(function(fx){
                forecast_id = fx['constant_values'].find(
                    x => x['constant_value'] == constant_value);
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
        var selected_forecast_id = $('#distribution-select').val();
        var constant_value_select = $('#constant-value-select');

        var non_static_constants = constant_value_select.find('option').slice(3);
        if (selected_forecast_id){
            $("#no-constant-value-distribution-selection").attr('hidden', 'hidden');
            non_static_constants.remove();

            var forecast = searchObjects('forecasts', selected_forecast_id);
            var units = determine_forecast_units(forecast);
            if(units == '%'){
                var cv_label = function(val){return `Prob( x ) = ${val} ${units}`};
            } else {
                var cv_label = function(val){return `Prob( x <= ${val} ${units} )`};
            }
            constant_values = forecast['constant_values'];
            constant_values.forEach(function(constant_value){
                let option = $('<option></option')
                    .attr('value', constant_value['forecast_id'])
                    .attr('data-measurement', constant_value['constant_value'])
                    .html(cv_label(constant_value['constant_value']));
                if (previous_constant == constant_value['constant_value'].toString()){
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
            }
            non_static_constants.remove();
            $("#no-constant-value-distribution-selection").removeAttr('hidden');
            $('#full-cdf-group').attr('hidden', 'hidden');
            $('#full-cdf-group').removeAttr('selected');
        }
        populateReferenceForecasts();
    }

    function newConstantValueSelector(){
        /* Builds the constant value selector */
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


    function deadbandSelector(){
        /*
         * Create a radio button and text input for selecting an uncertainty
         * deadband
         */
        var deadbandSelect= $(
            `<div><b>Uncertainty:</b><br>
             <input type="radio" name="deadband-select" value="null" checked> Ignore Uncertainty.<br>
             <input type="radio" name="deadband-select" value="observation_uncertainty"> Set deadband to observation uncertainty.<br>
             <input type="radio" name="deadband-select" value="user_supplied"> Set deadband to:
             <input type="number" step="any" min=0.0 max=100.0 name="deadband-value"> &percnt;<br></div>`);
        var db_wrapper = $('<div class="form-element full-width deadband-select-wrapper"></div>')
        db_wrapper.append(deadbandSelect);
        return db_wrapper;
    }


    function parseDeadband(){
        /*
         * Parses the deadband widgets into a readable display value, and a
         * valid string value.
         */
        var source = $('[name="deadband-select"]:checked').val();
        if(source == "user_supplied"){
            var val = $('[name="deadband-value"]').val();
            if(!$('[name="deadband-value"]')[0].reportValidity()){
                throw 'Deadband out of range';
            }
            return [val, val];

        }else if(source == "null"){
            return ["Ignore uncertainty.", "null"]
        }else if(source == "observation_uncertainty"){
            var obs_id = $('#observation-select').val();
            var obs = searchObjects("observations", obs_id);
            if(obs){
                obs_uncertainty = obs['uncertainty'].toString();
                return [obs_uncertainty, obs_uncertainty];
            }
        }
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
            forecasts = $('#distribution-select option').slice(2);
            forecasts.removeAttr('hidden');

            toHide = searchSelect(
                '#distribution-option-search',
                '#distribution-select', 2);
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
                    $('#no-distribution-site-selection').attr('hidden', true);
                } else {
                    $('#no-distribution-site-selection').removeAttr('hidden');
                }

                // create a set of elements to hide from selected site, variable and search
                toHide = toHide.add(forecasts.not(`[data-site-id=${site_id}]`));
            } else {

                toHide = toHide.add(forecasts.not('[data-aggregate-id]'));
                $('#no-distribution-selection').attr('hidden', true);
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
            selectedForecast = $('#distribution-select :selected');
            if (selectedForecast.length){
                aggregate_id = selectedForecast.data('aggregate-id');
                // hide aggregates based on search field
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
                $('#no-aggregate-distribution-selection').attr('hidden', true);
            } else {
                toHide = aggregates;
                $('#no-aggregate-distribution-selection').removeAttr('hidden');
            }
            toHide.attr('hidden', true);
        }

        function filterObservations(){
            /* Filter list of observations based on current site and variable.
             */
            observations = $('#observation-select option').slice(2);
            // get the attributes of the currently selected forecast
            selectedForecast = $('#distribution-select :selected');
            if (selectedForecast.length){
                // Show all of the observations
                observations.removeAttr('hidden');
                // retrieve the current site id and variable from the selected forecast
                site_id = selectedForecast.data('site-id');
                variable = selectedForecast.data('variable');
                $('#no-observation-distribution-selection').attr('hidden', true);

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

        var dbSelector = deadbandSelector();
        var constantValueSelector = newConstantValueSelector();
        var fxVariableSelector = createVariableSelect();

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
        widgetContainer.append(aggregateSelector);
        widgetContainer.append(fxSelector);
        widgetContainer.append(constantValueSelector);
        widgetContainer.append(refFxSelector);
        widgetContainer.append(obsSelector);
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
        forecast_select.change(applyFxDependentFilters);
        // TODO: puplate reference on cv select forecast_select.change(filterReferenceForecasts);
        forecast_select.change(populateConstantValues);
        constant_value_select.change(populateReferenceForecasts);

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
                    deadband_values = parseDeadband();
                }catch(error){
                    return;
                }
                constant_value_select.find('option:selected').each(function(){
                    let forecast_id = $(this).val();
                    let forecast = searchObjects('forecasts', selected_forecast.value);
                    let forecast_name = forecast['name'];
                    let forecast_type = 'probabilistic_forecast';
                    let constant_value_label = "Distribution";
                    let distribution_id = selected_forecast.value;
                    if (forecast_id == 'full-cdf-group'){
                        forecast_id = selected_forecast.value;
                    } else {
                        let units = determine_forecast_units(forecast);
                        let constant_value = $(this).data('measurement');
                        let axis = forecast['axis'];
                        forecast_type = 'probabilistic_forecast_constant_value';
                        if (units == '%'){
                            constant_value_label = `Prob(x) = ${constant_value} ${units}`
                        } else {
                            constant_value_label = `Prob(x <= ${constant_value} ${units})`
                        }
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
                        constant_value_label,
                        distribution_id,
                        forecast_type,
                    )
                });
                
                var variable = selected_forecast.dataset.variable;
                set_units(variable);
                $(".empty-reports-list").attr('hidden', 'hidden');
                forecast_select.css('border', '');
                observation_select.css('border', '');
                constant_value_select.css('border', '');
                toggle_reference_dependent_metrics();
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
                    let forecast = searchObjects('forecasts', selected_forecast.value);
                    let forecast_name = forecast['name'];
                    let forecast_type = 'probabilistic_forecast_constant_value';
                    let constant_value_label = "Distribution";
                    let distribution_id = selected_forecast.value;
                    if (forecast_id == 'full-cdf-group'){
                        forecast_id = selected_forecast;
                        forecast_type = 'probabilistic_forecast';
                    } else {
                        let units = determine_forecast_units(forecast);
                        let constant_value = $(this).data('measurement');
                        let axis = forecast['axis'];
                        if (units == '%'){
                            constant_value_label = `Prob(x) = ${constant_value} ${units}`
                        } else {
                            constant_value_label = `Prob(x) < ${constant_value} `
                        }
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
                        constant_value_label,
                        distribution_id,
                        forecast_type,
                    );
                });
                pair_container.append(pair);
                pair_index++;
                var variable = selected_forecast.dataset.variable;
                set_units(variable);

                $(".empty-reports-list")[0].hidden = true;
                forecast_select.css('border', '');
                aggregate_select.css('border', '');
                constant_value_select.css('border', '');
                toggle_reference_dependent_metrics();
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
    }
    if (errors){
       return false;
    } else {
        $('[name="metrics"]:disabled').removeAttr('disabled');
    }
}
