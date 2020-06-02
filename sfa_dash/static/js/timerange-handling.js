/* The MAX_DATA_RANGE_DAYS and MAX_PLOT_DATAPOINTS variables are expected to
 * exist as global variables injected by flask.
 */
function ParseStartEnd(){
    // Manually parse this string to avoid the implicit tz conversion based on
    // the users browser. We're asking users for UTC so, manually add Z to the end of
    // the dt string.
    startYear = $('#start-date').val().slice(0, 4);
    startMonth = $('#start-date').val().slice(5, 7);
    startDay = $('#start-date').val().slice(-2);
    $('.start').val(startYear+'-'+startMonth+'-'+startDay+'T'+$('#start-time').val()+'Z');

    endYear = $('#end-date').val().slice(0, 4);
    endMonth = $('#end-date').val().slice(5, 7);
    endDay = $('#end-date').val().slice(-2);
    $('.end').val(endYear+'-'+endMonth+'-'+endDay+'T'+$('#end-time').val()+'Z');
}

function getDateValues(){
    /* Returns the current start and end values as Date objects */
    start_date = document.getElementsByName('period-start-date')[0].value;
    start_time = document.getElementsByName('period-start-time')[0].value;
    end_date = document.getElementsByName('period-end-date')[0].value;
    end_time = document.getElementsByName('period-end-time')[0].value;

    start = new Date(start_date+' '+start_time);
    end = new Date(end_date+' '+end_time);
    return [start, end]
}

function insertWarning(title, msg){
    $('#form-errors').append(`<li class="alert alert-danger"><p><b>${title}: </b>${msg}</p></li>`);
}

function toggleDownloadUpdate(){
    /* Enable or disable download and update graph buttons based on the current
     * selected timerange.
     */
    $('#form-errors').empty()
    timerange = getDateValues();
    miliseconds = timerange[1] - timerange[0];
    days = miliseconds / (1000 * 60 * 60 * 24);
    if (days > 0){
        // limit maximum amount of data to download
        if (days > MAX_DATA_RANGE_DAYS){
            // disable download and plot update
            $('#download-submit').attr('disabled', true);
            $('#plot-range-adjust-submit').attr('disabled', true);

            insertWarning(
                'Maximum timerange exceeded',
                'Maximum of one year of data may be requested at once.'
            );
        } else {
            // enable download
            $('#download-submit').removeAttr('disabled');
            $('#plot-range-adjust-submit').removeAttr('disabled');
            // check if within limits for plotting
            if (typeof metadata !== 'undefined' && metadata.hasOwnProperty('interval_length')){
                var interval_length = parseInt(metadata['interval_length']);
            } else {
                var interval_length = 1;
            }
            var intervals = miliseconds / (interval_length * 1000 * 60);
            
            if (intervals > MAX_PLOT_DATAPOINTS){
                $('#plot-range-adjust-submit').attr('disabled', true);
                insertWarning(
                    'Plotting disabled',
                    `Maximum plottable points exceeded. Timerange includes 
                    ${intervals} data points and the maximum is 
                    ${MAX_PLOT_DATAPOINTS}.`);
            } else {
                $('#plot-range-adjust-submit').removeAttr('disabled');
            }
        }
    } else {
        insertWarning('Time range', 'Start must be before end.');
        $('#plot-range-adjust-submit').attr('disabled', true);
        $('#download-submit').attr('disabled', true);

    }
}

$(document).ready(function(){
    $('[name=period-start-date]').change(toggleDownloadUpdate);
    $('[name=period-start-time]').change(toggleDownloadUpdate);
    $('[name=period-end-date]').change(toggleDownloadUpdate);
    $('[name=period-end-time]').change(toggleDownloadUpdate);
    $('[name=period-start-date]').change();
    $('[name=period-end-date]').change();
});
