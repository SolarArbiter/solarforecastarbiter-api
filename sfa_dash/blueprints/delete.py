from flask import url_for, request, render_template, abort, redirect

from sfa_dash.api_interface import (sites, observations, forecasts,
                                    cdf_forecast_groups)
from sfa_dash.blueprints.dash import DataDashView


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

    def template_args(self, **kwargs):
        temp_args = {
            'metadata': render_template(self.metadata_template,
                                        **self.metadata),
            'site_metadata': self.metadata['site'],
            'uuid': self.metadata['uuid'],
            'data_type': self.data_type,
        }
        if 'errors' in kwargs:
            temp_args.update({'errors': kwargs['errors']})
        return temp_args

    def get(self, uuid, **kwargs):
        """Presents a deletion confirmation form that makes a post
        request to this endpoint on submission
        """
        metadata_request = self.api_handle.get_metadata(uuid)
        if metadata_request.status_code != 200:
            abort(404)
        self.metadata = metadata_request.json()
        self.metadata['uuid'] = uuid
        self.metadata['site'] = self.get_site_metadata(
            self.metadata['site_id'])
        self.metadata['site_link'] = self.generate_site_link(self.metadata)
        return render_template(
            self.template,
            **self.template_args(**kwargs))

    def post(self, uuid):
        """Carries out the delete request to the API"""
        confirmation_url = url_for(f'data_dashboard.delete_{self.data_type}',
                                   _external=True,
                                   uuid=uuid)
        if request.headers['Referer'] != confirmation_url:
            # If the user was directed from anywhere other than
            # the confirmation page, redirect to confirm.
            return redirect(confirmation_url)
        delete_request = self.api_handle.delete(uuid)
        if delete_request.status_code == 204:
            return redirect(url_for(f'data_dashboard.{self.data_type}s'))
        elif delete_request.status_code == 400:
            # Redirect and display errors if the delete request
            # failed
            response_json = delete_request.json()
            errors = response_json['errors']
            return self.get(uuid, errors=errors)
        elif delete_request.status_code == 404:
            abort(404)
        else:
            errors = {"error": ["Could not complete the requested action."]}
            return self.get(uuid, errors=errors)
