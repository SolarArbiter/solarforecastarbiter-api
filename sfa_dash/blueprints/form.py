import json

from flask import (Blueprint, render_template, request,
                   abort, redirect, url_for, make_response)
import pandas as pd
from sfa_dash.api_interface import (sites, observations, forecasts,
                                    cdf_forecasts, cdf_forecast_groups,
                                    aggregates)
from sfa_dash.blueprints.aggregates import (AggregateForm,
                                            AggregateObservationAdditionForm,
                                            AggregateObservationRemovalForm)
from sfa_dash.blueprints.base import BaseView
from sfa_dash.blueprints.reports import ReportForm
from sfa_dash.blueprints.util import handle_response
from sfa_dash.errors import DataRequestException


class MetadataForm(BaseView):
    """Base form view.
    """
    def __init__(self, data_type):
        self.data_type = data_type
        if data_type == 'forecast':
            self.template = 'forms/forecast_form.html'
            self.id_key = 'forecast_id'
            self.api_handle = forecasts
            self.formatter = self.forecast_formatter
            self.metadata_template = 'data/metadata/site_metadata.html'
        elif data_type == 'cdf_forecast_group':
            self.template = 'forms/cdf_forecast_group_form.html'
            self.id_key = 'forecast_id'
            self.api_handle = cdf_forecast_groups
            self.formatter = self.cdf_forecast_formatter
            self.metadata_template = 'data/metadata/site_metadata.html'
        elif data_type == 'observation':
            self.template = 'forms/observation_form.html'
            self.id_key = 'observation_id'
            self.api_handle = observations
            self.formatter = self.observation_formatter
            self.metadata_template = 'data/metadata/site_metadata.html'
        elif data_type == 'site':
            self.template = 'forms/site_form.html'
            self.id_key = 'site_id'
            self.api_handle = sites
            self.formatter = self.site_formatter
        else:
            raise ValueError(f'No metadata form defined for {data_type}')

    def flatten_dict(self, to_flatten):
        """Flattens nested dictionaries, removing keys of the nested elements.
        Useful for flattening API responses for prefilling forms on the
        dashboard.
        """
        flattened = {}
        for key, value in to_flatten.items():
            if isinstance(value, dict):
                flattened.update(self.flatten_dict(value))
            else:
                flattened[key] = value
        return flattened

    def parse_hhmm_field(self, data_dict, key_root):
        """ Extracts and parses the hours and minutes inputs to create a
        parseable time of day string in HH:MM format. These times are
        displayed as two select fields designated with a name (key_root)
        and _hours or _minutes suffix.

        Parameters
        ----------
        data_dict: dict
            Dictionary of posted form data

        key_root: string
            The shared part of the name attribute of the inputs to parse.
            e.g. 'issue_time' will parse and concatenate 'issue_time_hours'
            and 'issue_time_minutes'

        Returns
        -------
        string
            The time value in HH:MM format.
        """
        hours = int(data_dict[f'{key_root}_hours'])
        minutes = int(data_dict[f'{key_root}_minutes'])
        return f'{hours:02d}:{minutes:02d}'

    def parse_timedelta(self, data_dict, key_root):
        """Parse values from a timedelta form element, and return the value in
        minutes

        Parameters
        ----------
        data_dict: dict
            Dictionary of posted form data

        key_root: string
            The shared part of the name attribute of the inputs to parse.
            e.g. 'lead_time' will parse and concatenate 'lead_time_number'
            and 'lead_time_units'

        Returns
        -------
        int
            The number of minutes in the Timedelta.
        """
        value = int(data_dict[f'{key_root}_number'])
        units = data_dict[f'{key_root}_units']
        if units == 'minutes':
            return value
        elif units == 'hours':
            return value * 60
        elif units == 'days':
            return value * 1440
        else:
            raise ValueError('Invalid selection in time units field.')

    def site_formatter(self, site_dict):
        """Formats the result of a site webform into an API payload.

        Parameters
        ----------
        site_dict:  dict
            The posted form data parsed into a dict.
        Returns
        -------
        dictionary
            Form data formatted to the API spec.
        """
        tracking_keys = {
            'fixed': ['surface_tilt', 'surface_azimuth'],
            'single_axis': ['axis_azimuth', 'backtrack',
                            'axis_tilt', 'ground_coverage_ratio',
                            'max_rotation_angle'],
        }
        modeling_keys = ['ac_capacity', 'dc_capacity',
                         'ac_loss_factor', 'dc_loss_factor',
                         'temperature_coefficient', 'tracking_type']

        top_level_keys = ['name', 'elevation', 'latitude',
                          'longitude', 'timezone', 'extra_parameters']
        site_metadata = {key: site_dict[key]
                         for key in top_level_keys
                         if site_dict.get(key, "") != ""}
        if site_dict['site_type'] == 'power-plant':
            modeling_params = {key: site_dict[key]
                               for key in modeling_keys
                               if site_dict.get(key, "") != ""}
            tracking_type = site_dict['tracking_type']
            tracking_fields = {key: site_dict[key]
                               for key in tracking_keys[tracking_type]}
            modeling_params.update(tracking_fields)
            site_metadata['modeling_parameters'] = modeling_params
        return site_metadata

    def observation_formatter(self, observation_dict):
        """Formats the result of a observation webform into an API payload.

        Parameters
        ----------
        site_dict:  dict
            The posted form data parsed into a dict.
        Returns
        -------
        dictionary
            Form data formatted to the API spec.
        """
        observation_metadata = {}
        direct_keys = ['name', 'variable', 'interval_value_type',
                       'uncertainty', 'extra_parameters', 'interval_label',
                       'site_id']
        observation_metadata = {key: observation_dict[key]
                                for key in direct_keys
                                if observation_dict.get(key, "") != ""}
        observation_metadata['interval_length'] = self.parse_timedelta(
            observation_dict,
            'interval_length')
        return observation_metadata

    def set_location_id(self, form_data, forecast_metadata):
        if 'site_id' in form_data:
            forecast_metadata['site_id'] = form_data.get('site_id')
        if 'aggregate_id' in form_data:
            forecast_metadata['aggregate_id'] = form_data.get('aggregate_id')

    def forecast_formatter(self, forecast_dict):
        forecast_metadata = {}
        direct_keys = ['name', 'variable', 'interval_value_type',
                       'extra_parameters', 'interval_length',
                       'interval_label']
        forecast_metadata = {key: forecast_dict[key]
                             for key in direct_keys
                             if forecast_dict.get(key, '') != ''}
        self.set_location_id(forecast_dict, forecast_metadata)
        forecast_metadata['issue_time_of_day'] = self.parse_hhmm_field(
            forecast_dict,
            'issue_time')
        forecast_metadata['lead_time_to_start'] = self.parse_timedelta(
            forecast_dict,
            'lead_time')
        forecast_metadata['run_length'] = self.parse_timedelta(
            forecast_dict,
            'run_length')
        forecast_metadata['interval_length'] = self.parse_timedelta(
            forecast_dict,
            'interval_length')
        return forecast_metadata

    def get_site_metadata(self, site_id):
        return handle_response(sites.get_metadata(site_id))

    def cdf_forecast_formatter(self, forecast_dict):
        cdf_forecast_metadata = self.forecast_formatter(forecast_dict)
        constant_values = forecast_dict['constant_values'].split(',')
        cdf_forecast_metadata['constant_values'] = constant_values
        cdf_forecast_metadata['axis'] = forecast_dict['axis']
        return cdf_forecast_metadata

    def get(self):
        raise NotImplementedError

    def post(self):
        raise NotImplementedError


