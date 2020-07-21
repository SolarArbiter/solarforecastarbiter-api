from io import BytesIO
import json
import pandas as pd
import pytest


from sfa_api.conftest import (variables, interval_labels, BASE_URL,
                              VALID_OBS_VALUE_JSON, VALID_OBS_VALUE_CSV,
                              VALID_OBS_JSON, copy_update)


INVALID_NAME = copy_update(VALID_OBS_JSON, 'name', '#Nope')
INVALID_VARIABLE = copy_update(VALID_OBS_JSON,
                               'variable', 'invalid')
INVALID_INTERVAL_LABEL = copy_update(VALID_OBS_JSON,
                                     'interval_label', 'invalid')


empty_json_response = '{"interval_label":["Missing data for required field."],"interval_length":["Missing data for required field."],"interval_value_type":["Missing data for required field."],"name":["Missing data for required field."],"site_id":["Missing data for required field."],"uncertainty":["Missing data for required field."],"variable":["Missing data for required field."]}' # NOQA


def test_observation_post_success(api):
    r = api.post('/observations/',
                 base_url=BASE_URL,
                 json=VALID_OBS_JSON)
    assert r.status_code == 201
    assert 'Location' in r.headers


@pytest.mark.parametrize('payload,message', [
    (INVALID_VARIABLE, f'{{"variable":["Must be one of: {variables}."]}}'),
    (INVALID_INTERVAL_LABEL, f'{{"interval_label":["Must be one of: {interval_labels}."]}}'),  # NOQA
    ({}, empty_json_response),
    (INVALID_NAME, '{"name":["Invalid characters in string."]}')
])
def test_observation_post_bad_request(api, payload, message):
    r = api.post('/observations/',
                 base_url=BASE_URL,
                 json=payload)
    assert r.status_code == 400
    assert r.get_data(as_text=True) == f'{{"errors":{message}}}\n'


def test_observation_post_bad_site(api, missing_id):
    payload = copy_update(VALID_OBS_JSON, 'site_id', missing_id)
    r = api.post('/observations/',
                 base_url=BASE_URL,
                 json=payload)
    assert r.status_code == 404


def test_get_observation_links(api, observation_id):
    r = api.get(f'/observations/{observation_id}',
                base_url=BASE_URL)
    response = r.get_json()
    assert 'observation_id' in response
    assert '_links' in response


def test_get_observation_links_404(api, missing_id):
    r = api.get(f'/observations/{missing_id}',
                base_url=BASE_URL)
    assert r.status_code == 404


def test_get_observation_metadata(api, observation_id):
    r = api.get(f'/observations/{observation_id}/metadata',
                base_url=BASE_URL)
    response = r.get_json()
    assert 'observation_id' in response
    assert 'variable' in response
    assert 'name' in response
    assert 'site_id' in response
    assert response['created_at'].endswith('+00:00')
    assert response['modified_at'].endswith('+00:00')


def test_get_observation_metadata_404(api, missing_id):
    r = api.get(f'/observations/{missing_id}/metadata',
                base_url=BASE_URL)
    assert r.status_code == 404


