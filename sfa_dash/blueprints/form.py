import json
from json.decoder import JSONDecodeError

from flask import (Blueprint, render_template, request,
                   abort, redirect, url_for, flash)
from sfa_dash.api_interface import (sites, observations, forecasts,
                                    cdf_forecasts, cdf_forecast_groups,
                                    aggregates)
from sfa_dash.blueprints.aggregates import (AggregateObservationAdditionForm,
                                            AggregateObservationRemovalForm)
from sfa_dash.blueprints.base import BaseView
from sfa_dash.blueprints.reports import (ReportForm, RecomputeReportView,
                                         ReportCloneView)
from sfa_dash.errors import DataRequestException
from sfa_dash.form_utils import converters


class CreateForm(BaseView):
    def __init__(self, data_type, location_type=None):
        """Sets the appropriate instance variables based on data_type.

        Parameters
        ----------
        data_type: str
            Passed to MetadataForm.__init__ to set the proper template,
            api_handle, metadata_template, formatter, and id_key.
        location_type: str
            The type of location to use either 'site' or 'aggregate'

        Notes
        -----
        Instance variables:
            template
                The path to the form template to be rendered. tempaltes are
                found in sfa_dash/templates/forms.
            id_key
                The key used to reference the object's uuid. For example,
                observations have an id_key of 'observation_id'.
            api_handle
                The module in `sfa_dash.api_interface` that handles api
                interaction for the datatype.
            formatter
                The class in `sfa_dash.form_utils.converters` used to process
                form data into an api payload and vice versa.
            metadata_template
                The path to the template for rendering metadata to display to
                the user on the form. For exmaple, displaying site metadata
                when creating a new observation. Note that this field is
                is not used for sites or aggregates, which do not reference
                other objects at creation.
            metadata_handler
                 The module in `sfa_dash.api_interface` that handles api
                 interaction for a site or aggregate.
        """
        self.data_type = data_type
        if location_type is not None:
            if location_type in ['site', 'aggregate']:
                self.location_type = location_type
                if location_type == 'site':
                    self.metadata_handler = sites
                    self.metadata_template = 'data/metadata/site_metadata.html'
                else:
                    self.metadata_handler = aggregates
                    self.metadata_template = 'data/metadata/aggregate_metadata.html'  # noqa
            else:
                raise ValueError('Invalid location_type.')
        if data_type == 'forecast':
            self.template = 'forms/forecast_form.html'
            self.id_key = 'forecast_id'
            self.api_handle = forecasts
            self.formatter = converters.ForecastConverter
        elif data_type == 'cdf_forecast_group':
            self.template = 'forms/cdf_forecast_group_form.html'
            self.id_key = 'forecast_id'
            self.api_handle = cdf_forecast_groups
            self.formatter = converters.CDFForecastConverter
        elif data_type == 'observation':
            self.template = 'forms/observation_form.html'
            self.id_key = 'observation_id'
            self.api_handle = observations
            self.formatter = converters.ObservationConverter
        elif data_type == 'site':
            self.template = 'forms/site_form.html'
            self.id_key = 'site_id'
            self.api_handle = sites
            self.formatter = converters.SiteConverter
        elif data_type == 'aggregate':
            self.template = 'forms/aggregate_form.html'
            self.id_key = 'aggregate_id'
            self.api_handle = aggregates
            self.formatter = converters.AggregateConverter
        else:
            raise ValueError(f'No metadata form defined for {data_type}')

    def render_metadata_section(self, metadata, template=None):
        metadata_template = template or self.metadata_template
        return render_template(metadata_template, **metadata)

    def get(self, uuid=None):
        template_args = {}
        if uuid is not None:
            try:
                loc_metadata = self.metadata_handler.get_metadata(uuid)
            except DataRequestException as e:
                self.flash_api_errors(e.errors)
                return redirect(url_for(
                    f'data_dashboard.{self.data_type}s'))
            else:
                template_args[f'{self.location_type}_metadata'] = loc_metadata
                template_args['metadata_block'] = render_template(
                    self.metadata_template,
                    **loc_metadata)
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
                    loc_metadata = self.metadata_handler.get_metadata(uuid)
                except DataRequestException as e:
                    template_args['errors'].update(self.flatten_dict(e.errors))
                else:
                    template_args[f'{self.location_type}_metadata'] = loc_metadata  # noqa
                    template_args['metadata_block'] = render_template(
                        self.metadata_template,
                        **loc_metadata)
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

    def set_template_args(self):
        self.template_args = {}
        self.template_args['metadata_block'] = render_template(
            self.metadata_template,
            **self.metadata)
        self.template_args['metadata'] = self.safe_metadata()

    def get(self, uuid, **kwargs):
        try:
            self.metadata = self.api_handle.get_metadata(uuid)
            self.set_site_or_aggregate_metadata()
            self.metadata['site_link'] = self.generate_site_link(
                self.metadata)
        except DataRequestException as e:
            return render_template(self.template, errors=e.errors)
        else:
            self.set_template_args()
        return render_template(self.template, uuid=uuid, **self.template_args,
                               **kwargs)

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

    def set_template_args(self):
        """Attempts to fetch and render the site or aggregate metadata if
        needed, then converts metadata into form data for prefilling a form.

        Raises
        ------
        DataRequestException
            If the site or aggregate metadata could not be read.
        """
        self.template_args = {}
        if(
            self.data_type != 'site'
            and self.data_type != 'aggregate'
        ):
            self.set_site_or_aggregate_metadata()
            self.set_site_or_aggregate_link()

        # We must pass a metadata template path here, because we must
        # parse a site or aggregate from the object being cloned,
        # instead of relying on metadata_template being set by init.
        if 'site' in self.metadata:
            self.template_args['site_metadata'] = self.metadata['site']
            self.template_args['metadata'] = self.render_metadata_section(
                self.template_args['site_metadata'],
                'data/metadata/site_metadata.html')
        elif 'aggregate' in self.metadata:
            self.template_args['aggregate_metadata'] = self.metadata['aggregate']  # noqa
            self.template_args['metadata'] = self.render_metadata_section(
                self.template_args['aggregate_metadata'],
                'data/metadata/aggregate_metadata.html')
        form_data = self.formatter.payload_to_formdata(self.metadata)
        self.template_args['form_data'] = form_data

    def get(self, uuid=None):
        if uuid is not None:
            try:
                self.metadata = self.api_handle.get_metadata(uuid)
            except DataRequestException as e:
                self.flash_api_errors(e.errors)
                return redirect(url_for(
                    f'data_dashboard.{self.data_type}s'))
            else:
                try:
                    self.set_template_args()
                except DataRequestException:
                    flash('Could not read site metadata. Cloning failed.',
                          'error')
                    return redirect(
                        url_for(f'data_dashboard.{self.data_type}', uuid=uuid))
        return render_template(self.template, **self.template_args)


