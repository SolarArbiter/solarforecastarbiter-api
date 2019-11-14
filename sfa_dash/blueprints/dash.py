"""Dashboards are wrappers providing navigation and contextual content based
on site-section.
"""
from sfa_dash.blueprints.base import BaseView
from sfa_dash.api_interface import sites, aggregates
from sfa_dash.blueprints.util import handle_response
from sfa_dash.errors import DataRequestException
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
        return handle_response(sites.get_metadata(site_id))

    def set_site_or_aggregate_metadata(self):
        """Searches for a site_id or aggregate_id  in self.metadata
        and loads the expected metadata object from the api in either
        the 'site' or 'aggregate' key. If the object could not be retrieved,
        sets a warning, sets the 'plot' template argument to None and
        reraises the DataRequestError.
        """
        if self.metadata.get('site_id') is not None:
            try:
                self.metadata['site'] = self.get_site_metadata(
                    self.metadata['site_id'])
            except DataRequestException:
                self.temp_args.update({
                    'warnings': {
                        'Site Access': [
                            'Site inaccessible. Plots will not be displayed.']
                    },
                })
                raise
        elif self.metadata.get('aggregate_id'):
            try:
                self.metadata['aggregate'] = handle_response(
                    aggregates.get_metadata(self.metadata['aggregate_id']))
            except DataRequestException:
                self.temp_args.update({
                    'warnings': {
                        'Aggregate Access': [
                            'Aggregate inaccessible. Plots will not be '
                            'displayed.']
                    },
                })
                raise

    def set_site_or_aggregate_link(self):
        """Creates a url to the forecast's site or aggregate. For injection
        into the metadata template.

        Returns
        -------
        link_html: str
            An anchor tag referencing the site/aggregates page on the
            dashboard or a string uuid if the metadata wasn't not available,
            indicating that the current user does not have access to the
            site or aggregate.
        """
        if self.metadata.get('site_id') is not None:
            if self.metadata.get('site') is not None:
                site_metadata = self.metadata.get('site')
                site_name = site_metadata['name']
                site_id = site_metadata['site_id']
                site_href = url_for('data_dashboard.site_view',
                                    uuid=site_id)
                link_html = f'<a href="{site_href}">{site_name}</a>'
            else:
                link_html = self.metadata['site_id']
        elif self.metadata.get('aggregate_id') is not None:
            if self.metadata.get('aggregate') is not None:
                aggregate_metadata = self.metadata.get('aggregate')
                aggregate_name = aggregate_metadata['name']
                aggregate_id = aggregate_metadata['aggregate_id']
                aggregate_href = url_for('data_dashboard.aggregate_view',
                                         uuid=aggregate_id)
                link_html = f'<a href="{aggregate_href}">{aggregate_name}</a>'
            else:
                link_html = self.metadata['aggregate_id']
        else:
            link_html = 'Object Deleted'
        self.metadata['location_link'] = link_html

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
                                     site_id=self.metadata['site_id']),
            'observations_url': url_for('data_dashboard.observations',
                                        site_id=self.metadata['site_id']),
            'cdf_forecasts_url': url_for('data_dashboard.cdf_forecast_groups',
                                         site_id=self.metadata['site_id'])
        }
        temp_args['subnav'] = self.format_subnav(**subnav_kwargs)
        temp_args['breadcrumb'] = self.breadcrumb_html()
        temp_args['metadata'] = render_template(
            'data/metadata/site_metadata.html',
            **self.metadata)
        temp_args['site_id'] = self.metadata['site_id']
        return temp_args