ALMOST_EMPTY_JSON = {
    'values': [{}]
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
WRONG_INTERVAL_VALUE_JSON = {
    'values': [
        {'timestamp': '2019-01-22T17:56:00Z',
         'value': 3,
         'quality_flag': 0},
        {'timestamp': '2019-01-22T18:04:00Z',
         'value': 2,
         'quality_flag': 0},
        {'timestamp': '2019-01-22T18:07:00Z',
         'value': 1,
         'quality_flag': 0},
    ]
}
NON_BINARY_FLAG_JSON = {
    'values': [
        {'quality_flag': 'ham',
         'timestamp': "2019-01-22T17:56:36Z",
         'value': 3},
    ]
}
WRONG_DATE_FORMAT_CSV = "timestamp,value,quality_flag\nksdfjgn,32.93,0"
NON_NUMERICAL_VALUE_CSV = "timestamp,value,quality_flag\n2018-10-29T12:04:23Z,fgh,0" # NOQA
NON_BINARY_FLAG_CSV = "timestamp,value,quality_flag\n2018-10-29T12:04:23Z,32.93,B" # NOQA


def test_post_observation_values_valid_json(api, observation_id,
                                            mocked_queuing, mock_previous):
    mock_previous.return_value = pd.Timestamp('2019-01-22T17:49Z')
    res = api.post(f'/observations/{observation_id}/values',
                   base_url=BASE_URL,
                   json=VALID_OBS_VALUE_JSON)
    assert res.status_code == 201


def test_post_json_storage_call(api, observation_id, mocker,
                                mocked_queuing, mock_previous):
    storage = mocker.MagicMock()
    mocker.patch('sfa_api.utils.storage_interface.store_observation_values',
                 new=storage)
    storage.return_value = observation_id
    res = api.post(f'/observations/{observation_id}/values',
                   base_url=BASE_URL,
                   json=VALID_OBS_VALUE_JSON)
    assert res.status_code == 201
    storage.assert_called()


@pytest.mark.parametrize('payload', [
    'taco',
    {},
    ALMOST_EMPTY_JSON,
    WRONG_DATE_FORMAT_JSON,
    NON_NUMERICAL_VALUE_JSON,
    NON_BINARY_FLAG_JSON,
    WRONG_INTERVAL_VALUE_JSON
])
def test_post_observation_values_invalid_json(api, payload, observation_id,
                                              mock_previous):
    r = api.post(f'/observations/{observation_id}/values',
                 base_url=BASE_URL,
                 json=payload)
    assert r.status_code == 400


def test_post_observation_values_bad_previous(api, observation_id,
                                              mock_previous):
    mock_previous.return_value = pd.Timestamp('2019-01-22T17:50Z')
    res = api.post(f'/observations/{observation_id}/values',
                   base_url=BASE_URL,
                   json=VALID_OBS_VALUE_JSON)
    assert res.status_code == 400


@pytest.mark.parametrize('payload', [
    'taco',
    '',
    WRONG_DATE_FORMAT_CSV,
    NON_NUMERICAL_VALUE_CSV,
    NON_BINARY_FLAG_CSV
])
def test_post_observation_values_invalid_csv(api, payload, observation_id,
                                             mock_previous):
    r = api.post(f'/observations/{observation_id}/values',
                 base_url=BASE_URL,
                 headers={'Content-Type': 'text/csv'},
                 data=payload)
    assert r.status_code == 400


def test_post_observation_values_valid_csv(api, observation_id,
                                           mocked_queuing,
                                           mock_previous):
    r = api.post(f'/observations/{observation_id}/values',
                 base_url=BASE_URL,
                 headers={'Content-Type': 'text/csv'},
                 data=VALID_OBS_VALUE_CSV)
    assert r.status_code == 201


def test_get_observation_values_404(api, missing_id, startend):
    r = api.get(f'/observations/{missing_id}/values{startend}',
                base_url=BASE_URL)
    assert r.status_code == 404


@pytest.mark.parametrize('start,end,mimetype', [
    ('bad-date', 'also_bad', 'application/json'),
    ('bad-date', 'also_bad', 'text/csv'),
])
def test_get_observation_values_400(api, start, end, mimetype, observation_id):
    r = api.get(f'/observations/{observation_id}/values',
                base_url=BASE_URL,
                headers={'Accept': mimetype},
                query_string={'start': start, 'end': end})
    assert r.status_code == 400
    assert r.mimetype == 'application/json'


@pytest.mark.parametrize('start,end,mimetype', [
    ('2019-01-30T12:00:00Z', '2019-01-30T12:00:00Z', 'application/json'),
    ('2019-01-30T12:00:00Z', '2019-01-30T12:00:00Z', 'text/csv'),
    ('2019-01-30T12:00:00', '2019-01-30T12:00:00', 'application/json'),
    ('2019-01-30T12:00:00Z', '2019-01-30T05:00:00-07:00', 'text/csv'),

])
def test_get_observation_values_200(api, start, end, mimetype, observation_id):
    r = api.get(f'/observations/{observation_id}/values',
                base_url=BASE_URL,
                headers={'Accept': mimetype},
                query_string={'start': start, 'end': end})
    assert r.status_code == 200
    assert r.mimetype == mimetype


def test_post_and_get_values_json(api, observation_id, mocked_queuing,
                                  mock_previous):
    res = api.post(f'/observations/{observation_id}/values',
                   base_url=BASE_URL,
                   json=VALID_OBS_VALUE_JSON)
    assert res.status_code == 201
    start = '2019-01-22T17:54:00+00:00'
    end = '2019-01-22T18:04:00+00:00'
    res = api.get(f'/observations/{observation_id}/values',
                  base_url=BASE_URL,
                  headers={'Accept': 'application/json'},
                  query_string={'start': start, 'end': end})
    posted_data = res.get_json()
    assert VALID_OBS_VALUE_JSON['values'] == posted_data['values']


def test_post_and_get_values_csv(api, observation_id, mocked_queuing,
                                 mock_previous):
    r = api.post(f'/observations/{observation_id}/values',
                 base_url=BASE_URL,
                 headers={'Content-Type': 'text/csv'},
                 data=VALID_OBS_VALUE_CSV)
    assert r.status_code == 201
    start = '2019-01-22T12:05:00+00:00'
    end = '2019-01-22T12:20:00+00:00'
    r = api.get(f'/observations/{observation_id}/values',
                base_url=BASE_URL,
                headers={'Accept': 'text/csv'},
                query_string={'start': start, 'end': end})
    posted_data = r.data
    assert VALID_OBS_VALUE_CSV == posted_data.decode('utf-8')


@pytest.fixture()
def dummy_file():
    def req_file(filename, contents, content_type):
        return {filename: (contents, filename, content_type)}
    return req_file


@pytest.mark.parametrize('filename,str_content,content_type,start,end', [
    ('data.csv', VALID_OBS_VALUE_CSV, 'text/csv',
     '2019-01-22T12:05:00+00:00', '2019-01-22T12:20:00+00:00'),
    ('data.csv', VALID_OBS_VALUE_CSV, 'application/vnd.ms-excel',
     '2019-01-22T12:05:00+00:00', '2019-01-22T12:20:00+00:00'),
    ('data.json', json.dumps(VALID_OBS_VALUE_JSON), 'application/json',
     '2019-01-22T17:54:00+00:00', "2019-01-22T18:04:00+00:00"),
])
def test_posting_files(
        api, dummy_file, filename, str_content, content_type,
        observation_id, mocked_queuing, start, end,
        mock_previous):
    content = BytesIO(bytes(str_content, 'utf-8'))
    the_file = dummy_file(filename, content, content_type)
    file_post = api.post(
        f'/observations/{observation_id}/values',
        base_url=BASE_URL,
        content_type='multipart/form-data',
        data=the_file)
    assert file_post.status_code == 201
    if content_type == 'application/json':
        accept = 'application/json'
    else:
        accept = 'text/csv'
    r = api.get(f'/observations/{observation_id}/values',
                base_url=BASE_URL,
                headers={'Accept': accept},
                query_string={'start': start, 'end': end})
    posted_data = r.data
    decoded_response = posted_data.decode('utf-8')

    if content_type == 'application/json':
        expected = VALID_OBS_VALUE_JSON['values']
        assert expected == json.loads(decoded_response)['values']
    else:
        expected = VALID_OBS_VALUE_CSV
        assert expected == decoded_response


def test_post_file_invalid_utf(api, dummy_file, observation_id):
    content = BytesIO(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1\x00\x00\x00\x00\x00')
    the_file = dummy_file('broken.xls', content, 'application/vnd.ms-excel')
    file_post = api.post(
        f'/observations/{observation_id}/values',
        base_url=BASE_URL,
        content_type='multipart/form-data',
        data=the_file)
    assert file_post.status_code == 400
    expected = '{"errors":{"error":["File could not be decoded as UTF-8."]}}\n'
    assert file_post.get_data(as_text=True) == expected


def test_post_multiple_files(api, dummy_file, observation_id):
    content1 = BytesIO(bytes('valid_string'.encode('utf-8')))
    content2 = BytesIO(bytes('{"a":"B"}'.encode('utf-8')))

    file1 = dummy_file('file1.csv', content1, 'text/csv')
    file2 = dummy_file('file2.json', content2, 'application/json')
    file1.update(file2)
    file_post = api.post(
        f'/observations/{observation_id}/values',
        base_url=BASE_URL,
        content_type='multipart/form-data',
        data=file1)
    assert file_post.status_code == 400
    expected = '{"errors":{"error":["Multiple files found. Please upload one file at a time."]}}\n' # NOQA
    assert file_post.get_data(as_text=True) == expected


def test_post_file_no_file(api, observation_id):
    file_post = api.post(
        f'/observations/{observation_id}/values',
        base_url=BASE_URL,
        content_type='multipart/form-data',
        data={})
    assert file_post.status_code == 400
    expected = '{"errors":{"error":["Missing file in request body."]}}\n'
    assert file_post.get_data(as_text=True) == expected


def test_post_file_invalid_json(api, observation_id):
    incorrect_file_payload = {
        'data.json': (BytesIO(b'invalid'), 'data.json', 'application/json')
    }
    file_post = api.post(
        f'/observations/{observation_id}/values',
        base_url=BASE_URL,
        content_type='multipart/form-data',
        data=incorrect_file_payload)
    assert file_post.status_code == 400
    expected = '{"errors":{"error":["Malformed JSON."]}}\n'
    assert file_post.get_data(as_text=True) == expected


def test_post_file_invalid_mimetype(api, observation_id):
    incorrect_file_payload = {
        'data.csv': (BytesIO(b'invalid'), 'data.xls', 'application/videogame')
    }
    file_post = api.post(
        f'/observations/{observation_id}/values',
        base_url=BASE_URL,
        content_type='multipart/form-data',
        data=incorrect_file_payload)
    assert file_post.status_code == 400
    expected = '{"errors":{"error":["Unsupported Content-Type or MIME type."]}}\n' # noqa
    assert file_post.get_data(as_text=True) == expected


def test_get_latest_observation_values_200(api, observation_id, ghi_obs_vals):
    r = api.get(f'/observations/{observation_id}/values/latest',
                base_url=BASE_URL)
    assert r.status_code == 200
    assert r.mimetype == 'application/json'
    data = r.get_json()
    assert data['observation_id'] == observation_id
    assert len(data['values']) == 1
    assert data['values'][0]['timestamp'] == ghi_obs_vals.index[-1].strftime(
        '%Y-%m-%dT%H:%M:%SZ')


def test_get_latest_observation_values_404_fxid(api, forecast_id):
    r = api.get(f'/observations/{forecast_id}/values/latest',
                base_url=BASE_URL)
    assert r.status_code == 404


def test_get_latest_observation_values_404(api, missing_id):
    r = api.get(f'/observations/{missing_id}/values/latest',
                base_url=BASE_URL)
    assert r.status_code == 404


def test_get_latest_observation_values_new(api, new_observation):
    obs_id = new_observation()
    r = api.get(f'/observations/{obs_id}/values/latest',
                base_url=BASE_URL)
    assert r.status_code == 200
    data = r.get_json()
    assert len(data['values']) == 0


def test_get_observation_timerange_200(api, observation_id, ghi_obs_vals):
    r = api.get(f'/observations/{observation_id}/values/timerange',
                base_url=BASE_URL)
    assert r.status_code == 200
    assert r.mimetype == 'application/json'
    data = r.get_json()
    assert data['observation_id'] == observation_id
    assert data['max_timestamp'] == ghi_obs_vals.index[-1].isoformat()
    assert data['min_timestamp'] == ghi_obs_vals.index[0].isoformat()


def test_get_observation_timerange_404_fxid(api, forecast_id):
    r = api.get(f'/observations/{forecast_id}/values/timerange',
                base_url=BASE_URL)
    assert r.status_code == 404


def test_get_observation_timerange_404(api, missing_id):
    r = api.get(f'/observations/{missing_id}/values/timerange',
                base_url=BASE_URL)
    assert r.status_code == 404


def test_get_observation_timerange_new(api, new_observation):
    obs_id = new_observation()
    r = api.get(f'/observations/{obs_id}/values/timerange',
                base_url=BASE_URL)
    assert r.status_code == 200
    data = r.get_json()
    assert data['min_timestamp'] is None
    assert data['max_timestamp'] is None


EVENT_LABEL = copy_update(VALID_OBS_JSON, 'interval_label', 'event')
EVENT_VARIABLE = copy_update(VALID_OBS_JSON, 'variable', 'event')


@pytest.mark.parametrize('payload,message', [
    (EVENT_VARIABLE, ('{"events":["Both interval_label and variable must be '
                      'set to \'event\'."]}')),
    (EVENT_LABEL, ('{"events":["Both interval_label and variable must be '
                   'set to \'event\'."]}')),
])
def test_observation_post_bad_event(api, payload, message):
    r = api.post('/observations/',
                 base_url=BASE_URL,
                 json=payload)
    assert r.status_code == 400
    assert r.get_data(as_text=True) == f'{{"errors":{message}}}\n'


def test_get_observation_gaps_200(api, observation_id, addmayvalues):
    r = api.get(f'/observations/{observation_id}/values/gaps',
                query_string={'start': '2019-04-01T00:00Z',
                              'end': '2019-06-01T00:00Z'},
                base_url=BASE_URL)
    assert r.status_code == 200
    assert r.mimetype == 'application/json'
    data = r.get_json()
    assert '_links' in data
    assert data['observation_id'] == observation_id
    assert data['gaps'] == [
        {'timestamp': '2019-04-17T06:55:00+00:00',
         'next_timestamp': '2019-05-01T00:00:00+00:00'},
        {'timestamp': '2019-05-01T00:00:00+00:00',
         'next_timestamp': '2019-05-02T00:00:00+00:00'}
    ]


def test_get_observation_gaps_none(api, observation_id, addmayvalues):
    r = api.get(f'/observations/{observation_id}/values/gaps',
                query_string={'start': '2019-07-01T00:00Z',
                              'end': '2019-10-01T00:00Z'},
                base_url=BASE_URL)
    assert r.status_code == 200
    assert r.mimetype == 'application/json'
    data = r.get_json()
    assert '_links' in data
    assert data['observation_id'] == observation_id
    assert data['gaps'] == []


def test_get_observation_gaps_404(api, forecast_id, addmayvalues):
    r = api.get(f'/observations/{forecast_id}/values/gaps',
                query_string={'start': '2019-04-01T00:00Z',
                              'end': '2019-06-01T00:00Z'},
                base_url=BASE_URL)
    assert r.status_code == 404


def test_get_observation_gaps_400(api, observation_id, addmayvalues):
    r = api.get(f'/observations/{observation_id}/values/gaps',
                base_url=BASE_URL)
    assert r.status_code == 400


def test_get_observation_unflagged_200(api, observation_id, addmayvalues):
    r = api.get(f'/observations/{observation_id}/values/unflagged',
                query_string={'start': '2019-04-01T00:00Z',
                              'end': '2019-04-30T00:00Z',
                              'flag': 1},
                base_url=BASE_URL)
    assert r.status_code == 200
    assert r.mimetype == 'application/json'
    data = r.get_json()
    assert '_links' in data
    assert data['observation_id'] == observation_id
    assert data['dates'] == ['2019-04-14', '2019-04-15',
                             '2019-04-16', '2019-04-17']


def test_get_observation_unflagged_200_compound_flag(
        api, observation_id, addmayvalues):
    r = api.get(f'/observations/{observation_id}/values/unflagged',
                query_string={'start': '2019-05-01T00:00Z',
                              'end': '2019-06-01T00:00Z',
                              'flag': 5},
                base_url=BASE_URL)
    assert r.status_code == 200
    assert r.mimetype == 'application/json'
    data = r.get_json()
    assert '_links' in data
    assert data['observation_id'] == observation_id
    # 5/2 is flagged with 5, 5/1 only 1
    assert data['dates'] == ['2019-05-01']


def test_get_observation_unflagged_200_flag_limit(
        api, observation_id, addmayvalues):
    r = api.get(f'/observations/{observation_id}/values/unflagged',
                query_string={'start': '2019-05-01T00:00Z',
                              'end': '2019-06-01T00:00Z',
                              'flag': 65535},
                base_url=BASE_URL)
    assert r.status_code == 200
    assert r.mimetype == 'application/json'
    data = r.get_json()
    assert '_links' in data
    assert data['observation_id'] == observation_id
    assert data['dates'] == ['2019-05-01', '2019-05-02']


def test_get_observation_unflagged_200_tz(
        api, observation_id, addmayvalues):
    r = api.get(f'/observations/{observation_id}/values/unflagged',
                query_string={'start': '2019-05-01T00:00Z',
                              'end': '2019-06-01T00:00Z',
                              'flag': 6,
                              'timezone': 'Etc/GMT+5'},
                base_url=BASE_URL)
    assert r.status_code == 200
    assert r.mimetype == 'application/json'
    data = r.get_json()
    assert '_links' in data
    assert data['observation_id'] == observation_id
    # 5/2 is flagged with 5, 5/1 only 1, tz shifts
    assert data['dates'] == ['2019-04-30', '2019-05-01']


def test_get_observation_unflagged_none(api, observation_id, addmayvalues):
    r = api.get(f'/observations/{observation_id}/values/unflagged',
                query_string={'start': '2019-07-01T00:00Z',
                              'end': '2019-10-01T00:00Z',
                              'flag': 1},
                base_url=BASE_URL)
    assert r.status_code == 200
    assert r.mimetype == 'application/json'
    data = r.get_json()
    assert '_links' in data
    assert data['observation_id'] == observation_id
    assert data['dates'] == []


@pytest.mark.parametrize('qsup,err', [
    ({'flag': 'no'}, 'flag'),
    ({'flag': 2**17}, 'flag'),
    ({'flag': -1}, 'flag'),
    ({}, 'flag'),
    ({'flag': 1, 'timezone': 'bad'}, 'timezone'),
    ({'timezone': 'bad'}, 'timezone'),
    ({'timezone': 'bad'}, 'flag'),
    ({'start': ''}, 'start'),
    ({'end': ''}, 'end')
])
def test_get_observation_unflagged_400(api, observation_id, addmayvalues,
                                       qsup, err):
    query_string = {'start': '2019-04-01T00:00Z',
                    'end': '2019-06-01T00:00Z'}
    query_string.update(qsup)
    res = api.get(f'/observations/{observation_id}/values/unflagged',
                  query_string=query_string,
                  base_url=BASE_URL)
    assert res.status_code == 400
    assert err in res.get_data(as_text=True).lower()


def test_get_observation_unflagged_404_fxid(api, forecast_id, addmayvalues):
    r = api.get(f'/observations/{forecast_id}/values/unflagged',
                query_string={'start': '2019-04-01T00:00Z',
                              'end': '2019-06-01T00:00Z',
                              'flag': 1},
                base_url=BASE_URL)
    assert r.status_code == 404


@pytest.mark.parametrize('content_type,payload', [
    ('application/json', '{"values": ['+"1"*17*1024*1024+']}'),
    ('text/csv', 'timestamp,value,quality_flag\n'+"1"*17*1024*1024),
])
def test_post_observation_too_large(
        api, observation_id, content_type, payload):
    req = api.post(
            f'/observations/{observation_id}/values',
            environ_base={'Content-Type': content_type,
                          'Content-Length': 17*1024*1024},
            data=payload, base_url=BASE_URL)
    assert req.status_code == 413


@pytest.mark.parametrize('variable', [
    'ac_power',
    'dc_power',
    'poa_global',
    'availability',
])
def test_observation_post_power_at_weather_site(api, variable):
    obs_json = copy_update(VALID_OBS_JSON, 'variable', variable)
    r = api.post('/observations/',
                 base_url=BASE_URL,
                 json=obs_json)
    assert r.status_code == 400
