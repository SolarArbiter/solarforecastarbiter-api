import pandas as pd
import pytest


import json
import sfa_api


VALID_JSON = {
    "extra_parameters": '{"instrument": "Ascension Technology Rotating Shadowband Pyranometer"}', # NOQA
    "name": "Ashland OR, ghi",
    "site_id": "123e4567-e89b-12d3-a456-426655440001",
    "variable": "ghi",
    "interval_label": "start"
}
INVALID_VARIABLE = VALID_JSON.copy()
INVALID_VARIABLE['variable'] = 'banana'
INVALID_INTERVAL_LABEL = VALID_JSON.copy()
INVALID_INTERVAL_LABEL['interval_label'] = 'up'


empty_json_response = '{"name":["Missing data for required field."],"site_id":["Missing data for required field."],"variable":["Missing data for required field."]}\n' # NOQA


@pytest.fixture()
def uuid():
    return '123e4567-e89b-12d3-a456-426655440000'


@pytest.mark.parametrize('payload,message,status_code', [
    (VALID_JSON, 'Observation created.', 201),
    (INVALID_VARIABLE, '{"variable":["Not a valid choice."]}\n', 400),
    (INVALID_INTERVAL_LABEL, '{"interval_label":["Not a valid choice."]}\n',
     400),
    ({}, empty_json_response, 400)
])
def test_observation_post(api, payload, message, status_code):
    r = api.post('/observations/',
                 base_url='https://localhost',
                 json=json.dumps(payload))
    assert r.status_code == status_code
    assert r.get_data(as_text=True) == message
    if status_code == 201:
        assert 'Location' in r.headers
    else:
        assert 'Location' not in r.headers


def test_get_observation_links(api, uuid):
    r = api.get(f'/observations/{uuid}',
                base_url='https://localhost')
    response = r.get_json()
    assert 'obs_id' in response
    assert '_links' in response


def test_get_observation_metadata(api, uuid):
    r = api.get(f'/observations/{uuid}/metadata',
                base_url='https://localhost')
    response = r.get_json()
    assert 'obs_id' in response
    assert 'variable' in response
    assert 'name' in response
    assert 'site_id' in response


VALID_JSON = {
    'id': '123e4567-e89b-12d3-a456-426655440000',
    'values': [
        {'quality_flag': 0,
         'timestamp': "2019-01-22T17:54:36Z",
         'value': 1},
        {'quality_flag': 0,
         'timestamp': "2019-01-22T17:55:36Z",
         'value': '32.96'},
        {'quality_flag': 0,
         'timestamp': "2019-01-22T17:56:36Z",
         'value': 3}
    ]
}
WRONG_DATE_FORMAT_JSON = {
    'values': [
        {'quality_flag': 0,
         'timestamp': '20-2-3T11111F',
         'value': 3},
    ]
}
NON_NUMERICAL_VALUE_JSON = {
    'values': [
        {'quality_flag': 0,
         'timestamp': "2019-01-22T17:56:36Z",
         'value': 'four'},
    ]
}
NON_BINARY_FLAG_JSON = {
    'values': [
        {'quality_flag': 'ham',
         'timestamp': "2019-01-22T17:56:36Z",
         'value': 3},
    ]
}
VALID_CSV = "#I am a header comment, I am going to be ignored\ntimestamp,value,quality_flag\n2018-10-29T12:04:23Z,32.93,0\n2018-10-29T12:05:23Z,32.93,0\n2018-10-29T12:06:23Z,32.93,0\n2018-10-29T12:07:23Z,32.93,0\n" # NOQA
WRONG_DATE_FORMAT_CSV = "timestamp,value,quality_flag\nksdfjgn,32.93,0"
NON_NUMERICAL_VALUE_CSV = "timestamp,value,quality_flag\n2018-10-29T12:04:23Z,fgh,0" # NOQA
NON_BINARY_FLAG_CSV = "timestamp,value,quality_flag\n2018-10-29T12:04:23Z,32.93,B" # NOQA


# TODO: mock retrieval request to return a static observation for testing
def test_post_observation_values_valid_json(api, uuid):
    r = api.post(f'/observations/{uuid}/values',
                 base_url='https://localhost',
                 json=VALID_JSON)
    assert r.status_code == 201


def test_post_json_storage_call(api, mocker):
    mocker.patch('sfa_api.utils.storage.store_observation_values')
    data = pd.DataFrame(VALID_JSON['values'])
    data['timestamp'] = pd.to_datetime(data['timestamp'], utc=True)
    data['value'] = pd.to_numeric(data['value'], downcast="float")
    api.get('/observations/7365da38-2ee5-46ed-bd48-c84c4cc5a6c8/values',
            base_url='https://localhost',
            json=VALID_JSON)
    sfa_api.utils.storage.store_observation_values.asser_called_with(
        obs_id='7365da38-2ee5-46ed-bd48-c84c4cc5a6c8',
        observation_df=data)


@pytest.mark.parametrize('payload', [
    'taco',
    {},
    WRONG_DATE_FORMAT_JSON,
    NON_NUMERICAL_VALUE_JSON,
    NON_BINARY_FLAG_JSON
])
def test_post_observation_values_invalid_json(api, payload, uuid):
    r = api.post(f'/observations/{uuid}/values',
                 base_url='https://localhost',
                 json=payload)
    assert r.status_code == 400


@pytest.mark.parametrize('payload', [
    'taco',
    '',
    WRONG_DATE_FORMAT_CSV,
    NON_NUMERICAL_VALUE_CSV,
    NON_BINARY_FLAG_CSV
])
def test_post_observation_values_invalid_csv(api, payload, uuid):
    r = api.post(f'/observations/{uuid}/values',
                 base_url='https://localhost',
                 headers={'Content-Type': 'text/csv'},
                 data=payload)
    assert r.status_code == 400


def test_post_observation_values_valid_csv(api, uuid):
    r = api.post(f'/observations/{uuid}/values',
                 base_url='https://localhost',
                 headers={'Content-Type': 'text/csv'},
                 data=VALID_CSV)
    assert r.status_code == 201


@pytest.mark.parametrize('start,end,code', [
    ('bad-date', 'also_bad', 400),
    ('2019-01-30T12:00:00Z', '2019-01-30T12:00:00Z', 200),
])
def test_get_observation_values(api, start, end, code, uuid):
    r = api.get(f'/observations/{uuid}/values',
                base_url='https://localhost',
                query_string={'start': start, 'end': end})
    assert r.status_code == code
