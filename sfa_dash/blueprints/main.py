from collections import OrderedDict


from flask import Blueprint, render_template, url_for, request, g


from sfa_dash.api_interface import (users, observations, forecasts,
                                    cdf_forecasts, cdf_forecast_groups)
from sfa_dash.blueprints.aggregates import (AggregatesView, AggregateView,
                                            DeleteAggregateView)
from sfa_dash.blueprints.dash import DataDashView
from sfa_dash.blueprints.data_listing import DataListingView
from sfa_dash.blueprints.delete import DeleteConfirmation
from sfa_dash.blueprints.reports import (ReportsView, ReportView,
                                         DeleteReportView,
                                         DownloadReportView)
from sfa_dash.blueprints.sites import SingleSiteView, SitesListingView
from sfa_dash.blueprints.util import download_timeseries
from sfa_dash.errors import DataRequestException
from sfa_dash.filters import human_friendly_datatype


class SingleObjectView(DataDashView):
    """View for a single data object of type observation, forecast
    or cdf_forecast.
    """
    template = 'data/asset.html'

    def __init__(self, data_type):
        """Configures attributes of the view that vary between data type.
        The `data_type` can be configured when registering a url rule,
            e.g.
            <blueprint>.add_url_rule(
                SingleObjectView.as_view('observations',
                                         data_type='observation'))
        Examples can be found at the bottom of this file.
        """
        self.data_type = data_type
        if data_type == 'forecast':
            self.api_handle = forecasts
            self.metadata_template = 'data/metadata/forecast_metadata.html'
            self.id_key = 'forecast_id'
            self.plot_type = 'forecast'
        elif data_type == 'cdf_forecast':
            self.api_handle = cdf_forecasts
            self.metadata_template = 'data/metadata/cdf_forecast_metadata.html'
            self.id_key = 'forecast_id'
            self.plot_type = 'forecast'
        elif data_type == 'observation':
            self.api_handle = observations
            self.metadata_template = 'data/metadata/observation_metadata.html'
            self.id_key = 'observation_id'
            self.plot_type = 'observation'
        else:
            raise ValueError('Invalid data_type.')
        self.human_label = human_friendly_datatype(self.data_type)

    def get_breadcrumb_dict(self):
        """See BaseView.get_breadcrumb_dict.
        """
        breadcrumb_dict = OrderedDict()
        if self.data_type == 'cdf_forecast':
            listing_view = 'cdf_forecast_groups'
        else:
            listing_view = f'{self.data_type}s'
        # Insert site/aggregate link if available
        if self.metadata.get('site') is not None:
            breadcrumb_dict['Sites'] = url_for('data_dashboard.sites')
            breadcrumb_dict[self.metadata['site']['name']] = url_for(
                'data_dashboard.site_view',
                uuid=self.metadata['site_id'])
            breadcrumb_dict[f'{self.human_label}s'] = url_for(
                f'data_dashboard.{listing_view}',
                site_id=self.metadata['site_id'])
        elif self.metadata.get('aggregate') is not None:
            breadcrumb_dict['Aggregates'] = url_for(
                'data_dashboard.aggregates')
            breadcrumb_dict[self.metadata['aggregate']['name']] = url_for(
                'data_dashboard.aggregate_view',
                uuid=self.metadata['aggregate_id'])
            breadcrumb_dict[f'{self.human_label}s'] = url_for(
                f'data_dashboard.{listing_view}',
                aggregate_id=self.metadata['aggregate_id'])
        else:
            breadcrumb_dict[f'{self.human_label}s'] = url_for(
                f'data_dashboard.{listing_view}')
        # Insert a parent link for cdf_forecasts
        if self.data_type == 'cdf_forecast':
            breadcrumb_dict[self.metadata['name']] = url_for(
                f'data_dashboard.cdf_forecast_group_view',
                uuid=self.metadata['parent'])
            breadcrumb_dict[self.metadata['constant_value']] = url_for(
                f'data_dashboard.{self.data_type}_view',
                uuid=self.metadata[self.id_key])
        else:
            breadcrumb_dict[self.metadata['name']] = url_for(
                f'data_dashboard.{self.data_type}_view',
                uuid=self.metadata[self.id_key])
        return breadcrumb_dict

    def set_template_args(self, start, end, **kwargs):
        """Insert necessary template arguments. See data/asset.html in the
        template folder for how these are layed out.
        """
        self.temp_args['current_path'] = request.path
        self.temp_args['subnav'] = self.format_subnav(**kwargs)
        self.temp_args['breadcrumb'] = self.breadcrumb_html(
            self.get_breadcrumb_dict())
        self.temp_args['metadata_block'] = render_template(
            self.metadata_template,
            **self.metadata)
        self.temp_args['metadata'] = self.safe_metadata()
        self.temp_args['upload_link'] = url_for(
            f'forms.upload_{self.data_type}_data',
            uuid=self.metadata[self.id_key])

        if self.data_type != 'cdf_forecast':
            self.temp_args['delete_link'] = url_for(
                f'data_dashboard.delete_{self.data_type}',
                uuid=self.metadata[self.id_key])
        else:
            # update allowed actions based on parent cdf_forecast_group
            allowed = users.actions_on(self.metadata['parent'])
            g.allowed_actions = allowed['actions']

        self.temp_args['period_start_date'] = start.strftime('%Y-%m-%d')
        self.temp_args['period_start_time'] = start.strftime('%H:%M')
        self.temp_args['period_end_date'] = end.strftime('%Y-%m-%d')
        self.temp_args['period_end_time'] = end.strftime('%H:%M')
        self.temp_args.update(kwargs)

    def get(self, uuid, **kwargs):
        self.temp_args = {}
        # Attempt a request for the object's metadata. On an error,
        # inject the errors into the template arguments and skip
        # any further processing.
        try:
            self.metadata = self.api_handle.get_metadata(uuid)
        except DataRequestException as e:
            self.temp_args.update({'errors': e.errors})
        else:
            self.set_timerange()
            start, end = self.parse_start_end_from_querystring()
            try:
                self.set_site_or_aggregate_metadata()
            except DataRequestException:
                self.temp_args.update({'plot': None})
            else:
                self.insert_plot(uuid, start, end)
            finally:
                self.set_site_or_aggregate_link()
                self.set_template_args(start=start, end=end, **kwargs)
        return render_template(self.template, **self.temp_args)

    def post(self, uuid):
        """Data download endpoint.
        """
        return download_timeseries(self, uuid)


