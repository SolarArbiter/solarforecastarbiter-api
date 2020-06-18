""" Utility classes/functions. Mostly for handling api data.
"""
import json
from copy import deepcopy


from flask import render_template, url_for, request, make_response
from solarforecastarbiter import datamodel
from solarforecastarbiter.io import utils as io_utils
from solarforecastarbiter.plotting import timeseries


from sfa_dash.api_interface import (sites, forecasts, observations,
                                    cdf_forecast_groups, aggregates)
from sfa_dash.errors import DataRequestException


class DataTables(object):
    """Class used to render out listing (table) templates when there are
    intermediate requests to be made or the data must be massaged into
    something suitable for display.
    """
    observation_template = 'data/table/observation_table.html'
    forecast_template = 'data/table/forecast_table.html'
    site_template = 'data/table/site_table.html'
    cdf_forecast_template = 'data/table/cdf_forecast_table.html'

    @classmethod
    def creation_link(cls, data_type, site_id=None, aggregate_id=None):
        """Supplies the url for forms to create a new object of type `data_type`
        for the given site or aggregate, else returns None.
        """
        if site_id is not None:
            return url_for(f'forms.create_{data_type}', uuid=site_id)
        elif aggregate_id is not None:
            return url_for(f'forms.create_aggregate_{data_type}',
                           uuid=aggregate_id)
        else:
            return None

    @classmethod
    def create_table_elements(cls, data_list, id_key, view_name):
        """Creates a list of objects to be rendered as table by jinja template.
        This method handles types with a reference to a site or aggregate.
        Types are Observation, Forecast, and CDF Forecast Group.

        Parameters
        ----------
        data_list: list of dicts
            List of metadata dictionaries as returned from the API.
        id_key: str
            The name of the UUID of the metadata. e.g. `observation_id`
        view_name: str
            The dashboard view that handles displaying a single object of the
            given type. e.g. `data_dashboard.observation_view`.

        Returns
        -------
        list of dict
            A list of dictionaries with the following keys for displaying as a
            table.

            name:     Name of the forecast/observation.
            variable: Variable recorded by this object.
            provider: Name of the organization tha created the object
            location: A link displaying the site or aggregate name and linking
                      to its page on the dashboard. If the site or aggregate
                      cannot be read, this is set to Site/Aggregate
                      unavailable.
            link:     The URL for viewing the full metadata and timeseries of
                      the object.
        """
        sites_list = sites.list_metadata()
        location_dict = {site['site_id']: site for site in sites_list}
        if id_key != 'observation_id':
            no_location_text = 'Site/Aggregate unavailable'
            aggregates_list = aggregates.list_metadata()
            location_dict.update({agg['aggregate_id']: agg
                                  for agg in aggregates_list})
        else:
            no_location_text = 'Site unavailable'
        table_rows = []
        for data in data_list:
            table_row = {}
            if data.get('site_id') is not None:
                location_id = data['site_id']
                location_view_name = 'data_dashboard.site_view'
            elif data.get('aggregate_id') is not None:
                location_id = data['aggregate_id']
                location_view_name = 'data_dashboard.aggregate_view'
            else:
                location_id = None
            location = location_dict.get(location_id)
            if location is not None:
                location_name = location['name']
                location_href = url_for(location_view_name,
                                        uuid=location_id)
                location_link = (f'<a href="{location_href}">'
                                 f'{location_name}</a>')
            else:
                location_link = no_location_text
            table_row['name'] = data['name']
            table_row['variable'] = data['variable']
            table_row['provider'] = data.get('provider', '')
            table_row['location'] = location_link
            table_row['link'] = url_for(view_name,
                                        uuid=data[id_key])
            table_rows.append(table_row)
        return table_rows

    @classmethod
    def create_site_table_elements(cls, data_list):
        """Creates a dictionary to feed to the Site table template as the
        `table_rows` parameter.

        Parameters
        ----------
        data_list: list
            List of site metadata dictionaries, typically an API response from
            the /sites/ endpoint.

        Returns
        -------
        dict
            A dict of site data to pass to the template.
        """
        table_rows = []
        for data in data_list:
            table_row = {}
            table_row['name'] = data['name']
            table_row['provider'] = data.get('provider', '')
            table_row['latitude'] = data.get('latitude', '')
            table_row['longitude'] = data.get('longitude', '')
            table_row['climate_zones'] = data.get('climate_zones', [])
            table_row['link'] = url_for('data_dashboard.site_view',
                                        uuid=data['site_id'])
            table_rows.append(table_row)
        return table_rows

    @classmethod
    def get_observation_table(cls, site_id=None, aggregate_id=None):
        """Generates an html element containing a table of Observations. Uses
        :py:func:`create_table_elements` to format data for templating.

        Parameters
        ----------
        site_id: string
            The UUID of a site to filter for.

        obs_data: list of dict
          The observation metadata list as returned by the api.

        Returns
        -------
        string
            Rendered HTML table with search bar and a 'Create
            new Observation' button.
        """
        creation_link = cls.creation_link('observation', site_id=site_id)
        obs_data = observations.list_metadata(site_id=site_id)
        rows = cls.create_table_elements(
            obs_data,
            'observation_id',
            'data_dashboard.observation_view')
        rendered_table = render_template(cls.observation_template,
                                         table_rows=rows,
                                         creation_link=creation_link)
        return rendered_table, obs_data

    @classmethod
    def get_forecast_table(cls, site_id=None, aggregate_id=None):
        """Generates an html element containing a table of Forecasts. Uses
        :py:func:`create_table_elements` to format data for templating.


        Parameters
        ----------
        site_id: string
            The UUID of a site to filter for.
        forecast_data: list of dict
          The forecast metadata list as returned by the api.

        Returns
        -------
        rendered_table: string
            Rendered HTML table with search bar and a 'Create
            new Forecast' button.
        forecast_data: list of dict

        Raises
        ------
        DataRequestException
            If a site_id is passed and the user does not have access
            to that site or some other api error has occurred.
        """
        if site_id is not None or aggregate_id is not None:
            creation_link = cls.creation_link(
                'forecast', site_id=site_id, aggregate_id=aggregate_id)
        else:
            creation_link = None

        forecast_data = forecasts.list_metadata(
            site_id=site_id, aggregate_id=aggregate_id)
        rows = cls.create_table_elements(
            forecast_data,
            'forecast_id',
            'data_dashboard.forecast_view')
        rendered_table = render_template(cls.forecast_template,
                                         table_rows=rows,
                                         creation_link=creation_link)
        return rendered_table, forecast_data

    @classmethod
    def get_cdf_forecast_table(cls, site_id=None, aggregate_id=None):
        """Generates an html element containing a table of CDF Forecasts. Uses
        :py:func:`create_table_elements` to format data for templating.


        Parameters
        ----------
        site_id: string, optional
            The UUID of a site to filter for.

        Returns
        -------
        string
            Rendered HTML table with search bar and a 'Create
            new Probabilistic Forecast' button.
        cdf_forecast_data: list of dict
          The cdf forecast metadata list as returned by the api.
        Raises
        ------
        DataRequestException
            If a site_id is passed and the user does not have access
            to that site or some other api error has occurred.
        """
        if site_id is not None or aggregate_id is not None:
            creation_link = cls.creation_link(
                'cdf_forecast_group',
                site_id=site_id,
                aggregate_id=aggregate_id)
        else:
            creation_link = None
        cdf_forecast_data = cdf_forecast_groups.list_metadata(
            site_id=site_id,
            aggregate_id=aggregate_id)
        rows = cls.create_table_elements(
            cdf_forecast_data,
            'forecast_id',
            'data_dashboard.cdf_forecast_group_view')
        rendered_table = render_template(cls.cdf_forecast_template,
                                         table_rows=rows,
                                         creation_link=creation_link)
        return rendered_table, cdf_forecast_data

    @classmethod
    def get_site_table(cls):
        """Generates an html element containing a table of Sites.

        Returns
        -------
        rendered_table: string
            The rendered html template, including a table of sites, with search
            bar and 'Create new Site' button.

        site_data: list of dict
            The site metadata list as returned by the api.

        Raises
        ------
        DataRequestException
            If a site_id is passed and the user does not have access
            to that site or some other api error has occurred.
        """
        site_data = sites.list_metadata()
        rows = cls.create_site_table_elements(site_data)
        creation_link = url_for('forms.create_site')
        rendered_table = render_template(cls.site_template,
                                         creation_link=creation_link,
                                         table_rows=rows)
        return rendered_table, site_data


