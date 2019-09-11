""" Utility classes/functions. Mostly for handling api data.
"""
from copy import deepcopy


from flask import render_template, url_for
from solarforecastarbiter import datamodel
from solarforecastarbiter.io import utils as io_utils
from solarforecastarbiter.plotting import timeseries


from sfa_dash.api_interface import (sites, forecasts, observations,
                                    cdf_forecast_groups)


class DataTables(object):
    observation_template = 'data/table/observation_table.html'
    forecast_template = 'data/table/forecast_table.html'
    site_template = 'data/table/site_table.html'
    cdf_forecast_template = 'data/table/cdf_forecast_table.html'

    @classmethod
    def creation_link(cls, data_type, site_id=None):
        if site_id is not None:
            return url_for(f'forms.create_{data_type}', uuid=site_id)
        else:
            return url_for('data_dashboard.sites', create=data_type)

    @classmethod
    def create_table_elements(cls, data_list, id_key, **kwargs):
        """Creates a list of objects to be rendered as table by jinja template
        """
        sites_list_request = sites.list_metadata()
        sites_list = sites_list_request.json()
        site_dict = {site['site_id']: site for site in sites_list}
        table_rows = []
        for data in data_list:
            table_row = {}
            site_name = site_dict[data['site_id']]['name']
            site_href = url_for('data_dashboard.site_view',
                                uuid=data['site_id'])
            site_link = f'<a href={site_href}>{site_name}</a>'
            table_row['name'] = data['name']
            table_row['variable'] = data['variable']
            table_row['provider'] = data.get('provider', '')
            table_row['site'] = site_link
            if id_key == 'forecast_id':
                table_row['link'] = url_for('data_dashboard.forecast_view',
                                            uuid=data[id_key])
            else:
                table_row['link'] = url_for('data_dashboard.observation_view',
                                            uuid=data[id_key])
            table_rows.append(table_row)
        return table_rows

    @classmethod
    def get_observation_table(cls, site_id=None, **kwargs):
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
        creation_link = cls.creation_link('observation', site_id)
        obs_data_request = observations.list_metadata(site_id=site_id)
        obs_data = obs_data_request.json()
        rows = cls.create_table_elements(obs_data, 'observation_id', **kwargs)
        rendered_table = render_template(cls.observation_template,
                                         table_rows=rows,
                                         creation_link=creation_link,
                                         **kwargs)
        return rendered_table

    @classmethod
    def get_forecast_table(cls, site_id=None, **kwargs):
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
        """
        creation_link = cls.creation_link('forecast', site_id)
        forecast_data = forecasts.list_metadata(site_id=site_id).json()
        rows = cls.create_table_elements(forecast_data,
                                         'forecast_id',
                                         **kwargs)
        rendered_table = render_template(cls.forecast_template,
                                         table_rows=rows,
                                         creation_link=creation_link,
                                         **kwargs)
        return rendered_table

    @classmethod
    def get_cdf_forecast_table(cls, site_id=None, **kwargs):
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
        """
        creation_link = cls.creation_link('cdf_forecast_group', site_id)
        cdf_forecast_request = cdf_forecast_groups.list_metadata(
            site_id=site_id)
        cdf_forecast_data = cdf_forecast_request.json()
        rows = cls.create_cdf_forecast_elements(cdf_forecast_data,
                                                **kwargs)
        rendered_table = render_template(cls.cdf_forecast_template,
                                         table_rows=rows,
                                         creation_link=creation_link,
                                         **kwargs)
        return rendered_table

    @classmethod
    def create_cdf_forecast_elements(cls, data_list, **kwargs):
        sites_list_request = sites.list_metadata()
        sites_list = sites_list_request.json()
        site_dict = {site['site_id']: site for site in sites_list}
        table_rows = []
        for data in data_list:
            table_row = {}
            site_name = site_dict[data['site_id']]['name']
            site_href = url_for('data_dashboard.site_view',
                                uuid=data['site_id'])
            site_link = f'<a href={site_href}>{site_name}</a>'
            table_row['name'] = data['name']
            table_row['variable'] = data['variable']
            table_row['provider'] = data.get('provider', '')
            table_row['site'] = site_link
            table_row['link'] = url_for(
                'data_dashboard.cdf_forecast_group_view',
                uuid=data['forecast_id'])
            table_rows.append(table_row)
        return table_rows

    @classmethod
    def get_site_table(cls, create=None, **kwargs):
        """Generates an html element containing a table of Sites.

        Parameters
        ----------
        create: {'None', 'observation', 'forecast', 'cdf_forecast_group'}
            If set, Site names will be links to create an object of type
            `create` for the given site.

        Returns
        -------
        string
            The rendered html template, including a table of sites, with search
            bar and 'Create new Site' button.
        """
        site_data_request = sites.list_metadata()
        site_data = site_data_request.json()
        rows = cls.create_site_table_elements(site_data, create, **kwargs)
        if create is None:
            # If the create argument is present, we don't need a "Create
            # Site" button, because we're using the view as a selector for
            # another object's `site` field.
            creation_link = url_for('forms.create_site')
        else:
            creation_link = None
        rendered_table = render_template(cls.site_template,
                                         creation_link=creation_link,
                                         table_rows=rows)
        return rendered_table

    @classmethod
    def create_site_table_elements(cls, data_list, create=None, **kwargs):
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
        if create not in ['observation', 'forecast', 'cdf_forecast_group']:
            link_view = 'data_dashboard.site_view'
        else:
            link_view = f'forms.create_{create}'
        table_rows = []
        for data in data_list:
            table_row = {}
            table_row['name'] = data['name']
            table_row['provider'] = data.get('provider', '')
            table_row['latitude'] = data['latitude']
            table_row['longitude'] = data['longitude']
            table_row['link'] = url_for(link_view, uuid=data['site_id'])
            table_rows.append(table_row)
        return table_rows


def timeseries_adapter(type_, metadata, json_value_response):
    metadata = deepcopy(metadata)
    # ignores any modeling parameters as they aren't need for this
    site = datamodel.Site.from_dict(metadata['site'], raise_on_extra=False)
    metadata['site'] = site
    if type_ == 'forecast':
        obj = datamodel.Forecast.from_dict(metadata)
        data = io_utils.json_payload_to_forecast_series(json_value_response)
        return timeseries.generate_forecast_figure(
            obj, data, return_components=True)
    else:
        obj = datamodel.Observation.from_dict(metadata)
        data = io_utils.json_payload_to_observation_df(json_value_response)
        return timeseries.generate_observation_figure(
            obj, data, return_components=True)


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