class CreateForm(MetadataForm):
    def __init__(self, data_type):
        super().__init__(data_type)

    def render_metadata_section(self, metadata):
        return render_template(self.metadata_template, **metadata)

    def get(self, uuid=None):
        template_args = {}
        if uuid is not None:
            site_metadata = self.get_site_metadata(uuid)
            template_args['site_metadata'] = site_metadata
            template_args['metadata'] = self.render_metadata_section(
                site_metadata)
        return render_template(self.template, **template_args)

    def post(self, uuid=None):
        form_data = request.form
        formatted_form = self.formatter(form_data)
        template_args = {}
        try:
            created_uuid = handle_response(
                self.api_handle.post_metadata(formatted_form))
        except DataRequestException as e:
            if e.status_code == 404:
                errors = {
                    '404': [('You do not have permission to create '
                            f'{self.data_type}s. You may need to request '
                             'permissions from your organization '
                             'administrator.')]
                }
            else:
                errors = e.errors
            if 'errors' in template_args:
                template_args['errors'].update(
                    self.flatten_dict(errors))
            else:
                template_args['errors'] = self.flatten_dict(errors)
            if uuid is not None:
                try:
                    site_metadata = self.get_site_metadata(uuid)
                except DataRequestException as e:
                    template_args['errors'].update(self.flatten_dict(e.errors))
                else:
                    template_args['site_metadata'] = site_metadata
                    template_args['metadata'] = self.render_metadata_section(
                        site_metadata)
            return render_template(
                self.template, form_data=form_data, **template_args)
        return redirect(url_for(f'data_dashboard.{self.data_type}_view',
                                uuid=created_uuid))


