import pytest


VALID_FORECAST_JSON = {
    "extra_parameters": '{"instrument": "pyranometer"}',
    "name": "test forecast",
    "site_id": "123e4567-e89b-12d3-a456-426655440001",
    "variable": "ac_power",
    "interval_label": "beginning",
    "issue_time_of_day": "12:00",
    "lead_time_to_start": 60,
    "interval_length": 1,
    "run_length": 1440,
    "interval_value_type": "interval_mean",
    "axis": 'x',
    "constant_values": [5.0,20.0,50.0,80.0,95.0]
}


def copy_update(json, key, value):
    new_json = json.copy()
    new_json[key] = value
    return new_json


INVALID_VARIABLE = copy_update(VALID_FORECAST_JSON,
                               'variable', 'invalid')
INVALID_INTERVAL_LABEL = copy_update(VALID_FORECAST_JSON,
                                     'interval_label', 'invalid')
INVALID_ISSUE_TIME = copy_update(VALID_FORECAST_JSON,
                                 'issue_time_of_day', 'invalid')
INVALID_LEAD_TIME = copy_update(VALID_FORECAST_JSON,
                                'lead_time_to_start', 'invalid')
INVALID_INTERVAL_LENGTH = copy_update(VALID_FORECAST_JSON,
                                      'interval_length', 'invalid')
INVALID_RUN_LENGTH = copy_update(VALID_FORECAST_JSON,
                                 'run_length', 'invalid')
INVALID_VALUE_TYPE = copy_update(VALID_FORECAST_JSON,
                                 'interval_value_type', 'invalid')
INVALID_AXIS = copy_update(VALID_FORECAST_JSON,
                           'interval_value_type', 'invalid')
INVALID_CONSTANT_VALUES = copy_update(VALID_FORECAST_JSON,
                                     'interval_value_type',
                                     'invalid')


empty_json_response = '{"axis":["Missing data for required field."],"constant_values":["Missing data for required field."],"interval_label":["Missing data for required field."],"interval_length":["Missing data for required field."],"issue_time_of_day":["Missing data for required field."],"lead_time_to_start":["Missing data for required field."],"name":["Missing data for required field."],"run_length":["Missing data for required field."],"site_id":["Missing data for required field."],"variable":["Missing data for required field."]}' # NOQA


@pytest.mark.parametrize('payload,status_code', [
    (VALID_FORECAST_JSON, 201),
])
def test_forecast_post_success(api, payload, status_code):
    r = api.post('/forecasts/cdf/',
                 base_url='https://localhost',
                 json=payload)
    assert r.status_code == status_code
    assert 'Location' in r.headers


@pytest.mark.parametrize('payload,message', [
    (INVALID_VARIABLE, '{"variable":["Not a valid choice."]}'),
    (INVALID_INTERVAL_LABEL, '{"interval_label":["Not a valid choice."]}'),
    (INVALID_ISSUE_TIME, '{"issue_time_of_day":["Time not in %H:%M format."]}'), # NOQA
    (INVALID_LEAD_TIME, '{"lead_time_to_start":["Not a valid integer."]}'), # NOQA
    (INVALID_INTERVAL_LENGTH, '{"interval_length":["Not a valid integer."]}'), # NOQA
    (INVALID_RUN_LENGTH, '{"run_length":["Not a valid integer."]}'),
    (INVALID_VALUE_TYPE, '{"interval_value_type":["Not a valid choice."]}'),
    ({}, empty_json_response)
])
def test_cdf_forecast_group_post_bad_request(api, payload, message):
    r = api.post('/forecasts/cdf/',
                 base_url='https://localhost',
                 json=payload)
    assert r.status_code == 400
    assert r.get_data(as_text=True) == f'{{"errors":{message}}}\n'


def test_get_cdf_forecast_group_404(api, missing_id):
    r = api.get(f'/forecasts/cdf/{missing_id}',
                base_url='https://localhost')
    assert r.status_code == 404


def test_get_cdf_forecast_group_metadata(api, cdf_forecast_group_id):
    r = api.get(f'/forecasts/cdf/{cdf_forecast_group_id}',
                base_url='https://localhost')
    response = r.get_json()
    assert 'forecast_id' in response
    assert 'variable' in response
    assert 'name' in response
    assert 'site_id' in response


