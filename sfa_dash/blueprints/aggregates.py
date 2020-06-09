from collections import OrderedDict
from requests.exceptions import HTTPError

from flask import render_template, url_for, request, redirect
import pandas as pd

from sfa_dash.api_interface import observations, sites, aggregates
from sfa_dash.blueprints.base import BaseView
from sfa_dash.blueprints.util import (filter_form_fields,
                                      flatten_dict, download_timeseries)
from sfa_dash.errors import DataRequestException
from sfa_dash.form_utils.converters import AggregateConverter


class AggregatesView(BaseView):
    template = 'dash/aggregates.html'

    def get_breadcrumb_dict(self):
        breadcrumb_dict = OrderedDict()
        breadcrumb_dict['Aggregates'] = url_for('data_dashboard.aggregates')
        return breadcrumb_dict

    def template_args(self):
        aggregates_list = aggregates.list_metadata()
        return {
            "breadcrumb": self.breadcrumb_html(self.get_breadcrumb_dict()),
            "aggregates": aggregates_list,
        }


class AggregateForm(BaseView):
    """Form for creating a new aggregate.
    """
    template = 'forms/aggregate_form.html'

    def post(self):
        form_data = request.form
        api_payload = AggregateConverter.formdata_to_payload(form_data)
        try:
            aggregate_id = aggregates.post_metadata(api_payload)
        except DataRequestException as e:
            return render_template(
                self.template, errors=e.errors, form_data=form_data)
        return redirect(url_for(f'data_dashboard.aggregate_view',
                                uuid=aggregate_id))


class AggregateObservationAdditionForm(BaseView):
    """Form for adding new observations to an aggregate
    """
    template = 'forms/aggregate_observations_addition_form.html'
    metadata_template = 'data/metadata/aggregate_metadata.html'

    def get_breadcrumb_dict(self):
        breadcrumb_dict = OrderedDict()
        breadcrumb_dict['Aggregates'] = url_for('data_dashboard.aggregates')
        breadcrumb_dict[self.metadata['name']] = url_for(
            'data_dashboard.aggregate_view',
            uuid=self.metadata['aggregate_id'])
        breadcrumb_dict['Add Observations'] = ''
        return breadcrumb_dict

    def get_sites_and_observations(self):
        """Returns a dict of observations mapping uuid to an observation
        dict with nested site.

        Parameters
        ----------
        aggregate_metadata: dict
            The metadata of the aggregate used for filtering applicable
            observations.
        """
        sites_list = sites.list_metadata()
        observations_list = observations.list_metadata()

        # Remove observations with greater interval length
        observations_list = list(filter(
            lambda x: x['interval_length'] <= self.metadata['interval_length'],
            observations_list))

        # Remove observations with different variables
        observations_list = list(filter(
            lambda x: x['variable'] == self.metadata['variable'],
            observations_list))

        # Remove observations that exist in the aggregate and do not
        # have an effective_until set.
        effective_observations = [
            obs['observation_id']
            for obs in self.metadata['observations']
            if obs['effective_until'] is None]
        observations_list = list(filter(
            lambda x: x['observation_id'] not in effective_observations,
            observations_list))

        # Finally remove extra parameters, which may cause templating
        # issues.
        for obs in observations_list:
            del obs['extra_parameters']
        for site in sites_list:
            del site['extra_parameters']
        site_dict = {site['site_id']: site for site in sites_list}
        for obs in observations_list:
            obs['site'] = site_dict.get(obs['site_id'], None)
        return observations_list

    def template_args(self, **kwargs):
        observations = self.get_sites_and_observations()
        metadata = render_template(
            self.metadata_template, **self.metadata)
        aggregate = self.metadata.copy()
        template_arguments = {
            "observations": observations,
            "aggregate": aggregate,
            "metadata": metadata,
            "breadcrumb": self.breadcrumb_html(
                self.get_breadcrumb_dict()),
        }
        template_arguments.update(kwargs)
        return template_arguments

    def parse_observations(self, form_data):
        observation_ids = filter_form_fields('observation-', form_data)
        return observation_ids

    def aggregate_observation_formatter(self, form_data):
        formatted = {}
        # parse effective_from date, and zip it with all obs
        effective_from_date = form_data['effective-from-date']
        effective_from_time = form_data['effective-from-time']
        effective_from_dt = pd.Timestamp(
            f'{effective_from_date} {effective_from_time}', tz='utc')
        effective_from = effective_from_dt.isoformat()
        observation_ids = self.parse_observations(form_data)
        observations = zip(
            observation_ids,
            [effective_from] * len(observation_ids))
        observation_json = []
        for obs in observations:
            observation_json.append({
                'observation_id': obs[0],
                'effective_from': obs[1],
            })
        formatted['observations'] = observation_json
        return formatted

    def get(self, uuid, **kwargs):
        try:
            self.metadata = aggregates.get_metadata(uuid)
        except DataRequestException as e:
            return render_template(
                self.template, errors=e.errors)
        template_args = self.template_args(**kwargs)
        return render_template(self.template, **template_args)

    def post(self, uuid):
        form_data = request.form
        api_payload = self.aggregate_observation_formatter(form_data)
        try:
            aggregates.update(uuid, api_payload)
        except DataRequestException as e:
            if 'observations' in e.errors:
                # unpack list of errors related to observations
                errors = {
                    e: [msg] for e, msg in e.errors['observations'][0].items()}
            else:
                errors = e.errors
            return self.get(uuid, form_data=form_data,
                            errors=flatten_dict(errors))
        return redirect(url_for('data_dashboard.aggregate_view', uuid=uuid))