class CreateAggregateForecastForm(MetadataForm):
    """Endpoint for creating Forecasts that reference aggregates.
    """
    def __init__(self, data_type):
        self.data_type = data_type
        if data_type == 'forecast':
            self.template = 'forms/aggregate_forecast_form.html'
            self.id_key = 'forecast_id'
            self.api_handle = forecasts
            self.formatter = self.forecast_formatter
            self.metadata_template = 'data/metadata/aggregate_metadata.html'
        elif data_type == 'cdf_forecast_group':
            self.template = 'forms/aggregate_cdf_forecast_group_form.html'
            self.id_key = 'forecast_id'
            self.api_handle = cdf_forecast_groups
            self.formatter = self.cdf_forecast_formatter
            self.metadata_template = 'data/metadata/aggregate_metadata.html'
        else:
            raise ValueError(f'No metadata form defined for {data_type}')

    def get_aggregate_metadata(self, aggregate_id):
        return handle_response(aggregates.get_metadata(aggregate_id))

    def render_metadata_section(self, metadata):
        return render_template(
            self.metadata_template, **metadata)

    def get(self, uuid=None):
        template_args = {}
        if uuid is not None:
            aggregate_metadata = self.get_aggregate_metadata(uuid)
            template_args['aggregate_metadata'] = aggregate_metadata
            template_args['metadata'] = self.render_metadata_section(
                aggregate_metadata)
        return render_template(self.template, **template_args)

    def post(self, uuid=None):
        form_data = request.form
        formatted_form = self.formatter(form_data)
        template_args = {}
        try:
            created_uuid = handle_response(
                self.api_handle.post_metadata(formatted_form))
        except DataRequestException as e:
            if e.status_code == 404:
                errors = {
                    '404': [('You do not have permission to create '
                            f'{self.data_type}s. You may need to request '
                             'permissions from your organization '
                             'administrator.')]
                }
            else:
                errors = e.errors
            if 'errors' in template_args:
                template_args['errors'].update(
                    self.flatten_dict(errors))
            else:
                template_args['errors'] = self.flatten_dict(errors)
            if uuid is not None:
                try:
                    aggregate_metadata = self.get_aggregate_metadata(uuid)
                except DataRequestException as e:
                    template_args['errors'].update(self.flatten_dict(e.errors))
                else:
                    template_args['aggregate_metadata'] = aggregate_metadata
                    template_args['metadata'] = self.render_metadata_section(
                        aggregate_metadata)
            return render_template(
                self.template, form_data=form_data, **template_args)
        return redirect(url_for(f'data_dashboard.{self.data_type}_view',
                                uuid=created_uuid))


