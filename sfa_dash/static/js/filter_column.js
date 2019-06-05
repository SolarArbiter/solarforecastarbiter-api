/* Creates a set of organization names from the value of all td with 'provider-column'
 * class and creates a drop-down list of checkboxes for hiding table rows by organizaiton
 */
$(document).ready(function() {
    if ($('#provider-header').length){
        var availableOrgs = new Set([]);
        var orgs = $(".provider-column");
        for (i = 0; i < orgs.length; i++) {
            availableOrgs.add(orgs[i].textContent);
        }
        var filter_div = $("<div id='org-filters' class='collapse'>Filter by Organization <a href='#' role='button' id='org-filter-collapse'></a><br/><hr><ul class='org-filter-options'></ul></div>");
        filter_div.appendTo("#provider-header");
        availableOrgs.forEach(function (e) {$(".org-filter-options").append(`<li><input class="org-filter-option"value="${e}" type="checkbox" checked>${e}</li>`)});
        $('#org-filter-collapse').click(function() {
            $('#org-filters').collapse('toggle');
        });
        $(".org-filter-option").change(function() {
            console.log(`${this.checked}`);
            console.log(` content: ${this.value}`);
            if (this.checked) {
                $(`.provider-column:contains("${this.value}")`).parent().show();
            } else {
               $(`.provider-column:contains("${this.value}")`).parent().hide();
            }
        });
    }
});
