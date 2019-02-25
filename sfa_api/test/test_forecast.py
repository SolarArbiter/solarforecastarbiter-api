import pytest


import json


VALID_FORECAST_JSON = {
    "extra_parameters": '{"instrument": "Ascension Technology Rotating Shadowband Pyranometer"}', # NOQA
    "name": "DA Power",
    "site_id": "123e4567-e89b-12d3-a456-426655440001",
    "variable": "ac_power",
    "interval_label": "beginning",
    "issue_time_of_day": "12:00",
    "lead_time_to_start": "1 hour",
    "interval_length": "1 minute",
    "run_length": "1 hour",
    "value_type": "interval_mean",
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
                                 'value_type', 'invalid')


empty_json_response = '{"interval_length":["Missing data for required field."],"issue_time_of_day":["Missing data for required field."],"lead_time_to_start":["Missing data for required field."],"name":["Missing data for required field."],"run_length":["Missing data for required field."],"site_id":["Missing data for required field."],"variable":["Missing data for required field."]}\n' # NOQA


@pytest.fixture()
def uuid():
    return '123e4567-e89b-12d3-a456-426655440000'


@pytest.mark.parametrize('payload,message,status_code', [
    (VALID_FORECAST_JSON, 'Forecast created.', 201),
    (INVALID_VARIABLE, '{"variable":["Not a valid choice."]}\n', 400),
    (INVALID_INTERVAL_LABEL, '{"interval_label":["Not a valid choice."]}\n',
     400),
    (INVALID_ISSUE_TIME, '{"issue_time_of_day":["Time not in HH:MM format."]}\n', 400), # NOQA
    (INVALID_LEAD_TIME, '{"lead_time_to_start":["Invalid time format."]}\n', 400), # NOQA
    (INVALID_INTERVAL_LENGTH, '{"interval_length":["Invalid time format."]}\n', 400), # NOQA
    (INVALID_RUN_LENGTH, '{"run_length":["Invalid time format."]}\n', 400),
    (INVALID_VALUE_TYPE, '{"value_type":["Not a valid choice."]}\n', 400),
    ({}, empty_json_response, 400)
])
def test_forecast_post(api, payload, message, status_code):
    r = api.post('/forecasts/',
                 base_url='https://localhost',
                 json=json.dumps(payload))
    assert r.status_code == status_code
    assert r.get_data(as_text=True) == message
    if status_code == 201:
        assert 'Location' in r.headers
    else:
        assert 'Location' not in r.headers


def test_get_forecast_links(api, uuid):
    r = api.get(f'/forecasts/{uuid}',
                base_url='https://localhost')
    response = r.get_json()
    assert 'forecast_id' in response
    assert '_links' in response


def test_get_forecast_metadata(api, uuid):
    r = api.get(f'/forecasts/{uuid}/metadata',
                base_url='https://localhost')
    response = r.get_json()
    assert 'forecast_id' in response
    assert 'variable' in response
    assert 'name' in response
    assert 'site_id' in response


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


# TODO: mock retrieval request to return a static forecast for testing
def test_post_forecast_values_valid_json(api, uuid):
    r = api.post(f'/forecasts/{uuid}/values',
                 base_url='https://localhost',
                 json=VALID_VALUE_JSON)
    assert r.status_code == 201


def test_post_json_storage_call(api, uuid, mocker):
    storage = mocker.patch('sfa_api.utils.storage.store_forecast_values')
    storage.return_value = uuid
    api.post(f'/forecasts/{uuid}/values',
             base_url='https://localhost',
             json=VALID_VALUE_JSON)
    storage.assert_called()


@pytest.mark.parametrize('payload', [
    'taco',
    {},
    WRONG_DATE_FORMAT_VALUE_JSON,
    NON_NUMERICAL_VALUE_JSON,
])
def test_post_forecast_values_invalid_json(api, payload, uuid):
    r = api.post(f'/forecasts/{uuid}/values',
                 base_url='https://localhost',
                 json=payload)
    assert r.status_code == 400


@pytest.mark.parametrize('payload', [
    'taco',
    '',
    WRONG_DATE_FORMAT_CSV,
    NON_NUMERICAL_VALUE_CSV,
])
def test_post_forecast_values_invalid_csv(api, payload, uuid):
    r = api.post(f'/forecasts/{uuid}/values',
                 base_url='https://localhost',
                 headers={'Content-Type': 'text/csv'},
                 data=payload)
    assert r.status_code == 400


def test_post_forecast_values_valid_csv(api, uuid):
    r = api.post(f'/forecasts/{uuid}/values',
                 base_url='https://localhost',
                 headers={'Content-Type': 'text/csv'},
                 data=VALID_CSV)
    assert r.status_code == 201


@pytest.mark.parametrize('start,end,code,mimetype', [
    ('bad-date', 'also_bad', 400, 'application/json'),
    ('2019-01-30T12:00:00Z', '2019-01-30T12:00:00Z', 200, 'application/json'),
    ('bad-date', 'also_bad', 400, 'text/csv'),
    ('2019-01-30T12:00:00Z', '2019-01-30T12:00:00Z', 200, 'text/csv'),
])
def test_get_forecast_values_json(api, start, end, code, mimetype, uuid):
    r = api.get(f'/forecasts/{uuid}/values',
                base_url='https://localhost',
                headers={'Accept': mimetype},
                query_string={'start': start, 'end': end})
    assert r.status_code == code
    if code == 400:
        assert r.mimetype == 'application/json'
    else:
        assert r.mimetype == mimetype