class UploadForm(BaseView):
    def __init__(self, data_type):
        self.data_type = data_type
        if data_type == 'observation':
            self.template = 'forms/observation_upload_form.html'
            self.metadata_template = 'data/metadata/observation_metadata.html'
            self.api_handle = observations
        elif data_type == 'forecast':
            self.template = 'forms/forecast_upload_form.html'
            self.metadata_template = 'data/metadata/forecast_metadata.html'
            self.api_handle = forecasts
        elif data_type == 'cdf_forecast':
            self.template = 'forms/cdf_forecast_upload_form.html'
            self.metadata_template = 'data/metadata/cdf_forecast_metadata.html'
            self.api_handle = cdf_forecasts
        else:
            raise ValueError(f'No upload form defined for {data_type}')

    def render_metadata_section(self, metadata):
        return render_template(self.metadata_template, **metadata)

    def get(self, uuid):
        temp_args = {}
        try:
            metadata_dict = handle_response(
                self.api_handle.get_metadata(uuid))
            metadata_dict['site_link'] = self.generate_site_link(
                metadata_dict)
        except DataRequestException as e:
            temp_args = {'errors': e.errors}
        else:
            temp_args.update(
                {'metadata': self.render_metadata_section(metadata_dict)})
        return render_template(self.template, uuid=uuid, **temp_args)

    def post(self, uuid):
        if request.mimetype != 'multipart/form-data':
            abort(415)
        if f'{self.data_type}-data' not in request.files:
            return 'no file part in request'
        posted_file = request.files[f'{self.data_type}-data']
        if posted_file.filename == '':
            return 'no filename'
        if (
                posted_file.mimetype == 'text/csv' or
                posted_file.mimetype == 'application/vnd.ms-excel'
        ):
            posted_data = posted_file.read()
            try:
                decoded_data = posted_data.decode('utf-8')
            except UnicodeDecodeError:
                errors = {
                    'file-type': [
                        'Failed to decode file. Please ensure file is a CSV '
                        'with UTF-8 encoding. This error can sometimes occur '
                        'when a csv is improperly exported from excel.'],
                }
                return render_template(self.template, uuid=uuid, errors=errors)
            else:
                post_request = self.api_handle.post_values(
                    uuid,
                    decoded_data,
                    json=False)
        elif posted_file.mimetype == 'application/json':
            posted_data = json.load(posted_file)
            post_request = self.api_handle.post_values(uuid, posted_data)
        else:
            errors = {
                'mime-type': [f'Unsupported file type {posted_file.mimetype}.']
            }
            return render_template(self.template, uuid=uuid, errors=errors)
        try:
            handle_response(post_request)
        except DataRequestException as e:
            return render_template(self.template, uuid=uuid, errors=e.errors)
        else:
            return redirect(url_for(f'data_dashboard.{self.data_type}_view',
                                    uuid=uuid))


class DownloadForm(BaseView):
    def __init__(self, data_type):
        self.data_type = data_type
        if data_type == 'observation':
            self.template = 'forms/observation_download_form.html'
            self.metadata_template = 'data/metadata/observation_metadata.html'
            self.api_handle = observations
        elif data_type == 'forecast':
            self.template = 'forms/forecast_download_form.html'
            self.metadata_template = 'data/metadata/forecast_metadata.html'
            self.api_handle = forecasts
        elif data_type == 'cdf_forecast':
            self.template = 'forms/cdf_forecast_download_form.html'
            self.metadata_template = 'data/metadata/cdf_forecast_metadata.html'
            self.api_handle = cdf_forecasts
        elif data_type == 'aggregate':
            self.template = 'forms/aggregate_download_form.html'
            self.metadata_template = 'data/metadata/aggregate_metadata.html'
            self.api_handle = aggregates
        else:
            raise ValueError(f'No Download form configured for {data_type}.')

    def format_params(self, form_data):
        """Parses start and end time and the format from the posted form.
        Returns headers and query parameters for requesting the data.

        Parameters
        ----------
        form_data: dict
            Dictionary of posted form values.

        Returns
        -------
        headers: dict
            The accept headers set to 'text/csv' or 'application/json'
            based on the selected format.
        params: dict
            Query parameters start and end, both formatted in iso8601 and
            localized to the provided timezone.
        """
        start_date = form_data["period-start-date"]
        start_time = form_data["period-start-time"]
        start_dt = pd.Timestamp(f'{start_date} {start_time}', tz='utc')
        end_date = form_data["period-end-date"]
        end_time = form_data["period-end-time"]
        end_dt = pd.Timestamp(f'{end_date} {end_time}', tz='utc')
        params = {
            'start': start_dt.isoformat(),
            'end': end_dt.isoformat(),
        }
        headers = {'Accept': form_data['format']}
        return headers, params

    def template_args(self, uuid):
        try:
            metadata_dict = handle_response(
                self.api_handle.get_metadata(uuid))
        except DataRequestException as e:
            return {'errors': e.errors}
        metadata_dict['site_link'] = self.generate_site_link(metadata_dict)
        metadata = render_template(self.metadata_template, **metadata_dict)
        return {'metadata': metadata, 'uuid': uuid}

    def get(self, uuid):
        return render_template(self.template, **self.template_args(uuid))

    def post(self, uuid):
        form_data = request.form
        try:
            headers, params = self.format_params(form_data)
        except ValueError:
            errors = {'start-end': ['Invalid datetime']}
            response = make_response(render_template(
                self.template, form_data=form_data,
                errors=errors, **self.template_args(uuid)), 400)
            return response
        else:
            try:
                data = handle_response(
                    self.api_handle.get_values(
                        uuid, headers=headers, params=params))
            except DataRequestException as e:
                return render_template(
                    self.template, **self.template_args(uuid), errors=e.errors)
            else:
                if form_data['format'] == 'application/json':
                    response = make_response(json.dumps(data))
                    response.headers.set('Content-Type', 'application/json')
                    response.headers.set(
                        'Content-Disposition',
                        'attachment',
                        filename='data.json')
                elif form_data['format'] == 'text/csv':
                    response = make_response(data)
                    response.headers.set('Content-Type', 'text/csv')
                    response.headers.set(
                        'Content-Disposition',
                        'attachment',
                        filename='data.csv')
                else:
                    raise ValueError('Invalid Format.')
            return response


