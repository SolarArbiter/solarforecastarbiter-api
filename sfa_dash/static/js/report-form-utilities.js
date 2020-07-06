/******************************************************************************
 * Makes common report form handling functions available via the report_utils
 * global variable
 *****************************************************************************/
report_utils = new Object();

// Globals for keeping track of previous obs/ref fx selections between changing
// forecasts.
previous_observation = null;
previous_reference_forecast = null;


report_utils.fill_existing_pairs = function(){
    /*
     * Fill object pairs found in the form_data global var.
     */
    try{
        var object_pairs = form_data['report_parameters']['object_pairs'];
    } catch(error) {
        return;
    }

    // Create a list to unpack as arguments of addPair. This allows passing
    // extra args for cdf forecasts.
    var pair_container = $('.object-pair-list');
    object_pairs.forEach(function(pair){
        var pair_args = [];

        // Parse information about the observation or aggregate for the pair.
        if (pair.hasOwnProperty('observation')){
            var truth_type = 'observation';
        } else {
            var truth_type = 'aggregate';
        }
        let truth_id = pair[truth_type];
        let truth_metadata = report_utils.searchObjects(truth_type+'s', truth_id);

        // Push the truth_type, truth_name, truth_id arguments
        pair_args.push(truth_type);
        pair_args.push(truth_metadata['name']);
        pair_args.push(truth_id);

        // Parse forecast name and metadata
        let forecast_id = pair['forecast'];
        let forecast_metadata = report_utils.searchObjects('forecasts', forecast_id);

        // Push fx_name, fx_id arguments
        pair_args.push(forecast_metadata['name']);
        pair_args.push(forecast_id);

        // Parse Reference forecast information
        let reference_forecast_id = pair['reference_forecast'];
        if (reference_forecast_id){
            // If a reference Forecast exists, locate its metadata
            var reference_forecast_metadata = report_utils.searchObjects(
                'forecasts',
                reference_forecast_id);
        } else {
            // Reference forecast does not exist for this pair, display "Unset"
            // as the reference forecast value
            var reference_forecast_metadata = {'name': 'Unset'};
        }

        // Push the ref_fx_name, ref_fx_id arguments
        pair_args.push(reference_forecast_metadata['name']);
        pair_args.push(reference_forecast_id);

        // Parse the value and label of pair uncertainty
        if (pair['uncertainty'] == 'observation_uncertainty'){
            uncertainty_label = `${truth_metadata['uncertainty']}%`;
            uncertainty_value = 'observation_uncertainty';
        } else {
            [uncertainty_label, uncertainty_value] = report_utils.parseDeadband(
            pair['uncertainty']);
        }

        // Push db_label, db_value arguments
        pair_args.push(uncertainty_label);
        pair_args.push(uncertainty_value);

        // Parse and push forecast_type argument
        forecast_type = pair['forecast_type'];
        pair_args.push(forecast_type);

        // If the forecast type is probabilistic, we need to include the
        // constant value and distribution id. This is so that pairs are
        // properly nested when displayed.
        if (forecast_type.startsWith('probabilistic_')){
            if (forecast_type == 'probabilistic_forecast'){
                var distribution_id = forecast_metadata['forecast_id'];
                var constant_value_label = 'Distribution';
            } else {
                // Probabilistic forecast constant values distribution id is
                // found in the 'parent' key. The constant_value_label function
                // creates a label using the correct units based on the axis
                // and variable of the forecast.
                var distribution_id = forecast_metadata['parent'];
                var constant_value_label = report_utils.constant_value_label(
                    forecast_metadata, forecast_metadata['constant_value']);
            }
            // Push the constant_value, distribution_id arguments
            pair_args.push(constant_value_label);
            pair_args.push(distribution_id);
        }
        // Add the pair to the container. Note that the addPair function is not
        // defined here. See report-form-handling.js for an example.
        addPair(...pair_args);

        // Hide the "no object pairs" warning message.
        $(".empty-reports-list").attr('hidden', 'hidden');

        // Set the global units variable, so that any further selections will
        // need to have similar units.
        report_utils.set_units(forecast_metadata['variable']);
    });
}

report_utils.toggle_reference_dependent_metrics = function(){
    /*
     * Disables and de-selects the forecast skill metric if not all of the
     * object pairs have reference foreasts.
     */

    // Determine if a reference forecast is selected for any of the already
    // selected object pairs
    var reference_exist = $('.reference-forecast-value').map(function(){
        return $(this).val();
    }).get().some(x=>x!='null');

    // If reference forecasts exist, remove  the reference warning, otherwise
    // insert a warning after the skill metric.
    var skill = $('[name=metrics][value=s]');
    if (reference_exist){
        // show skill remove warning
        $('#reference-warning').remove();
    } else {
        // hide skill, insert warning
        if ($('#reference-warning').length == 0){
            $(`<span id="reference-warning" class="warning-message">
               (Requires reference forecast selection)</span>`
             ).insertAfter(skill.next());
        }
    }
}

/******************************************************************************
 *
 * Set and unset current units based on a variable.
 *
 *****************************************************************************/
//global current_units variable
current_units = null;


report_utils.unset_units = function(filter_callback=null){
    current_units = null;
    // Call to setVariables to repopulate the options in the Variable <select>
    // element.
    report_utils.setVariables()
    if (filter_callback){
        filter_callback();
    }
}

report_utils.set_units = function(variable, filter_callback=null){
    /* Sets the global current_units based on the variable parameter. This is
     * to enforce similar units across all object pairs.
     */
    units = sfa_dash_config.VARIABLE_UNIT_MAP[variable];
    if(units){
        current_units = units;
    }
    report_utils.setVariables();
    if (filter_callback){
        filter_callback();
    }
}

