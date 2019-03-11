import pytest


VALID_OBS_JSON = {
    "extra_parameters": '{"instrument": "Ascension Technology Rotating Shadowband Pyranometer"}', # NOQA
    "name": "Ashland OR, ghi",
    "site_id": "123e4567-e89b-12d3-a456-426655440001",
    "variable": "ghi",
    "interval_label": "beginning"
}


def copy_update(json, key, value):
    new_json = json.copy()
    new_json[key] = value
    return new_json


INVALID_VARIABLE = copy_update(VALID_OBS_JSON,
                               'variable', 'invalid')
INVALID_INTERVAL_LABEL = copy_update(VALID_OBS_JSON,
                                     'interval_label', 'invalid')


empty_json_response = '{"interval_label":["Missing data for required field."],"name":["Missing data for required field."],"site_id":["Missing data for required field."],"variable":["Missing data for required field."]}' # NOQA


def test_observation_post_success(api):
    r = api.post('/observations/',
                 base_url='https://localhost',
                 json=VALID_OBS_JSON)
    assert r.status_code == 201
    assert 'Location' in r.headers


@pytest.mark.parametrize('payload,message', [
    (INVALID_VARIABLE, '{"variable":["Not a valid choice."]}'),
    (INVALID_INTERVAL_LABEL, '{"interval_label":["Not a valid choice."]}'),
    ({}, empty_json_response)
])
def test_observation_post_bad_request(api, payload, message):
    r = api.post('/observations/',
                 base_url='https://localhost',
                 json=payload)
    assert r.status_code == 400
    assert r.get_data(as_text=True) == f'{{"errors":{message}}}\n'


def test_get_observation_links(api, obs_id):
    r = api.get(f'/observations/{obs_id}',
                base_url='https://localhost')
    response = r.get_json()
    assert 'obs_id' in response
    assert '_links' in response


def test_get_observation_links_404(api, missing_obs_id):
    r = api.get(f'/observations/{missing_obs_id}',
                base_url='https://localhost')
    assert r.status_code == 404


def test_get_observation_metadata(api, obs_id):
    r = api.get(f'/observations/{obs_id}/metadata',
                base_url='https://localhost')
    response = r.get_json()
    assert 'obs_id' in response
    assert 'variable' in response
    assert 'name' in response
    assert 'site_id' in response


def test_get_observation_metadata_404(api, missing_obs_id):
    r = api.get(f'/observations/{missing_obs_id}/metadata',
                base_url='https://localhost')
    assert r.status_code == 404


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


def test_post_observation_values_valid_json(api, obs_id):
    r = api.post(f'/observations/{obs_id}/values',
                 base_url='https://localhost',
                 json=VALID_JSON)
    assert r.status_code == 201


def test_post_json_storage_call(api, obs_id, mocker):
    storage = mocker.patch('sfa_api.demo.store_observation_values')
    storage.return_value = obs_id
    api.post(f'/observations/{obs_id}/values',
             base_url='https://localhost',
             json=VALID_JSON)
    storage.assert_called()


@pytest.mark.parametrize('payload', [
    'taco',
    {},
    WRONG_DATE_FORMAT_JSON,
    NON_NUMERICAL_VALUE_JSON,
    NON_BINARY_FLAG_JSON
])
def test_post_observation_values_invalid_json(api, payload, obs_id):
    r = api.post(f'/observations/{obs_id}/values',
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
def test_post_observation_values_invalid_csv(api, payload, obs_id):
    r = api.post(f'/observations/{obs_id}/values',
                 base_url='https://localhost',
                 headers={'Content-Type': 'text/csv'},
                 data=payload)
    assert r.status_code == 400


def test_post_observation_values_valid_csv(api, obs_id):
    r = api.post(f'/observations/{obs_id}/values',
                 base_url='https://localhost',
                 headers={'Content-Type': 'text/csv'},
                 data=VALID_CSV)
    assert r.status_code == 201


def test_get_observation_values_404(api, missing_obs_id):
    r = api.get(f'/observations/{missing_obs_id}/values',
                base_url='https://localhost')
    assert r.status_code == 404


@pytest.mark.parametrize('start,end,mimetype', [
    ('bad-date', 'also_bad', 'application/json'),
    ('bad-date', 'also_bad', 'text/csv'),
])
def test_get_observation_values_400(api, start, end, mimetype, obs_id):
    r = api.get(f'/observations/{obs_id}/values',
                base_url='https://localhost',
                headers={'Accept': mimetype},
                query_string={'start': start, 'end': end})
    assert r.status_code == 400
    assert r.mimetype == 'application/json'


@pytest.mark.parametrize('start,end,mimetype', [
    ('2019-01-30T12:00:00Z', '2019-01-30T12:00:00Z', 'application/json'),
    ('2019-01-30T12:00:00Z', '2019-01-30T12:00:00Z', 'text/csv'),
])
def test_get_observation_values_200(api, start, end, mimetype, obs_id):
    r = api.get(f'/observations/{obs_id}/values',
                base_url='https://localhost',
                headers={'Accept': mimetype},
                query_string={'start': start, 'end': end})
    assert r.status_code == 200
    assert r.mimetype == mimetype
