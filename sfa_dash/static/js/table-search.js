/* Jquery for filtering and searching tables.
 * 
 * For simple column filtering, give an html table header an id of '<name>-header' and
 * give each td in its column the '<name>-column' class. add a call to the block of
 * createFilterOptions() functions at the bottom of the file with the <name> applied to 
 * your html.
 *
 * Defines filter functions that return a jquery object list of items that need to be hidden
 * from the table. The functions should be added to the `toHideFns` array to be called by
 * callback functions. At the end of the file, your widgets should have their callback set to
 * the `applyTableFilters` function.
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
         * Creates a list of rows to hide  based on which rows do not contain 
         * the current search term.
         */
        var searchTerm = $(".search").val();
        var searchSplit = searchTerm.replace(/ /g, "'):containsi('")
        return $(".results tbody tr").not(":containsi('" + searchSplit + "')")
    }

    function filterColumns(optionSelector, columnSelector){
        /*
         * Returns a list of rows to hide where the row does not contain a <td>
         * with class columnSelector and innerHTML matching a the checked
         * options with class optionSelector.
         *
         * @param: {string} optionSelector  jQuery selector for checkbox
         *                                  elements to base filtering off of.
         *
         * @param: {string  columnSelector  jQuery selector of the td element
         *                                  labelling it a member of the column
         *                                  to filter.
         *
         * @returns: {jQuery} A collection of tr elements that do not match the
         *                    selected filtering options.
         */
        rowsToHide = $([]);
        $(optionSelector).each(function (e){
            if (!this.checked){
                rowsToHide = rowsToHide.add(
                    $(`${columnSelector}:contains("${this.value}")`).parent());
            }
        });
        return rowsToHide
    }
    /*
     * END filter functions
     */
    
    /*
     * Functions to apply filters.
     */

    // toHideFns is a list of functions that are to be iterated through to
    // collect a list of elements to hide after a filter or search has changed.
    // Callbacks can be appended to this list to ensure that elements are 
    // hidden through updates.
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
    
    function createFilterOptions(columnName){
        /*
         * Creates a collapsible filter menu if a table header exists with id
         * columnName-header. Adds an appropriate callback to the toHideFns
         * array.
         *
         * This expects that the <th> element has id '<columnName>-header' and
         * that the corresponding <td> elements are labeled with class
         * '<columnName>-column'
         */
        if ($(`#${columnName}-header`).length){
            columnTitle = $(`#${columnName}-header`).text();
            // Wrap the table header in a button that will collapse the list
            // of checkboxes for filtering.
            $(`#${columnName}-header`).wrapInner(
                `<button type="button" class="btn btn-th dropdown-toggle table-option-toggle"
                  data-toggle="collapse" data-target="#${columnName}-filters">
                  </button>`);                           
            
            // Create a Set of options from the contents of each of the column's
            // <td> elements
            var availableOptions = new Set($(`.${columnName}-column`).map(function(){
                return $(this).text();
            }));

            // Collapsible div containing the list of checkboxes, this is the 
            // target of the button that the table header was wrapped in.
            var filter_div = $(`
                <div id='${columnName}-filters' class='collapse table-filters'>
                    Filter by ${columnTitle}
                    <a href='#' role='button' id='${columnName}-filter-collapse' class="table-option-collapse">x</a>
                    <br/><hr>
                    <ul class='${columnName}-filter-options table-filter-options'></ul>
                </div>`);
            filter_div.appendTo(`#${columnName}-header`);

            // Create a checkbox input for each option in the set.
            availableOptions.forEach(function (e) {
                $(`.${columnName}-filter-options`).append(`
                    <li><input class="${columnName}-filter-option" value="${e}" type="checkbox" checked>${e}</li>`)});
            $(`#${columnName}-filter-collapse`).click(function() {
                $(`#${columnName}-filters`).collapse('toggle');
            });
            
            // Append a filtering function to the list of filter functions to
            // be called onChange
            toHideFns.push(function(){
                return filterColumns(
                    `.${columnName}-filter-option`,
                    `.${columnName}-column`
                );
            });
            // Register an onchange event to call the function that applies
            // all of the filtering functions found in toHideFns.
            $(`.${columnName}-filter-option`).change(applyTableFilters);
        }
    }

    //Always include a generic search for tables.
    toHideFns.push(searchTable);
    
    // Call createFilterOptions with a column name here to have it
    // become automagically filterable.
    createFilterOptions('provider');
    createFilterOptions('variable');
    createFilterOptions('site');
    createFilterOptions('site-or-aggregate');
    createFilterOptions('action');
    createFilterOptions('object-type');
    createFilterOptions('applies-to-all');

    /*
     * Register DOM element callbacks
     */
    $(".search").keyup(applyTableFilters);
    if ($(".search").val() != null){
        // if searchbar is filled on page load, apply filters
        applyTableFilters();
    }
});