report_utils.searchObjects = function(object_type, object_id){
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
        if (object_type == 'forecasts'
            && page_data.hasOwnProperty('constant_values')){
            // If constant values are present, and we're searching for a
            // forecast, merge the constant values.
            objects = objects.concat(page_data['constant_values']);
        }
        var id_prop = object_type.slice(0, -1) + '_id';
        var metadata = objects.find(e => e[id_prop] == object_id);
    }catch(error){
        return null;
    }
    return metadata;
}

report_utils.setVariables = function(){
	/* Displays or hides options in the variable <select> element based on the
     * current units.
     */
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

report_utils.createVariableSelect = function(){
    /* Created a <select element with options defined in the
     * sfa_dash_config.VARIABLE_NAMES object. Returns a JQuery object and does
     * not modify the DOM directly.
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

report_utils.insertErrorMessage = function(title, msg){
    /* Inserts an error message in the ul#form-errors element. This is
     * typically found just above the submit button, so that users can be
     * alerted to validation issues that are not easily enforcable via
     * setCustomValidity.
     */
    $('#form-errors').append(
        $('<li></li')
            .addClass('alert alert-danger')
            .html(`<p><b>${title}: </b>${msg}</p>`)
    );
}

report_utils.validateReport = function(){
    /*
     * Callback before the report form is submitted. Any js validation should
     * occur here.
     */

    // remove any existing errors
    $('#form-errors').empty();
    var errors = 0;

    // assert at least one pair was selected.
    if ($('.object-pair').length == 0){
        report_utils.insertErrorMessage(
            "Analysis Pairs",
            "Must specify at least one Observation, Forecast pair.");
        errors++;
    }
    if (errors){
        return false;
    }
}
report_utils.validateDatetime = function(dt_string, enforce_utc=true){
    if (enforce_utc){
        var iso_re = /(\d{4})-?(\d{2})-?(\d{2})T(\d{2})\:?(\d{2})(Z|\+00:?00)$/;
    } else {
        var iso_re = /(\d{4})-?(\d{2})-?(\d{2})T(\d{2})\:?(\d{2})(Z|(\+|\-)\d{2}:?\d{2})?$/
    }
    return dt_string.match(iso_re);
}
report_utils.registerDatetimeValidator = function(input_name){
    /*
     * Applies a regex validator to ensure ISO8601 compliance. This is however, very strict. We
     * will need a better solution.
     *
     * @param {string} input_name - The name attribute of the input that needs
     *                              validation.
     */
    $(`[name="${input_name}"]`).keyup(function (){
        if(report_utils.validateDatetime($(`[name="${input_name}"]`).val())) {
              $(`[name="${input_name}"]`)[0].setCustomValidity("");
        } else {
              $(`[name="${input_name}"]`)[0].setCustomValidity(
                  'Please enter a datetime in ISO 8601 format with timezone ' +
                  'Z or offset +00:00 and no units smaller than minutes, e.g ' +
                  '"2020-01-01T12:00Z');
        }
    });
    $(`[name="${input_name}"]`).change(function() {
        this.reportValidity();
    });
}

report_utils.searchSelect = function(inputSelector, selectSelector, offset=0){
    /*
     * Retrieves the value the <input> element identified by inputSelector and
     * returns a jquery list of the <option> elements inside the element
     * identified by selectSelector that do not contain the value.
     * Passing an offset ignores the first offset items.
     *
     * @param {string} inputSelector
     *      JQuery selector of the input element used to provide search terms.
     *
     * @param {string} selectSelector
     *      JQuery selector of select element of options to be searched.
     *
     * @param {int} offset
     *      Number of options to skip. This is useful for skipping the static
     *      disabled options e.g. "No forecast selected".
     */
    var searchTerm = $(inputSelector).val();
    var searchSplit = searchTerm.replace(/ /g, "'):containsi('");
    return $(selectSelector + " option").slice(offset).not(":containsi('" + searchSplit + "')");
}

report_utils.applyFxDependentFilters = function(){
    filterObservations();
    filterAggregates();
    filterReferenceForecasts();
}

report_utils.newSelector = function(field_name, depends_on=null, required=true){
    /*
     * Returns a JQuery object containing labels and select elements with base
     * options.
     *
     * Initializes with one default and one optional select option:
     *     Always adds an option containing "No matching <field_Type>s
     *     If depends_on is provided, inserts a "Please select a <depends_on> option>
     *
     *  @param {string} field_name
     *      The display name used for the field. The field_name will also be
     *      used as the name attribute of the input element, but all lowercase
     *      with any spaces converted to '-' characters.
     *
     *  @param {string} depends_on
     *      The name of a field that this one depends on. used to insert a
     *      disabled option for displaying "No <depends_on> selected" with
     *      the id attribute "no-<field_name>-<depend_on>s" where field_name
     *      is transformed as described above.
     *
     *  @param {bool} required
     *      Whether or not the field is required.
     *
     *  @returns JQuery
     *      Handle to the <select> element.
     */
    var field_type = field_name.toLowerCase().replace(/ /g, '-');
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

report_utils.deadbandSelector = function(){
    /*
     * Create a radio button and text input for selecting an uncertainty
     * deadband.
     */
    var deadbandSelect= $(
        `<div><b>Uncertainty:</b><br>
         <input type="radio" name="deadband-select" value="null" checked> Ignore uncertainty<br>
         <input type="radio" name="deadband-select" value="observation_uncertainty"> Set deadband to observation uncertainty: <span id="selected-obs-uncertainty">No observation selected</span><br>
         <input type="radio" name="deadband-select" value="user_supplied"> Set deadband to:
         <input id="custom-deadband" type="number" step="any" min=0.0 max=100.0 name="deadband-value"> &percnt;<br></div>`);
    var db_wrapper = $('<div class="form-element full-width deadband-select-wrapper"></div>')
    db_wrapper.append(deadbandSelect);
    return db_wrapper;
}


report_utils.parseDeadband = function(value=null){
    /*
     * Parses the deadband widgets into a readable display value, and a
     * valid string value.
     *
     * @param {string} value
     *      An uncertainty value, if provided returns a label of the value
     *      suffixed with %. If not provided, parses values from the
     *      input with name deadband-select.
     *
     * @returns {array}
     *      An array where the first element is a string label for displaying
     *      to the user, and the second element is the actual uncertainty
     *      value.
     */
    if (!value){
        var source = $('[name="deadband-select"]:checked').val();
        if (source == "null"){
            return ["Ignore uncertainty", "null"]
        } else if (source == "user_supplied"){
            var val = $('[name="deadband-value"]').val();
            if(!$('[name="deadband-value"]')[0].reportValidity()){
                throw 'Deadband out of range';
            }
            return [`${val}&percnt;`, val]
        } else if (source == "observation_uncertainty"){
            var obs_id = $('#observation-select').val();
            var obs = report_utils.searchObjects("observations", obs_id);
            if(obs){
                var obs_val = obs['uncertainty'];
            }
            return [`${obs_val}&percnt;`, 'observation_uncertainty'];
        }
    } else {
        var val = value;
        var str_val = `${val}&percnt;`;
        return [str_val, val];
    }
}


report_utils.constant_value_label = function(forecast, value){
    /*  Creates a label for displaying a constant value to the user. Display
     *  is dependent on units and axis of the forecast.
     *
     *  @param {Object} forecast
     *      Object containing forecast metadata.
     *
     *  @param {float} value
     *      The actual constant_value.
     *
     *  @returns {string}
     *      The Constant value label to display to a user.
     */
    let units = report_utils.determine_forecast_units(forecast);
    if(units == '%'){
        return `Prob( x ) = ${value} ${units}`;
    } else {
       return `Prob( x <= ${value} ${units} )`;
    }
}

report_utils.determine_forecast_units = function(forecast){
    /*  Determines which units to use based on a forecast's metadata. If the
     *  forecast does not have an axis field, or the axis field is 'y', the
     *  units corresponding to the forecast's variable will be returned.
     *  Otherwise, percentage points are assumed.
     *
     *  @param {Object} forecast
     *      Object containing forecast metadata.
     *
     */
    var units = '%';
    if (!forecast.hasOwnProperty('axis') || forecast['axis'] == 'x'){
        units = sfa_dash_config.VARIABLE_UNIT_MAP[forecast['variable']];
    }
    return units;
}

report_utils.register_uncertainty_handler = function(obs_option_selector){
    /* Creates an onchange handler that updates 'use observation uncertainty'
     * option based on the current selection.
     *
     * @param {string} obs_option_selector
     *      JQuery selector string for the select input to watch.
     *
     */
    $(obs_option_selector).change(function(){
        obs_id = $(this).val();
        if (obs_id){
            observation = report_utils.searchObjects('observations', obs_id);
            uncertainty = observation['uncertainty'];
            $('#selected-obs-uncertainty').html(`${uncertainty}&percnt;`);
        } else {
            $('#selected-obs-uncertainty').html("No observation selected");
        }
    });
}

report_utils.store_prev_observation = function(){
    /* Ochange callback that stores the currently selected node into the
     * `previous_observation` global if it has changed.
     */
    if ($(this).val()){
        var selected = $(this).children('option:selected')[0];
        if (!selected.isSameNode(previous_observation)){
            previous_observation = selected;
        }
    }
}

report_utils.store_prev_reference_forecast = function(){
    /* Ochange callback that stores the currently selected node into the
     * `previous_reference_forecast` global if it has changed.
     */
    if ($(this).val()){
        var selected = $(this).children('option:selected')[0];
        if (!selected.isSameNode(previous_reference_forecast)){
            previous_reference_forecast = selected;
        }
    }
}

report_utils.restore_prev_value = function(the_node){
    /*  Sets the previous value as selected if it is no longer hidden.
     *
     *  @param {node} the_node
     *      Variable that stores the dom node that was previously selected. See
     *      `previous_observation` at the top of this file.
     */
    if (the_node && !$(the_node).prop('hidden')){
         $(the_node).prop('selected', true);
    }
}

/*
 * Cost Class definitions
 */
class TimeOfDayCost{
    constructor({times=[], cost=[], aggregation='sum', net=false,
                fill='forward'} = {}
    ){
        this.times = times;
        this.cost = cost;
        this.aggregation = aggregation;
        this.net = net;
        this.fill = fill;
    }

}
class DatetimeCost{
    constructor({datetimes=[], cost=[], aggregation='sum', net=false,
                fill='forward', timezone= null} = {}
    ){
        this.datetimes = datetimes;
        this.cost = cost;
        this.aggregation = aggregation;
        this.net = net;
        this.fill = fill;
        if (timezone){
            this.timezone = timezone;
        } else {
            this.timezone = null;
        }
    }

}
class ConstantCost{
    constructor({cost= 0.0, aggregation='sum', net=false} = {}){
        this.cost = cost;
        this.aggregation = aggregation;
        this.net = net;
    }
}

class CostBand{
    constructor({
        error_range=[-Infinity, Infinity],
        cost_function='timeofday',
        cost_function_parameters=null
    } = {}){
        this.error_range = error_range;
        this.cost_function = cost_function;
        var param_class = report_utils.get_cost_class(cost_function);
        if (cost_function_parameters == null){
            this.cost_function_parameters = new param_class();
        } else {
            this.cost_function_parameters = new param_class(
                cost_function_parameters);
        }
    }

}
class ErrorBandCost{
    // bands: array of CostBand
    constructor({bands = []} = {}){
        this.bands = bands.map(x => new CostBand(x));
    }
}
class Cost{
    constructor({name=null, type='timeofday', parameters=null} = {}){
        this.name = name;
        this.type = type;
        var param_class = report_utils.get_cost_class(type);
        if (!parameters){
            this.parameters = new param_class();
        } else {
            this.parameters = new param_class(parameters);
        }
    }
}
report_utils.get_cost_class = function(cost_type){
    switch (cost_type){
        case 'timeofday':
            return TimeOfDayCost;
        case 'datetime':
            return DatetimeCost;
        case 'errorband':
            return ErrorBandCost;
        case 'constant':
            return ConstantCost;
        default:
            return null;
    }
}

/*
 * Cost field creation functions
 */
report_utils.suffix_name = function(the_name, index){
    return (index!=null ? the_name + `-${index}` : the_name);
}

report_utils.many_costs_field = function(the_div, cost_obj, index=null){
    /*  Inserts a costs field expecting input to be comma separated list
     *  of float costs.
     *
     *  @param {jQuery} the_div
     *      Div to insert field into.
     *  @param {Object} cost_obj
     *      Existing cost object to parse values from.
     *  @param {int} index
     *      Integer index used to identify index of the field, for use when
     *      the costs are a part of an ErrorBandCost.
     *
     *  @returns {Jquery} cost_field
     *      Returns a handle to the jquery object, so that the caller can
     *      register custom callbacks such as asserting dependence on the
     *      datetimes or times field.
     */
    var costs_field = $('<input>')
        .attr('name', report_utils.suffix_name('cost-costs', index))
        .attr('type', 'text')
        .attr('required', true)
        .attr('value', cost_obj.cost.map(x => x.toFixed(2)).join(', '))
        .attr('placeholder', '1.0, 1.2, 1.5')
        .addClass('form-control');
    the_div.append($('<br/><label>Costs: </label>'));
    the_div.append(costs_field);
    return costs_field;
}

report_utils.cost_aggregation_field = function(the_div, cost_obj, index=null){
    /*  Inserts an aggregation field with options "sum" and "mean".
     *
     *  @param {Jquery} the_div
     *      Div to insert field into.
     *  @param {Object} cost_obj
     *      Existing cost object to parse value from.
     *  @param {int} index
     *      Integer index used to identify index of the field, for use when
     *      the aggregation defines a value for one of the bands in an
     *      ErrorBandCost.
     *  @returns {Jquery}
     *      Handle to the jQuery object so that the caller can register any
     *      custom callbacks.
     */
    var input_wrapper = $('<div>').css('position', 'relative');
    var agg_input_name = report_utils.suffix_name('cost-aggregation', index)
    var agg_field_sum = $(`<input
            type="radio"
            id="${report_utils.suffix_name('cost-aggregation-sum', index)}"
            name="${agg_input_name}"
            value="sum"
            ${cost_obj.aggregation == 'sum' ? 'checked' : ''}>
           <label for="${report_utils.suffix_name('cost-aggregation-sum', index)}">sum</label>`)
    var agg_field_mean = $(`<input
            type="radio"
            id="${report_utils.suffix_name('cost-aggregation-mean', index)}"
            name="${agg_input_name}"
            value="mean"
            ${cost_obj.aggregation == 'mean' ? 'checked' : ''}>
           <label for="${report_utils.suffix_name('cost-aggregation-sum', index)}">mean</label>`)
    const [help_button, help_text] = report_utils.help_popup(
        agg_input_name,
        `The aggregation parameter controls how the cost for each error
        value in the timeseries are aggregated (e.g. summed or averaged)
        into a single cost number.`
    )
    input_wrapper.append($('<label>Aggregation: </label>'));
    input_wrapper.append(agg_field_sum);
    input_wrapper.append(agg_field_mean);
    input_wrapper.append(help_button);
    input_wrapper.append(help_text);
    the_div.append(input_wrapper);
    return the_div.find(`[name=${agg_input_name}]`);
}

report_utils.cost_net_field = function(the_div, cost_obj, index=null){
    /*  Inserts a boolean net field.
     *
     *  @param {Jquery} the_div
     *      Div to insert field into.
     *  @param {Object} cost_obj
     *      Existing cost object to parse value from.
     *  @param {int} index
     *      Integer index used to identify index of the field, for use when
     *      the net field defines a value for one of the bands in an
     *      ErrorBandCost.
     *
     *  @returns {Jquery}
     *      Handle to the jQuery object so that the caller can register any
     *      custom callbacks.
     */
    var input_wrapper = $('<div>').css('position', 'relative');
    var net_field_name = report_utils.suffix_name('cost-net', index)
    var net_field = $('<input>')
        .attr('type', 'checkbox')
        .attr('id', net_field_name)
        .attr('name', net_field_name)
        .prop('checked', cost_obj.net);

    const [help_button, help_text] = report_utils.help_popup(
        net_field_name,
        `The net parameter indicates if the aggregation should keep the sign
        of the error, or take the absolute value of the error before
        aggregating.`
    )
    input_wrapper.append($('<label>Net: </label>'));
    input_wrapper.append(net_field);
    input_wrapper.append(help_button);
    input_wrapper.append(help_text);
    the_div.append(input_wrapper);
    return net_field;
}

report_utils.cost_fill_field = function(the_div, cost_obj, index=null){
    /*  Inserts a fill field with radio buttons and options forward/backward.
     *
     *  @param {Jquery} the_div
     *      Div to insert field into.
     *  @param {Object} cost_obj
     *      Existing cost object to parse value from.
     *  @param {int} index
     *      Integer index used to identify index of the field, for use when
     *      the fill field defines a value for one of the bands in an
     *      ErrorBandCost.
     *
     *  @returns {Jquery}
     *      Handle to the jQuery object so that the caller can register any
     *      custom callbacks.
     */
    var input_wrapper = $('<div>').css('position', 'relative');
    var fill_field_name = report_utils.suffix_name('cost-fill', index);
    var fill_field_forward = $(`<input
            type="radio"
            id="${report_utils.suffix_name('cost-fill-forward', index)}"
            name="${fill_field_name}"
            value="forward"
            ${cost_obj.fill == 'forward' ? 'checked' : ''}>
           <label for="${report_utils.suffix_name('cost-fill-forward', index)}">forward</label>`);
    var fill_field_backward = $(`<input
            type="radio"
            id="${report_utils.suffix_name('cost-fill', index)}"
            name="${fill_field_name}"
            value="mean"
            ${cost_obj.fill == 'backward' ? 'checked' : ''}>
           <label for="${report_utils.suffix_name('cost-fill-backward', index)}">backward</label>`);
    const [help_button, help_text] = report_utils.help_popup(
        fill_field_name,
        `The fill parameter specifies how the costs should be extended to
        times that are not included in times.`
    )
    input_wrapper.append($('<label>Fill: </label>'));
    input_wrapper.append(fill_field_forward);
    input_wrapper.append(fill_field_backward);
    input_wrapper.append(help_button);
    input_wrapper.append(help_text);
    the_div.append(input_wrapper)
    return the_div.find(`[name=${fill_field_name}]`);
}

report_utils.cost_timezone_field = function(the_div, cost_obj, index=null){
    /*  Inserts a timezone field populated with options from the
     *  sfa_dash_config TIMEZONES config.
     *
     *  @param {Jquery} the_div
     *      Div to insert field into.
     *  @param {Object} cost_obj
     *      Cost object with existing timezone field.
     *  @param {int} index
     *      Integer index used to identify index of the field, for use when
     *      the timezone field defines a value for one of the bands in an
     *      ErrorBandCost.
     *
     *  @returns {Jquery}
     *      Handle to the jQuery object so that the caller can register any
     *      custom callbacks.
     */
    var input_wrapper = $('<div>').css('position', 'relative');
    var timezone_name = report_utils.suffix_name('cost-timezone', index);
    var tz_select = $('<select>')
        .attr('name', timezone_name)
        .addClass('form-control unset-width');
    var selected_tz = cost_obj.timezone;

    tz_select.append($('<option>')
        .attr('value', 'null')
        .html('None')
        .prop('selected', selected_tz == null));
    // populate the timezone options from config
    Object.entries(sfa_dash_config.TIMEZONES).forEach(tz => tz_select.append(
        $('<option>')
            .attr('value', tz[0])
            .html(tz[1])
            .prop('selected', tz[1] == selected_tz)
    ));
    const [help_button, help_text] = report_utils.help_popup(
        timezone_name,
        `The timezone parameter defines the timezone if datetimes are not
        localized, and if timezone is None, the timezone of the errors is
        used.`
    )
    input_wrapper.append($('<br/><label>Timezone: </label>'));
    input_wrapper.append(tz_select);
    input_wrapper.append(help_button);
    input_wrapper.append(help_text);

    the_div.append(input_wrapper);
    return tz_select;
}

/*
 * Cost model ui creation functions. These create all of the inputs needed to
 * create a new cost object, and will keep up to date with a passed in Cost
 * object, or create new ones as necessary.
 */
report_utils.timeofday_cost = function(cost_obj, index=null){
    var the_div = $('<div>');
    var times_field = $('<input>')
        .attr('name', report_utils.suffix_name('cost-times', index))
        .attr('type', 'text')
        .attr('value', cost_obj.times.join(', '))
        .attr('placeholder', '00:00, 06:00, 18:00')
        .addClass('form-control');
    the_div.append($('<label>Times: </label>'));
    the_div.append(times_field);

    var costs_field = report_utils.many_costs_field(the_div, cost_obj, index);

    // register change handlers to enforce same length times and costs, and
    // validate inputs.
    times_field.change(function(){
        var times = this.value.split(',');
        var errors = [];
        var invalid_indices = [];

        cost_obj.times = [];

        times.forEach(function(tod, idx){
            function validate_tod(tod){
                let re = /\d{1,2}:\d{2}/;
                if(tod.match(re)){
                    let components = tod.split(':');
                    let hours = parseInt(components[0]);
                    if (hours > 23 || hours < 0){
                        return false;
                    }
                    let minutes = parseInt(components[1]);
                    if (minutes > 59 || minutes < 0){
                        return false;
                    }
                    return true;
                } else {
                    return false;
                }
            }
            if (!validate_tod(tod)){
                invalid_indices.push(idx);
            } else {
                cost_obj.times[idx] = tod;
            }
        });
        if (invalid_indices.length){
            errors.push(
                `Value ${invalid_indices.join(',')} are not valid time of day
                values. Please use HH:MM format, separated by commas.`);
        }
        if (times.length != cost_obj.cost.length){
            errors.push('Times and costs must be of equal length.');
        }
        if (errors.length > 0){
            this.setCustomValidity(errors.join('\n'));
        } else {
            this.setCustomValidity('');
            // check if the costs field is valid, and double check now that
            // the fields are the same length
            let costs_field = $(
                `[name=${report_utils.suffix_name('cost-costs', index)}]`);
            if (!costs_field[0].checkValidity()){
                costs_field.change();
            }
        }
        this.reportValidity();
    });
    costs_field.change(function(){
        var costs = this.value.split(',');
        var errors = [];
        var invalid_indices = [];

        cost_obj.cost = [];

        costs.forEach(function(cost, idx){
            if (isNaN(parseFloat(cost))){
                invalid_indices.push(idx+1);
            } else {
                cost_obj.cost[idx] = parseFloat(cost);
            }
        });

        if(invalid_indices.length){
            errors.push(`Values ${invalid_indices.join(',')} are not valid
                        costs. Please provide float values separated by
                        commas.`);
        }
        if (costs.length != cost_obj.times.length){
            errors.push('Costs and times must be of equal length.');
        }
        if (errors.length > 0){
            this.setCustomValidity(errors.join('\n'));
        } else {
            this.setCustomValidity('');
            // check if the timess field is valid, and double check now that
            // the fields are the same length
            let times_field = $(
                `[name=${report_utils.suffix_name('cost-times', index)}]`);
            if (!times_field[0].checkValidity()){
                times_field.change();
            }
        }
        this.reportValidity();
    });

    var agg_field = report_utils.cost_aggregation_field(the_div, cost_obj, index);
    agg_field.change(function(){cost_obj.aggregation = this.value});

    var net_field = report_utils.cost_net_field(the_div, cost_obj, index);
    net_field.change(function(){cost_obj.net = this.value});

    var fill_field = report_utils.cost_fill_field(the_div, cost_obj, index);
    fill_field.change(function(){cost_obj.fill = this.value});

    var timezone_field = report_utils.cost_timezone_field(
        the_div, cost_obj, index);
    timezone_field.change(function(){cost_obj.timezone = this.value});

    return the_div
}
report_utils.datetime_cost = function(cost_obj, index=null){
    var the_div = $('<div>');
    var datetimes_field = $('<input>')
        .attr('name', report_utils.suffix_name('cost-datetimes', index))
        .attr('type', 'text')
        .attr('required', true)
        .attr('value', cost_obj.datetimes.join(', '))
        .attr('placeholder', '2020-01-01T00:00Z, 2020-01-02T06:00Z, 2020-01-03T00:00Z')
        .addClass('form-control');
    the_div.append($('<label>Datetimes: </label>'));
    the_div.append(datetimes_field);
    var costs_field = report_utils.many_costs_field(the_div, cost_obj, index);

    datetimes_field.change(function(){
        var datetimes = this.value.split(',');
        var errors = [];
        var invalid_indices = [];

        cost_obj.datetimes = [];

        datetimes.forEach(function(dt, idx){
            if (!report_utils.validateDatetime(dt)){
                invalid_indices.push(idx);
            } else {
                cost_obj.datetimes[idx] = dt;
            }
        });
        if (invalid_indices.length){
            errors.push(
                `Value ${invalid_indices.join(',')} are not valid UTC datetime
                values. Please use ISO 8601 format with a timezone of 'Z' or
                '+00:00' offset and no units smaller than minutes, separated
                by commas.`);
        }
        if (datetimes.length != cost_obj.cost.length){
            errors.push('Datetimes and costs must be of equal length.');
        }
        if (errors.length > 0){
            this.setCustomValidity(errors.join('\n'));
        } else {
            this.setCustomValidity('');
            // check if the costs field is valid, and double check now that
            // the fields are the same length
            let costs_field = $(
                `[name=${report_utils.suffix_name('cost-costs', index)}]`);
            if (!costs_field[0].checkValidity()){
                costs_field.change();
            }
        }
        this.reportValidity();
    });
    costs_field.change(function(){
        var costs = this.value.split(',');
        var errors = [];
        var invalid_indices = [];

        cost_obj.cost = [];

        costs.forEach(function(cost, idx){
            if (isNaN(parseFloat(cost))){
                invalid_indices.push(idx+1);
            } else {
                cost_obj.cost[idx] = parseFloat(cost);
            }
        });

        if(invalid_indices.length){
            errors.push(`Values ${invalid_indices.join(',')} are not valid
                        costs. Please provide float values separated by
                        commas.`);
        }
        if (costs.length != cost_obj.datetimes.length){
            errors.push('Costs and times must be of equal length.');
        }
        if (errors.length > 0){
            this.setCustomValidity(errors.join('\n'));
        } else {
            this.setCustomValidity('');
            // check if the datetimes field is valid, and rerun validation
            // now that the fields are the same length
            let datetimes_field = $(
                `[name=${report_utils.suffix_name("cost-datetimes", index)}]`);
            if(!datetimes_field[0].checkValidity()){
                datetimes_field.change();
            }
        }
        this.reportValidity();
    });

    var agg_field = report_utils.cost_aggregation_field(
        the_div, cost_obj, index);
    agg_field.change(function(){cost_obj.aggregation = this.value});

    var net_field = report_utils.cost_net_field(the_div, cost_obj, index);
    net_field.change(function(){cost_obj.net = this.value});

    var fill_field = report_utils.cost_fill_field(the_div, cost_obj, index);
    fill_field.change(function(){cost_obj.fill = this.value});

    var timezone_field = report_utils.cost_timezone_field(
        the_div, cost_obj, index);
    timezone_field.change(function(){cost_obj.timezone = this.value});
    return the_div
}
report_utils.constant_cost = function(cost_obj, index=null){
    /* Returns inputs for defining a constant cost.
     * @param {ConstantCost} cost_obj
     *     ConstantCost object to store values into/parse values from.
     * @param {int} index
     *     If passed, suffixes the name of inputs with an integer
     *
     */
    var the_div = $('<div>');

    var cost_field = $('<input>')
        .attr('name', report_utils.suffix_name('cost-value', index))
        .attr('type', 'text')
        .attr('required', true)
        .attr('value', cost_obj.cost.toFixed(2))
        .addClass('form-control unset-width');
    cost_field.change(function(){
        if (!isNaN(parseFloat(this.value))){
            cost_obj.value = parseFloat(this.value);
            this.setCustomValidity('');
        } else {
            this.setCustomValidity('Cost must be a float.');
        }
    });
    the_div.append($('<label>Cost: $</label>'));
    the_div.append(cost_field);

    var agg_field = report_utils.cost_aggregation_field(the_div, cost_obj, index);
    agg_field.change(function(){cost_obj.aggregation = this.value});

    var net_field = report_utils.cost_net_field(the_div, cost_obj, index);
    net_field.change(function(){cost_obj.net = this.value});
    return the_div;
}

report_utils.cost_band = function(cost_obj, index=null){
    var the_div = $('<div>')
        .addClass('error-band-container');
    var param_container = $('<div>')
        .addClass('error-band-params-container');
    var tod_band_radio = $(`<input
        type="radio"
        id="errorband-tod-select"
        name="${report_utils.suffix_name('cost-band-cost-function', index)}"
        value="timeofday"
        ${cost_obj.cost_function == 'timeofday' ? 'checked' : ''}>
        <label>Time of Day</label>`);
    tod_band_radio.change(function(){
        if (!(cost_obj.cost_function_parameters instanceof TimeOfDayCost)){
            cost_obj.cost_function_parameters = new TimeOfDayCost();
        }
        param_container.empty();
        param_container.html(
            report_utils.timeofday_cost(
                cost_obj.cost_function_parameters, index)
        );
    });
    var dt_band_radio = $(`<input
        type="radio"
        id="errorband-dt-select"
        name="${report_utils.suffix_name('cost-band-cost-function', index)}"
        value="datetime"
        ${cost_obj.cost_function == 'datetime' ? 'checked' : ''}>
        <label>Datetime</label>`);
    dt_band_radio.change(function(){
        if (!(cost_obj.cost_function_parameters instanceof DatetimeCost)){
            cost_obj.cost_function_parameters = new DatetimeCost();
        }
        param_container.empty();
        param_container.html(
            report_utils.datetime_cost(
                cost_obj.cost_function_parameters, index)
        );
    });
    var constant_band_radio = $(`<input
        type="radio"
        id="errorband-constant-select"
        name="${report_utils.suffix_name('cost-band-cost-function', index)}"
        value="constant"
        ${cost_obj.cost_function == 'constant' ? 'checked' : ''}>
        <label>Constant</label>`);
    constant_band_radio.change(function(){
        if (!(cost_obj.cost_function_parameters instanceof ConstantCost)){
            cost_obj.cost_function_parameters = new ConstantCost();
        }
        param_container.empty();
        param_container.html(
            report_utils.constant_cost(
                cost_obj.cost_function_parameters, index)
        );
    });
    var error_range_start = $(`<input
        type="text"
        name="${report_utils.suffix_name('cost-band-error-start', index)}"
        value="${cost_obj.error_range[0]}">`)
        .addClass('form-control unset-width');
    error_range_start.change(function(){
        if (!isNaN(parseFloat(this.value))){
            var value = parseFloat(this.value);
            var end_input = $(
                `[name="${report_utils.suffix_name('cost-band-error-end', index)}"]`);
            if (value >= end_input.val()){
                this.setCustomValidity(
                    "Error range start must be less than end.");
            }else{
                this.setCustomValidity('');
                cost_obj.error_range[0] = value;
            }
        } else {
            this.setCustomValidity(
                "Error range start must be a float or +/- Infinity.");
        }
        this.reportValidity();
    });
    var error_range_end = $(`<input
        type="text"
        step="any"
        name="${report_utils.suffix_name('cost-band-error-end', index)}"
        value="${cost_obj.error_range[1]}">`)
        .addClass('form-control unset-width');
    error_range_end.change(function(){
        if (!isNaN(parseFloat(this.value))){
            var value = parseFloat(this.value);
            var start_input = $(
                `[name="${report_utils.suffix_name('cost-band-error-start', index)}"]`);
            if (value <= start_input.val()){
                this.setCustomValidity(
                    "Error range end must be greater than start.");
            }else{
                this.setCustomValidity('');
                cost_obj.error_range[1] = value;
            }
        } else {
            this.setCustomValidity(
                "Error range end must be a float or +/- Infinity.");
        }
        this.reportValidity();
    })
    the_div.append($('<label>Error Range Start:</label>'));
    the_div.append(error_range_start);
    the_div.append($('<br><label>Error Range End:</label>'));
    the_div.append(error_range_end);
    the_div.append($('<br><label>Errorband Cost Function: </label><br>'));
    the_div.append(tod_band_radio);
    the_div.append(dt_band_radio);
    the_div.append(constant_band_radio);
    the_div.append(param_container);

    // fire change event to initialize the first paramters
    the_div.find(`[name=${report_utils.suffix_name('cost-band-cost-function', index)}]:checked`)
        .change();
    removal_button = $(
        '<a role="button" class="error-band-delete-button">remove</a>');
    removal_button.click(function(){
        $(this).parent().remove();
        if ($('.error-band-container').length == 0){
            $('.error-bands-container').append(
                $(`<div class="error-band-container alert-warning">
                   No error bands</div>`)
            );
        }
    });
    the_div.append(removal_button);
    return the_div;
}
report_utils.errorband_cost = function(cost_obj){
    var index = cost_obj.bands.length;
    var the_div = $('<div>');
    var error_bands_container = $('<div>')
        .addClass('error-bands-container');

    function insert_errorband(cost_band, band_index){
        error_bands_container.append(
                report_utils.cost_band(cost_band, band_index));
        $('.error-band-container.alert-warning').remove();
    }

    var add_band_button = $('<a>')
        .attr('role', 'button')
        .addClass('btn btn-primary btn-sm')
        .html('Add Error Band')
        .click(function(){
            cost_obj.bands[index] = new CostBand();
            insert_errorband(cost_obj.bands[index], index);
            index++;
        });
    the_div.append($('<br><label>Error Bands:</label><br>'));
    the_div.append(add_band_button);
    // add any bands from existing cost.
    if (cost_obj.bands.length > 0){
        cost_obj.bands.forEach(function(band, idx){
            insert_errorband(band, idx);
        });
    } else {
        error_bands_container.append(
            $(`<div class="error-band-container alert-warning">
              No error bands</div>`));
    }
    the_div.append(error_bands_container);
    return the_div;

}

/*
 * Primary cost entrypoint. Initializes the cost inputs inside the container
 * with id `cost-container`
 */
report_utils.insert_cost_widget = function(){
    /* Creates a widget for defining cost metrics. Contains nested functions
     * for defining each type of cost model, for nesting within error band.
     */
    // only create cost widgets if the cost container contains no html
    report_utils.init_cost_parameters_toggle();
    if (!$.trim($('#cost-container').html())){
        report_utils.initialize_cost();
        var widget_div = $('<div>')
            .addClass('cost-definition');

        // Create radio buttons for selecting the type of cost
        var timeofday = $('<input id="master-cost-timeofday" type="radio" name="cost-primary-type" value="timeofday"><label>Time of Day</label>');
        timeofday.change(function(){
            if (cost.type != this.value){
                cost.parameters = new TimeOfDayCost();
            }
            cost.type = this.value;
            $('#primary-cost-fields').html(
                report_utils.timeofday_cost(cost.parameters)
            );
        });

        var datetime = $('<input  id="master-cost-datetime"type="radio" name="cost-primary-type" value="datetime"><label>Datetime</label>');
        datetime.change(function(){
            if (cost.type != this.value){
               cost.parameters = new DatetimeCost();
            }
            cost.type = this.value;
            $('#primary-cost-fields').html(
                report_utils.datetime_cost(cost.parameters)
            );
        });

        var constant = $('<input  id="master-cost-constant"type="radio" name="cost-primary-type" value="constant"><label>Constant</label>');
        constant.change(function(){
         if (cost.type != this.value){
                cost.parameters = new ConstantCost();
            }
            cost.type = this.value;
            $('#primary-cost-fields').html(
                report_utils.constant_cost(cost.parameters)
            );
        });

        var errorband = $('<input id="master-cost-errorband"type="radio" name="cost-primary-type" value="errorband"><label>Error Band</label>');
        errorband.change(function(){
            if (cost.type != this.value){
                cost.parameters = new ErrorBandCost();
            }
            cost.type = this.value;
            $('#primary-cost-fields').html(
                report_utils.errorband_cost(cost.parameters)
            );
        });
        /*
         * Container to hold top-level cost options. This allows the user to select
         * the primary cost type. Adds a '#primary-cost-fields' div for holding the
         * inputs used for setting the appropriate attributes.
         */
        var cost_name_wrapper = $('<div>')
            .css('position', 'relative');
        var cost_name = $('<div>')
            .addClass('input-wrapper')
            .append($('<input><br/>')
                .attr('name', 'cost-primary-name')
                .attr('required', true)
                .attr('value', cost.name)
                .addClass('form-control name-field')
                .change(function(){
                    cost.name = this.value;
                })
            );
        const [name_help_button, name_help_text] = report_utils.help_popup(
            'cost-primary-name',
            `A name for this set of cost parameters. Will be used when
            displaying cost metrics in the rendered report.`
        )
        cost_name_wrapper.append(cost_name);
        cost_name_wrapper.append(name_help_button)
        cost_name_wrapper.append(name_help_text)
        var cost_type_wrapper = $('<div>')
            .css('position', 'relative');
        const [type_help_button, type_help_text] = report_utils.help_popup(
            'cost-primary-type',
            `The type of cost function to be used for this set of cost
            parameters.`
        )
        cost_type_wrapper.append(timeofday);
        cost_type_wrapper.append(datetime);
        cost_type_wrapper.append(constant);
        cost_type_wrapper.append(errorband);
        cost_type_wrapper.append(type_help_button);
        cost_type_wrapper.append(type_help_text);

        var primary_cost = $('<div>')
            .css('position', 'relative')
            .addClass('primary-cost-container')
            .append($('<label>Name</label><br>'))
            .append(cost_name_wrapper)
            .append($('<label class="mt-1">Cost Function</label><br>'))
            .append(cost_type_wrapper)
            .append($('<div>')
                .attr('id','primary-cost-fields'));
        widget_div.append(primary_cost);

        $('#cost-container').append(widget_div);
        // if cost has a type value, select it.
        primary_cost.find(`[name=cost-primary-type][value=${cost.type}]`)
            .prop('checked', true);
        primary_cost.find(`[name=cost-primary-type]:checked`).trigger('change');
    }
}

report_utils.initialize_cost = function(){
    /* Initialize global cost var from api costs.*/
    if (typeof cost === 'undefined'){
        try{
            var costs = form_data['report_parameters']['costs'];
        } catch(error) {
            // Continue, to allow setting cost to a new Cost object.
        }
        if (typeof costs !== 'undefined' && costs.length > 0){
            // only handling one cost to start
            var first_cost = costs[0];
            cost = new Cost(first_cost);
        } else {
            cost = new Cost();
        }
    }
}

report_utils.init_cost_parameters_toggle = function(){
    cost_metric = $('[name=metrics][value=cost]');
    cost_metric.next().after(
        $('<a role="button" id="cost-param-collapse" data-toggle="collapse" data-target="#cost-block" class="collapser-button collapsed"> </a>'));
    cost_metric.change(function(){
        if (this.checked){
            $('#cost-container').prop('disabled', false);
            $('#cost-block').collapse('show');
        } else {
            $('#cost-container').prop('disabled', true);
            $('#cost-block').collapse('hide');
        }
    });
    if (cost_metric.prop('checked')){
        cost_metric.change();
    }
}
report_utils.help_popup = function(help_name, help_text){
    var help_button = $(`<a data-toggle="collapse" data-target=".${help_name}-help-text" role="button" href="" class="help-button">?</a>`);
    var help_box = $(`<span class="${help_name}-help-text form-text text-muted help-text collapse" aria-hidden="">${help_text}</span>`);
    return [help_button, help_box]
}
report_utils.register_forecast_fill_method_validator = function(
    forecast_type='deterministic'){
    var forecast_fill = $('[name=forecast_fill_method]')
    forecast_fill.change(function(){
        if (this.value == 'provided'){
            $('[name=provided_forecast_fill_method]').prop('disabled', false);
        } else {
            $('[name=provided_forecast_fill_method]').prop('disabled', true);
        }
    });
    if (forecast_type == 'event'){
        $('[name=provided_forecast_fill_method]')
            .prop('step', 1)
            .prop('min', 0)
            .prop('max', 1);
    }
}