class AggregateObservationRemovalForm(BaseView):
    """Form for adding new observations to an aggregate
    """
    template = 'forms/aggregate_observations_removal_form.html'
    metadata_template = 'data/metadata/aggregate_metadata.html'

    def get_breadcrumb_dict(self):
        breadcrumb_dict = OrderedDict()
        breadcrumb_dict['Aggregates'] = url_for('data_dashboard.aggregates')
        breadcrumb_dict[self.metadata['name']] = url_for(
            'data_dashboard.aggregate_view',
            uuid=self.metadata['aggregate_id'])
        breadcrumb_dict['Remove Observation'] = ''
        return breadcrumb_dict

    def aggregate_observation_formatter(self, form_data, observation_id):
        formatted = {}
        effective_until_date = form_data['effective-until-date']
        effective_until_time = form_data['effective-until-time']
        effective_until_dt = pd.Timestamp(
            f'{effective_until_date} {effective_until_time}', tz='utc')
        effective_until = effective_until_dt.isoformat()
        observation_json = [{
            'observation_id': observation_id,
            'effective_until': effective_until,
        }]
        formatted['observations'] = observation_json
        return formatted

    def template_args(self, observation_id, **kwargs):
        metadata = render_template(
            self.metadata_template, **self.metadata)
        aggregate = self.metadata.copy()
        del aggregate['extra_parameters']
        template_arguments = {
            "aggregate": aggregate,
            "metadata": metadata,
            "breadcrumb": self.breadcrumb_html(
                self.get_breadcrumb_dict()),
        }
        try:
            observation = observations.get_metadata(observation_id)
        except DataRequestException:
            template_arguments['warnings'] = {
                'observation': ['Observation could not be read.']
            }
        else:
            template_arguments['observation'] = observation
        template_arguments.update(kwargs)
        return template_arguments

    def get(self, uuid, observation_id, **kwargs):
        try:
            self.metadata = aggregates.get_metadata(uuid)
        except DataRequestException as e:
            return render_template(
                self.template, errors=e.errors)
        template_args = self.template_args(observation_id, **kwargs)
        return render_template(self.template, **template_args)

    def post(self, uuid, observation_id):
        form_data = request.form
        api_payload = self.aggregate_observation_formatter(
            form_data, observation_id)
        try:
            aggregates.update(uuid, api_payload)
        except DataRequestException as e:
            if 'observations' in e.errors:
                # unpack list of errors related to observations
                errors = {
                    e: [msg] for e, msg in e.errors['observations'][0].items()}
            else:
                errors = e.errors
            return self.get(uuid, form_data=form_data,
                            errors=flatten_dict(errors))
        return redirect(url_for('data_dashboard.aggregate_view', uuid=uuid))


