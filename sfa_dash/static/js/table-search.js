/* Jquery for filtering and searching tables.
 * Defines filter functions that return a jquery object list of items that need to be hidden
 * from the table. The functions should be added to the `toHideFns` array to be called by
 * callback functions. At the end of the file, your widgets should have their callback set to
 * the `applyTableFilters` function
 *
 * The containsi filter was borrowed from the below codepen:
 * https://codepen.io/adobewordpress/pen/gbewLV
 */
$(document).ready(function() {
    /* Add containsi filter to JQuery selectors that selects for any word in a phrase */
    $.extend($.expr[':'], {'containsi': function(elem, i, match, array){
            lowerElementText = (elem.textContent || elem.innerText || '').toLowerCase()
            // Here, match is the array the anonymous filter  function was applied on,
            // and the 3rd element is the text of the search box.
            return lowerElementText.indexOf((match[3] || "").toLowerCase()) >= 0;
        }
    });

    /*
     * Filter functions
     *
     * Check some state within the dom, and return a jquery object list of elements
     * to hide.
     */
    function searchTable() {
        /*
         * Reads the value of the search input and creates a list of rows to hide
         * based on which rows do not contain the search term
         */
        var searchTerm = $(".search").val();
        var searchSplit = searchTerm.replace(/ /g, "'):containsi('")
        return $(".results tbody tr").not(":containsi('" + searchSplit + "')")
    }
    function filteredOrgs() {
        /*
         * Iterates through the `.org-filter-option` checkboxes, for each unchecked box,
         * builds a list of tr elements whose `.provider-column` fields contain the
         * checkboxes value and returns the concatenated list.
         */
        orgsToHide = $([]);
        $('.org-filter-option').each(function (e){
            if (!this.checked){
                orgsToHide = orgsToHide.add($(`.provider-column:contains("${this.value}")`).parent());
            }
        });
        return orgsToHide
    }
    /*
     * Filter application functions
     */
    var toHideFns = []
    function allHiddenElements(){
        /*
         * Returns a JQuery object list of rows that need to be hidden
         * by concatenating the results of calls to the toHideFns.
         */
        elements = $([]);
        toHideFns.forEach(function(e){
            elements = elements.add(e());
        });
        return elements
    }
    function applyTableFilters() {
        /*
         * Gets a list of table rows, and then builds a list of all the
         * rows to be excluded due to filters, removes the rows to hide
         * from all rows, sets the remainder to visible and hides the
         * others.
         */
        allRows = $(".results tbody tr").not('.warning.no-result');
        rowsToHide = allHiddenElements();
        visibleRows = allRows.not(rowsToHide);
        visibleRows.attr('visible', 'true');
        rowsToHide.attr('visible', 'false');
        
        var jobCount = $('.results tbody tr[visible="true"]').length;
        if(jobCount == '0') {$('.no-result').show();}
        else {$('.no-result').hide();}
    }
    toHideFns.push(searchTable);
    /*
     * If the Provider header id exists, build a dropdown ul of checkboxes from the
     * list of organizations in the table.
     */
    if ($('#provider-header').length){
        var availableOrgs = new Set([]);
        var orgs = $(".provider-column")
        for (i = 0; i < orgs.length; i++) {
            availableOrgs.add(orgs[i].textContent);
        }
        var filter_div = $("<div id='org-filters' class='collapse'>Filter by Organization <a href='#' role='button' id='org-filter-collapse'></a><br/><hr><ul class='org-filter-options'></ul></div>");
        filter_div.appendTo("#provider-header");
        availableOrgs.forEach(function (e) {$(".org-filter-options").append(`<li><input class="org-filter-option"value="${e}" type="checkbox" checked>${e}</li>`)});
        $('#org-filter-collapse').click(function() {
            $('#org-filters').collapse('toggle');
        });
        toHideFns.push(filteredOrgs);
    }
    /*
     * Register DOM element callbacks
     */
    $(".search").keyup(applyTableFilters);
    if ($(".search").val() != null){
        // if searchbar is filled on page load, apply filters
        applyTableFilters();
    }
    $(".org-filter-option").change(applyTableFilters);

});
