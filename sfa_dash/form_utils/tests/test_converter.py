from copy import deepcopy


import pandas as pd
import pytest
from werkzeug.datastructures import ImmutableMultiDict


from sfa_dash.form_utils import converters


def without_extra(the_dict):
    new_dict = deepcopy(the_dict)
    new_dict.pop('extra_parameters', None)
    new_dict.pop('_links', None)
    new_dict.pop('forecast_id', None)
    new_dict.pop('observation_id', None)
    new_dict.pop('provider', None)
    new_dict.pop('created_at', None)
    new_dict.pop('modified_at', None)
    return new_dict


def test_site_converter_roundtrip_no_modeling(site):
    expected = without_extra(site)
    expected.pop('site_id')
    expected.pop('modeling_parameters')
    form_data = converters.SiteConverter.payload_to_formdata(site)
    api_data = converters.SiteConverter.formdata_to_payload(form_data)
    assert api_data == expected


def test_site_converter_roundtrip(site_with_modeling_params):
    expected = without_extra(site_with_modeling_params)
    expected.pop('site_id')

    none_keys = [k for k, v in expected['modeling_parameters'].items()
                 if v is None]
    for key in none_keys:
        expected['modeling_parameters'].pop(key)
    form_data = converters.SiteConverter.payload_to_formdata(
        site_with_modeling_params)
    api_data = converters.SiteConverter.formdata_to_payload(form_data)
    assert api_data == expected


def test_site_converter_payload_to_formdata(site):
    form_data = converters.SiteConverter.payload_to_formdata(site)
    assert form_data['name'] == 'Weather Station'
    assert form_data['elevation'] == 595.0
    assert form_data['latitude'] == 42.19
    assert form_data['longitude'] == -122.7
    assert form_data['timezone'] == 'Etc/GMT+8'
    assert form_data['site_type'] == 'weather-station'


def test_site_converter_payload_to_formdata_fixed(site_with_modeling_params):
    form_data = converters.SiteConverter.payload_to_formdata(
        site_with_modeling_params)
    assert form_data['name'] == 'Power Plant 1'
    assert form_data['elevation'] == 786.0
    assert form_data['latitude'] == 43.73403
    assert form_data['longitude'] == -96.62328
    assert form_data['timezone'] == 'Etc/GMT+6'
    assert form_data['site_type'] == 'power-plant'
    assert form_data['ac_capacity'] == 0.015
    assert form_data['ac_loss_factor'] == 0.0
    assert form_data['dc_capacity'] == 0.015
    assert form_data['dc_loss_factor'] == 0.0
    assert form_data['surface_azimuth'] == 180.0
    assert form_data['surface_tilt'] == 45.0
    assert form_data['temperature_coefficient'] == -0.2
    assert form_data['tracking_type'] == 'fixed'


def test_site_converter_payload_to_formdata_single_axis(
        site_with_modeling_params):
    single_axis = deepcopy(site_with_modeling_params)
    single_axis['modeling_parameters'].pop('surface_tilt')
    single_axis['modeling_parameters'].pop('surface_azimuth')
    single_axis['modeling_parameters']['tracking_type'] = 'single_axis'
    single_axis['modeling_parameters']['axis_tilt'] = 45.0
    single_axis['modeling_parameters']['axis_azimuth'] = 180.0
    single_axis['modeling_parameters']['max_rotation_angle'] = 180.0
    single_axis['modeling_parameters']['ground_coverage_ratio'] = 0.7
    form_data = converters.SiteConverter.payload_to_formdata(
        single_axis)
    assert form_data['name'] == 'Power Plant 1'
    assert form_data['elevation'] == 786.0
    assert form_data['latitude'] == 43.73403
    assert form_data['longitude'] == -96.62328
    assert form_data['timezone'] == 'Etc/GMT+6'
    assert form_data['site_type'] == 'power-plant'
    assert form_data['ac_capacity'] == 0.015
    assert form_data['ac_loss_factor'] == 0.0
    assert form_data['dc_capacity'] == 0.015
    assert form_data['dc_loss_factor'] == 0.0
    assert form_data['axis_azimuth'] == 180.0
    assert form_data['axis_tilt'] == 45.0
    assert form_data['temperature_coefficient'] == -0.2
    assert form_data['tracking_type'] == 'single_axis'
    assert form_data['ground_coverage_ratio'] == 0.7
    assert form_data['max_rotation_angle'] == 180.0


