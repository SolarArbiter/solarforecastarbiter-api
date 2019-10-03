from flask import abort
from functools import partial
import pytest


from sfa_api.conftest import (variables, interval_value_types, interval_labels,
                              BASE_URL, VALID_CDF_FORECAST_JSON, copy_update,
                              VALID_FX_VALUE_JSON, VALID_CDF_VALUE_CSV)


INVALID_NAME = copy_update(VALID_CDF_FORECAST_JSON, 'name', '@drain')
INVALID_VARIABLE = copy_update(VALID_CDF_FORECAST_JSON,
                               'variable', 'invalid')
INVALID_INTERVAL_LABEL = copy_update(VALID_CDF_FORECAST_JSON,
                                     'interval_label', 'invalid')
INVALID_ISSUE_TIME = copy_update(VALID_CDF_FORECAST_JSON,
                                 'issue_time_of_day', 'invalid')
INVALID_LEAD_TIME = copy_update(VALID_CDF_FORECAST_JSON,
                                'lead_time_to_start', 'invalid')
INVALID_INTERVAL_LENGTH = copy_update(VALID_CDF_FORECAST_JSON,
                                      'interval_length', 'invalid')
INVALID_RUN_LENGTH = copy_update(VALID_CDF_FORECAST_JSON,
                                 'run_length', 'invalid')
INVALID_VALUE_TYPE = copy_update(VALID_CDF_FORECAST_JSON,
                                 'interval_value_type', 'invalid')
INVALID_AXIS = copy_update(VALID_CDF_FORECAST_JSON,
                           'interval_value_type', 'invalid')
INVALID_CONSTANT_VALUES = copy_update(VALID_CDF_FORECAST_JSON,
                                      'interval_value_type',
                                      'invalid')


empty_json_response = '{"axis":["Missing data for required field."],"constant_values":["Missing data for required field."],"interval_label":["Missing data for required field."],"interval_length":["Missing data for required field."],"issue_time_of_day":["Missing data for required field."],"lead_time_to_start":["Missing data for required field."],"name":["Missing data for required field."],"run_length":["Missing data for required field."],"site_id":["Missing data for required field."],"variable":["Missing data for required field."]}' # NOQA


@pytest.mark.parametrize('payload,status_code', [
    (VALID_CDF_FORECAST_JSON, 201),
])
def test_cdf_forecast_group_post_success(api, payload, status_code):
    r = api.post('/forecasts/cdf/',
                 base_url=BASE_URL,
                 json=payload)
    assert r.status_code == status_code
    assert 'Location' in r.headers


@pytest.mark.parametrize('payload,message', [
    (INVALID_VARIABLE, f'{{"variable":["Must be one of: {variables}."]}}'),
    (INVALID_INTERVAL_LABEL, f'{{"interval_label":["Must be one of: {interval_labels}."]}}'), # NOQA
    (INVALID_ISSUE_TIME, '{"issue_time_of_day":["Time not in %H:%M format."]}'), # NOQA
    (INVALID_LEAD_TIME, '{"lead_time_to_start":["Not a valid integer."]}'), # NOQA
    (INVALID_INTERVAL_LENGTH, '{"interval_length":["Not a valid integer."]}'), # NOQA
    (INVALID_RUN_LENGTH, '{"run_length":["Not a valid integer."]}'),
    (INVALID_VALUE_TYPE, f'{{"interval_value_type":["Must be one of: {interval_value_types}."]}}'), # NOQA
    ({}, empty_json_response),
    (INVALID_NAME, '{"name":["Invalid characters in string."]}')
])
def test_cdf_forecast_group_post_bad_request(api, payload, message):
    r = api.post('/forecasts/cdf/',
                 base_url=BASE_URL,
                 json=payload)
    assert r.status_code == 400
    assert r.get_data(as_text=True) == f'{{"errors":{message}}}\n'


def test_get_cdf_forecast_group_404(api, missing_id):
    r = api.get(f'/forecasts/cdf/{missing_id}',
                base_url=BASE_URL)
    assert r.status_code == 404


def test_get_cdf_forecast_group_metadata(api, cdf_forecast_group_id):
    r = api.get(f'/forecasts/cdf/{cdf_forecast_group_id}',
                base_url=BASE_URL)
    response = r.get_json()
    assert 'forecast_id' in response
    assert 'variable' in response
    assert 'name' in response
    assert 'site_id' in response


def test_get_forecast_metadata_404(api, missing_id):
    r = api.get(f'/forecasts/cdf/{missing_id}/metadata',
                base_url=BASE_URL)
    assert r.status_code == 404


WRONG_DATE_FORMAT_VALUE_JSON = {
    'values': [
        {'timestamp': '20-2-3T11111F',
         'value': 3},
    ]
}
NON_NUMERICAL_VALUE_JSON = {
    'values': [
        {'timestamp': "2019-01-22T17:56:36Z",
         'value': 'four'},
    ]
}
WRONG_DATE_FORMAT_CSV = "timestamp,value\nksdfjgn,32.93"
NON_NUMERICAL_VALUE_CSV = "timestamp,value\n2018-10-29T12:04:23Z,fgh" # NOQA


def test_post_forecast_values_valid_json(api, cdf_forecast_id):
    r = api.post(f'/forecasts/cdf/single/{cdf_forecast_id}/values',
                 base_url=BASE_URL,
                 json=VALID_FX_VALUE_JSON)
    assert r.status_code == 201


