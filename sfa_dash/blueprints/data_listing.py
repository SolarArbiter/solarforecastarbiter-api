from sfa_dash.blueprints.base import BaseView
from sfa_dash.blueprints.util import DataTables
from sfa_dash.api_interface import sites
from flask import render_template, request, url_for, abort


class DataListingView(BaseView):
    """Lists accessible forecasts/observations.
    """
    template = 'org/obs.html'
    subnav_format = {
        '{observations_url}': 'Observations',
        '{forecasts_url}': 'Forecasts',
        '{cdf_forecasts_url}': 'Probabilistic Forecasts',
    }

    def __init__(self, data_type, **kwargs):
        """
        """
        if data_type == 'forecast':
            self.table_function = DataTables.get_forecast_table
        elif data_type == 'observation':
            self.table_function = DataTables.get_observation_table
        elif data_type == 'cdf_forecast':
            self.table_function = DataTables.get_cdf_forecast_table
        else:
            raise Exception
        self.data_type = data_type

    def breadcrumb_html(self, site_id=None, organization=None, **kwargs):
        breadcrumb_format = '/<a href="{url}">{text}</a>'
        breadcrumb = ''
        if self.data_type == 'cdf_forecast':
            type_label = 'CDF Forecast'
        else:
            type_label = self.data_type.title()
        if site_id is not None:
            site_metadata_request = sites.get_metadata(site_id)
            if site_metadata_request.status_code != 200:
                abort(404)
            site_metadata = site_metadata_request.json()
            breadcrumb += breadcrumb_format.format(
                url=url_for('data_dashboard.sites_view'),
                text='Sites')
            breadcrumb += breadcrumb_format.format(
                url=url_for('data_dashboard.site_view', uuid=site_id),
                text=site_metadata['name'])
        breadcrumb += breadcrumb_format.format(
            url=url_for(f'data_dashboard.{self.data_type}s', site_id=site_id),
            text=type_label)
        return breadcrumb

    def get_template_args(self, **kwargs):
        """Create a dictionary containing the required arguments for the template
        """
        template_args = {}
        subnav_kwargs = {
            'observations_url': url_for('data_dashboard.observations',
                                        **kwargs),
            'forecasts_url': url_for('data_dashboard.forecasts',
                                     **kwargs),
            'cdf_forecasts_url': url_for('data_dashboard.cdf_forecasts',
                                         **kwargs)
        }
        template_args['subnav'] = self.format_subnav(**subnav_kwargs)
        template_args['data_table'] = self.table_function(**kwargs)
        template_args['current_path'] = request.path
        template_args['breadcrumb'] = self.breadcrumb_html(**kwargs)
        return template_args

    def get(self, **kwargs):
        """
        """
        site_id = request.args.get('site_id')
        if site_id is not None:
            kwargs.update({'site_id': site_id})
        return render_template(self.template,
                               **self.get_template_args(**kwargs))
