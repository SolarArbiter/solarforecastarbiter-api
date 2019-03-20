import json

from flask import Blueprint, render_template, request, abort, redirect, url_for
from sfa_dash.api_interface import sites, observations, forecasts
from sfa_dash.blueprints.base import BaseView


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
        if data_type == 'observation':
            self.template = 'forms/obs_form.html'
            self.id_key = 'obs_id'
            self.api_handle = observations
            self.formatter = self.observation_formatter
            self.metadata_template = 'data/metadata/site_metadata.html'
        if data_type == 'site':
            self.template = 'forms/site_form.html'
            self.id_key = 'site_id'
            self.api_handle = sites
            self.formatter = self.site_formatter

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
            The number of minutes in the Timedelta or 'NaT' if invalid units
            are provided.

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
            return 'NaT'

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
        modeling_keys = ['ac_capacity', 'dc_capacity',
                         'ac_loss_factor', 'dc_loss_factor',
                         'temperature_coefficient', 'axis_azimuth',
                         'tracking_type', 'backtrack',
                         'axis_tilt', 'ground_coverage_ratio',
                         'surface_tilt', 'surface_azimuth']
        top_level_keys = ['name', 'elevation', 'latitude',
                          'longitude', 'timezone', 'extra_parameters']
        site_metadata = {key: site_dict[key]
                         for key in top_level_keys
                         if site_dict.get(key, "") != ""}
        modeling_params = {key: site_dict[key]
                           for key in modeling_keys
                           if site_dict.get(key, "") != ""}
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
        direct_keys = ['name', 'variable', 'value_type', 'uncertainty',
                       'extra_parameters', 'interval_label', 'site_id']
        observation_metadata = {key: observation_dict[key]
                                for key in direct_keys
                                if observation_dict.get(key, "") != ""}
        observation_metadata['interval_length'] = self.parse_timedelta(
                observation_dict,
                'interval_length')
        return observation_metadata

    def forecast_formatter(self, forecast_dict):
        forecast_metadata = {}
        direct_keys = ['name', 'variable', 'value_type', 'extra_parameters',
                       'interval_length', 'interval_label', 'site_id']
        forecast_metadata = {key: forecast_dict[key]
                             for key in direct_keys
                             if forecast_dict.get(key, '') != ''}
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

    def get(self):
        raise NotImplementedError

    def post(self):
        raise NotImplementedError


class CreateForm(MetadataForm):
    def __init__(self, data_type):
        super().__init__(data_type)

    def get_site_metadata(self, site_id):
        site_metadata_request = sites.get_metadata(site_id)
        if site_metadata_request.status_code != 200:
            abort(404)
        site_metadata = site_metadata_request.json()
        return site_metadata

    def render_metadata_section(self, metadata):
        return render_template(self.metadata_template, **metadata)

    def get(self, site_id=None):
        template_args = {}
        if site_id is not None:
            site_metadata = self.get_site_metadata(site_id)
            template_args['site_metadata'] = site_metadata
            template_args['metadata'] = self.render_metadata_section(
                site_metadata)
        return render_template(self.template, **template_args)

    def post(self, site_id=None):
        form_data = request.form
        formatted_form = self.formatter(form_data)
        response = self.api_handle.post_metadata(formatted_form)
        template_args = {}
        if site_id is not None:
            site_metadata = self.get_site_metadata(site_id)
            template_args['site_metadata'] = site_metadata
            template_args['metadata'] = self.render_metadata_section(
                site_metadata)

        if response.status_code == 201:
            uuid = response.text
            return redirect(url_for(f'data_dashboard.{self.data_type}_view',
                                    uuid=uuid))
        elif response.status_code == 400:
            errors = response.json()['errors']
            template_args['errors'] = self.flatten_dict(errors)
        elif response.status_code == 401:
            template_args['errors'] = {'Unauthorized': 'You do not have'
                                       'permissions to create resources '
                                       f'of type {self.data_type}'}
        else:
            template_args['errors'] = {'Error': 'Something went wrong, please '
                                       'contact a site administrator.'}

        return render_template(self.template, form_data=form_data,
                               **template_args)


class UploadForm(BaseView):
    def __init__(self, data_type):
        self.data_type = data_type
        if data_type == 'observation':
            self.template = 'forms/obs_data_form.html'
            self.metadata_template = 'data/metadata/observation_metadata.html'
            self.api_handle = observations
        if data_type == 'forecast':
            self.template = 'forms/forecast_data_form.html'
            self.metadata_template = 'data/metadata/forecast_metadata.html'
            self.api_handle = forecasts

    def render_metadata_section(self, metadata):
        return render_template(self.metadata_template, **metadata)

    def get(self, uuid):
        metadata_request = self.api_handle.get_metadata(uuid)
        if metadata_request.status_code != 200:
            abort(404)
        metadata_dict = metadata_request.json()
        metadata_dict['site_link'] = self.generate_site_link(metadata_dict)
        metadata = self.render_metadata_section(metadata_dict)
        return render_template(self.template, uuid=uuid, metadata=metadata)

    def post(self, uuid):
        if request.mimetype != 'multipart/form-data':
            abort(415)
        if f'{self.data_type}-data' not in request.files:
            return 'no file part in request'
        posted_file = request.files[f'{self.data_type}-data']
        if posted_file.filename == '':
            return 'no filename'
        if posted_file.mimetype == 'text/csv':
            posted_data = posted_file.read()
            post_request = self.api_handle.post_values(
                uuid,
                posted_data.decode('utf-8'),
                json=False)
        elif posted_file.mimetype == 'application/json':
            posted_data = json.load(posted_file)
            post_request = self.api_handle.post_values(uuid, posted_data)
        if post_request.status_code != 201:
            errors = post_request.json()['errors']
            return render_template(self.template, uuid=uuid, errors=errors)
        else:
            return redirect(url_for(f'data_dashboard.{self.data_type}_view',
                                    uuid=uuid))


forms_blp = Blueprint('forms', 'forms')
forms_blp.add_url_rule('/sites/create',
                       view_func=CreateForm.as_view('create_site',
                                                    data_type='site'))
forms_blp.add_url_rule('/sites/<site_id>/observations/create',
                       view_func=CreateForm.as_view('create_site_observation',
                                                    data_type='observation'))
forms_blp.add_url_rule('/sites/<site_id>/forecasts/create',
                       view_func=CreateForm.as_view('create_site_forecast',
                                                    data_type='forecast'))
forms_blp.add_url_rule('/observations/<uuid>/upload',
                       view_func=UploadForm.as_view('upload_observation_data',
                                                    data_type='observation'))
forms_blp.add_url_rule('/forecasts/<uuid>/upload',
                       view_func=UploadForm.as_view('upload_forecast_data',
                                                    data_type='forecast'))