def test_get_forecast_metadata_404(api, missing_forecast_id):
    r = api.get(f'/forecasts/cdf{missing_forecast_id}/metadata',
                base_url='https://localhost')
    assert r.status_code == 404


VALID_VALUE_JSON = {
    'id': '123e4567-e89b-12d3-a456-426655440000',
    'values': [
        {'timestamp': "2019-01-22T17:54:36Z",
         'value': 1},
        {'timestamp': "2019-01-22T17:55:36Z",
         'value': '32.96'},
        {'timestamp': "2019-01-22T17:56:36Z",
         'value': 3}
    ]
}
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
VALID_CSV = "#I am a header comment, I am going to be ignored\ntimestamp,value\n2018-10-29T12:04:23Z,32.93\n2018-10-29T12:05:23Z,32.93\n2018-10-29T12:06:23Z,32.93\n2018-10-29T12:07:23Z,32.93\n" # NOQA
WRONG_DATE_FORMAT_CSV = "timestamp,value\nksdfjgn,32.93"
NON_NUMERICAL_VALUE_CSV = "timestamp,value\n2018-10-29T12:04:23Z,fgh" # NOQA


def test_post_forecast_values_valid_json(api, cdf_forecast_id):
    r = api.post(f'/forecasts/cdf/single/{cdf_forecast_id}/values',
                 base_url='https://localhost',
                 json=VALID_VALUE_JSON)
    assert r.status_code == 201


def test_post_json_storage_call(api, cdf_forecast_id, mocker):
    storage = mocker.patch('sfa_api.demo.store_cdf_forecast_values')
    storage.return_value = cdf_forecast_id
    api.post(f'/forecasts/cdf/single/{cdf_forecast_id}/values',
             base_url='https://localhost',
             json=VALID_VALUE_JSON)
    storage.assert_called()


def test_post_values_404(api, missing_id, mocker):
    storage = mocker.patch('sfa_api.demo.store_forecast_values')
    storage.return_value = None
    r = api.post(f'/forecasts/cdf/single/{missing_id}/values',
                 base_url='https://localhost',
                 json=VALID_VALUE_JSON)
    assert r.status_code == 404


@pytest.mark.parametrize('payload', [
    'taco',
    {},
    WRONG_DATE_FORMAT_VALUE_JSON,
    NON_NUMERICAL_VALUE_JSON,
])
def test_post_forecast_values_invalid_json(api, payload, cdf_forecast_id):
    r = api.post(f'/forecasts/cdf/single/{cdf_forecast_id}/values',
                 base_url='https://localhost',
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
                 base_url='https://localhost',
                 headers={'Content-Type': 'text/csv'},
                 data=payload)
    assert r.status_code == 400


def test_post_forecast_values_valid_csv(api, cdf_forecast_id):
    r = api.post(f'/forecasts/cdf/single/{cdf_forecast_id}/values',
                 base_url='https://localhost',
                 headers={'Content-Type': 'text/csv'},
                 data=VALID_CSV)
    assert r.status_code == 201


def test_get_forecast_values_404(api, missing_id):
    r = api.get(f'/forecasts/cdf/single/{missing_id}/values',
                base_url='https://localhost')
    assert r.status_code == 404


@pytest.mark.parametrize('start,end,mimetype', [
    ('bad-date', 'also_bad', 'application/json'),
    ('bad-date', 'also_bad', 'text/csv'),
])
def test_get_forecast_values_400(api, start, end, mimetype, cdf_forecast_id):
    r = api.get(f'/forecasts/cdf/single/{cdf_forecast_id}/values',
                base_url='https://localhost',
                headers={'Accept': mimetype},
                query_string={'start': start, 'end': end})
    assert r.status_code == 400
    assert r.mimetype == 'application/json'


@pytest.mark.parametrize('start,end,mimetype', [
    ('2019-01-30T12:00:00Z', '2019-01-30T12:00:00Z', 'application/json'),
    ('2019-01-30T12:00:00Z', '2019-01-30T12:00:00Z', 'text/csv'),
])
def test_get_cdf_forecast_values_200(api, start, end, mimetype, cdf_forecast_id):
    r = api.get(f'/forecasts/cdf/single/{cdf_forecast_id}/values',
                base_url='https://localhost',
                headers={'Accept': mimetype},
                query_string={'start': start, 'end': end})
    assert r.status_code == 200
    assert r.mimetype == mimetype
