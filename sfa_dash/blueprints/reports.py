from flask import (request, redirect, url_for, render_template, send_file,
                   current_app, flash)

from solarforecastarbiter.datamodel import Report, RawReport
from solarforecastarbiter.io.utils import load_report_values
from solarforecastarbiter.reports.template import (
    get_template_and_kwargs, render_html, render_pdf)

from sfa_dash.api_interface import (observations, forecasts, sites, reports,
                                    aggregates, cdf_forecast_groups)
from sfa_dash.utils import check_sign_zip
from sfa_dash.blueprints.base import BaseView
from sfa_dash.blueprints.util import filter_form_fields
from sfa_dash.errors import DataRequestException


ALLOWED_REPORT_TYPES = ['deterministic', 'probabilistic', 'event']


class ReportsView(BaseView):
    template = 'data/reports.html'

    def set_template_args(self):
        try:
            reports_list = reports.list_metadata()
        except DataRequestException as e:
            return {'errors': e.errors}
        self.template_args = {
            "page_title": 'Reports',
            "reports": reports_list,
        }


class ReportForm(BaseView):
    def set_template(self):
        if self.report_type == 'event':
            self.template = 'forms/event_report_form.html'
        elif self.report_type == 'probabilistic':
            self.template = 'forms/probabilistic_report_form.html'
        else:
            self.template = 'forms/report_form.html'

    def __init__(self, report_type):
        if report_type not in ALLOWED_REPORT_TYPES:
            raise ValueError('Invalid report_type.')
        else:
            self.report_type = report_type
            self.set_template()

    def get_pairable_objects(self):
        """Requests the forecasts and observations from
        the api for injecting into the dom as a js variable
        """
        observation_list = observations.list_metadata()
        if self.report_type == 'probabilistic':
            forecast_list = cdf_forecast_groups.list_metadata()
        else:
            forecast_list = forecasts.list_metadata()
        site_list = sites.list_metadata()
        aggregate_list = aggregates.list_metadata()
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

    def set_template_args(self):
        self.template_args = {
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

        reference_forecasts = filter_form_fields('reference-forecast-',
                                                 form_data)

        uncertainty_values = filter_form_fields('deadband-value-', form_data)
        forecast_types = filter_form_fields('forecast-type-', form_data)
        pairs = [{'forecast': f,
                  truth_types[i]: truth_ids[i],
                  'reference_forecast': reference_forecasts[i],
                  'uncertainty': uncertainty_values[i],
                  'forecast_type': forecast_types[i]}
                 for i, f in enumerate(fx)]
        return pairs

    def parse_filters(self, form_data):
        """Create a list of dictionary filters. Currently just supports
        `quality_flags` which supports a list of quality flag names to exclude.
        """
        filters = []
        quality_flags = request.form.getlist('quality_flags')
        if quality_flags:
            filters.append({'quality_flags': quality_flags})
        return filters

    def apply_crps(self, params):
        """Checks for "probabilistic_forecast' forecast_type in object pairs
        and if found, appends the CRPS metric to the metrics options.
        """
        pair_fx_types = [f['forecast_type'] for f in params['object_pairs']]
        if'probabilistic_forecast' in pair_fx_types:
            new_params = params.copy()
            new_params['metrics'].append('crps')
            return new_params
        else:
            return params

    def parse_report_parameters(self, form_data):
        params = {}
        params['name'] = form_data['name']
        params['object_pairs'] = self.zip_object_pairs(form_data)
        params['metrics'] = request.form.getlist('metrics')
        params['categories'] = request.form.getlist('categories')
        # filters do not currently work in API
        params['filters'] = self.parse_filters(form_data)
        params['start'] = form_data['period-start']
        params['end'] = form_data['period-end']
        params = self.apply_crps(params)
        return params

    def report_formatter(self, form_data):
        formatted = {}
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
            return self.get(form_data=api_payload, errors=errors)
        try:
            report_id = reports.post_metadata(api_payload)
        except DataRequestException as e:
            if e.status_code == 404:
                errors = {
                    '404': [('You do not have permission to create '
                             'reports. You may need to request '
                             'permissions from your organization '
                             'administrator.')]
                }
            else:
                errors = e.errors
            return self.get(form_data=api_payload, errors=errors)
        return redirect(url_for(
            'data_dashboard.report_view',
            uuid=report_id,
        ))


def build_report(metadata):
    """Reorganizes report processed values into the propper place for
    plotting and creates a `solarforecastarbiter.datamodel.Report` object.
    """
    report = Report.from_dict(metadata)
    if metadata['raw_report'] is not None:
        raw_report = RawReport.from_dict(metadata['raw_report'])
        pfxobs = load_report_values(raw_report, metadata['values'])
        report = report.replace(raw_report=raw_report.replace(
            processed_forecasts_observations=pfxobs))
    return report


class ReportView(BaseView):
    template = 'data/report.html'

    def should_include_timeseries(self):
        if self.metadata['status'] != 'complete':
            return False
        raw_report = self.metadata['raw_report']
        pfxobs = raw_report['processed_forecasts_observations']
        total_data_points = 0
        for fxobs in pfxobs:
            fxobs_data_points = fxobs['valid_point_count'] * 2
            total_data_points = total_data_points + fxobs_data_points
        return total_data_points < current_app.config['REPORT_DATA_LIMIT']

    def set_template_args(self):
        include_timeseries = self.should_include_timeseries()
        report_object = build_report(self.metadata)
        report_template, report_kwargs = get_template_and_kwargs(
            report_object,
            request.url_root.rstrip('/'),
            include_timeseries,
            True
        )
        report_kwargs.update({
            'report_template': report_template,
            'dash_url': request.url_root.rstrip('/'),
            'include_metrics_toc': False,
            'includes_bokeh': True
        })
        if not include_timeseries:
            # display a message about omitting timeseries
            download_link = url_for('data_dashboard.download_report_html',
                                    uuid=self.metadata['report_id'])
            script = ''
            div = f"""<div class="alert alert-warning">
    <strong>Warning</strong> To improve performance timeseries plots have been
    omitted from this report. You may download a copy of this report with the
    timeseries plots included:
    <a href="{download_link}">Download HTML Report.</a></div>"""
            report_kwargs.update({
                'timeseries_div': div,
                'timeseries_script': script,
            })
        self.template_args = report_kwargs

    def set_metadata(self, uuid):
        """Loads all necessary data for loading a
        `solarforecastarbiter.datamodel.Report` with processed forecasts and
        observations.
        """
        metadata = reports.get_metadata(uuid)
        metadata['report_parameters']['object_pairs'] = []
        self.metadata = metadata

    def get(self, uuid):
        try:
            self.set_metadata(uuid)
        except DataRequestException as e:
            return render_template(self.template, uuid=uuid, errors=e.errors)
        return super().get()


class DownloadReportView(ReportView):
    def __init__(self, format_, **kwargs):
        self.format_ = format_

    def get(self, uuid):
        try:
            self.set_metadata(uuid)
        except DataRequestException as e:
            errors = {'errors': e.errors}
            return ReportView().get(uuid, errors=errors)

        # don't do the work of making a report if the format is incorrect
        if self.format_ not in ('html', 'pdf'):
            raise ValueError(
                'Only html and pdf report downloads are currently supported')

        fname = self.metadata['report_parameters']['name'].replace(
                ' ', '_')
        report_object = build_report(self.metadata)
        # render to right format
        if self.format_ == 'html':
            bytes_out = render_html(
                report_object,
                request.url_root.rstrip('/'),
                with_timeseries=True, body_only=False
            ).encode('utf-8')
        elif self.format_ == 'pdf':
            bytes_out = render_pdf(
                report_object,
                request.url_root.rstrip('/'),
            )

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

    def set_template_args(self):
        self.template_args = {
            'data_type': 'report',
            'uuid': self.metadata['report_id'],
            'metadata': render_template(
                self.metadata_template,
                data_type='Report',
                metadata_object=self.metadata
            ),
        }

    def get(self, uuid):
        try:
            self.metadata = reports.get_metadata(uuid)
        except DataRequestException as e:
            return render_template(self.template, data_type='report',
                                   uuid=uuid, errors=e.errors)
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
            reports.delete(uuid)
        except DataRequestException as e:
            return self.get(uuid, errors=e.errors)
        return redirect(url_for(
            f'data_dashboard.reports',
            messages={'delete': ['Success']}))


class RecomputeReportView(BaseView):
    """View to recompute a report. Requests a recompute and redirects the user
    to the reports listing view.
    """
    def get(self, uuid):
        try:
            reports.recompute(uuid)
        except DataRequestException as e:
            self.flash_api_errors(e.errors)
        else:
            flash('Report recomputed successfully.', 'message')
        return redirect(url_for('data_dashboard.report_view',
                                uuid=uuid))
