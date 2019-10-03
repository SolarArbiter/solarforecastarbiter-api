function ParseStartEnd(){
    // Manually parse this string to avoid the implicit tz conversion based on
    // the users browser. We're asking users for UTC so, manually add Z to the end of
    // the dt string.
    startYear = $('#start-date').val().slice(0, 4);
    startMonth = $('#start-date').val().slice(5, 7);
    startDay = $('#start-date').val().slice(-2);
    $('#start').val(startYear+'-'+startMonth+'-'+startDay+'T'+$('#start-time').val()+'Z');

    endYear = $('#end-date').val().slice(0, 4);
    endMonth = $('#end-date').val().slice(5, 7);
    endDay = $('#end-date').val().slice(-2);
    $('#end').val(endYear+'-'+endMonth+'-'+endDay+'T'+$('#end-time').val()+'Z');
}
$(document).ready(function(){
    // To mimic the behavior of the backend, parse the urp parameters
    // to utc for setting the current value of the start/end widgets.
    var urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('start')){
        start = new Date(urlParams.get('start'))
        day = start.getUTCDate().toString().padStart(2, 0);
        month = (start.getUTCMonth()+1).toString().padStart(2, 0);
        $('#start-date').val(start.getUTCFullYear()+"-"+(month)+"-"+(day));
        hours = start.getUTCHours().toString().padStart(2, 0);
        minutes = start.getUTCMinutes().toString().padStart(2, 0);
        $('#start-time').val(hours+':'+minutes);
    }
    if (urlParams.has('end')){
        end = new Date(urlParams.get('end'))
        day = end.getUTCDate().toString().padStart(2, 0);
        month = (end.getUTCMonth()+1).toString().padStart(2, 0);
        $('#end-date').val(end.getUTCFullYear()+"-"+(month)+"-"+(day));
        hours = end.getUTCHours().toString().padStart(2, 0);
        minutes = end.getUTCMinutes().toString().padStart(2, 0);
        $('#end-time').val(hours+':'+minutes);
    }
})
