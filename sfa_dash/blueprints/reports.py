"""Draft of reports endpoints/pages. Need to integrate core report generation.
"""
from flask import request, redirect, url_for, render_template
from requests.exceptions import HTTPError

from solarforecastarbiter.reports.main import report_to_html_body
from sfa_dash.api_interface import observations, forecasts, sites, reports
from sfa_dash.blueprints.base import BaseView
from sfa_dash.blueprints.util import filter_form_fields


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
        observation_request = observations.list_metadata()
        forecast_request = forecasts.list_metadata()
        site_request = sites.list_metadata()
        observation_list = observation_request.json()
        for obs in observation_list:
            del obs['extra_parameters']
        forecast_list = forecast_request.json()
        for fx in forecast_list:
            del fx['extra_parameters']
        site_list = site_request.json()
        for site in site_list:
            del site['extra_parameters']
        return {
            'observations': observation_list,
            'forecasts': forecast_list,
            'sites': site_list
        }

    def template_args(self):
        return {
            "page_data": self.get_pairable_objects(),
        }

    def zip_object_pairs(self, form_data):
        """Create a list of observation, forecast tuples from the the
        (forecast-n, observation-n) input elements inserted by
        report-handling.js
        """
        fx = filter_form_fields('forecast-id-', form_data)
        obs = filter_form_fields('observation-id-', form_data)
        pairs = list(zip(fx, obs))
        return pairs

    def parse_metrics(self, form_data):
        """Collect the keys (name attributes) of the form elements with a value
        attribute of metrics. These elements are checkbox inputs, and are only
        included in the form data when selected.
        """
        return [k.lower() for k, v in form_data.items() if v == 'metrics']

    def parse_filters(self, form_data):
        """Return an empty array until we know more about how we want
        to configure these filters
        """
        return []

    def parse_report_parameters(self, form_data):
        params = {}
        params['object_pairs'] = self.zip_object_pairs(form_data)
        params['metrics'] = self.parse_metrics(form_data)
        params['filters'] = self.parse_filters(form_data)
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
            return super().get(form_data=form_data, errors=errors)
        try:
            reports.post_metadata(api_payload)
        except HTTPError as e:
            if e.response.status_code == 400:
                # flatten error response to handle nesting
                errors = e.response.json()['errors']
                return super().get(form_data=form_data, errors=errors)
            elif e.response.status_code == 404:
                errors = {'error': ['Permission to create report denied.']}
            else:
                errors = {'error': ['An unrecoverable error occured.']}
            return super().get(form_data=form_data, errors=errors)
        return redirect(url_for(
            'data_dashboard.reports',
            messages={'creation': 'successful'}))


class ReportView(BaseView):
    template = 'data/report.html'

    def template_args(self):
        report_template = report_to_html_body(self.metadata)
        return {'report': report_template,
                'bokeh_script': True}

    def get(self, uuid):
        self.metadata = reports.get_metadata(uuid)
        return super().get()


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

    def get(self, uuid, **kwargs):
        self.metadata = reports.get_metadata(uuid)
        return super().get(**kwargs)

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
