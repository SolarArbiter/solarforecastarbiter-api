"""Draft of reports endpoints/pages. Need to integrate core report generation.
"""
from flask import (request, redirect, url_for, render_template, send_file,
                   current_app)
from requests.exceptions import HTTPError
from solarforecastarbiter.reports.main import report_to_html_body
from solarforecastarbiter.reports.template import full_html
from sfa_dash.api_interface import (observations, forecasts, sites, reports,
                                    aggregates)


from sfa_dash.utils import check_sign_zip
from sfa_dash.blueprints.base import BaseView
from sfa_dash.blueprints.util import filter_form_fields, handle_response


class ReportsView(BaseView):
    template = 'dash/reports.html'

    def template_args(self):
        reports_list = reports.list_full_reports()
        return {
            "page_title": 'Reports',
            "reports": reports_list,
        }


class ReportForm(BaseView):
    template = 'forms/report_form.html'

    def get_pairable_objects(self):
        """Requests the forecasts and observations from
        the api for injecting into the dom as a js variable
        """
        observation_list = handle_response(
            observations.list_metadata())
        forecast_list = handle_response(forecasts.list_metadata())
        site_list = handle_response(sites.list_metadata())
        aggregate_list = handle_response(aggregates.list_metadata())
        for obs in observation_list:
            del obs['extra_parameters']
        for fx in forecast_list:
            del fx['extra_parameters']
        for site in site_list:
            del site['extra_parameters']
        for agg in aggregate_list:
            del agg['extra_parameters']
        return {
            'observations': observation_list,
            'forecasts': forecast_list,
            'sites': site_list,
            'aggregates': aggregate_list
        }

    def template_args(self):
        return {
            "page_data": self.get_pairable_objects(),
        }

    def zip_object_pairs(self, form_data):
        """Create a list of object pair dictionaries containing a
        forecast and either an observation or aggregate.
        """
        # Forecasts can be parsed directly
        fx = filter_form_fields('forecast-id-', form_data)

        # observations and aggregates are passed in as truth-id-{index}
        # and truth-type-{index}, so we must match these with the
        # appropriately indexed forecast.
        truth_ids = filter_form_fields('truth-id-', form_data)
        truth_types = filter_form_fields('truth-type-', form_data)
        pairs = [{'forecast': f, truth_types[i]: truth_ids[i]}
                 for i, f in enumerate(fx)]
        return pairs

    def parse_filters(self, form_data):
        """Return an empty array until we know more about how we want
        to configure these filters
        """
        return []

    def parse_report_parameters(self, form_data):
        params = {}
        params['object_pairs'] = self.zip_object_pairs(form_data)
        params['metrics'] = request.form.getlist('metrics')
        params['categories'] = request.form.getlist('categories')
        # filters do not currently work in API
        # params['filters'] = self.parse_filters(form_data)
        params['start'] = form_data['period-start']
        params['end'] = form_data['period-end']
        return params

    def report_formatter(self, form_data):
        formatted = {}
        formatted['name'] = form_data['name']
        formatted['report_parameters'] = self.parse_report_parameters(
            form_data)
        return formatted

    def post(self):
        form_data = request.form
        api_payload = self.report_formatter(form_data)
        if len(api_payload['report_parameters']['object_pairs']) == 0:
            errors = {
                'error': [('Must include at least 1 Forecast, Observation '
                           'pair.')],
            }
            return super().get(form_data=api_payload, errors=errors)
        try:
            reports.post_metadata(api_payload)
        except HTTPError as e:
            if e.response.status_code == 400:
                # flatten error response to handle nesting
                errors = e.response.json()['errors']
            elif e.response.status_code == 404:
                errors = {'error': ['Permission to create report denied.']}
            else:
                errors = {'error': ['An unrecoverable error occured.']}
            return super().get(form_data=api_payload, errors=errors)
        return redirect(url_for(
            'data_dashboard.reports',
            messages={'creation': 'successful'}))


class ReportView(BaseView):
    template = 'data/report.html'

    def template_args(self):
        report_template = report_to_html_body(self.metadata)
        return {'report': report_template,
                'includes_bokeh': True}

    def get(self, uuid):
        try:
            self.metadata = reports.get_metadata(uuid)
        except ValueError as e:
            # Core threw an error trying to calculate the report
            errors = {
                'Access': ['Report could not be loaded in the failed state.'],
                'errors': [str(e)],
            }
            return render_template(self.template, uuid=uuid, errors=errors)
        return super().get()


class DownloadReportView(BaseView):
    def __init__(self, format_, **kwargs):
        self.format_ = format_

    def get(self, uuid):
        metadata = reports.get_metadata(uuid)
        # render to right format
        if self.format_ == 'html':
            fname = metadata.name.replace(' ', '_')
            body = report_to_html_body(metadata)
            # should make a nice template for standalone reports
            bytes_out = full_html(body).encode('utf-8')
        else:
            raise ValueError(
                'Only html report downloads is currently supported')
        out = check_sign_zip(bytes_out, fname + f'.{self.format_}',
                             current_app.config['GPG_KEY_ID'],
                             current_app.config['GPG_PASSPHRASE_FILE'])
        return send_file(
            out,
            'application/zip',
            as_attachment=True,
            attachment_filename=fname + '.zip',
            add_etags=False)


class DeleteReportView(BaseView):
    template = 'forms/deletion_form.html'
    metadata_template = 'data/metadata/report_metadata.html'

    def template_args(self):
        return {
            'data_type': 'report',
            'uuid': self.metadata.report_id,
            'metadata': render_template(
                self.metadata_template,
                data_type='Report',
                metadata_object=self.metadata
            ),
        }

    def get(self, uuid):
        try:
            self.metadata = reports.get_metadata(uuid)
        except ValueError as e:
            errors = {
                'Access': ['Report could not be loaded in the failed state.'],
                'Report Computation': [str(e)],
            }
            return render_template(self.template, data_type='report',
                                   uuid=uuid, errors=errors)
        return super().get()

    def post(self, uuid):
        confirmation_url = url_for(f'data_dashboard.delete_report',
                                   _external=True,
                                   uuid=uuid)
        if request.headers['Referer'] != confirmation_url:
            # If the user was directed from anywhere other than
            # the confirmation page, redirect to confirm.
            return redirect(confirmation_url)
        try:
            delete_request = reports.delete(uuid)
        except HTTPError as e:
            if e.response.status_code == 400:
                # Redirect and display errors if the delete request
                # failed
                response_json = delete_request.json()
                errors = response_json['errors']
            elif e.response.status_code == 404:
                errors = {
                    "404": ['The requested object could not be found.']
                }
            else:
                errors = {
                    "error": ["Could not complete the requested action."]
                }
            return self.get(uuid, errors=errors)
        return redirect(url_for(
            f'data_dashboard.reports',
            messages={'delete': ['Success']}))
