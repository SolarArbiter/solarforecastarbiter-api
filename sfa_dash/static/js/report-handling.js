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
        function insertSelectOptions(index){
            /*
             * Generates select options for a observation, forecast pair
             */
            var observation_selector = `[name="observation-${index}"]`;
            var forecast_selector = `[name="forecast-${index}"]`;
            $.each(page_data['observations'], function(){
                $(observation_selector).append(
                    $('<option></option>')
                        .html(this.name)
                        .val(this.observation_id)
                        .attr('data-site-id', this.site_id));
            });
            $.each(page_data['forecasts'], function(){
                $(forecast_selector).append(
                    $('<option></option>')
                        .html(this.name)
                        .val(this.forecast_id)
                        .attr('data-site-id', this.site_id));
            });
            $(observation_selector).change(function (){
                /*
                 * React to a change in observation to hide any non-applicable forecasts from the
                 * select list and remove the current selection if it is invalid.
                 */
                observation_site = $(observation_selector + ' option:selected').attr('data-site-id')
                if (observation_site){
                    forecasts = $(forecast_selector + ' option').slice(1);
                    forecasts.removeAttr('hidden');
                    forecasts.each(function (fx){
                        if (this.dataset.siteId != observation_site){
                            this.hidden = true;
                            // If the current selected forecast is invalid, reset the selection
                            if (this.dataset.siteId != $(forecast_selector).val()){
                                $(forecast_selector).val('select a forecast');
                            }
                        }
                    });
                }
            });
        }
  
        function newPair(){
          /* 
           *  Generate the base HTML for a new pair of observation, forecast select options.
           *  The options should be initialized by calling insertSelectOptions with the
           *  current pair index
           */
          var new_object_pair = $(`<li class="object-pair object-pair-${pair_index}">
                      <div class="form-element">
                        <label>Observation</label><br>
                        <div class="input-wrapper">
                          <select class="form-control observation-field" name="observation-${pair_index}" required>
                          <option disabled value selected>select an observation</option>
                          </select>
                        </div>
                        <a data-toggle="collapse" data-target=".observation-${pair_index}-help-text" role="button" href="" class="help-button">?</a>
                        <span class="observation-${pair_index}-help-text form-text text-muted help-text collapse" aria-hidden="">Observation to compare Forecast against.</span>
                      </div>
                      <div class="form-element">
                        <label>Forecast</label><br>
                        <div class="input-wrapper">
                          <select class="form-control forecast-field" name="forecast-${pair_index}" required>
                          <option disabled value selected>select a forecast</option>
                          </select>
                        </div>
                        <a data-toggle="collapse" data-target=".forecast-${pair_index}-help-text" role="button" href="" class="help-button">?</a>
                        <span class="forecast-${pair_index}-help-text form-text text-muted help-text collapse" aria-hidden="">Forecast to compare.</span>
                      </div>
                   <a role="button" class="object-pair-delete-button">x</a>
                   </li>`);
            var remove_button = new_object_pair.find(".object-pair-delete-button");
            remove_button.click(function(){new_object_pair.remove();});
            return new_object_pair;
        }
        
  
        /*
         * Initialize pair_index, and a global handle to the object_pair container
         */
        pair_container = $('.object-pair-list');
        pair_index = 0;
        
        // Initialize the first object_pair
        pair_container.append(newPair());
        insertSelectOptions(pair_index);
        pair_index++;
  
        $('#add-object-pair').click(function(){
            /*
             * 'Add a Forecast, Observation pair button callback
             *
             * On click, appends a new pair of inputs inside the 'pair_container' div, initializes
             * their select options and increment the pair_index.
             */
            pair_container.append(newPair());
            insertSelectOptions(pair_index);
            pair_index++;
        });
    }
    registerDatetimeValidator('period-start');
    registerDatetimeValidator('period-end')
});
