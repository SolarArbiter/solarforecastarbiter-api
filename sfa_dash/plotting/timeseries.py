from bokeh.embed import components
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
import pandas as pd

from sfa_dash.filters import api_varname_to_units, api_to_dash_varname


def build_df(json):
    """Parses a Solar Forecast Arbiter API JSON
    response into a pandas dataframe

    Parameters
    ----------
    json: dict
        The parsed API response from a /values endpoints.

    Returns
    -------
    Dataframe
        A dataframe parsed from the response's 'values' field.
    """
    values = json.get('values')
    if not values:
        raise ValueError('Empty Values field')
    df = pd.DataFrame(values)
    df = df.set_index('timestamp')
    df.index = pd.to_datetime(df.index)
    return df


def build_y_axis_label(metadata):
    """Builds a y axis label from a metadata object.

    Parameters
    ----------
    metadata:
        Metadata dictionary for the resource. Must include the "variable"
        key.

    Returns
    string
        The appropriate x axis label.
    """
    variable = metadata['variable']
    var_name = api_to_dash_varname(variable)
    units = api_varname_to_units(variable)
    label = f'{var_name} {units}'
    return label


def build_figure_title(metadata, start, end):
    """Builds a title for the plot from a metadata object.

    Parameters
    ----------
    metadata: dict
        Metadata dictionary used to label the plot. Must include a 'site'
        key containing a nested site object as well as the 'variable' key.

    start: datetime-like
        The start of the interval being plot.

    end: datetime-like
        The end of the interval being plot.

    Returns
    -------
    string
        The appropriate figure title.
    """
    object_name = metadata['name']
    start_string = start.strftime('%Y-%m-%d %H:%M')
    end_string = end.strftime('%Y-%m-%d %H:%M')
    figure_title = (f'{object_name} {start_string} to {end_string} UTC')
    return figure_title


def generate_figure(metadata, json_value_response):
    """Creates a bokeh figure from API responses

    Parameters
    ----------
    metadata: dict
        Metadata dictionary used to label the plot. Must include
        a full nested site object. Only works with Metadata for
        types observation, forecast and cdf_forecast.

    json_response: dict
        The json response parsed into a dictionary.

    Raises
    ------
    ValueError
        When the supplied json contains an empty "values" field.
    """
    df = build_df(json_value_response)
    period_start = df.index[0]
    period_end = df.index[-1]
    # If there is more than 3 days of data, limit the default x_range
    # to display only the most recent 3 day. Users will be able to scroll
    # to see past data.
    x_range_start = df.index[df.index.get_loc(period_end - pd.Timedelta('3d'),
                                              method='bfill')]
    cds = ColumnDataSource(df)
    figure_title = build_figure_title(metadata, period_start, period_end)
    fig = figure(title=figure_title, sizing_mode='scale_width', plot_width=900,
                 plot_height=300, x_range=(x_range_start, period_end),
                 x_axis_type='datetime', tools='pan,wheel_zoom,reset')
    fig.line(x='timestamp', y='value', source=cds)
    fig.yaxis.axis_label = build_y_axis_label(metadata)
    fig.xaxis.axis_label = 'Time'
    return components(fig)
