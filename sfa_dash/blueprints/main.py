from sfa_dash.blueprints.dash import DataDashView
from sfa_dash.blueprints.data_listing import DataListingView
from sfa_dash.blueprints.sites import SingleSiteView, SitesListingView
from sfa_dash.api_interface import observations, forecasts
from flask import (Blueprint, render_template,
                   url_for, redirect, abort)
from flask.views import MethodView


class SingleObservationView(DataDashView):
    template = 'data/asset.html'

    def breadcrumb_html(self, **kwargs):
        breadcrumb_format = '/<a href="{url}">{text}</a>'
        breadcrumb = ''
        breadcrumb += breadcrumb_format.format(
            url=url_for('data_dashboard.sites_view'),
            text='Sites')
        breadcrumb += breadcrumb_format.format(
            url=url_for('data_dashboard.site_view',
                        uuid=self.metadata['site_id']),
            text=self.metadata['site']['name'])
        breadcrumb += breadcrumb_format.format(
            url=url_for('data_dashboard.observations',
                        site_id=self.metadata['site_id']),
            text='Observations')
        breadcrumb += breadcrumb_format.format(
            url=url_for('data_dashboard.observation_view',
                        uuid=self.metadata['obs_id']),
            text=self.metadata['name'])
        return breadcrumb

    def get(self, uuid, **kwargs):
        metadata_request = observations.get_metadata(uuid)
        if metadata_request.status_code != 200:
            abort(404)
        self.metadata = metadata_request.json()
        self.metadata['site'] = self.get_site_metadata(
            self.metadata['site_id'])
        temp_args = self.template_args(**kwargs)
        self.metadata['site_link'] = self.generate_site_link(self.metadata)
        temp_args['metadata'] = render_template(
            'data/metadata/observation_metadata.html',
            **self.metadata)
        temp_args['upload_link'] = url_for(
            'forms.upload_observation_data',
            uuid=uuid)
        temp_args['download_link'] = url_for(
            'forms.download_observation_data',
            uuid=uuid)
        return render_template(self.template, **temp_args)


class SingleForecastView(DataDashView):
    template = 'data/asset.html'

    def breadcrumb_html(self, **kwargs):
        breadcrumb_format = '/<a href="{url}">{text}</a>'
        breadcrumb = ''
        breadcrumb += breadcrumb_format.format(
            url=url_for('data_dashboard.sites_view'),
            text='Sites')
        breadcrumb += breadcrumb_format.format(
            url=url_for('data_dashboard.site_view',
                        uuid=self.metadata['site_id']),
            text=self.metadata['site']['name'])
        breadcrumb += breadcrumb_format.format(
            url=url_for('data_dashboard.forecasts',
                        uuid=self.metadata['site_id']),
            text='Forecasts')
        breadcrumb += breadcrumb_format.format(
            url=url_for('data_dashboard.forecast_view',
                        uuid=self.metadata['forecast_id']),
            text=self.metadata['name'])
        return breadcrumb

    def get(self, uuid, **kwargs):
        metadata_request = forecasts.get_metadata(uuid)
        if metadata_request.status_code != 200:
            abort(404)
        self.metadata = metadata_request.json()
        temp_args = self.template_args(**kwargs)
        self.metadata['site_link'] = self.generate_site_link(self.metadata)
        temp_args['metadata'] = render_template(
            'data/metadata/forecast_metadata.html',
            **self.metadata)
        temp_args['upload_link'] = url_for(
            'forms.upload_forecast_data',
            uuid=uuid)
        temp_args['download_link'] = url_for(
            'forms.download_forecast_data',
            uuid=uuid)
        return render_template(self.template, **temp_args)


class AccessView(DataDashView):
    template = 'data/access.html'


class ReportsView(DataDashView):
    template = 'data/reports.html'


class TrialsView(DataDashView):
    template = 'data/trials.html'


class ToSites(MethodView):
    """Temporary redirect to sites until landing/homepage is
    designed.
    """
    def get(self):
        return redirect(url_for('data_dashboard.sites_view'), 302)


data_dash_blp = Blueprint('data_dashboard', 'data_dashboard')
data_dash_blp.add_url_rule(
    '/sites/',
    view_func=SitesListingView.as_view('sites_view'))
data_dash_blp.add_url_rule(
    '/sites/<uuid>/',
    view_func=SingleSiteView.as_view('site_view'))
data_dash_blp.add_url_rule(
    '/sites/<uuid>/<name>/access',
    view_func=AccessView.as_view('observation_named_access'))
data_dash_blp.add_url_rule(
    '/sites/<uuid>/<name>/reports',
    view_func=ReportsView.as_view('observation_named_reports'))
data_dash_blp.add_url_rule(
    '/sites/<uuid>/<name>/trials',
    view_func=TrialsView.as_view('observation_named_trials'))
data_dash_blp.add_url_rule(
    '/observations/',
    view_func=DataListingView.as_view('observations', data_type='observation'))
data_dash_blp.add_url_rule(
    '/observations/<uuid>',
    view_func=SingleObservationView.as_view('observation_view'))
data_dash_blp.add_url_rule(
    '/forecasts/',
    view_func=DataListingView.as_view('forecasts', data_type='forecast'))
data_dash_blp.add_url_rule(
    '/forecasts/<uuid>',
    view_func=SingleForecastView.as_view('forecast_view'))

# Temporary redirect to sites page
data_dash_blp.add_url_rule('/', view_func=ToSites.as_view('root_redirect'))