def test_site_converter_formdata_to_payload(site_with_modeling_params):
    form_data = {
        'name': 'Power Plant 1',
        'elevation': 786.0,
        'latitude': 43.73403,
        'longitude': -96.62328,
        'timezone': 'Etc/GMT+6',
        'site_type': 'power-plant',
        'ac_capacity': 0.015,
        'ac_loss_factor': 0.0,
        'dc_capacity': 0.015,
        'dc_loss_factor': 0.0,
        'surface_azimuth': 180.0,
        'surface_tilt': 45.0,
        'temperature_coefficient': -0.2,
        'tracking_type': 'fixed',
    }
    api_payload = converters.SiteConverter.formdata_to_payload(form_data)
    assert api_payload == {
        'name': 'Power Plant 1',
        'elevation': 786.0,
        'latitude': 43.73403,
        'longitude': -96.62328,
        'timezone': 'Etc/GMT+6',
        'modeling_parameters': {
            'ac_capacity': 0.015,
            'ac_loss_factor': 0.0,
            'dc_capacity': 0.015,
            'dc_loss_factor': 0.0,
            'surface_azimuth': 180.0,
            'surface_tilt': 45.0,
            'temperature_coefficient': -0.2,
            'tracking_type': 'fixed',
        },
    }


def test_observation_converter_roundtrip(observation):
    form_data = converters.ObservationConverter.payload_to_formdata(
        observation)
    api_data = converters.ObservationConverter.formdata_to_payload(form_data)
    assert api_data == without_extra(observation)


def test_observation_converter_payload_to_formdata(observation):
    form_data = converters.ObservationConverter.payload_to_formdata(
        observation)
    assert form_data == {
        'name': 'GHI Instrument 1',
        'variable': 'ghi',
        'interval_label': 'beginning',
        'interval_value_type': 'interval_mean',
        'interval_length_number': 5,
        'interval_length_units': 'minutes',
        'uncertainty': 0.1,
        'site_id': observation['site_id'],
    }


def test_observation_converter_formdata_to_payload(observation):
    form_data = {
        'name': 'GHI Instrument 1',
        'variable': 'ghi',
        'interval_label': 'beginning',
        'interval_value_type': 'interval_mean',
        'interval_length_number': 5,
        'interval_length_units': 'minutes',
        'uncertainty': 0.1,
        'site_id': observation['site_id']
    }
    api_data = converters.ObservationConverter.formdata_to_payload(
        form_data)
    assert api_data == {
        'name': 'GHI Instrument 1',
        'variable': 'ghi',
        'interval_label': 'beginning',
        'interval_value_type': 'interval_mean',
        'interval_length': 5,
        'uncertainty': 0.1,
        'site_id': observation['site_id']
    }


def test_forecast_converter_roundtrip(forecast):
    form_data = converters.ForecastConverter.payload_to_formdata(forecast)
    api_data = converters.ForecastConverter.formdata_to_payload(form_data)
    assert api_data == without_extra(forecast)


def test_forecast_converter_payload_to_formdata(forecast):
    form_data = converters.ForecastConverter.payload_to_formdata(forecast)
    assert form_data == {
        'interval_label': 'beginning',
        'interval_length_number': 5,
        'interval_length_units': 'minutes',
        'interval_value_type': 'interval_mean',
        'issue_time_of_day_hours': 6,
        'issue_time_of_day_minutes': 0,
        'lead_time_to_start_number': 1.0,
        'lead_time_to_start_units': 'hours',
        'name': 'DA GHI',
        'run_length_number': 1.0,
        'run_length_units': 'days',
        'variable': 'ghi',
        'aggregate_id': None,
        'site_id': forecast['site_id'],
    }


def test_forecast_converter_formdata_to_payload(forecast):
    form_data = {
        'interval_label': 'beginning',
        'interval_length_number': 5,
        'interval_length_units': 'minutes',
        'interval_value_type': 'interval_mean',
        'issue_time_of_day_hours': 6,
        'issue_time_of_day_minutes': 0,
        'lead_time_to_start_number': 1.0,
        'lead_time_to_start_units': 'hours',
        'name': 'DA GHI',
        'run_length_number': 1.0,
        'run_length_units': 'days',
        'variable': 'ghi',
        'aggregate_id': None,
        'site_id': forecast['site_id'],
    }
    api_data = converters.ForecastConverter.formdata_to_payload(form_data)
    assert api_data == {
        'interval_label': 'beginning',
        'interval_length': 5,
        'interval_value_type': 'interval_mean',
        'issue_time_of_day': '06:00',
        'lead_time_to_start': 60,
        'name': 'DA GHI',
        'run_length': 1440,
        'variable': 'ghi',
        'aggregate_id': None,
        'site_id': forecast['site_id'],
    }