class AggregateView(BaseView):
    """Standard view of a single aggregate.
    """
    template = 'data/aggregate.html'
    metadata_template = 'data/metadata/aggregate_metadata.html'
    api_handle = aggregates
    plot_type = 'aggregate'
    human_label = 'Aggregate'
    subnav_format = subnav_format = {
        '{observations_url}': 'Observations',
        '{forecasts_url}': 'Forecasts',
        '{cdf_forecasts_url}': 'Probabilistic Forecasts',
    }

    def get_breadcrumb_dict(self):
        breadcrumb_dict = OrderedDict()
        breadcrumb_dict['Aggregates'] = url_for('data_dashboard.aggregates')
        breadcrumb_dict[self.metadata['name']] = url_for(
            'data_dashboard.aggregate_view',
            uuid=self.metadata['aggregate_id'])
        return breadcrumb_dict

    def set_template_args(self, start, end, **kwargs):
        self.temp_args.update({
            'metadata_block': render_template(
                self.metadata_template, **self.metadata),
            'observations': self.observation_list,
            'breadcrumb': self.breadcrumb_html(
                self.get_breadcrumb_dict()),
            'metadata': self.safe_metadata(),
            'subnav': self.format_subnav(
                observations_url=url_for(
                    'data_dashboard.aggregate_view',
                    uuid=self.metadata['aggregate_id']),
                forecasts_url=url_for(
                    'data_dashboard.forecasts',
                    aggregate_id=self.metadata['aggregate_id']),
                cdf_forecasts_url=url_for(
                    'data_dashboard.cdf_forecast_groups',
                    aggregate_id=self.metadata['aggregate_id'])),
            'period_start_date': start.strftime('%Y-%m-%d'),
            'period_start_time': start.strftime('%H:%M'),
            'period_end_date': end.strftime('%Y-%m-%d'),
            'period_end_time': end.strftime('%H:%M'),
        })
        self.temp_args.update(kwargs)

    def template_args(self):
        return self.temp_args

    def get(self, uuid, **kwargs):
        self.temp_args = {}
        try:
            self.metadata = self.api_handle.get_metadata(uuid)
        except DataRequestException as e:
            self.temp_args.update({'errors': e.errors})
        else:
            start, end = self.parse_start_end_from_querystring()
            self.observation_list = []
            observations_list = observations.list_metadata()
            observation_dict = {obs['observation_id']: obs
                                for obs in observations_list}
            for obs in self.metadata['observations']:
                curr_id = obs['observation_id']
                if curr_id in observation_dict:
                    observation = observation_dict[curr_id].copy()
                    observation.update(obs)
                    self.observation_list.append(observation)
            self.insert_plot(uuid, start, end)
            self.set_template_args(start, end, **kwargs)
        return render_template(self.template, **self.temp_args)

    def post(self, uuid):
        """Download endpoint.
        """
        return download_timeseries(self, uuid)


class DeleteAggregateView(BaseView):
    template = 'forms/deletion_form.html'
    metadata_template = 'data/metadata/aggregate_metadata.html'

    def template_args(self):
        return {
            'data_type': 'aggregate',
            'uuid': self.metadata['aggregate_id'],
            'metadata': render_template(
                self.metadata_template,
                data_type='Aggregate',
                **self.metadata
            ),
        }

    def get(self, uuid, **kwargs):
        try:
            self.metadata = aggregates.get_metadata(uuid)
        except DataRequestException as e:
            return render_template(self.template, errors=e.errors)
        return super().get(**kwargs)

    def post(self, uuid):
        confirmation_url = url_for(f'data_dashboard.delete_aggregate',
                                   _external=True,
                                   uuid=uuid)
        if request.headers['Referer'] != confirmation_url:
            # If the user was directed from anywhere other than
            # the confirmation page, redirect to confirm.
            return redirect(confirmation_url)
        try:
            delete_request = aggregates.delete(uuid)
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
            f'data_dashboard.aggregates',
            messages={'delete': ['Success']}))
