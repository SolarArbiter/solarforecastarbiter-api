// Onclick functions to check/uncheck visible table rows
// assumes the first td in each row contains a checkbox input
$(document).ready(function(){
    function setCheck(table_id, check_state) {
        rows = Array.from($(table_id+' tbody tr[visible="true"]'));
        rows.forEach(function(elem){
            elem.cells[0].children[0].checked = check_state;
        });
    };
    $('#check-button').click(function(){
        setCheck('#permission-table', true);
    });
    $('#uncheck-button').click(function(){
        setCheck('#permission-table', false);
    });
});
