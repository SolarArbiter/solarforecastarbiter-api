"""Contains converter objects for changing form submissions to api schema
compliant dictionaries for posting and vice versa.

Each converter subclasses the FormCoverter base class to enforce a common
interface. The converter's `form` attribute is the path of the form template
the converter is expected to parse.
"""
from abc import ABC, abstractmethod
from functools import reduce
from math import isinf


from sfa_dash.form_utils import utils


class FormConverter(ABC):
    """Abstract base class to serve as an interface.
    """
    form = None

    @classmethod
    @abstractmethod
    def payload_to_formdata(cls, payload_dict):
        """Converts an API schema compliant dictionary to a dict used for
        prefilling form fields.

        Parameters
        ----------
        payload_dict: dict
            API json schema object parsed into a dictionary.

        Returns
        -------
        dict
            Dictionary that mirrors the format of Flask's request.form. Keys
            should be the name of the HTML input element.
        """
        pass

    @classmethod
    @abstractmethod
    def formdata_to_payload(cls, form_dict):
        """Converts a dictionary of form submission data into a API schema
        compliant dictionary to a dict used for

        Parameters
        ----------
        form_dict: dict
            Dictionary of form submission data. Usually just Flask's
            request.form dict.

        Returns
        -------
        payload_dict: dict
            API json schema object parsed into a dictionary.
        """
        pass


class SiteConverter(FormConverter):
    form = 'forms/site_form.html'
    tracking_keys = {
        'fixed': ['surface_tilt', 'surface_azimuth'],
        'single_axis': ['axis_azimuth', 'backtrack', 'axis_tilt',
                        'ground_coverage_ratio', 'max_rotation_angle'],
    }
    modeling_keys = ['ac_capacity', 'dc_capacity', 'ac_loss_factor',
                     'dc_loss_factor', 'temperature_coefficient',
                     'tracking_type']

    top_level_keys = ['name', 'elevation', 'latitude', 'longitude', 'timezone',
                      'extra_parameters']

    @classmethod
    def payload_to_formdata(cls, payload_dict):
        """Converts an api response to a form data dictionary for filling a
        form.

        Parameters
        ----------
        payload_dict: dict
            API json response as a python dict

        Returns
        -------
        dict
            dictionary of form data.
        """
        form_dict = {key: payload_dict[key]
                     for key in cls.top_level_keys
                     if key != 'extra_parameters'}
        # test if any 'modeling_parameter' items are not None
        is_plant = reduce(lambda a, b: a or b,
                          [x is not None for x in
                           payload_dict['modeling_parameters'].values()])
        if is_plant:
            form_dict['site_type'] = 'power-plant'
            modeling_params = payload_dict['modeling_parameters']
            for key in cls.modeling_keys:
                form_dict[key] = modeling_params[key]
            for key in cls.tracking_keys[modeling_params['tracking_type']]:
                form_dict[key] = modeling_params[key]
        else:
            form_dict['site_type'] = 'weather-station'
        return form_dict

    @classmethod
    def formdata_to_payload(cls, form_dict):
        """Formats the result of a site webform into an API payload.

        Parameters
        ----------
        form_dict:  dict
            The posted form data parsed into a dict.
        Returns
        -------
        dictionary
            Form data formatted to the API spec.
        """
        site_metadata = {key: form_dict[key]
                         for key in cls.top_level_keys
                         if form_dict.get(key, "") != ""}
        if form_dict['site_type'] == 'power-plant':
            modeling_params = {key: form_dict[key]
                               for key in cls.modeling_keys
                               if form_dict.get(key, "") != ""}
            tracking_type = form_dict['tracking_type']
            tracking_fields = {key: form_dict[key]
                               for key in cls.tracking_keys[tracking_type]}
            modeling_params.update(tracking_fields)
            site_metadata['modeling_parameters'] = modeling_params
        return site_metadata


class ObservationConverter(FormConverter):
    form = 'forms/observation_form.html'

    # keys that can be directly read from the form or api response
    direct_keys = ['name', 'variable', 'interval_value_type',
                   'uncertainty', 'extra_parameters', 'interval_label',
                   'site_id']

    @classmethod
    def payload_to_formdata(cls, payload_dict):
        """Converts an observation metadata dict into a form_data dict.

        Parameters
        ----------
        payload: dict
            API observation metadata json repsonse as a dict.

        Returns
        -------
        dict
            A dictionary for filling out form fields where keys are input name
            attributes.
        """
        form_dict = {key: payload_dict[key]
                     for key in cls.direct_keys
                     if key != 'extra_parameters'}
        form_dict.update(
            utils.parse_timedelta_from_api(
                payload_dict,
                'interval_length'
            )
        )
        return form_dict

    @classmethod
    def formdata_to_payload(cls, form_dict):
        """Formats the result of a observation webform into an API payload.

        Parameters
        ----------
        form_dict:  dict
            The posted form data parsed into a dict.
        Returns
        -------
        dictionary
            Form data formatted to the API spec.
        """
        obs_metadata = {}
        obs_metadata = {key: form_dict[key]
                        for key in cls.direct_keys
                        if form_dict.get(key, "") != ""}
        obs_metadata['interval_length'] = utils.parse_timedelta_from_form(
            form_dict,
            'interval_length')
        return obs_metadata