def test_cdfforecast_converter_roundtrip(cdf_forecast):
    form_data = converters.CDFForecastConverter.payload_to_formdata(
        cdf_forecast)
    api_data = converters.CDFForecastConverter.formdata_to_payload(form_data)
    extra_removed = without_extra(cdf_forecast)
    constant_values = [cv['constant_value']
                       for cv in cdf_forecast['constant_values']]
    extra_removed['constant_values'] = constant_values
    assert api_data == extra_removed


def test_cdfforecast_converter_payload_to_formdata(cdf_forecast):
    form_data = converters.CDFForecastConverter.payload_to_formdata(
        cdf_forecast)
    assert form_data == {
        'aggregate_id': None,
        'axis': 'y',
        'constant_values': "5.0,20.0,50.0,80.0,95.0",
        'interval_label': 'beginning',
        'interval_length_number': 5,
        'interval_length_units': 'minutes',
        'interval_value_type': 'interval_mean',
        'issue_time_of_day_hours': 6,
        'issue_time_of_day_minutes': 0,
        'lead_time_to_start_number': 1.0,
        'lead_time_to_start_units': 'hours',
        'name': 'DA GHI',
        'run_length_number': 1.0,
        'run_length_units': 'days',
        'site_id': '123e4567-e89b-12d3-a456-426655440001',
        'variable': 'ghi'
    }


def test_cdfforecast_converter_formdata_to_payload(forecast):
    form_data = {
        'aggregate_id': None,
        'axis': 'y',
        'constant_values': "5.0,20.0,50.0,80.0,95.0",
        'interval_label': 'beginning',
        'interval_length_number': 5,
        'interval_length_units': 'minutes',
        'interval_value_type': 'interval_mean',
        'issue_time_of_day_hours': 6,
        'issue_time_of_day_minutes': 0,
        'lead_time_to_start_number': 1.0,
        'lead_time_to_start_units': 'hours',
        'name': 'DA GHI',
        'run_length_number': 1.0,
        'run_length_units': 'days',
        'site_id': '123e4567-e89b-12d3-a456-426655440001',
        'variable': 'ghi'
    }
    api_data = converters.CDFForecastConverter.formdata_to_payload(form_data)
    assert api_data == {
        'aggregate_id': None,
        'axis': 'y',
        'constant_values': [5.0, 20.0, 50.0, 80.0, 95.0],
        'interval_label': 'beginning',
        'interval_length': 5,
        'interval_value_type': 'interval_mean',
        'issue_time_of_day': "06:00",
        'lead_time_to_start': 60,
        'name': 'DA GHI',
        'run_length': 1440,
        'site_id': '123e4567-e89b-12d3-a456-426655440001',
        'variable': 'ghi'
    }


def test_aggregate_converter_payload_to_formdata(aggregate):
    form_data = converters.AggregateConverter.payload_to_formdata(aggregate)
    assert form_data == {
        'aggregate_type': 'mean',
        'description': 'ghi agg',
        'interval_label': 'ending',
        'interval_length_number': 1,
        'interval_length_units': 'hours',
        'name': 'Test Aggregate ghi',
        'timezone': 'America/Denver',
        'variable': 'ghi'}


def test_aggregate_converter_formdata_to_payload():
    form_data = {
        'aggregate_type': 'mean',
        'description': 'ghi agg',
        'extra_parameters': 'extra',
        'interval_label': 'ending',
        'interval_length_number': 60,
        'interval_length_units': 'minutes',
        'name': 'Test Aggregate ghi',
        'timezone': 'America/Denver',
        'variable': 'ghi'}
    api_data = converters.AggregateConverter.formdata_to_payload(form_data)
    assert api_data == {
        'aggregate_type': 'mean',
        'description': 'ghi agg',
        'extra_parameters': 'extra',
        'interval_label': 'ending',
        'interval_length': 60,
        'name': 'Test Aggregate ghi',
        'timezone': 'America/Denver',
        'variable': 'ghi'}


