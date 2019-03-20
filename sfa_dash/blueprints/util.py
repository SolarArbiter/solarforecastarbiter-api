""" Utility classes/functions. Mostly for handling api data.
"""
from sfa_dash.api_interface import sites, forecasts, observations
from flask import render_template, url_for


class DataTables(object):
    observation_template = 'data/table/observation_table.html'
    forecast_template = 'data/table/forecast_table.html'
    site_template = 'data/table/site_table.html'

    @classmethod
    def create_table_elements(cls, data_list, id_key, **kwargs):
        """Creates a list of objects to be rendered as table by jinja template
        """
        table_rows = []
        for data in data_list:
            table_row = {}
            site_name = data['site']['name']
            table_row['name'] = data['name']
            table_row['variable'] = data['variable']
            table_row['provider'] = data.get('provider', 'Test User')
            table_row['uuid'] = data[id_key]
            table_row['site'] = site_name
            if id_key == 'forecast_id':
                table_row['link'] = url_for('data_dashboard.forecast_view',
                                            uuid=data[id_key])
            else:
                table_row['link'] = url_for('data_dashboard.observation_view',
                                            uuid=data[id_key])
            table_rows.append(table_row)
        return table_rows

    @classmethod
    def create_site_table_elements(cls, data_list, id_key, **kwargs):
        table_rows = []
        for data in data_list:
            table_row = {}
            table_row['name'] = data['name']
            table_row['provider'] = 'Test User'
            table_row['latitude'] = data['latitude']
            table_row['longitude'] = data['longitude']
            table_row['uuid'] = data[id_key]
            table_row['link'] = url_for("data_dashboard.site_view",
                                        uuid=data['site_id'])
            table_rows.append(table_row)
        return table_rows

    @classmethod
    def get_observation_table(cls, **kwargs):
        """Returns a rendered observation table.
        TODO: fix parameters.
        """
        site_id = kwargs.get('site_id')
        obs_data = observations.list_metadata(site_id=site_id).json()
        rows = cls.create_table_elements(obs_data, 'obs_id', **kwargs)
        rendered_table = render_template(cls.observation_template,
                                         table_rows=rows,
                                         **kwargs)
        return rendered_table

    @classmethod
    def get_forecast_table(cls, **kwargs):
        """
        """
        site_id = kwargs.get('site_id')
        forecast_data = forecasts.list_metadata(site_id=site_id).json()
        rows = cls.create_table_elements(forecast_data,
                                         'forecast_id',
                                         **kwargs)
        rendered_table = render_template(cls.forecast_template,
                                         table_rows=rows,
                                         **kwargs)
        return rendered_table

    @classmethod
    def get_site_table(cls, **kwargs):
        """
        """
        site_data = sites.list_metadata().json()
        rows = cls.create_site_table_elements(site_data, 'site_id', **kwargs)
        rendered_table = render_template(cls.site_template, table_rows=rows)
        return rendered_table
