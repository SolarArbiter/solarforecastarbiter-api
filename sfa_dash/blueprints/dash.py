"""Dashboards are wrappers providing navigation and contextual content based
on site-section.
"""
from sfa_dash.blueprints.base import BaseView
from sfa_dash.api_interface import sites
from flask import render_template, request, url_for


class DataDashView(BaseView):
    subnav_format = {}

    def template_args(self, **kwargs):
        temp_args = {}
        temp_args['current_path'] = request.path
        temp_args['subnav'] = self.format_subnav(**kwargs)
        temp_args['breadcrumb'] = self.breadcrumb_html(**kwargs)
        return temp_args

    def get_site_metadata(self, site_id):
        site_request = sites.get_metadata(site_id)
        return site_request.json()

    def get(self, **kwargs):
        return render_template(self.template, **self.template_args(**kwargs))


class SiteDashView(BaseView):
    template = 'data/site.html'
    subnav_format = {
        '{observations_url}': 'Observations',
        '{forecasts_url}': 'Forecasts',
        '{cdf_forecasts_url}': 'Probabilistic Forecasts',
    }

    def template_args(self, **kwargs):
        """
        """
        temp_args = {}
        subnav_kwargs = {
            'forecasts_url': url_for('data_dashboard.forecasts',
                                     uuid=self.metadata['site_id']),
            'observations_url': url_for('data_dashboard.observations',
                                        uuid=self.metadata['site_id']),
            'cdf_forecasts_url': url_for('data_dashboard.cdf_forecast_groups',
                                         uuid=self.metadata['site_id'])
        }
        temp_args['subnav'] = self.format_subnav(**subnav_kwargs)
        temp_args['breadcrumb'] = self.breadcrumb_html()
        temp_args['metadata'] = render_template(
            'data/metadata/site_metadata.html',
            **self.metadata)
        temp_args['site_id'] = self.metadata['site_id']
        return temp_args