def test_report_converter_formdata_to_payload(report):
    form_data = ImmutableMultiDict([
        ('name', 'NREL MIDC OASIS GHI Forecast Analysis'),
        ('period-start', '2019-04-01T07:00Z'),
        ('period-end', '2019-06-01T06:59Z'),
        ('forecast-id-0', '11c20780-76ae-4b11-bef1-7a75bdc784e3'),
        ('truth-id-0', '123e4567-e89b-12d3-a456-426655440000'),
        ('truth-type-0', 'observation'),
        ('reference-forecast-0', 'null'),
        ('deadband-value-0', 'null'),
        ('forecast-type-0', 'forecast'),
        ('observation-aggregate-radio', 'observation'),
        ('site-select', '123e4567-e89b-12d3-a456-426655440001'),
        ('forecast-select', '11c20780-76ae-4b11-bef1-7a75bdc784e3'),
        ('observation-select', '123e4567-e89b-12d3-a456-426655440000'),
        ('deadband-select', 'null'),
        ('deadband-value', ''),
        ('metrics', 'mae'),
        ('metrics', 'rmse'),
        ('categories', 'total'),
        ('categories', 'date'),
        ('quality_flags', 'USER FLAGGED'),
        ('forecast_fill_method', 'forward'),
        ('_csrf_token', '8a0771df3643d252cbafe4838263dbf7097f4982')]
    )
    api_payload = converters.ReportConverter.formdata_to_payload(form_data)
    expected = report['report_parameters']
    params = api_payload['report_parameters']
    assert params['categories'] == expected['categories']
    assert params['metrics'] == expected['metrics']
    assert params['filters'] == expected['filters']
    assert pd.Timestamp(params['start']) == pd.Timestamp(expected['start'])
    assert pd.Timestamp(params['end']) == pd.Timestamp(expected['end'])
    assert params['object_pairs'] == [{'cost': None, **pair}
                                      for pair in expected['object_pairs']]
    assert params['name'] == expected['name']
    assert params['forecast_fill_method'] == 'forward'


def test_report_converter_payload_to_formdata(report):
    form_data = converters.ReportConverter.payload_to_formdata(report)
    form_data = form_data['report_parameters']
    assert form_data['name'] == 'NREL MIDC OASIS GHI Forecast Analysis'
    assert form_data['period-start'] == '2019-04-01T07:00:00+00:00'
    assert form_data['period-end'] == '2019-06-01T06:59:00+00:00'
    assert form_data['metrics'] == ['mae', 'rmse']
    assert form_data['categories'] == ['total', 'date']
    assert form_data['quality_flags'] == ['USER FLAGGED']
    assert form_data['object_pairs'] == [{
        'forecast': '11c20780-76ae-4b11-bef1-7a75bdc784e3',
        'observation': '123e4567-e89b-12d3-a456-426655440000',
        'reference_forecast': None,
        'uncertainty': None,
        'forecast_type': 'forecast',
    }]
    assert form_data['costs'] == [{
        'name': 'example cost',
        'type': 'constant',
        'parameters': {
            'cost': 1.1,
            'aggregation': 'sum',
            'net': False,
        }
    }]


def test_report_converter_payload_to_formdata_defaults(report):
    report = deepcopy(report)
    report['report_parameters'].pop('metrics')
    report['report_parameters'].pop('categories')
    report['report_parameters'].pop('filters')
    form_data = converters.ReportConverter.payload_to_formdata(report)
    form_data = form_data['report_parameters']
    assert form_data['metrics'] == []
    assert form_data['categories'] == []
    assert form_data['quality_flags'] == []