@pytest.fixture()
def patched_store_values(mocker):
    new = mocker.MagicMock()
    mocker.patch('sfa_api.utils.storage_interface.store_cdf_forecast_values',
                 new=new)
    mocker.patch('sfa_api.demo.store_cdf_forecast_values',
                 new=new)
    return new


def test_post_json_storage_call(api, cdf_forecast_id, patched_store_values):
    patched_store_values.return_value = cdf_forecast_id
    api.post(f'/forecasts/cdf/single/{cdf_forecast_id}/values',
             base_url=BASE_URL,
             json=VALID_FX_VALUE_JSON)
    patched_store_values.assert_called()


def test_post_values_missing(api, missing_id):
    r = api.post(f'/forecasts/cdf/single/{missing_id}/values',
                 base_url=BASE_URL,
                 json=VALID_FX_VALUE_JSON)
    assert r.status_code == 404


def test_post_values_cant_read(api, forecast_id, mocker):
    new = mocker.MagicMock()
    new.side_effect = partial(abort, 404)
    mocker.patch('sfa_api.utils.storage_interface.read_cdf_forecast',
                 new=new)
    mocker.patch('sfa_api.demo.read_cdf_forecast',
                 new=new)
    res = api.post(f'/forecasts/cdf/single/{forecast_id}/values',
                   base_url=BASE_URL,
                   json=VALID_FX_VALUE_JSON)
    assert res.status_code == 404


@pytest.mark.parametrize('payload', [
    'taco',
    {},
    WRONG_DATE_FORMAT_VALUE_JSON,
    NON_NUMERICAL_VALUE_JSON,
])
def test_post_forecast_values_invalid_json(api, payload, cdf_forecast_id):
    r = api.post(f'/forecasts/cdf/single/{cdf_forecast_id}/values',
                 base_url=BASE_URL,
                 json=payload)
    assert r.status_code == 400


@pytest.mark.parametrize('payload', [
    'taco',
    '',
    WRONG_DATE_FORMAT_CSV,
    NON_NUMERICAL_VALUE_CSV,
])
def test_post_forecast_values_invalid_csv(api, payload, cdf_forecast_id):
    r = api.post(f'/forecasts/cdf/single/{cdf_forecast_id}/values',
                 base_url=BASE_URL,
                 headers={'Content-Type': 'text/csv'},
                 data=payload)
    assert r.status_code == 400


def test_post_forecast_values_valid_csv(api, cdf_forecast_id):
    r = api.post(f'/forecasts/cdf/single/{cdf_forecast_id}/values',
                 base_url=BASE_URL,
                 headers={'Content-Type': 'text/csv'},
                 data=VALID_CDF_VALUE_CSV)
    assert r.status_code == 201


def test_get_forecast_values_404(api, missing_id):
    r = api.get(f'/forecasts/cdf/single/{missing_id}/values',
                base_url=BASE_URL)
    assert r.status_code == 404


@pytest.mark.parametrize('start,end,mimetype', [
    ('bad-date', 'also_bad', 'application/json'),
    ('bad-date', 'also_bad', 'text/csv'),
])
def test_get_forecast_values_400(api, start, end, mimetype, cdf_forecast_id):
    r = api.get(f'/forecasts/cdf/single/{cdf_forecast_id}/values',
                base_url=BASE_URL,
                headers={'Accept': mimetype},
                query_string={'start': start, 'end': end})
    assert r.status_code == 400
    assert r.mimetype == 'application/json'


@pytest.mark.parametrize('start,end,mimetype', [
    ('2019-01-30T12:00:00Z', '2019-01-30T12:00:00Z', 'application/json'),
    ('2019-01-30T12:00:00Z', '2019-01-30T12:00:00Z', 'text/csv'),
])
def test_get_cdf_forecast_values_200(api, start, end, mimetype,
                                     cdf_forecast_id):
    r = api.get(f'/forecasts/cdf/single/{cdf_forecast_id}/values',
                base_url=BASE_URL,
                headers={'Accept': mimetype},
                query_string={'start': start, 'end': end})
    assert r.status_code == 200
    assert r.mimetype == mimetype


def test_post_and_get_values_json(api, cdf_forecast_id):
    r = api.post(f'/forecasts/cdf/single/{cdf_forecast_id}/values',
                 base_url=BASE_URL,
                 json=VALID_FX_VALUE_JSON)
    assert r.status_code == 201
    start = '2019-01-22T17:54:00+00:00'
    end = '2019-01-22T18:04:00+00:00'
    r = api.get(f'/forecasts/cdf/single/{cdf_forecast_id}/values',
                base_url=BASE_URL,
                headers={'Accept': 'application/json'},
                query_string={'start': start, 'end': end})
    posted_data = r.get_json()
    assert VALID_FX_VALUE_JSON['values'] == posted_data['values']


def test_post_and_get_values_csv(api, cdf_forecast_id):
    r = api.post(f'/forecasts/cdf/single/{cdf_forecast_id}/values',
                 base_url=BASE_URL,
                 headers={'Content-Type': 'text/csv'},
                 data=VALID_CDF_VALUE_CSV)
    assert r.status_code == 201
    start = '2019-01-22T12:05:00+00:00'
    end = '2019-01-22T12:20:00+00:00'
    r = api.get(f'/forecasts/cdf/single/{cdf_forecast_id}/values',
                base_url=BASE_URL,
                headers={'Accept': 'text/csv'},
                query_string={'start': start, 'end': end})
    posted_data = r.data
    assert VALID_CDF_VALUE_CSV == posted_data.decode('utf-8')