class ForecastConverter(FormConverter):
    form = 'forms/forecast_form.html'
    direct_keys = ['name', 'variable', 'interval_value_type',
                   'extra_parameters', 'interval_label']

    @classmethod
    def payload_to_formdata(cls, payload_dict):
        """Converts an forecast metadata dict into a form_data dict.

        Parameters
        ----------
        payload: dict
            API forecast metadata json repsonse as a dict.

        Returns
        -------
        dict
            A dictionary for filling out form fields where keys are input name
            attributes.
        """
        form_dict = {key: payload_dict[key]
                     for key in cls.direct_keys
                     if key != 'extra_parameters'}
        form_dict.update(utils.get_location_id(payload_dict))
        form_dict.update(
            utils.parse_hhmm_field_from_api(payload_dict, 'issue_time_of_day')
        )
        form_dict.update(
            utils.parse_timedelta_from_api(payload_dict, 'lead_time_to_start')
        )
        form_dict.update(
            utils.parse_timedelta_from_api(payload_dict, 'run_length')
        )
        form_dict.update(
            utils.parse_timedelta_from_api(payload_dict, 'interval_length')
        )
        return form_dict

    @classmethod
    def formdata_to_payload(cls, form_dict):
        """Formats the result of a forecast webform into an API payload.

        Parameters
        ----------
        form_dict:  dict
            The posted form data parsed into a dict.
        Returns
        -------
        dictionary
            Form data formatted to the API spec.
        """
        fx_metadata = {}
        fx_metadata = {key: form_dict[key]
                       for key in cls.direct_keys
                       if form_dict.get(key, '') != ''}
        fx_metadata.update(utils.get_location_id(form_dict))
        fx_metadata['issue_time_of_day'] = utils.parse_hhmm_field_from_form(
            form_dict,
            'issue_time_of_day')
        fx_metadata['lead_time_to_start'] = utils.parse_timedelta_from_form(
            form_dict,
            'lead_time_to_start')
        fx_metadata['run_length'] = utils.parse_timedelta_from_form(
            form_dict,
            'run_length')
        fx_metadata['interval_length'] = utils.parse_timedelta_from_form(
            form_dict,
            'interval_length')
        return fx_metadata


class CDFForecastConverter(FormConverter):
    form = 'forms/cdf_forecast_group_form.html'

    @classmethod
    def payload_to_formdata(cls, payload_dict):
        """Converts a CDF forecast metadata dict into a form_data dict.

        Parameters
        ----------
        payload: dict
            API CDFforecast metadata json repsonse as a dict.

        Returns
        -------
        dict
            A dictionary for filling out form fields where keys are input name
            attributes.
        """
        form_data = ForecastConverter.payload_to_formdata(payload_dict)
        constant_values = [str(cv['constant_value'])
                           for cv in payload_dict['constant_values']]
        form_data['constant_values'] = ','.join(constant_values)
        form_data['axis'] = payload_dict['axis']
        return form_data

    @classmethod
    def formdata_to_payload(cls, form_dict):
        """Formats the result of a cdf forecast webform into an API payload.

        Parameters
        ----------
        form_dict:  dict
            The posted form data parsed into a dict.

        Returns
        -------
        dictionary
            Form data formatted to the API spec.
        """
        fx_metadata = ForecastConverter.formdata_to_payload(form_dict)
        constant_values = [float(x)
                           for x in form_dict['constant_values'].split(',')]
        fx_metadata['constant_values'] = constant_values
        fx_metadata['axis'] = form_dict['axis']
        return fx_metadata


class AggregateConverter(FormConverter):
    form = 'forms/aggregate_form.html'
    direct_keys = ['name', 'description', 'interval_label', 'aggregate_type',
                   'variable', 'timezone', 'extra_parameters']

    @classmethod
    def payload_to_formdata(cls, payload_dict):
        """Converts an aggregate metadata dict into a form_data dict.

        Parameters
        ----------
        payload: dict
            API forecast metadata json repsonse as a dict.

        Returns
        -------
        dict
            A dictionary for filling out form fields where keys are input name
            attributes.

        Notes
        -----
            This function fills the aggregate ceation form and does not copy
            its corresponding observation.
        """
        form_dict = {key: payload_dict[key]
                     for key in cls.direct_keys
                     if key != 'extra_parameters'}
        form_dict.update(utils.parse_timedelta_from_api(
            payload_dict, 'interval_length'))
        return form_dict

    @classmethod
    def formdata_to_payload(cls, form_dict):
        """Converts an aggregate form submission dict to an api post payload.

        Parameters
        ----------
        form_dict: dict
            The posted form data parsed into a dict.

        Returns
        -------
        dict
            Form data formatted to API spec.
        """
        formatted = {key: form_dict[key]
                     for key in cls.direct_keys
                     if form_dict.get(key, '') != ''}
        formatted['interval_length'] = utils.parse_timedelta_from_form(
            form_dict, 'interval_length')
        return formatted


