""" Utility classes/functions. Mostly for handling api data.
"""
from copy import deepcopy


from flask import render_template, url_for, request
from solarforecastarbiter import datamodel
from solarforecastarbiter.io import utils as io_utils
from solarforecastarbiter.plotting import timeseries


from sfa_dash.api_interface import (sites, forecasts, observations,
                                    cdf_forecast_groups, aggregates)
from sfa_dash.errors import DataRequestException


class DataTables(object):
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
        """Creates a list of objects to be rendered as table by jinja template
        """
        sites_list = handle_response(sites.list_metadata())
        location_dict = {site['site_id']: site for site in sites_list}
        if id_key != 'observation_id':
            no_location_text = 'Site/Aggregate unavailable'
            aggregates_list = handle_response(aggregates.list_metadata())
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
            table_row['latitude'] = data['latitude']
            table_row['longitude'] = data['longitude']
            table_row['link'] = url_for('data_dashboard.site_view',
                                        uuid=data['site_id'])
            table_rows.append(table_row)
        return table_rows

    @classmethod
    def get_observation_table(cls, site_id=None, aggregate_id=None):
        """Generates an html element containing a table of Observations

        Parameters
        ----------
        site_id: string
            The UUID of a site to filter for.

        Returns
        -------
        string
            Rendered HTML table with search bar and a 'Create
            new Observation' button.
        """
        creation_link = cls.creation_link('observation', site_id=site_id)
        obs_data = handle_response(
            observations.list_metadata(site_id=site_id))
        rows = cls.create_table_elements(
            obs_data,
            'observation_id',
            'data_dashboard.observation_view')
        rendered_table = render_template(cls.observation_template,
                                         table_rows=rows,
                                         creation_link=creation_link)
        return rendered_table

    @classmethod
    def get_forecast_table(cls, site_id=None, aggregate_id=None):
        """Generates an html element containing a table of Forecasts

        Parameters
        ----------
        site_id: string
            The UUID of a site to filter for.

        Returns
        -------
        string
            Rendered HTML table with search bar and a 'Create
            new Forecast' button.

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

        forecast_data = handle_response(
            forecasts.list_metadata(site_id=site_id,
                                    aggregate_id=aggregate_id))
        rows = cls.create_table_elements(
            forecast_data,
            'forecast_id',
            'data_dashboard.forecast_view')
        rendered_table = render_template(cls.forecast_template,
                                         table_rows=rows,
                                         creation_link=creation_link)
        return rendered_table

    @classmethod
    def get_cdf_forecast_table(cls, site_id=None, aggregate_id=None):
        """Generates an html element containing a table of CDF Forecasts.

        Parameters
        ----------
        site_id: string, optional
            The UUID of a site to filter for.

        Returns
        -------
        string
            Rendered HTML table with search bar and a 'Create
            new Probabilistic Forecast' button.

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
        cdf_forecast_data = handle_response(
            cdf_forecast_groups.list_metadata(site_id=site_id,
                                              aggregate_id=aggregate_id))
        rows = cls.create_table_elements(
            cdf_forecast_data,
            'forecast_id',
            'data_dashboard.cdf_forecast_group_view')
        rendered_table = render_template(cls.cdf_forecast_template,
                                         table_rows=rows,
                                         creation_link=creation_link)
        return rendered_table

    @classmethod
    def get_site_table(cls):
        """Generates an html element containing a table of Sites.

        Returns
        -------
        string
            The rendered html template, including a table of sites, with search
            bar and 'Create new Site' button.

        Raises
        ------
        DataRequestException
            If a site_id is passed and the user does not have access
            to that site or some other api error has occurred.
        """
        site_data = handle_response(sites.list_metadata())
        rows = cls.create_site_table_elements(site_data)
        creation_link = url_for('forms.create_site')
        rendered_table = render_template(cls.site_template,
                                         creation_link=creation_link,
                                         table_rows=rows)
        return rendered_table


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
    return [form_data[key]
            for key in form_data.keys()
            if key.startswith(prefix)]


def handle_response(request_object):
    """Parses the response from a request object. On an a resolvable
    error, raises a DataRequestException with a default error
    message.

    Parameters
    ----------
    request_object: requests.Response
        The response object from an executed request.

    Returns
    -------
    dict, str or None
        Note that this function checks the content-type of a response
        and returns the appropriate type. A Dictionary parsed from a
        JSON object, or a string. Returns None when a 204 is encountered.
        Users should be mindful of the expected response body from the
        API.

    Raises
    ------
    sfa_dash.errors.DataRequestException
        If a recoverable 400 level error has been encountered.
        The errors attribute will contain a dict of errors.
    requests.exceptions.HTTPError
        If the status code received from the API could not be
        handled.
    """
    if not request_object.ok:
        errors = {}
        if request_object.status_code == 400:
            errors = request_object.json()
        elif request_object.status_code == 401:
            errors = {
                '401': "You do not have permission to create this resource."
            }
        elif request_object.status_code == 404:
            previous_page = request.headers.get('Referer', None)
            errors = {'404': (
                'The requested object could not be found. You may need to '
                'request access from the data owner.')
            }
            if previous_page is not None and previous_page != request.url:
                errors['404'] = errors['404'] + (
                    f' <a href="{previous_page}">Return to the previous '
                    'page.</a>')
        elif request_object.status_code == 422:
            errors = request_object.json()['errors']
        if errors:
            raise DataRequestException(request_object.status_code, **errors)
        else:
            # Other errors should be due to bugs and not by attempts to reach
            # inaccessible data. Allow exceptions to be raised
            # so that they can be reported to Sentry.
            request_object.raise_for_status()
    if request_object.request.method == 'GET':
        # all GET endpoints should return a JSON object
        if request_object.headers['Content-Type'] == 'application/json':
            return request_object.json()
        else:
            return request_object.text
    # POST responses should contain a single string uuid of a newly created
    # object unless a 204 No Content was returned.
    if request_object.request.method == 'POST':
        if request_object.status_code != 204:
            return request_object.text


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
