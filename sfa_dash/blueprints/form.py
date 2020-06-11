import json
from json.decoder import JSONDecodeError

from flask import (Blueprint, render_template, request,
                   abort, redirect, url_for, flash)
from sfa_dash.api_interface import (sites, observations, forecasts,
                                    cdf_forecasts, cdf_forecast_groups,
                                    aggregates)
from sfa_dash.blueprints.aggregates import (AggregateForm,
                                            AggregateObservationAdditionForm,
                                            AggregateObservationRemovalForm)
from sfa_dash.blueprints.base import BaseView
from sfa_dash.blueprints.reports import ReportForm, RecomputeReportView
from sfa_dash.errors import DataRequestException
from sfa_dash.form_utils import converters


class MetadataForm(BaseView):
    """Base form view.
    """
    def __init__(self, data_type):
        self.data_type = data_type
        if data_type == 'forecast':
            self.template = 'forms/forecast_form.html'
            self.id_key = 'forecast_id'
            self.api_handle = forecasts
            self.formatter = converters.ForecastConverter
            self.metadata_template = 'data/metadata/site_metadata.html'
        elif data_type == 'cdf_forecast_group':
            self.template = 'forms/cdf_forecast_group_form.html'
            self.id_key = 'forecast_id'
            self.api_handle = cdf_forecast_groups
            self.formatter = converters.CDFForecastConverter
            self.metadata_template = 'data/metadata/site_metadata.html'
        elif data_type == 'observation':
            self.template = 'forms/observation_form.html'
            self.id_key = 'observation_id'
            self.api_handle = observations
            self.formatter = converters.ObservationConverter
            self.metadata_template = 'data/metadata/site_metadata.html'
        elif data_type == 'site':
            self.template = 'forms/site_form.html'
            self.id_key = 'site_id'
            self.api_handle = sites
            self.formatter = converters.SiteConverter
        else:
            raise ValueError(f'No metadata form defined for {data_type}')

    def get(self):
        raise NotImplementedError

    def post(self):
        raise NotImplementedError


class CreateForm(MetadataForm):
    def __init__(self, data_type):
        super().__init__(data_type)

    def render_metadata_section(self, metadata, template=None):
        metadata_template = template or self.metadata_template
        return render_template(metadata_template, **metadata)

    def get(self, uuid=None):
        template_args = {}
        if uuid is not None:
            try:
                site_metadata = sites.get_metadata(uuid)
            except DataRequestException as e:
                self.flash_api_errors(e.errors)
                return redirect(url_for(
                    f'data_dashboard.{self.data_type}s'))
            else:
                template_args['site_metadata'] = site_metadata
                template_args['metadata'] = self.render_metadata_section(
                    site_metadata)
        return render_template(self.template, **template_args)

    def post(self, uuid=None):
        form_data = request.form
        formatted_form = self.formatter.formdata_to_payload(form_data)
        template_args = {}
        try:
            created_uuid = self.api_handle.post_metadata(formatted_form)
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
                    site_metadata = sites.get_metadata(uuid)
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
            self.formatter = converters.ForecastConverter
            self.metadata_template = 'data/metadata/aggregate_metadata.html'
        elif data_type == 'cdf_forecast_group':
            self.template = 'forms/aggregate_cdf_forecast_group_form.html'
            self.id_key = 'forecast_id'
            self.api_handle = cdf_forecast_groups
            self.formatter = converters.CDFForecastConverter
            self.metadata_template = 'data/metadata/aggregate_metadata.html'
        else:
            raise ValueError(f'No metadata form defined for {data_type}')

    def get_aggregate_metadata(self, aggregate_id):
        return aggregates.get_metadata(aggregate_id)

    def render_metadata_section(self, metadata):
        return render_template(
            self.metadata_template, **metadata)

    def get(self, uuid=None):
        template_args = {}
        if uuid is not None:
            try:
                aggregate_metadata = self.get_aggregate_metadata(uuid)
            except DataRequestException as e:
                self.flash_api_errors(e.errors)
                return redirect(url_for(f'data_dashboard.aggregates'))
            else:
                template_args['aggregate_metadata'] = aggregate_metadata
                template_args['metadata'] = self.render_metadata_section(
                    aggregate_metadata)
        return render_template(self.template, **template_args)

    def post(self, uuid=None):
        form_data = request.form
        formatted_form = self.formatter.formdata_to_payload(form_data)
        template_args = {}
        try:
            created_uuid = self.api_handle.post_metadata(formatted_form)
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

    def get(self, uuid, **kwargs):
        temp_args = {}
        try:
            metadata_dict = self.api_handle.get_metadata(uuid)
            metadata_dict['site_link'] = self.generate_site_link(
                metadata_dict)
        except DataRequestException as e:
            temp_args = {'errors': e.errors}
        else:
            temp_args.update(
                {'metadata': self.render_metadata_section(metadata_dict)})
        return render_template(self.template, uuid=uuid, **temp_args, **kwargs)

    def post(self, uuid):
        errors = {}
        if request.mimetype != 'multipart/form-data':
            abort(415)
        if f'{self.data_type}-data' not in request.files:
            errors = {"file-part": ['No file part in request.']}
        posted_file = request.files[f'{self.data_type}-data']
        if posted_file.filename == '':
            errors = {'filename': ['No filename.']}
        # if the file was not found in the request, skip parsing
        if not errors:
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
                            'Failed to decode file. Please ensure file is a '
                            'CSV with UTF-8 encoding. This error can sometimes'
                            ' occur when a csv is improperly exported from '
                            'excel.'],
                    }
                else:
                    try:
                        self.api_handle.post_values(uuid, decoded_data,
                                                    json=False)
                    except DataRequestException as e:
                        errors = e.errors
            elif posted_file.mimetype == 'application/json':
                try:
                    posted_data = json.load(posted_file)
                except JSONDecodeError:
                    errors = {
                        'json': ["Error parsing JSON file."]
                    }
                else:
                    try:
                        self.api_handle.post_values(uuid, posted_data)
                    except DataRequestException as e:
                        errors = e.errors
            else:
                errors = {
                    'mime-type': [
                        f'Unsupported file type {posted_file.mimetype}.']
                }
        if errors:
            return self.get(uuid=uuid, errors=errors)
        else:
            return redirect(url_for(f'data_dashboard.{self.data_type}_view',
                                    uuid=uuid))


