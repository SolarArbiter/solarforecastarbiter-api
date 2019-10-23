"""Dashboards are wrappers providing navigation and contextual content based
on site-section.
"""
from sfa_dash.blueprints.base import BaseView
from sfa_dash.api_interface import sites
from sfa_dash.blueprints.util import handle_response
from flask import render_template, request, url_for
import pandas as pd


class DataDashView(BaseView):
    subnav_format = {}

    def template_args(self, **kwargs):
        temp_args = {}
        temp_args['current_path'] = request.path
        temp_args['subnav'] = self.format_subnav(**kwargs)
        temp_args['breadcrumb'] = self.breadcrumb_html(**kwargs)
        return temp_args

    def get_site_metadata(self, site_id):
        return handle_response(sites.get_metadata(site_id))

    def parse_start_end_from_querystring(self):
        """Attempts to find the start and end query parameters. If not found,
        returns defaults spanning the last three days. Used for setting
        reasonable defaults for requesting data for plots.

        Returns
        -------
        start,end
            Tuple of ISO 8601 datetime strings representing the start, end.
        """
        # set default arg to an invalid timestamp, to trigger ValueError
        start_arg = request.args.get('start', 'x')
        end_arg = request.args.get('end', 'x')
        try:
            start = pd.Timestamp(start_arg)
        except ValueError:
            start = pd.Timestamp.utcnow() - pd.Timedelta('3days')
        try:
            end = pd.Timestamp(end_arg)
        except ValueError:
            end = pd.Timestamp.utcnow()
        return start.isoformat(), end.isoformat()

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
