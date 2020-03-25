from flask import url_for, request, render_template, redirect

from sfa_dash.api_interface import (sites, observations, forecasts,
                                    cdf_forecast_groups)
from sfa_dash.blueprints.dash import DataDashView
from sfa_dash.errors import DataRequestException


class DeleteConfirmation(DataDashView):
    def __init__(self, data_type):
        if data_type == 'forecast':
            self.api_handle = forecasts
            self.metadata_template = 'data/metadata/forecast_metadata.html'
        elif data_type == 'observation':
            self.api_handle = observations
            self.metadata_template = 'data/metadata/observation_metadata.html'
        elif data_type == 'cdf_forecast_group':
            self.api_handle = cdf_forecast_groups
            self.metadata_template = 'data/metadata/cdf_forecast_group_metadata.html' # NOQA
        elif data_type == 'site':
            self.api_handle = sites
            self.metadata_template = 'data/metadata/site_metadata.html'
        else:
            raise ValueError(f'No Deletetion Form defined for {data_type}.')
        self.data_type = data_type
        self.template = 'forms/deletion_form.html'

    def set_template_args(self, **kwargs):
        self.temp_args.update({
            'metadata': render_template(self.metadata_template,
                                        **self.metadata),
            'uuid': self.metadata['uuid'],
            'data_type': self.data_type,
        })
        if 'errors' in kwargs:
            self.temp_args.update({'errors': kwargs['errors']})

    def get(self, uuid, **kwargs):
        """Presents a deletion confirmation form that makes a post
        request to this endpoint on submission
        """
        try:
            self.metadata = self.api_handle.get_metadata(uuid)
        except DataRequestException as e:
            return render_template(self.template, uuid=uuid, errors=e.errors)
        else:
            self.temp_args = {}
            try:
                self.set_site_or_aggregate_metadata()
            except DataRequestException:
                pass
            self.metadata['uuid'] = uuid
            self.set_site_or_aggregate_link()
            self.set_template_args(**kwargs)
        return render_template(self.template, **self.temp_args)

    def post(self, uuid):
        """Carries out the delete request to the API"""
        confirmation_url = url_for(f'data_dashboard.delete_{self.data_type}',
                                   _external=True,
                                   uuid=uuid)
        if request.headers['Referer'] != confirmation_url:
            # If the user was directed from anywhere other than
            # the confirmation page, redirect to confirm.
            return redirect(confirmation_url)
        try:
            self.api_handle.delete(uuid)
        except DataRequestException as e:
            return self.get(uuid, errors=e.errors)
        return redirect(url_for(f'data_dashboard.{self.data_type}s'))