class CloneForm(CreateForm):
    def __init__(self, data_type):
        super().__init__(data_type)

    def fill_nested_metadata(self):
        pass

    def get(self, uuid=None):
        template_args = {}
        if uuid is not None:
            try:
                self.metadata = self.api_handle.get_metadata(uuid)
            except DataRequestException as e:
                self.flash_api_errors(e.errors)
                return redirect(url_for(
                    f'data_dashboard.{self.data_type}s'))
            else:
                if(
                    self.data_type != 'site'
                    and self.data_type != 'aggregate'
                ):
                    try:
                        self.set_site_or_aggregate_metadata()
                    except DataRequestException:
                        flash('Could not read site metadata. Cloning failed.',
                              'error')
                        return redirect(f'data_dashboard.{self.data_type}',
                                        uuid=uuid)
                    self.set_site_or_aggregate_link()

                if 'site' in self.metadata:
                    template_args['site_metadata'] = self.metadata['site']
                    template_args['metadata'] = self.render_metadata_section(
                        template_args['site_metadata'])
                elif 'aggregate' in self.metadata:
                    template_args['aggregate_metadata'] = self.metadata['aggregate']  # noqa
                    template_args['metadata'] = self.render_metadata_section(
                        template_args['aggregate_metadata'],
                        'data/metadata/aggregate_metadata.html')
                form_data = self.formatter.payload_to_formdata(self.metadata)
        return render_template(self.template, form_data=form_data,
                               **template_args)


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
forms_blp.add_url_rule('/sites/<uuid>/clone',
                       view_func=CloneForm.as_view('clone_site',
                                                   data_type='site'))
forms_blp.add_url_rule('/observations/<uuid>/clone',
                       view_func=CloneForm.as_view('clone_observation',
                                                   data_type='observation'))
forms_blp.add_url_rule('/forecasts/single/<uuid>/clone',
                       view_func=CloneForm.as_view('clone_forecast',
                                                   data_type='forecast'))
forms_blp.add_url_rule('/forecasts/cdf/<uuid>/clone',
                       view_func=CloneForm.as_view(
                           'clone_cdf_forecast_group',
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
forms_blp.add_url_rule('/reports/deterministic/create',
                       view_func=ReportForm.as_view(
                           'create_deterministic_report',
                           report_type='deterministic'))
forms_blp.add_url_rule('/reports/event/create',
                       view_func=ReportForm.as_view(
                           'create_event_report',
                           report_type='event'))
forms_blp.add_url_rule('/reports/probabilistic/create',
                       view_func=ReportForm.as_view(
                           'create_probabilistic_report',
                           report_type='probabilistic'))
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
forms_blp.add_url_rule('/reports/<uuid>/recompute',
                       view_func=RecomputeReportView.as_view(
                           'recompute_report'))
