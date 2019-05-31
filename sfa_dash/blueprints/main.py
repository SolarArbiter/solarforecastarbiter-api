from flask import (Blueprint, render_template,
                   url_for, abort)


from sfa_dash.blueprints.dash import DataDashView
from sfa_dash.blueprints.data_listing import DataListingView
from sfa_dash.blueprints.sites import SingleSiteView, SitesListingView
from sfa_dash.blueprints.delete import DeleteConfirmation
from sfa_dash.blueprints.util import timeseries_adapter
from sfa_dash.api_interface import (observations, forecasts,
                                    cdf_forecasts, cdf_forecast_groups)


class SingleObservationView(DataDashView):
    template = 'data/asset.html'

    def breadcrumb_html(self, **kwargs):
        breadcrumb_format = '/<a href="{url}">{text}</a>'
        breadcrumb = ''
        breadcrumb += breadcrumb_format.format(
            url=url_for('data_dashboard.sites'),
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
                        uuid=self.metadata['observation_id']),
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
        values_request = observations.get_values(uuid)
        if values_request.status_code == 200:
            script_plot = timeseries_adapter(
                'observation',
                self.metadata,
                values_request.json())
            if script_plot is None:
                temp_args.update(
                    {'messages':
                        {'Data': ["No data available for this Observation."]}
                     }
                )
            else:
                temp_args.update({'plot': script_plot[1],
                                  'bokeh_script': script_plot[0]})
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
        temp_args['delete_link'] = url_for(
            f'data_dashboard.delete_observation',
            uuid=uuid)
        return render_template(self.template, **temp_args)


class SingleCDFForecastView(DataDashView):
    template = 'data/asset.html'

    def breadcrumb_html(self, **kwargs):
        breadcrumb_format = '/<a href="{url}">{text}</a>'
        breadcrumb = ''
        breadcrumb += breadcrumb_format.format(
            url=url_for('data_dashboard.sites'),
            text='Sites')
        breadcrumb += breadcrumb_format.format(
            url=url_for('data_dashboard.site_view',
                        uuid=self.metadata['site_id']),
            text=self.metadata['site']['name'])
        breadcrumb += breadcrumb_format.format(
            url=url_for('data_dashboard.cdf_forecast_groups',
                        uuid=self.metadata['site_id']),
            text='CDF Forecasts')
        breadcrumb += breadcrumb_format.format(
            url=url_for('data_dashboard.cdf_forecast_group_view',
                        uuid=self.metadata['parent']),
            text=self.metadata['name'])
        breadcrumb += breadcrumb_format.format(
            url=url_for('data_dashboard.cdf_forecast_view',
                        uuid=self.metadata['forecast_id']),
            text=self.metadata['constant_value'])
        return breadcrumb

    def get(self, uuid, **kwargs):
        metadata_request = cdf_forecasts.get_metadata(uuid)
        if metadata_request.status_code != 200:
            abort(404)
        self.metadata = metadata_request.json()
        self.metadata['site'] = self.get_site_metadata(
            self.metadata['site_id'])
        temp_args = self.template_args(**kwargs)
        values_request = cdf_forecasts.get_values(uuid)
        if values_request.status_code == 200:
            script_plot = timeseries_adapter(
                'forecast',
                self.metadata,
                values_request.json())
            if script_plot is None:
                temp_args.update(
                    {'messages':
                        {'Data': ["No data available for this Forecast."]}
                     }
                )
            else:
                temp_args.update({'plot': script_plot[1],
                                  'bokeh_script': script_plot[0]})
        self.metadata['site_link'] = self.generate_site_link(self.metadata)
        temp_args['metadata'] = render_template(
            'data/metadata/cdf_forecast_metadata.html',
            **self.metadata)
        temp_args['upload_link'] = url_for(
            'forms.upload_cdf_forecast_data',
            uuid=uuid)
        temp_args['download_link'] = url_for(
            'forms.download_cdf_forecast_data',
            uuid=uuid)
        return render_template(self.template, **temp_args)