def timeseries_adapter(type_, metadata, json_value_response):
    metadata = deepcopy(metadata)
    # ignores any modeling parameters as they aren't need for this
    if 'site' in metadata:
        site = datamodel.Site.from_dict(metadata['site'], raise_on_extra=False)
        metadata['site'] = site
    elif 'aggregate' in metadata:
        # Patch aggregates so data model doesn't throw an error. We don't
        # need to load all of the observations when plotting forecasts.
        metadata['aggregate']['observations'] = []
    if type_ == 'forecast':
        obj = datamodel.Forecast.from_dict(metadata)
        data = io_utils.json_payload_to_forecast_series(json_value_response)
        return timeseries.generate_forecast_figure(
            obj, data, return_components=True, limit=None)
    elif type_ == 'observation':
        obj = datamodel.Observation.from_dict(metadata)
        data = io_utils.json_payload_to_observation_df(json_value_response)
        return timeseries.generate_observation_figure(
            obj, data, return_components=True, limit=None)
    else:
        # remove observations, we aren't using them for plotting aggregates
        metadata['observations'] = []
        obj = datamodel.Aggregate.from_dict(metadata, raise_on_extra=False)
        data = io_utils.json_payload_to_observation_df(json_value_response)
        return timeseries.generate_observation_figure(
            obj, data, return_components=True, limit=None)


