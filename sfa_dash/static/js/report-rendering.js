/* 
 * Adds functionality for searching/nesting metrics plots. Plots should be
 * wrapped in a <div> element with class "metric-block" and the following data
 * attributes:
 *     data-category: The metric category, e.g. total, hourly.
 *     data-metric: The metric described in the plot.
 *     data-forecast: Name of the forecast.
 *
 * The content inside of the metric-block is arbitrary, this code only alters
 * the layout of the page.
 */
function hideEmptyMetricSections(){
    /* Hide all empty sections after a search for forecast.
     */
    metricSections = $('.plot-attribute-wrapper');
    metricSections.removeAttr('hidden');
    metricSections.prev().removeAttr('hidden');
    $('.plot-attribute-wrapper').each(function(){
        // this specific attribute selector is to avoid the less-specific
        // behavior of jquery's :hidden selector which will select any element
        // that is not currently visible. including child of hidden elements.
        if ($(this).find('.metric-block:not([hidden=hidden])').length == 0){
            $(this).attr('hidden', true);
            $(this).prev().attr('hidden', true)
        }
    });
}
function hideMetricsOnSearch(){
    /*
     * Hides metrics whose forecasts names do not match the search term.
     */
    searchTerm = $(".search").val().toLowerCase();
    $('.metric-block').removeAttr('hidden');
    $('[class*="collapse-forecast-"]').removeAttr('hidden');
    noMatch = $('.metric-block').filter(function(i, el){
        plotForecast = el.dataset.forecast.toLowerCase();
        return plotForecast != 'all' && plotForecast.indexOf(searchTerm) < 0;
    });

    // Hide the headers of non-matching forecasts to avoid empty sections
    noMatchHeaderClasses = new Set(noMatch.map(function(){return $(this).data('forecast')}));
    noMatchHeaderClasses.forEach(function(fx){
        headers = $(`.collapse-forecast-${fx.replace(/ /g,"-").toLowerCase()}`);
        noMatch = noMatch.add(headers);
    });
    noMatch.attr('hidden', true);

    // Apply sorting and load visible visible plots before hiding empty
    // sections. 
    applySorting();
    loadVisiblePlots();
    hideEmptyMetricSections();
}
function genericSort(a, b){
    if (a > b){
        return -1;
    } else if (a < b){
        return 1;
    }
    return 0;
}

function sortByMetric(a, b){
    return genericSort(a.dataset.metric, b.dataset.metric);
}

function sortByCategory(a, b){
    return genericSort(a.dataset.category, b.dataset.category);
}

function sortByForecast(a,b){
    return genericSort(a.dataset.forecast, b.dataset.forecast);
}

function selectSortFn(type){
    if (type == 'Category'){
        return sortByCategory;
    }else if (type == 'Forecast'){
        return sortByForecast;
    }else if (type == "Metric"){
        return sortByMetric;
    }
}

function humanReadableLabel(type, label){
    /* Converts the internal label for a metric or category to a human-friendly
     * format.
     *
     * WARNING: This function requires that the global variables 'deterministic_metrics'
     * and 'metric_categories' be supplied as json objects mapping internal
     * labels to their human-friendly versions.
     */
    if (type == 'Metric'){
        return deterministic_metrics[label];
    } else if (type == 'Category'){
        return metric_categories[label];
    } else {
        return label;
    }
}

function createContainerDiv(parentValue, type, value){
    /* Creates a heading and div for the type and value. The heading acts as a
     * collapse button for each div. When parentValue is not null, parentValue
     * is appended as a class to the div to differentiate between sub sections.
     *
     * e.g. If we are nesting by metrics->category->forecast, we need to be
     * able to select the 'total' category in each metric section without
     * expanding them all at once. So passing in the metric's value allows us
     * to select the specific category to expand like so:
     *     'data-wrapper-category-total.{metric name}'
     */
    parentValueClass = parentValue ? ' '+parentValue.replace(/ |\^/g, "-") : "";
    wrapperClass = `data-wrapper-${type.toLowerCase()}-${value.replace(/ |\^/g,"-").toLowerCase()}${parentValueClass}`

    label = humanReadableLabel(type, value);
    collapse_button = $(`<a role="button" data-toggle="collapse" class="report-plot-section-heading collapse-${type.toLowerCase()}-${value.replace(/ |\^/g,"-").toLowerCase()} collapsed"
                            data-target=".${wrapperClass.replace(/ /g,".")}">
                         <p class="h4 report-plot-section-heading-text">${type}: ${label}</p></a>`)
    wrapper = $(`<div class="plot-attribute-wrapper ${wrapperClass} collapse"></div>`);

    // register callback to load plots when expanded
    wrapper.on("show.bs.collapse", function(){
        $(this).addClass('loading-plots');
    }).on("shown.bs.collapse", function(){
        loadVisiblePlots();
        $(this).removeClass('loading-plots');
    });
    return [wrapper, collapse_button]
}