def test_report_converter_formdata_to_payload_costs(report):
    form_data = ImmutableMultiDict([
        ('name', 'NREL MIDC OASIS GHI Forecast Analysis'),
        ('period-start', '2019-04-01T07:00Z'),
        ('period-end', '2019-06-01T06:59Z'),
        ('forecast-id-0', '11c20780-76ae-4b11-bef1-7a75bdc784e3'),
        ('truth-id-0', '123e4567-e89b-12d3-a456-426655440000'),
        ('truth-type-0', 'observation'),
        ('reference-forecast-0', 'null'),
        ('deadband-value-0', 'null'),
        ('forecast-type-0', 'forecast'),
        ('observation-aggregate-radio', 'observation'),
        ('site-select', '123e4567-e89b-12d3-a456-426655440001'),
        ('forecast-select', '11c20780-76ae-4b11-bef1-7a75bdc784e3'),
        ('observation-select', '123e4567-e89b-12d3-a456-426655440000'),
        ('deadband-select', 'null'),
        ('deadband-value', ''),
        ('metrics', 'mae'),
        ('metrics', 'rmse'),
        ('categories', 'total'),
        ('categories', 'date'),
        ('quality_flags', 'USER FLAGGED'),
        ('cost-primary-type', 'timeofday'),
        ('cost-primary-name', 'this is a cost'),
        ('cost-times', '06:00,18:00'),
        ('cost-net', False),
        ('cost-costs', '1.5,3.0'),
        ('cost-aggregation', 'sum'),
        ('cost-fill', 'forward'),
        ('cost-timezone', 'null'),
        ('_csrf_token', '8a0771df3643d252cbafe4838263dbf7097f4982')]
    )
    api_payload = converters.ReportConverter.formdata_to_payload(form_data)
    params = api_payload['report_parameters']
    assert params['costs'] == [{
        'name': 'this is a cost',
        'type': 'timeofday',
        'parameters': {
            'times': ['06:00', '18:00'],
            'cost': [1.5, 3.0],
            'aggregation': 'sum',
            'fill': 'forward',
            'net': False,
        }
    }]
    for object_pair in params['object_pairs']:
        assert object_pair['cost'] == 'this is a cost'


def test_report_converter_parse_form_errorband_costs():
    form_data = ImmutableMultiDict([
        ('cost-band-error-start-0', 1),
        ('cost-band-error-end-0', 5),
        ('cost-band-cost-function-0', 'constant'),
        ('cost-value-0', '1.0'),
        ('cost-aggregation-0', 'sum'),
        ('cost-net-0', True),
        ('cost-band-error-start-1', 5),
        ('cost-band-error-end-1', 10),
        ('cost-band-cost-function-1', 'timeofday'),
        ('cost-times-1', '00:00,12:00'),
        ('cost-costs-1', '1.5,2.5'),
        ('cost-aggregation-1', 'mean'),
        ('cost-fill-1', 'forward'),
        ('cost-net-1', False),
        ('cost-timezone-1', 'America/Denver'),
        ('cost-band-error-start-2', -5),
        ('cost-band-error-end-2', 1),
        ('cost-band-cost-function-2', 'datetime'),
        ('cost-datetimes-2', '2020-01-01T00:00Z,2020-01-01T12:00Z'),
        ('cost-costs-2', '1.0,3.0'),
        ('cost-aggregation-2', 'sum'),
        ('cost-net-2', True),
        ('cost-fill-2', 'forward'),
        ('cost-timezone-2', 'GMT'),
    ])
    params = converters.ReportConverter.parse_form_errorband_cost(form_data)
    bands = params['bands']
    assert bands[0] == {
        'error_range': [1, 5],
        'cost_function': 'constant',
        'cost_function_parameters': {
            'cost': 1.0,
            'aggregation': 'sum',
            'net': True,
        }
    }
    assert bands[1] == {
        'error_range': [5, 10],
        'cost_function': 'timeofday',
        'cost_function_parameters': {
            'times': ['00:00', '12:00'],
            'cost': [1.5, 2.5],
            'aggregation': 'mean',
            'fill': 'forward',
            'net': False,
            'timezone': 'America/Denver',
        }
    }
    assert bands[2] == {
        'error_range': [-5, 1],
        'cost_function': 'datetime',
        'cost_function_parameters': {
            'datetimes': ['2020-01-01T00:00Z', '2020-01-01T12:00Z'],
            'cost': [1.0, 3.0],
            'aggregation': 'sum',
            'fill': 'forward',
            'net': True,
            'timezone': 'GMT',
        }
    }


@pytest.mark.parametrize('form_vals,expected', [
    ([('forecast_fill_method', 'forward')], 'forward'),
    ([('forecast_fill_method', 'drop')], 'drop'),
    ([('forecast_fill_method', 'provided'),
      ('provided_forecast_fill_method', '5.0')], '5.0'),
])
def test_report_converter_parse_form_fill_method(form_vals, expected):
    form_data = ImmutableMultiDict(form_vals)
    parsed = converters.ReportConverter.parse_fill_method(form_data)
    assert parsed == expected
