$(document).ready(function() {
    $('.report-details-expander').click(function(){
        $(this).next().removeAttr('hidden');
    });
    $('.report-details-closer').click(function(){
        $(this).parent().attr('hidden', true);
    });
})
