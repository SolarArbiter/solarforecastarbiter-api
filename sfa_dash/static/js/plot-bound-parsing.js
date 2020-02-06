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