forms_blp = Blueprint('forms', 'forms')
forms_blp.add_url_rule('/sites/create',
                       view_func=CreateForm.as_view('create_site',
                                                    data_type='site'))
forms_blp.add_url_rule('/aggregates/create',
                       view_func=CreateForm.as_view('create_aggregate',
                                                    data_type='aggregate',
                                                    location_type='site'))
forms_blp.add_url_rule('/sites/<uuid>/observations/create',
                       view_func=CreateForm.as_view('create_observation',
                                                    data_type='observation',
                                                    location_type='site'))
forms_blp.add_url_rule('/sites/<uuid>/forecasts/single/create',
                       view_func=CreateForm.as_view('create_forecast',
                                                    data_type='forecast',
                                                    location_type='site'))
forms_blp.add_url_rule('/sites/<uuid>/forecasts/cdf/create',
                       view_func=CreateForm.as_view(
                           'create_cdf_forecast_group',
                           data_type='cdf_forecast_group',
                           location_type='site'))

forms_blp.add_url_rule('/aggregates/<uuid>/forecasts/single/create',
                       view_func=CreateForm.as_view(
                           'create_aggregate_forecast',
                           data_type='forecast',
                           location_type='aggregate'))
forms_blp.add_url_rule('/aggregates/<uuid>/forecasts/cdf/create',
                       view_func=CreateForm.as_view(
                           'create_aggregate_cdf_forecast_group',
                           data_type='cdf_forecast_group',
                           location_type='aggregate'))


# cloning endpoints
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
forms_blp.add_url_rule('/reports/<uuid>/clone',
                       view_func=ReportCloneView.as_view('clone_report'))
# upload endpoints
forms_blp.add_url_rule('/observations/<uuid>/upload',
                       view_func=UploadForm.as_view('upload_observation_data',
                                                    data_type='observation'))
forms_blp.add_url_rule('/forecasts/single/<uuid>/upload',
                       view_func=UploadForm.as_view('upload_forecast_data',
                                                    data_type='forecast'))
forms_blp.add_url_rule('/forecasts/cdf/single/<uuid>/upload',
                       view_func=UploadForm.as_view('upload_cdf_forecast_data',
                                                    data_type='cdf_forecast'))
# Report specific forms
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
forms_blp.add_url_rule('/reports/<uuid>/recompute',
                       view_func=RecomputeReportView.as_view(
                           'recompute_report'))
# Aggregate specific forms
forms_blp.add_url_rule('/aggregates/<uuid>/add',
                       view_func=AggregateObservationAdditionForm.as_view(
                           'add_aggregate_observations'))
forms_blp.add_url_rule('/aggregates/<uuid>/remove/<observation_id>',
                       view_func=AggregateObservationRemovalForm.as_view(
                           'remove_aggregate_observations'))
