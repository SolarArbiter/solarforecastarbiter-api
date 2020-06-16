"""Dashboards are wrappers providing navigation and contextual content based
on site-section.
"""
from sfa_dash.blueprints.base import BaseView
from flask import render_template, request, url_for


class DataDashView(BaseView):
    subnav_format = {}

    def set_template_args(self, **kwargs):
        self.template_args = {}
        self.template_args['current_path'] = request.path
        self.template_args['subnav'] = self.format_subnav(**kwargs)
        self.template_args['breadcrumb'] = self.breadcrumb_html(**kwargs)

    def get(self, **kwargs):
        self.set_template_args(**kwargs)
        return render_template(self.template, **self.template_args)


class SiteDashView(BaseView):
    template = 'data/site.html'
    subnav_format = {
        '{observations_url}': 'Observations',
        '{forecasts_url}': 'Forecasts',
        '{cdf_forecasts_url}': 'Probabilistic Forecasts',
    }

    def set_template_args(self, **kwargs):
        self.template_args = {}
        subnav_kwargs = {
            'forecasts_url': url_for('data_dashboard.forecasts',
                                     site_id=self.metadata['site_id']),
            'observations_url': url_for('data_dashboard.observations',
                                        site_id=self.metadata['site_id']),
            'cdf_forecasts_url': url_for('data_dashboard.cdf_forecast_groups',
                                         site_id=self.metadata['site_id'])
        }
        self.template_args['subnav'] = self.format_subnav(**subnav_kwargs)
        self.template_args['breadcrumb'] = self.breadcrumb_html()
        self.template_args['metadata'] = self.safe_metadata()
        self.template_args['metadata_block'] = render_template(
            'data/metadata/site_metadata.html',
            **self.metadata)
        self.template_args['site_id'] = self.metadata['site_id']