class SingleForecastView(DataDashView):
    template = 'data/asset.html'

    def breadcrumb_html(self, **kwargs):
        breadcrumb_format = '/<a href="{url}">{text}</a>'
        breadcrumb = ''
        breadcrumb += breadcrumb_format.format(
            url=url_for('data_dashboard.sites'),
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
        self.metadata['site'] = self.get_site_metadata(
            self.metadata['site_id'])
        temp_args = self.template_args(**kwargs)
        values_request = forecasts.get_values(uuid)
        if values_request.status_code == 200:
            script_plot = timeseries_adapter(
                'forecast',
                self.metadata,
                values_request.json())
            if script_plot is None:
                temp_args.update(
                    {'messages':
                        {'Data': ["No data available for this Forecast."]}
                     }
                )
            else:
                temp_args.update({'plot': script_plot[1],
                                  'bokeh_script': script_plot[0]})
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
        temp_args['delete_link'] = url_for(
            f'data_dashboard.delete_forecast',
            uuid=uuid)
        return render_template(self.template, **temp_args)


class SingleCDFForecastGroupView(DataDashView):
    template = 'data/cdf_forecast.html'

    def breadcrumb_html(self, **kwargs):
        breadcrumb_format = '/<a href="{url}">{text}</a>'
        breadcrumb = ''
        breadcrumb += breadcrumb_format.format(
            url=url_for('data_dashboard.sites'),
            text='Sites')
        breadcrumb += breadcrumb_format.format(
            url=url_for('data_dashboard.site_view',
                        uuid=self.metadata['site_id']),
            text=self.metadata['site']['name'])
        breadcrumb += breadcrumb_format.format(
            url=url_for('data_dashboard.cdf_forecast_groups',
                        uuid=self.metadata['site_id']),
            text='CDF Forecasts')
        breadcrumb += breadcrumb_format.format(
            url=url_for('data_dashboard.cdf_forecast_group_view',
                        uuid=self.metadata['forecast_id']),
            text=self.metadata['name'])
        return breadcrumb

    def get(self, uuid, **kwargs):
        metadata_request = cdf_forecast_groups.get_metadata(uuid)
        if metadata_request.status_code != 200:
            abort(404)
        self.metadata = metadata_request.json()
        self.metadata['site'] = self.get_site_metadata(
            self.metadata['site_id'])
        temp_args = self.template_args(**kwargs)
        self.metadata['site_link'] = self.generate_site_link(self.metadata)
        temp_args['metadata'] = self.metadata
        temp_args['metadata_section'] = render_template(
            'data/metadata/cdf_forecast_group_metadata.html',
            **self.metadata)
        temp_args['delete_link'] = url_for(
            f'data_dashboard.delete_cdf_forecast_group',
            uuid=uuid)
        return render_template(self.template, **temp_args)


class AccessView(DataDashView):
    template = 'data/access.html'


class ReportsView(DataDashView):
    template = 'data/reports.html'


class TrialsView(DataDashView):
    template = 'data/trials.html'


data_dash_blp = Blueprint('data_dashboard', 'data_dashboard')

data_dash_blp.add_url_rule(
    '/sites/',
    view_func=SitesListingView.as_view('sites'))
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
    '/forecasts/single/',
    view_func=DataListingView.as_view('forecasts', data_type='forecast'))
data_dash_blp.add_url_rule(
    '/forecasts/cdf/',
    view_func=DataListingView.as_view('cdf_forecast_groups',
                                      data_type='cdf_forecast_group'))
data_dash_blp.add_url_rule(
    '/forecasts/single/<uuid>',
    view_func=SingleForecastView.as_view('forecast_view'))
data_dash_blp.add_url_rule(
    '/forecasts/cdf/<uuid>',
    view_func=SingleCDFForecastGroupView.as_view('cdf_forecast_group_view'))
data_dash_blp.add_url_rule(
    '/forecasts/cdf/single/<uuid>',
    view_func=SingleCDFForecastView.as_view('cdf_forecast_view'))

data_dash_blp.add_url_rule(
    '/sites/<uuid>/delete',
    view_func=DeleteConfirmation.as_view('delete_site', data_type='site'))
data_dash_blp.add_url_rule(
    '/observations/<uuid>/delete',
    view_func=DeleteConfirmation.as_view(
        'delete_observation', data_type='observation'))
data_dash_blp.add_url_rule(
    '/forecasts/single/<uuid>/delete',
    view_func=DeleteConfirmation.as_view(
        'delete_forecast', data_type='forecast'))
data_dash_blp.add_url_rule(
    '/forecasts/cdf/<uuid>/delete',
    view_func=DeleteConfirmation.as_view(
        'delete_cdf_forecast_group', data_type='cdf_forecast_group'))