class SingleCDFForecastGroupView(SingleObjectView):
    template = 'data/cdf_forecast.html'
    metadata_template = 'data/metadata/cdf_forecast_group_metadata.html'
    human_label = human_friendly_datatype('cdf_forecast')

    def __init__(self):
        pass

    def get_breadcrumb_dict(self, **kwargs):
        """See BaseView.get_breadcrumb_dict.
        """
        breadcrumb_dict = OrderedDict()
        if self.metadata.get('site') is not None:
            # If the site is accessible, add /sites/<site name>
            # to the breadcrumb.
            breadcrumb_dict['Sites'] = url_for('data_dashboard.sites')
            breadcrumb_dict[self.metadata['site']['name']] = url_for(
                'data_dashboard.site_view',
                uuid=self.metadata['site_id'])
            breadcrumb_dict[f'{self.human_label}s'] = url_for(
                'data_dashboard.cdf_forecast_groups',
                site_id=self.metadata['site_id'])
        elif self.metadata.get('aggregate') is not None:
            breadcrumb_dict['Aggregates'] = url_for(
                'data_dashboard.aggregates')
            breadcrumb_dict[self.metadata['aggregate']['name']] = url_for(
                'data_dashboard.aggregate_view',
                uuid=self.metadata['aggregate_id'])
            breadcrumb_dict[f'{self.human_label}s'] = url_for(
                f'data_dashboard.cdf_forecast_groups',
                aggregate_id=self.metadata['aggregate_id'])
        else:
            breadcrumb_dict[f'{self.human_label}s'] = url_for(
                'data_dashboard.cdf_forecast_groups')
        breadcrumb_dict[self.metadata['name']] = url_for(
            'data_dashboard.cdf_forecast_group_view',
            uuid=self.metadata['forecast_id'])
        return breadcrumb_dict

    def set_template_args(self, **kwargs):
        """Insert necessary template arguments. See data/asset.html in the
        template folder for how these are layed out.
        """
        self.temp_args['current_path'] = request.path
        self.temp_args['subnav'] = self.format_subnav(**kwargs)
        self.temp_args['breadcrumb'] = self.breadcrumb_html(
            self.get_breadcrumb_dict())
        self.temp_args['metadata_block'] = render_template(
            self.metadata_template,
            **self.metadata)
        self.temp_args['metadata'] = self.safe_metadata()
        self.temp_args['constant_values'] = self.metadata['constant_values']
        self.temp_args['delete_link'] = url_for(
            f'data_dashboard.delete_cdf_forecast_group',
            uuid=self.metadata['forecast_id'])

    def get(self, uuid, **kwargs):
        self.temp_args = {}
        try:
            self.metadata = cdf_forecast_groups.get_metadata(uuid)
        except DataRequestException as e:
            self.temp_args.update({'errors': e.errors})
        else:
            try:
                self.set_site_or_aggregate_metadata()
            except DataRequestException:
                pass
            finally:
                self.set_site_or_aggregate_link()
                self.set_template_args()
        return render_template(self.template, **self.temp_args)