def filter_form_fields(prefix, form_data):
    """Creates a list of values from a dictionary where
    keys start with prefix. Mainly used for gathering lists
    from form data.
        e.g. If a role form's permissions fields are prefixed
             with "role-permission-<index>" passing in a prefix
             if 'role-permission-' will return all of the inputs
             values as a list.

    Parameters
    ----------
    prefix: str
        The key prefix to search for.
    form_data: Dict
        The dictionary of form data to search for.

    Returns
    -------
    list
        List of all values where the corresponding key began with prefix.
    """
    values = [form_data[key]
              for key in form_data.keys()
              if key.startswith(prefix)]
    return [None if v == 'null' else v for v in values]


def parse_timedelta(data_dict, key_root):
    """Parse values from a timedelta form element, and return the value in
    minutes

    Parameters
    ----------
    data_dict: dict
        Dictionary of posted form data

    key_root: string
        The shared part of the name attribute of the inputs to parse.
        e.g. 'lead_time' will parse and concatenate 'lead_time_number'
        and 'lead_time_units'

    Returns
    -------
    int
        The number of minutes in the Timedelta.
    """
    value = int(data_dict[f'{key_root}_number'])
    units = data_dict[f'{key_root}_units']
    if units == 'minutes':
        return value
    elif units == 'hours':
        return value * 60
    elif units == 'days':
        return value * 1440
    else:
        raise ValueError('Invalid selection in time units field.')


def flatten_dict(to_flatten):
    """Flattens nested dictionaries, removing keys of the nested elements.
    Useful for flattening API responses for prefilling forms on the
    dashboard.
    """
    flattened = {}
    for key, value in to_flatten.items():
        if isinstance(value, dict):
            flattened.update(flatten_dict(value))
        else:
            flattened[key] = value
    return flattened


def json_file_response(filename, values):
    """Generates a flask.Response object containing a json file, and the
    correct headers.

    Parameters
    ----------
    filename: str
    values: dict
        API response of a values endpoint on the form of a dictionary.

    Returns
    -------
    flask.Response
        Contains a json file with Content-Type and Content-Disposition headers.
    """
    response = make_response(json.dumps(values))
    response.headers.set('Content-Type', 'application/json')
    response.headers.set(
        'Content-Disposition',
        'attachment',
        filename=f'{filename}.json')
    return response


def csv_file_response(filename, values):
    """Generates a flask.Response object containing a csv file, and the
    correct headers.

    Parameters
    ----------
    filename: str
    values: dict
        API response of a values endpoint on the form of a dictionary.

    Returns
    -------
    flask.Response
        Contains a csv file with Content-Type and Content-Disposition headers.
    """
    response = make_response(values)
    response.headers.set('Content-Type', 'text/csv')
    response.headers.set(
        'Content-Disposition',
        'attachment',
        filename=f'{filename}.csv')
    return response


def download_timeseries(view_class, uuid):
    """Handle downloading timeseries data given a methodView instance with a
    set `api_handle` attribute.

    Expects a `start` and `end` query parameter as well as posted form data
     with the key `format` containing a Content-Type html header value.

    The endpoint makes a request to the api, and returns a file of the
    requested type.
    """
    form_data = request.form
    try:
        headers, params = view_class.format_download_params(form_data)
    except ValueError:
        errors = {'start-end': ['Invalid datetime']}
        return view_class.get(uuid, form_data=form_data, errors=errors)
    else:
        try:
            data = view_class.api_handle.get_values(
                uuid,
                headers=headers,
                params=params)
        except DataRequestException as e:
            return render_template(
                view_class.template,
                **view_class.template_args(uuid),
                errors=e.errors)
        else:
            try:
                metadata = view_class.api_handle.get_metadata(uuid)
            except DataRequestException:
                filename = 'data'
            else:
                name = metadata['name'].replace(' ', '_')
                time_range = f"{params['start']}-{params['end']}"
                filename = f'{name}_{time_range}'
            if form_data['format'] == 'application/json':
                response = json_file_response(filename, data)
            elif form_data['format'] == 'text/csv':
                response = csv_file_response(filename, data)
            else:
                response = make_response("Invalid media type.", 415)
        return response
