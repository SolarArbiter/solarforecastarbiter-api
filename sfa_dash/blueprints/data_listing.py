"""Flask endpoints for listing Observations, Forecasts and CDF Forecasts.
Defers actual table creation and rendering to DataTables in the util module.
"""
from flask import render_template, request, url_for


from sfa_dash.api_interface import sites, aggregates
from sfa_dash.blueprints.base import BaseView
from sfa_dash.blueprints.util import DataTables
from sfa_dash.filters import human_friendly_datatype

from sfa_dash.errors import DataRequestException


class DataListingView(BaseView):
    """Lists accessible forecasts/observations.
    """
    template = 'data/table.html'
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
        elif data_type == 'cdf_forecast_group':
            self.table_function = DataTables.get_cdf_forecast_table
        else:
            raise Exception
        self.data_type = data_type

    def get_breadcrumb(self, location_metadata={}):
        """Build the breadcrumb dictionary for the listing page.
        Parameters
        ----------
        location_metadata:  dict
            Dict of aggregate or site metadata to use for building
            the breadcrumb.
        """
        breadcrumb = []
        human_label = human_friendly_datatype(self.data_type)
        if 'site_id' in location_metadata:
            breadcrumb.append(('Sites', url_for('data_dashboard.sites')))
            breadcrumb.append(
                (location_metadata['name'],
                 url_for(
                     'data_dashboard.site_view',
                     uuid=location_metadata['site_id']))
            )
            breadcrumb.append(
                (f'{human_label}s',
                 url_for(
                     f'data_dashboard.{self.data_type}s',
                     site_id=location_metadata['site_id']))
            )
        elif 'aggregate_id' in location_metadata:
            breadcrumb.append(
                ('Aggregates', url_for('data_dashboard.aggregates')))
            breadcrumb.append(
                (location_metadata['name'],
                 url_for(
                     'data_dashboard.aggregate_view',
                     uuid=location_metadata['aggregate_id']))
            )
            breadcrumb.append(
                (f'{human_label}s',
                 url_for(
                     f'data_dashboard.{self.data_type}s',
                     aggregate_id=location_metadata['aggregate_id']))
            )
        return breadcrumb

    def get_subnav_kwargs(self, site_id=None, aggregate_id=None):
        """Creates a dict to be unpacked as arguments when calling the
        BaseView.format_subnav function resulting dict is used to format the
        fstring keys found in the DataListingView.subnav_format variable.
        """
        subnav_kwargs = {}
        if aggregate_id is not None:
            subnav_kwargs['observations_url'] = url_for(
                'data_dashboard.aggregate_view', uuid=aggregate_id)
        else:
            subnav_kwargs['observations_url'] = url_for(
                'data_dashboard.observations',
                site_id=site_id, aggregate_id=aggregate_id)
        subnav_kwargs['forecasts_url'] = url_for(
            'data_dashboard.forecasts',
            site_id=site_id, aggregate_id=aggregate_id)
        subnav_kwargs['cdf_forecasts_url'] = url_for(
            'data_dashboard.cdf_forecast_groups',
            site_id=site_id, aggregate_id=aggregate_id)
        return subnav_kwargs

    def set_template_args(self, site_id=None, aggregate_id=None):
        """Builds a dictionary of the appropriate template arguments.
        """
        self.template_args = {}
        # If an id was passed in, set the breadcrumb. The request for location
        # metadata may triggers an error if the object doesnt exist or the user
        # does not have access. So we can handle with a 404 message instead of
        # silently failing and listing all objects.
        if site_id is not None or aggregate_id is not None:
            if site_id is not None:
                location_metadata = sites.get_metadata(site_id)
            else:
                location_metadata = aggregates.get_metadata(aggregate_id)
            self.template_args['breadcrumb'] = self.breadcrumb_html(
                self.get_breadcrumb(location_metadata))

        else:
            self.template_args['page_title'] = 'Forecasts and Observations'

        self.template_args['subnav'] = self.format_subnav(
            **self.get_subnav_kwargs(site_id=site_id,
                                     aggregate_id=aggregate_id))
        table, _ = self.table_function(site_id, aggregate_id)
        self.template_args['data_table'] = table
        self.template_args['current_path'] = request.path

    def get(self):
        """This endpoints results in creating a table of the datatype passed to
        __init__. A site_id or aggregate_id can passed to create a filtered
        list of the given type for that site or aggregate.
        """
        try:
            self.set_template_args(
                request.args.get('site_id'),
                request.args.get('aggregate_id'))
        except DataRequestException as e:
            return render_template(self.template, errors=e.errors)
        return render_template(self.template, **self.template_args)