forms_blp = Blueprint('forms', 'forms')
forms_blp.add_url_rule('/sites/create',
                       view_func=CreateForm.as_view('create_site',
                                                    data_type='site'))
forms_blp.add_url_rule('/sites/<uuid>/observations/create',
                       view_func=CreateForm.as_view('create_observation',
                                                    data_type='observation'))
forms_blp.add_url_rule('/sites/<uuid>/forecasts/single/create',
                       view_func=CreateForm.as_view('create_forecast',
                                                    data_type='forecast'))
forms_blp.add_url_rule('/sites/<uuid>/forecasts/cdf/create',
                       view_func=CreateForm.as_view(
                           'create_cdf_forecast_group',
                           data_type='cdf_forecast_group'))
forms_blp.add_url_rule('/observations/<uuid>/upload',
                       view_func=UploadForm.as_view('upload_observation_data',
                                                    data_type='observation'))
forms_blp.add_url_rule('/forecasts/single/<uuid>/upload',
                       view_func=UploadForm.as_view('upload_forecast_data',
                                                    data_type='forecast'))
forms_blp.add_url_rule('/forecasts/cdf/single/<uuid>/upload',
                       view_func=UploadForm.as_view('upload_cdf_forecast_data',
                                                    data_type='cdf_forecast'))
forms_blp.add_url_rule('/observations/<uuid>/download',
                       view_func=DownloadForm.as_view(
                           'download_observation_data',
                           data_type='observation'))
forms_blp.add_url_rule('/forecasts/single/<uuid>/download',
                       view_func=DownloadForm.as_view('download_forecast_data',
                                                      data_type='forecast'))
forms_blp.add_url_rule('/forecasts/cdf/single/<uuid>/download',
                       view_func=DownloadForm.as_view(
                           'download_cdf_forecast_data',
                           data_type='cdf_forecast'))
forms_blp.add_url_rule('/aggregates/<uuid>/download',
                       view_func=DownloadForm.as_view(
                           'download_aggregate_data',
                           data_type='aggregate'))
forms_blp.add_url_rule('/reports/create',
                       view_func=ReportForm.as_view('create_report'))
forms_blp.add_url_rule('/aggregates/create',
                       view_func=AggregateForm.as_view(
                           'create_aggregate'))
forms_blp.add_url_rule('/aggregates/<uuid>/add',
                       view_func=AggregateObservationAdditionForm.as_view(
                           'add_aggregate_observations'))
forms_blp.add_url_rule('/aggregates/<uuid>/remove/<observation_id>',
                       view_func=AggregateObservationRemovalForm.as_view(
                           'remove_aggregate_observations'))
forms_blp.add_url_rule('/aggregates/<uuid>/forecasts/single/create',
                       view_func=CreateAggregateForecastForm.as_view(
                           'create_aggregate_forecast',
                           data_type='forecast'))
forms_blp.add_url_rule('/aggregates/<uuid>/forecasts/cdf/create',
                       view_func=CreateAggregateForecastForm.as_view(
                           'create_aggregate_cdf_forecast_group',
                           data_type='cdf_forecast_group'))
