/*
 *  Creates inputs for defining observation, forecast pairs for a report.
 */
$(document).ready(function() {
    function registerDatetimeValidator(input_name){
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
    if ($('.object-pair-list')[0]){
        function addPair(obsName, obsId, fxName, fxId){
            var new_object_pair = $(`<div class="object-pair object-pair-${pair_index}">
                      <div class="form-element">
                        <div class="input-wrapper">
                          <input type="text" class="form-control observation-field" name="observation-name-${pair_index}"  required disabled value="${obsName}"/>
                          <input type="hidden" class="form-control observation-field" name="observation-id-${pair_index}" required value="${obsId}"/>
                        </div>
                      </div>
                      <div class="form-element">
                        <div class="input-wrapper">
                          <input type="text" class="form-control forecast-field" name="forecast-name-${pair_index}" required disabled value="${fxName}"/>
                          <input type="hidden" class="form-control forecast-field" name="forecast-id-${pair_index}" required value="${fxId}"/>
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
        
        function createPairSelector(){
          /* 
           * Generate the two select widgets and button for adding new object pairs  
           */
          var widgetContainer = $('<div class="pair-selector-wrapper show"></div>');
          var obsSelector = $(`<div class="form-element">
                        <label>Select an Observation</label><br>
                        <div class="input-wrapper">
                          <select id="observation-select" class="form-control observation-field" name="observation-select" size="15">
                          </select>
                        </div>
                      </div>`);
          var fxSelector = $(`<div class="form-element">
                        <label>Select a Forecast</label><br>
                        <div class="input-wrapper">
                          <select id="forecast-select" class="form-control forecast-field" name="forecast-select" size="15">
                            <option name="no-forecasts" disabled>No matching Forecasts</option>
                          </select>
                        </div>
                     </div>`);
            var addButton = $('<a role="button" class="btn btn-primary" id="add-object-pair" style="padding-left: 1em">Add a Forecast, Observation pair</a>');
            widgetContainer.append(obsSelector);
            widgetContainer.append(fxSelector);
            widgetContainer.append(addButton);

            // add options to the select elements from page_data
            var observation_select = obsSelector.find('#observation-select');
            var forecast_select = fxSelector.find('#forecast-select');
            $.each(page_data['observations'], function(){
                observation_select.append(
                    $('<option></option>')
                        .html(this.name)
                        .val(this.observation_id)
                        .attr('data-site-id', this.site_id)
                        .attr('data-variable', this.variable));
            });
            $.each(page_data['forecasts'], function(){
                forecast_select.append(
                    $('<option></option>')
                        .html(this.name)
                        .val(this.forecast_id)
                        .attr('hidden', true)
                        .attr('data-site-id', this.site_id)
                        .attr('data-variable', this.variable));
            });
            observation_select.change(function (){
                /*
                 * React to a change in observation to hide any non-applicable forecasts from the
                 * select list and remove the current selection if it is invalid.
                 */
                observation = observation_select.find('option:selected');
                observation_site = observation.attr('data-site-id');
                observation_variable = observation.attr('data-variable');
                if (observation_site){
                    forecasts = forecast_select.find('option');
                    forecasts.removeAttr('hidden');
                    forecasts.each(function (fx){
                        if (this.dataset.siteId != observation_site || this.dataset.variable != observation_variable){
                            this.hidden = true;
                        } else if (this.hidden){
                            this.hidden = false;
                        }
                    });
                    // if the currently selected forecast is hidden, deselect it.
                    if (forecast_select.find(':selected')[0] && forecast_select.find(':selected')[0].hidden ) {
                        forecast_select.val('');
                    }
                    // Hide/show the "no matching forecasts options
                    if (forecast_select.find('option').not(":hidden").length == 0){
                        $('[name="no-forecasts"]')[0].hidden = false;
                    } else {
                        $('[name="no-forecasts"]')[0].hidden = true;
                    }
                }
            });
            addButton.click(function(){
                /*
                 * 'Add a Forecast, Observation pair button on button click
                 *
                 * On click, appends a new pair of inputs inside the 'pair_container' div, initializes
                 * their select options and increment the pair_index.
                 */
                // check if both inputs have a selection
                if (observation_select.val() && forecast_select.val()){
                    var selected_observation = observation_select.find('option:selected')[0];
                    var selected_forecast = forecast_select.find('option:selected')[0];
                    pair = addPair(selected_observation.text,
                                   selected_observation.value,
                                   selected_forecast.text,
                                   selected_forecast.value);
                    
                    pair_container.append(pair);
                    pair_index++;
                    $(".empty-reports-list")[0].hidden = true;
                    forecast_select.css('border', '');
                    observation_select.css('border', '');
                } else {
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
        
        pair_selector = createPairSelector();
        pair_control_container.append($('<a role="button" class="full-width object-pair-button" data-toggle="collapse" data-target=".pair-selector-wrapper">Add Observation Forecast pairs</a>'));
        pair_control_container.append(pair_selector);
        
    }
    registerDatetimeValidator('period-start');
    registerDatetimeValidator('period-end')
});