function createSubsetContainers(sortOrder, valueSet){
    /* Builds the containing divs based on the first two elements of the 
     * sort order such that each nested container has a 
     * data-wrapper-{field}-{value} class for later selection. Nested divs
     * will have the value of their parent div added as a class to
     * differentiate targets for collapsing.
     *
     * example:
     *   <div class="data-wrapper-metric-mae">
     *     <div class="data-wrapper-category-total mae">
     *     </div>
     *   </div>
     */
    container = $('<div class="plot-container"></div>');
    valueSet[0].forEach(function (firstSetItem){
        [top_level, top_collapse] = createContainerDiv(null, sortOrder[0], firstSetItem);
        valueSet[1].forEach(function (secondSetItem){
            [second_level, second_collapse] = createContainerDiv(
                firstSetItem,
                sortOrder[1],
                secondSetItem
            );
            top_level.append(second_collapse);
            top_level.append(second_level);
        })
        container.append(top_collapse);
        container.append(top_level);
    });
    container.find('a:first').removeClass('collapsed');
    firstElement = container.find('div.plot-attribute-wrapper:first');
    firstElement.addClass('show');
    firstElement.find('a').removeClass('collapsed');
    firstElement.find('div.plot-attribute-wrapper').addClass('show');
    return container;
}

function containerSelector(sortOrder, metricBlock){
    /*
     * Returns a selector for the proper container to insert the metricBlock
     * in to.
     */
    firstType = sortOrder[0].toLowerCase();
    firstValue = metricBlock.dataset[firstType].replace(/\s+|\^/g, '-').toLowerCase();
    secondType = sortOrder[1].toLowerCase();
    secondValue = metricBlock.dataset[secondType].replace(/\s+|\^/g, '-').toLowerCase();
    return `.data-wrapper-${firstType}-${firstValue} .data-wrapper-${secondType}-${secondValue}`;
}

function getSortedMetricBlocks(){
    /*
     * Builds and returns the new nested div structure based on the current
     * state of the sorting list.
     */
    
    // Determine the current order of the sorting list.
    sortOrder = $('.metric-sort .metric-sort-value').map(function(){
        return $(this).text();
    });

    // Create Sets from the unique metrics, categories and forecasts in the
    // report. These Sets will be used to create unique containers.
    categories = new Set($('.metric-block').map(function(){return this.dataset.category;}));
    metrics = new Set($('.metric-block').map(function(){return this.dataset.metric;}));
    forecasts = new Set($('.metric-block').map(function(){return this.dataset.forecast;}));

    // Create an ordered list of Sets based upon the current sorting order so
    // we can create containers from all permutations of the first two sets.
    orderedSets = sortOrder.map(function(){
        if (this == 'Category'){
            return categories;
        }else if(this == 'Forecast'){
            return forecasts;
        }else{
            return metrics;
        }
    });


    // Sort the metric blocks. Blocks should remain in order when they are
    // later sorted into their respective containers.
    sortedMetricBlocks = $('.metric-block').sort(selectSortFn(sortOrder[-1]));

    // Build nested divs for the first two sets of sorting attributes
    nestedContainers = createSubsetContainers(sortOrder, orderedSets);

    // Insert each metric block into it's container.
    $('.metric-block').each(function(){
        nestedContainers.find(containerSelector(sortOrder, this)).append(this);
    });
    return nestedContainers;
}

function applySorting(event, ui){
    /*
     * Callback fired when the sorting order changes. Replaces the html within
     * the outermost wrapper div with the sorted result.
     */
    $("#metric-plot-wrapper").html(getSortedMetricBlocks());
}

function sortingLi(sortBy){
    /*
     * Generate a list element with prefixed up/down arrows for controlling the
     * sorting order.
     */
    liElem = $('<li class="metric-sort"></li>');
    upButton = $('<a role="button" class="arrow-up"></a>');
    upButton.click(upButtonCallback);
    downButton = $('<a role="button" class="arrow-down"></a>');
    downButton.click(downButtonCallback);
    liElem.append(upButton);
    liElem.append(downButton);
    liElem.append(`<span class="metric-sort-value">${sortBy}</span>`);
    return liElem;
}


function upButtonCallback(){
    // Move the current element's parent li before the next li in the list.
    $(this).parent().prev().before($(this).parent());
    hideMetricsOnSearch();
}


function downButtonCallback(){
    // Move the current element's parent li after the next li in the list.
    $(this).parent().next().after($(this).parent());
    hideMetricsOnSearch();
}


async function renderPlotly(div, plotSpec){
    Plotly.newPlot(div, plotSpec);
}


function loadVisiblePlots(){
    for(var key in metric_plots){
        if(metric_plots.hasOwnProperty(key)){
            var plotDiv = $(`#${key}`);
            var isHidden = plotDiv.attr('hidden');
            var parentVisible = plotDiv.parent().hasClass('show');
            var plotExists = plotDiv.hasClass('js-plotly-plot');
            
            if(!isHidden && !plotExists && parentVisible){
                renderPlotly(plotDiv[0], metric_plots[key]);
            }
        }
    }
}

$(document).ready(function(){
    /* Create sorting widgets to insert into the template, we do this here
     * because there may be cases where we won't include js, and want to
     * statically print all of the metrics.
     */
    sortingWidgets = $('<ul id="metrics-sort-list"></ul>');
    sortingWidgets.append(sortingLi("Metric"));
    sortingWidgets.append(sortingLi("Category"));
    sortingWidgets.append(sortingLi("Forecast"));
    searchBar = $('<input type="text" placeholder="Search by forecast name" class="search">');
    searchBar.keyup(hideMetricsOnSearch);
    metricSortingWrapper = $('<div id="metric-sorting"></div>')
    metricSortingWrapper.prepend(searchBar);
    metricSortingWrapper.prepend(sortingWidgets);
    metricSortingWrapper.prepend($('<div><b>Use the arrows below to reorder the metrics plots.</b><div>'));
    $('#metric-plot-wrapper').before($(metricSortingWrapper));
    hideMetricsOnSearch();
});