class AccessView(DataDashView):
    template = 'data/access.html'


class TrialsView(DataDashView):
    template = 'data/trials.html'


# Url Rule Registration
# The url rules here are broken into sections based on their function.
# For instance, all views that display a tabulated listing of metadata
# are grouped under 'Listing pages'. The view names for each section
# follow a pattern that you should follow when adding new views. The
# patterns help to ensure predictable arguments when calling the
# built-in flask url_for() function.
data_dash_blp = Blueprint('data_dashboard', 'data_dashboard')

# Listing pages
# view name pattern: '<data_type>s'
data_dash_blp.add_url_rule(
    '/sites/',
    view_func=SitesListingView.as_view('sites'))
data_dash_blp.add_url_rule(
    '/observations/',
    view_func=DataListingView.as_view('observations', data_type='observation'))
data_dash_blp.add_url_rule(
    '/forecasts/single/',
    view_func=DataListingView.as_view('forecasts', data_type='forecast'))
data_dash_blp.add_url_rule(
    '/forecasts/cdf/',
    view_func=DataListingView.as_view('cdf_forecast_groups',
                                      data_type='cdf_forecast_group'))
data_dash_blp.add_url_rule(
    '/reports/',
    view_func=ReportsView.as_view('reports'))
data_dash_blp.add_url_rule(
    '/aggregates/',
    view_func=AggregatesView.as_view('aggregates'))

# Views for a single piece of metadata
# view name pattern: '<data_type>_view'
data_dash_blp.add_url_rule(
    '/sites/<uuid>/',
    view_func=SingleSiteView.as_view('site_view'))
data_dash_blp.add_url_rule(
    '/observations/<uuid>',
    view_func=SingleObjectView.as_view(
        'observation_view', data_type='observation'))
data_dash_blp.add_url_rule(
    '/forecasts/single/<uuid>',
    view_func=SingleObjectView.as_view(
        'forecast_view', data_type='forecast'))
data_dash_blp.add_url_rule(
    '/forecasts/cdf/single/<uuid>',
    view_func=SingleObjectView.as_view(
        'cdf_forecast_view', data_type='cdf_forecast'))
data_dash_blp.add_url_rule(
    '/forecasts/cdf/<uuid>',
    view_func=SingleCDFForecastGroupView.as_view('cdf_forecast_group_view'))
data_dash_blp.add_url_rule(
    '/reports/<uuid>',
    view_func=ReportView.as_view('report_view'))
data_dash_blp.add_url_rule(
    '/aggregates/<uuid>',
    view_func=AggregateView.as_view('aggregate_view'))


# Download forms
data_dash_blp.add_url_rule(
    '/reports/<uuid>/download/html',
    view_func=DownloadReportView.as_view(
        'download_report_html', format_='html'))
data_dash_blp.add_url_rule(
    '/reports/<uuid>/download/pdf',
    view_func=DownloadReportView.as_view(
        'download_report_pdf', format_='pdf'))


# Deletion forms
# View name pattern: 'delete_<data_type>'
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
data_dash_blp.add_url_rule(
    '/reports/<uuid>/delete',
    view_func=DeleteReportView.as_view('delete_report'))
data_dash_blp.add_url_rule(
    '/aggregates/<uuid>/delete',
    view_func=DeleteAggregateView.as_view('delete_aggregate'))