class ReportConverter(FormConverter):
    @classmethod
    def zip_object_pairs(cls, form_data):
        """Create a list of object pair dictionaries containing a
        forecast and either an observation or aggregate.
        """
        # Forecasts can be parsed directly
        fx = utils.filter_form_fields('forecast-id-', form_data)

        # observations and aggregates are passed in as truth-id-{index}
        # and truth-type-{index}, so we must match these with the
        # appropriately indexed forecast.
        truth_ids = utils.filter_form_fields('truth-id-', form_data)
        truth_types = utils.filter_form_fields('truth-type-', form_data)

        reference_forecasts = utils.filter_form_fields(
            'reference-forecast-', form_data)

        uncertainty_values = utils.filter_form_fields(
            'deadband-value-', form_data)
        forecast_types = utils.filter_form_fields(
            'forecast-type-', form_data)
        pairs = [{'forecast': f,
                  truth_types[i]: truth_ids[i],
                  'reference_forecast': reference_forecasts[i],
                  'uncertainty': uncertainty_values[i],
                  'forecast_type': forecast_types[i]}
                 for i, f in enumerate(fx)]
        return pairs

    @classmethod
    def parse_api_filters(cls, report_parameters):
        quality_flags = []
        for f in report_parameters.get('filters', []):
            if 'quality_flags' in f.keys():
                quality_flags = quality_flags + f['quality_flags']
        return {
            'quality_flags': quality_flags
        }

    @classmethod
    def extract_tods(cls, value):
        """Parses time of day values from a csv string"""
        return [v.strip() for v in value.split(',')]

    @classmethod
    def extract_datetimes(cls, value):
        return [v.strip() for v in value.split(',')]

    @classmethod
    def extract_many_costs(cls, value):
        costs = value.split(',')
        # if cost prevents parsing empty string in case of value = ''
        costs = [float(cost) for cost in costs if cost]
        return costs

    @classmethod
    def parse_form_constant_cost(cls, form_data, index=None):
        if index is not None:
            suffix = f'-{index}'
        else:
            suffix = ''
        cost = float(form_data[f'cost-value{suffix}'])
        aggregation = form_data[f'cost-aggregation{suffix}']
        net = form_data.get(f'cost-net{suffix}', False)
        return {
            'cost': cost,
            'aggregation': aggregation,
            'net': net,
        }

    @classmethod
    def parse_form_datetime_cost(cls, form_data, index=None):
        if index is not None:
            suffix = f'-{index}'
        else:
            suffix = ''
        datetimes = cls.extract_datetimes(form_data[f'cost-datetimes{suffix}'])
        costs = cls.extract_many_costs(form_data[f'cost-costs{suffix}'])
        aggregation = form_data[f'cost-aggregation{suffix}']
        fill = form_data[f'cost-fill{suffix}']
        net = form_data.get(f'cost-net{suffix}', False)
        timezone = form_data[f'cost-timezone{suffix}']
        payload = {
            'datetimes': datetimes,
            'cost': costs,
            'aggregation': aggregation,
            'fill': fill,
            'net': net,
        }
        if timezone is not None and timezone != 'null':
            payload.update({'timezone': timezone})
        return payload

    @classmethod
    def parse_form_tod_cost(cls, form_data, index=None):
        if index is not None:
            suffix = f'-{index}'
        else:
            suffix = ''
        times = cls.extract_tods(form_data[f'cost-times{suffix}'])
        costs = cls.extract_many_costs(form_data[f'cost-costs{suffix}'])
        aggregation = form_data[f'cost-aggregation{suffix}']
        fill = form_data[f'cost-fill{suffix}']
        net = form_data.get(f'cost-net{suffix}', False)
        timezone = form_data[f'cost-timezone{suffix}']
        payload = {
            'times': times,
            'cost': costs,
            'aggregation': aggregation,
            'fill': fill,
            'net': net,
        }
        if timezone is not None and timezone != 'null':
            payload.update({'timezone': timezone})
        return payload

    @classmethod
    def parse_form_errorband_cost(cls, form_data, index=None):
        # get number of error band indices from start_fields, these indices
        # may not be contiguous if the user removed/added more bands
        error_band_indices = [key.split('-')[-1]
                              for key in form_data.keys()
                              if key.startswith('cost-band-error-start-')]
        bands = []
        for i in error_band_indices:
            error_range_start = form_data[f'cost-band-error-start-{i}']
            error_range_end = form_data[f'cost-band-error-end-{i}']
            error_range = [error_range_start, error_range_end]
            cost_function = form_data[f'cost-band-cost-function-{i}']
            param_func = cls.get_form_cost_parser(cost_function)
            parameters = param_func(form_data, i)
            bands.append({
                'error_range': error_range,
                'cost_function': cost_function,
                'cost_function_parameters': parameters,
            })
        return {'bands': bands}

    @classmethod
    def get_form_cost_parser(cls, cost_type):
        if cost_type == 'timeofday':
            return cls.parse_form_tod_cost
        elif cost_type == 'datetime':
            return cls.parse_form_datetime_cost
        elif cost_type == 'constant':
            return cls.parse_form_constant_cost
        elif cost_type == 'errorband':
            return cls.parse_form_errorband_cost
        else:
            raise ValueError('Invalid cost_type')

    @classmethod
    def parse_form_costs(cls, form_data):
        """Parses costs from form data into an api-conforming dictionary.
        """
        cost_name = form_data.get('cost-primary-name')

        # Check for existence of cost name before trying to parse the rest,
        # as cost is an optional attribute.
        if cost_name is not None:
            cost_type = form_data['cost-primary-type']
            parameter_parser = cls.get_form_cost_parser(cost_type)
            cost_parameters = parameter_parser(form_data)
            return [{
                'name': cost_name,
                'type': cost_type,
                'parameters': cost_parameters,
            }]
        else:
            return []

    @classmethod
    def parse_form_filters(cls, form_data):
        """Create a list of dictionary filters. Currently just supports
        `quality_flags` which supports a list of quality flag names to exclude.
        """
        filters = []
        quality_flags = form_data.getlist('quality_flags')
        if quality_flags:
            filters.append({'quality_flags': quality_flags})
        return filters

    @classmethod
    def apply_crps(cls, params):
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

    @classmethod
    def parse_fill_method(cls, form_dict):
        fill_method = form_dict.get('forecast_fill_method', 'drop')
        if fill_method == 'provided':
            fill_method = form_dict['provided_forecast_fill_method']
        return fill_method

    @classmethod
    def stringify_infinite_error_ranges(cls, payload_costs):
        """Necessary for loading data into front end javascript. The js value
        Infinity is not valid JSON, and must be manually converted to the
        string "Infinity".
        """
        for cost in payload_costs:
            if cost['type'] == 'errorband':
                for band in cost['parameters']['bands']:
                    for i, bound in enumerate(band['error_range']):
                        if isinf(float(bound)):
                            if float(bound) > 0:
                                band['error_range'][i] = "Infinity"
                            else:
                                band['error_range'][i] = "-Infinity"
        return payload_costs

    @classmethod
    def formdata_to_payload(cls, form_dict):
        report_params = {}
        report_params['name'] = form_dict['name']

        costs = cls.parse_form_costs(form_dict)
        report_params['costs'] = costs
        report_params['object_pairs'] = cls.zip_object_pairs(form_dict)
        report_params['metrics'] = form_dict.getlist('metrics')
        report_params['categories'] = form_dict.getlist('categories')
        report_params['filters'] = cls.parse_form_filters(form_dict)
        report_params['start'] = form_dict['period-start']
        report_params['end'] = form_dict['period-end']
        report_params['forecast_fill_method'] = cls.parse_fill_method(
            form_dict)
        report_params = cls.apply_crps(report_params)
        report_dict = {'report_parameters': report_params}
        if len(costs) > 0:
            cost_name = costs[0]['name']
        else:
            cost_name = None
        for pair in report_params['object_pairs']:
            pair.update({'cost': cost_name})
        return report_dict

    @classmethod
    def payload_to_formdata(cls, payload_dict):
        form_params = {}
        report_parameters = payload_dict['report_parameters']
        form_params['name'] = report_parameters['name']
        form_params['categories'] = report_parameters.get('categories', [])
        form_params['metrics'] = report_parameters.get('metrics', [])
        form_params['period-start'] = report_parameters['start']
        form_params['period-end'] = report_parameters['end']
        form_params['costs'] = cls.stringify_infinite_error_ranges(
            report_parameters.get('costs', []))
        form_params['forecast_fill_method'] = report_parameters.get(
            'forecast_fill_method',
            'drop'
        )

        # Objects pairs are left in the api format for parsing in javascript
        # see sfa_dash/static/js/report-utilities.js fill_object_pairs function
        form_params['object_pairs'] = report_parameters['object_pairs']
        form_params.update(cls.parse_api_filters(report_parameters))
        return {'report_parameters': form_params}
