from io import BytesIO
import json


import pandas as pd
import pytest


from sfa_api.conftest import (variables, interval_value_types, interval_labels,
                              BASE_URL, VALID_FORECAST_JSON, copy_update,
                              VALID_FX_VALUE_JSON, VALID_FX_VALUE_CSV,
                              VALID_FORECAST_AGG_JSON, UNSORTED_FX_VALUE_JSON,
                              ADJ_FX_VALUE_JSON, demo_forecasts,
                              _get_large_test_payload)
from sfa_api.utils.storage_interface import POWER_VARIABLES


INVALID_NAME = copy_update(VALID_FORECAST_JSON, 'name', 'Bad semicolon;')
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
INVALID_BOTH_IDS = copy_update(
    VALID_FORECAST_JSON, 'aggregate_id',
    '458ffc27-df0b-11e9-b622-62adb5fd6af0')
INVALID_NO_IDS = VALID_FORECAST_JSON.copy()
del INVALID_NO_IDS['site_id']


empty_json_response = '{"interval_label":["Missing data for required field."],"interval_length":["Missing data for required field."],"interval_value_type":["Missing data for required field."],"issue_time_of_day":["Missing data for required field."],"lead_time_to_start":["Missing data for required field."],"name":["Missing data for required field."],"run_length":["Missing data for required field."],"variable":["Missing data for required field."]}' # NOQA


@pytest.fixture(params=['missing', 'obs', 'fx'])
def bad_id(missing_id, observation_id, inaccessible_forecast_id, request):
    if request.param == 'missing':
        return missing_id
    elif request.param == 'fx':
        return inaccessible_forecast_id
    else:
        return observation_id


@pytest.mark.parametrize('payload,status_code', [
    (VALID_FORECAST_JSON, 201),
    (VALID_FORECAST_AGG_JSON, 201),
    (copy_update(VALID_FORECAST_JSON, 'aggregate_id', None), 201),
    (copy_update(VALID_FORECAST_AGG_JSON, 'site_id', None), 201),
])
def test_forecast_post_success(api, payload, status_code):
    res = api.post('/forecasts/single/',
                   base_url=BASE_URL,
                   json=payload)
    assert res.status_code == status_code
    assert 'Location' in res.headers


@pytest.mark.parametrize('payload,message', [
    (INVALID_VARIABLE, f'{{"variable":["Must be one of: {variables}."]}}'),
    (INVALID_INTERVAL_LABEL, f'{{"interval_label":["Must be one of: {interval_labels}."]}}'), # NOQA
    (INVALID_ISSUE_TIME, '{"issue_time_of_day":["Time not in %H:%M format."]}'), # NOQA
    (INVALID_LEAD_TIME, '{"lead_time_to_start":["Not a valid integer."]}'), # NOQA
    (INVALID_INTERVAL_LENGTH, '{"interval_length":["Not a valid integer."]}'), # NOQA
    (INVALID_RUN_LENGTH, '{"run_length":["Not a valid integer."]}'),
    (INVALID_VALUE_TYPE, f'{{"interval_value_type":["Must be one of: {interval_value_types}."]}}'), # NOQA
    ({}, empty_json_response),
    (INVALID_NAME, '{"name":["Invalid characters in string."]}'),
    (INVALID_BOTH_IDS, '{"_schema":["Forecasts can only be associated with one site or one aggregate, so only site_id or aggregate_id may be provided"]}'),  # NOQA
    (INVALID_NO_IDS, '{"_schema":["One of site_id or aggregate_id must be provided"]}'),  # NOQA
])
def test_forecast_post_bad_request(api, payload, message):
    res = api.post('/forecasts/single/',
                   base_url=BASE_URL,
                   json=payload)
    assert res.status_code == 400
    assert res.get_data(as_text=True) == f'{{"errors":{message}}}\n'


def test_forecast_post_invalid_site(api, missing_id):
    payload = copy_update(VALID_FORECAST_JSON, 'site_id', missing_id)
    res = api.post('/forecasts/single/',
                   base_url=BASE_URL,
                   json=payload)
    assert res.status_code == 404


def test_forecast_post_site_id_is_aggregate(api, aggregate_id):
    payload = copy_update(VALID_FORECAST_JSON, 'site_id', aggregate_id)
    res = api.post('/forecasts/single/',
                   base_url=BASE_URL,
                   json=payload)
    assert res.status_code == 404


def test_forecast_post_invalid_aggregate(api, missing_id):
    payload = copy_update(VALID_FORECAST_AGG_JSON, 'aggregate_id', missing_id)
    res = api.post('/forecasts/single/',
                   base_url=BASE_URL,
                   json=payload)
    assert res.status_code == 404


def test_forecast_post_aggregate_id_is_site(api, site_id):
    payload = copy_update(VALID_FORECAST_AGG_JSON, 'aggregate_id', site_id)
    res = api.post('/forecasts/single/',
                   base_url=BASE_URL,
                   json=payload)
    assert res.status_code == 404


def test_get_forecast_links(api, forecast_id):
    r = api.get(f'/forecasts/single/{forecast_id}',
                base_url=BASE_URL)
    response = r.get_json()
    assert 'forecast_id' in response
    assert '_links' in response


@pytest.mark.parametrize('fx_id', demo_forecasts.keys())
def test_get_forecast_metadata_links(api, fx_id):
    r = api.get(f'/forecasts/single/{fx_id}/metadata',
                base_url=BASE_URL)
    response = r.get_json()
    assert 'forecast_id' in response
    assert '_links' in response
    assert 'site' in response['_links']
    assert 'aggregate' in response['_links']


def test_get_forecast_404(api, bad_id):
    r = api.get(f'/forecasts/single/{bad_id}',
                base_url=BASE_URL)
    assert r.status_code == 404


def test_get_forecast_metadata(api, forecast_id):
    r = api.get(f'/forecasts/single/{forecast_id}/metadata',
                base_url=BASE_URL)
    response = r.get_json()
    assert 'forecast_id' in response
    assert 'variable' in response
    assert 'name' in response
    assert 'site_id' in response
    assert 'aggregate_id' in response
    assert response['created_at'].endswith('+00:00')
    assert response['modified_at'].endswith('+00:00')


def test_get_forecast_metadata_404(api, bad_id):
    r = api.get(f'/forecasts/single/{bad_id}/metadata',
                base_url=BASE_URL)
    assert r.status_code == 404


WRONG_DATE_FORMAT_VALUE_JSON = {
    'values': [
        {'timestamp': '20-2-3T11111F',
         'value': 3},
    ]
}
WRONG_INTERVAL_VALUE_JSON = {
    'values': [
        {'timestamp': '2019-01-22T17:56:00Z',
         'value': 3},
        {'timestamp': '2019-01-22T18:04:00Z',
         'value': 2},
        {'timestamp': '2019-01-22T18:07:00Z',
         'value': 1},
    ]
}
NON_NUMERICAL_VALUE_JSON = {
    'values': [
        {'timestamp': "2019-01-22T17:56:36Z",
         'value': 'four'},
    ]
}
WRONG_DATE_FORMAT_CSV = "timestamp,value\nksdfjgn,32.93"
NON_NUMERICAL_VALUE_CSV = "timestamp,value\n2018-10-29T12:04:00:00+00,fgh" # NOQA


@pytest.mark.parametrize('vals', (VALID_FX_VALUE_JSON, UNSORTED_FX_VALUE_JSON))
def test_post_forecast_values_valid_json(api, forecast_id, mock_previous,
                                         vals):
    mock_previous.return_value = pd.Timestamp('2019-01-22T17:44Z')
    res = api.post(f'/forecasts/single/{forecast_id}/values',
                   base_url=BASE_URL,
                   json=vals)
    assert res.status_code == 201


def test_post_forecast_values_valid_json_with_restriction(
        api, forecast_id, mock_previous, restrict_fx_upload):
    mock_previous.return_value = pd.Timestamp('2019-11-01T06:55Z')
    restrict_fx_upload.return_value = pd.Timestamp('2019-11-01T05:59Z')
    res = api.post(f'/forecasts/single/{forecast_id}/values',
                   base_url=BASE_URL,
                   json=ADJ_FX_VALUE_JSON)
    assert res.status_code == 201


def test_post_forecast_values_valid_json_restricted(
        api, forecast_id, mock_previous, restrict_fx_upload):
    mock_previous.return_value = pd.Timestamp('2019-11-01T06:55Z')
    restrict_fx_upload.return_value = pd.Timestamp('2019-11-01T06:59Z')
    res = api.post(f'/forecasts/single/{forecast_id}/values',
                   base_url=BASE_URL,
                   json=ADJ_FX_VALUE_JSON)
    assert res.status_code == 400


def test_post_forecast_values_valid_json_restricted_val(
        api, forecast_id, mock_previous, restrict_fx_upload):
    mock_previous.return_value = pd.Timestamp('2019-01-22T06:55Z')
    restrict_fx_upload.return_value = pd.Timestamp('2019-01-22T05:59Z')
    # init should be 07:00Z, but not for valid fx json
    res = api.post(f'/forecasts/single/{forecast_id}/values',
                   base_url=BASE_URL,
                   json=VALID_FX_VALUE_JSON)
    assert res.status_code == 400


@pytest.fixture()
def patched_store_values(mocker):
    new = mocker.MagicMock()
    mocker.patch('sfa_api.utils.storage_interface.store_forecast_values',
                 new=new)
    return new


def test_post_json_storage_call(api, forecast_id, patched_store_values,
                                mock_previous):
    patched_store_values.return_value = forecast_id
    api.post(f'/forecasts/single/{forecast_id}/values',
             base_url=BASE_URL,
             json=VALID_FX_VALUE_JSON)
    patched_store_values.assert_called()


def test_post_values_missing_id(api, missing_id, mock_previous):
    # previously check if patched_store_values was called, shouldn't
    # even try now if forecast does not exist
    res = api.post(f'/forecasts/single/{missing_id}/values',
                   base_url=BASE_URL,
                   json=VALID_FX_VALUE_JSON)
    assert res.status_code == 404


def test_post_forecast_values_bad_previous(api, forecast_id,
                                           mock_previous):
    mock_previous.return_value = pd.Timestamp('2019-01-22T17:50Z')
    res = api.post(f'/forecasts/single/{forecast_id}/values',
                   base_url=BASE_URL,
                   json=VALID_FX_VALUE_JSON)
    assert res.status_code == 400


@pytest.mark.parametrize('payload', [
    'taco',
    {},
    WRONG_DATE_FORMAT_VALUE_JSON,
    NON_NUMERICAL_VALUE_JSON,
    WRONG_INTERVAL_VALUE_JSON
])
def test_post_forecast_values_invalid_json(api, payload, forecast_id,
                                           mock_previous):
    r = api.post(f'/forecasts/single/{forecast_id}/values',
                 base_url=BASE_URL,
                 json=payload)
    assert r.status_code == 400


@pytest.mark.parametrize('payload', [
    'taco',
    '',
    WRONG_DATE_FORMAT_CSV,
    NON_NUMERICAL_VALUE_CSV,
])
def test_post_forecast_values_invalid_csv(api, payload, forecast_id,
                                          mock_previous):
    r = api.post(f'/forecasts/single/{forecast_id}/values',
                 base_url=BASE_URL,
                 headers={'Content-Type': 'text/csv'},
                 data=payload)
    assert r.status_code == 400


def test_post_forecast_values_valid_csv(api, forecast_id, mock_previous):
    r = api.post(f'/forecasts/single/{forecast_id}/values',
                 base_url=BASE_URL,
                 headers={'Content-Type': 'text/csv'},
                 data=VALID_FX_VALUE_CSV)
    assert r.status_code == 201


@pytest.mark.parametrize('vals,status', [
    (VALID_FX_VALUE_JSON, 400),
    ({'values': [
        {'timestamp': "2019-01-22T17:54:00Z",
         'value': 1.0},
        {'timestamp': "2019-01-22T17:59:00Z",
         'value': 1.0},
        {'timestamp': "2019-01-22T18:04:00Z",
         'value': 0.0}
    ]}, 201)
])
def test_post_forecast_values_event_data(api, mock_previous, vals, status):
    mock_previous.return_value = pd.Timestamp('2019-01-22T17:44Z')
    forecast_id = list(demo_forecasts.keys())[-1]
    res = api.post(f'/forecasts/single/{forecast_id}/values',
                   base_url=BASE_URL,
                   json=vals)
    assert res.status_code == status


def test_get_forecast_values_404(api, bad_id, startend):
    r = api.get(f'/forecasts/single/{bad_id}/values{startend}',
                base_url=BASE_URL)
    assert r.status_code == 404


@pytest.mark.parametrize('start,end,mimetype', [
    ('bad-date', 'also_bad', 'application/json'),
    ('bad-date', 'also_bad', 'text/csv'),
])
def test_get_forecast_values_400(api, start, end, mimetype, forecast_id):
    r = api.get(f'/forecasts/single/{forecast_id}/values',
                base_url=BASE_URL,
                headers={'Accept': mimetype},
                query_string={'start': start, 'end': end})
    assert r.status_code == 400
    assert r.mimetype == 'application/json'


@pytest.mark.parametrize('start,end,mimetype', [
    ('2019-01-30T12:00:00Z', '2019-01-30T12:00:00Z', 'application/json'),
    ('2019-01-30T05:00:00-07:00', '2019-01-30T12:00:00Z', 'application/json'),
    ('2019-01-30T12:00:00Z', '2019-01-30T12:00:00Z', 'text/csv'),
    ('2019-01-30T12:00:00', '2019-01-30T13:00:00', 'text/csv'),
])
def test_get_forecast_values_200(api, start, end, mimetype, forecast_id):
    r = api.get(f'/forecasts/single/{forecast_id}/values',
                base_url=BASE_URL,
                headers={'Accept': mimetype},
                query_string={'start': start, 'end': end})
    assert r.status_code == 200
    assert r.mimetype == mimetype


def test_post_and_get_values_json(api, forecast_id, mock_previous):
    r = api.post(f'/forecasts/single/{forecast_id}/values',
                 base_url=BASE_URL,
                 json=VALID_FX_VALUE_JSON)
    assert r.status_code == 201
    start = '2019-01-22T17:54:00+00:00'
    end = '2019-01-22T18:04:00+00:00'
    r = api.get(f'/forecasts/single/{forecast_id}/values',
                base_url=BASE_URL,
                headers={'Accept': 'application/json'},
                query_string={'start': start, 'end': end})
    posted_data = r.get_json()
    assert VALID_FX_VALUE_JSON['values'] == posted_data['values']
    assert 'timestamp' in posted_data['values'][0]
    assert 'value' in posted_data['values'][0]


def test_post_and_get_values_csv(api, forecast_id, mock_previous):
    r = api.post(f'/forecasts/single/{forecast_id}/values',
                 base_url=BASE_URL,
                 headers={'Content-Type': 'text/csv'},
                 data=VALID_FX_VALUE_CSV)
    assert r.status_code == 201
    start = '2019-01-22T12:05:00+00:00'
    end = '2019-01-22T12:20:00+00:00'
    r = api.get(f'/forecasts/single/{forecast_id}/values',
                base_url=BASE_URL,
                headers={'Accept': 'text/csv'},
                query_string={'start': start, 'end': end})
    posted_data = r.data
    assert VALID_FX_VALUE_CSV == posted_data.decode('utf-8')


def test_get_latest_forecast_value_200(api, forecast_id, fx_vals):
    r = api.get(f'/forecasts/single/{forecast_id}/values/latest',
                base_url=BASE_URL)
    assert r.status_code == 200
    assert r.mimetype == 'application/json'
    data = r.get_json()
    assert data['forecast_id'] == forecast_id
    assert len(data['values']) == 1
    assert data['values'][0]['timestamp'] == fx_vals.index[-1].strftime(
        '%Y-%m-%dT%H:%M:%SZ')


def test_get_latest_forecast_value_new(api, new_forecast):
    forecast_id = new_forecast()
    r = api.get(f'/forecasts/single/{forecast_id}/values/latest',
                base_url=BASE_URL)
    assert r.status_code == 200
    assert r.mimetype == 'application/json'
    data = r.get_json()
    assert data['forecast_id'] == forecast_id
    assert len(data['values']) == 0


def test_get_latest_forecast_value_404(api, inaccessible_forecast_id):
    r = api.get(f'/forecasts/single/{inaccessible_forecast_id}/values/latest',
                base_url=BASE_URL)
    assert r.status_code == 404


def test_get_latest_forecast_value_404_obsid(api, observation_id):
    r = api.get(f'/forecasts/single/{observation_id}/values/latest',
                base_url=BASE_URL)
    assert r.status_code == 404


def test_get_forecast_timerange_200(api, forecast_id, fx_vals):
    r = api.get(f'/forecasts/single/{forecast_id}/values/timerange',
                base_url=BASE_URL)
    assert r.status_code == 200
    assert r.mimetype == 'application/json'
    data = r.get_json()
    assert data['forecast_id'] == forecast_id
    assert data['max_timestamp'] == fx_vals.index[-1].isoformat()
    assert data['min_timestamp'] == fx_vals.index[0].isoformat()


def test_get_forecast_timerange_new(api, new_forecast):
    forecast_id = new_forecast()
    r = api.get(f'/forecasts/single/{forecast_id}/values/timerange',
                base_url=BASE_URL)
    assert r.status_code == 200
    assert r.mimetype == 'application/json'
    data = r.get_json()
    assert data['forecast_id'] == forecast_id
    assert data['min_timestamp'] is None
    assert data['max_timestamp'] is None


def test_get_forecast_timerange_404(api, inaccessible_forecast_id):
    r = api.get(
        f'/forecasts/single/{inaccessible_forecast_id}/values/timerange',
        base_url=BASE_URL)
    assert r.status_code == 404


def test_get_forecast_timerange_404_obsid(api, observation_id):
    r = api.get(f'/forecasts/single/{observation_id}/values/timerange',
                base_url=BASE_URL)
    assert r.status_code == 404


EVENT_LABEL = copy_update(VALID_FORECAST_JSON, 'interval_label', 'event')
EVENT_VARIABLE = copy_update(VALID_FORECAST_JSON, 'variable', 'event')


@pytest.mark.parametrize('payload,message', [
    (EVENT_VARIABLE, ('{"events":["Both interval_label and variable must be '
                      'set to \'event\'."]}')),
    (EVENT_LABEL, ('{"events":["Both interval_label and variable must be '
                   'set to \'event\'."]}')),
])
def test_forecast_post_bad_event(api, payload, message):
    r = api.post('/forecasts/single/',
                 base_url=BASE_URL,
                 json=payload)
    assert r.status_code == 400
    assert r.get_data(as_text=True) == f'{{"errors":{message}}}\n'


def test_get_forecast_gaps_200(api, forecast_id, addmayvalues):
    r = api.get(f'/forecasts/single/{forecast_id}/values/gaps',
                query_string={'start': '2019-04-01T00:00Z',
                              'end': '2019-06-01T00:00Z'},
                base_url=BASE_URL)
    assert r.status_code == 200
    assert r.mimetype == 'application/json'
    data = r.get_json()
    assert '_links' in data
    assert data['forecast_id'] == forecast_id
    assert data['gaps'] == [{'timestamp': '2019-04-17T06:55:00+00:00',
                             'next_timestamp': '2019-05-01T00:00:00+00:00'}]


def test_get_forecast_gaps_none(api, forecast_id, addmayvalues):
    r = api.get(f'/forecasts/single/{forecast_id}/values/gaps',
                query_string={'start': '2019-07-01T00:00Z',
                              'end': '2019-10-01T00:00Z'},
                base_url=BASE_URL)
    assert r.status_code == 200
    assert r.mimetype == 'application/json'
    data = r.get_json()
    assert '_links' in data
    assert data['forecast_id'] == forecast_id
    assert data['gaps'] == []


def test_get_forecast_gaps_404(api, inaccessible_forecast_id):
    r = api.get(
        f'/forecasts/single/{inaccessible_forecast_id}/values/gaps',
        query_string={'start': '2019-04-01T00:00Z',
                      'end': '2019-06-01T00:00Z'},
        base_url=BASE_URL)
    assert r.status_code == 404


def test_get_forecast_gaps_404_obsid(api, observation_id, addmayvalues):
    r = api.get(f'/forecasts/single/{observation_id}/values/gaps',
                query_string={'start': '2019-04-01T00:00Z',
                              'end': '2019-06-01T00:00Z'},
                base_url=BASE_URL)
    assert r.status_code == 404


def test_get_forecast_gaps_400(api, inaccessible_forecast_id):
    r = api.get(
        f'/forecasts/single/{inaccessible_forecast_id}/values/gaps',
        query_string={'start': '2019-04-01T00:00Z'},
        base_url=BASE_URL)
    assert r.status_code == 400


@pytest.mark.parametrize('content_type,payload', [
    ('application/json', '{"values": [1, 2]}'),
    ('text/csv', 'timestamp,value\n'+"1,2"),
])
def test_post_forecast_too_large_from_header(
        api, forecast_id, content_type, payload, mocker):
    req_headers = mocker.patch('sfa_api.utils.request_handling.request')
    req_headers.headers = {'Content-Length': 17*1024*1024}
    req = api.post(
            f'/forecasts/single/{forecast_id}/values',
            environ_base={'Content-Type': content_type,
                          'Content-Length': 17*1024*1024},
            data=payload, base_url=BASE_URL)
    assert req.status_code == 413


@pytest.mark.parametrize('content_type', [
    'application/json',
    'text/csv',
])
def test_post_forecast_too_large_from_body(
        api, forecast_id, content_type, mocker):
    payload = _get_large_test_payload(content_type)
    req = api.post(
            f'/forecasts/single/{forecast_id}/values',
            environ_base={'Content-Type': content_type},
            data=payload, base_url=BASE_URL)
    assert req.status_code == 413


@pytest.mark.parametrize('variable', [
    'ac_power',
    'dc_power',
    'poa_global',
    'availability',
    'curtailment'
])
def test_forecast_post_power_at_weather_site(api, variable):
    payload = copy_update(VALID_FORECAST_JSON, 'variable', variable)
    res = api.post('/forecasts/single/',
                   base_url=BASE_URL,
                   json=payload)
    assert res.status_code == 400
    assert res.json == {
        "errors": {
            "site": ["Site must have modeling parameters to create "
                     f"{', '.join(POWER_VARIABLES)} records."]
        }
    }


def test_forecast_post_mismatched_aggregate_variable(api):
    payload = copy_update(VALID_FORECAST_AGG_JSON, 'variable', 'ac_power')
    res = api.post('/forecasts/single/',
                   base_url=BASE_URL,
                   json=payload)
    assert res.status_code == 400
    assert res.json == {
        "errors": {
            "variable": ["Forecast variable must match aggregate."]
        }
    }


@pytest.mark.parametrize('filename, str_content,content_type,start,end', [
    ('data.csv', VALID_FX_VALUE_CSV, 'text/csv',
     '2019-01-22T12:05:00+00:00', '2019-01-22T12:20:00+00:00'),
    ('data.csv', VALID_FX_VALUE_CSV, 'application/vnd.ms-excel',
     '2019-01-22T12:05:00+00:00', '2019-01-22T12:20:00+00:00'),
    ('data.json', json.dumps(VALID_FX_VALUE_JSON), 'application/json',
     '2019-01-22T17:54:00+00:00', '2019-01-22T18:04:00+00:00'),
])
def test_posting_files(
        api, dummy_file, filename, str_content, content_type, forecast_id,
        start, end, mock_previous):
    content = BytesIO(bytes(str_content, 'utf-8'))
    the_file = dummy_file(filename, content, content_type)
    file_post = api.post(
        f'/forecasts/single/{forecast_id}/values',
        base_url=BASE_URL,
        content_type='multipart/form-data',
        data=the_file)
    assert file_post.status_code == 201

    if content_type == 'application/json':
        accept = 'application/json'
    else:
        accept = 'text/csv'
    req = api.get(f'/forecasts/single/{forecast_id}/values',
                  base_url=BASE_URL,
                  headers={'Accept': accept},
                  query_string={'start': start, 'end': end})
    posted_data = req.data
    decoded_response = posted_data.decode('utf-8')
    if content_type == 'application/json':
        expected = VALID_FX_VALUE_JSON['values']
        assert expected == json.loads(decoded_response)['values']
    else:
        expected = VALID_FX_VALUE_CSV
        assert expected == decoded_response


def test_post_file_invalid_utf(api, dummy_file, forecast_id):
    content = BytesIO(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1\x00\x00\x00\x00\x00')
    the_file = dummy_file('broken.xls', content, 'application/vnd.ms-excel')
    file_post = api.post(
        f'/forecasts/single/{forecast_id}/values',
        base_url=BASE_URL,
        content_type='multipart/form-data',
        data=the_file)
    assert file_post.status_code == 400
    expected = '{"errors":{"error":["File could not be decoded as UTF-8."]}}\n'
    assert file_post.get_data(as_text=True) == expected


def test_post_multiple_files(api, dummy_file, forecast_id):
    content1 = BytesIO(bytes('valid_string'.encode('utf-8')))
    content2 = BytesIO(bytes('{"a":"B"}'.encode('utf-8')))

    file1 = dummy_file('file1.csv', content1, 'text/csv')
    file2 = dummy_file('file2.json', content2, 'application/json')
    file1.update(file2)
    file_post = api.post(
        f'/forecasts/single/{forecast_id}/values',
        base_url=BASE_URL,
        content_type='multipart/form-data',
        data=file1)
    assert file_post.status_code == 400
    expected = '{"errors":{"error":["Multiple files found. Please upload one file at a time."]}}\n' # NOQA
    assert file_post.get_data(as_text=True) == expected


def test_post_file_no_file(api, forecast_id):
    file_post = api.post(
        f'/forecasts/single/{forecast_id}/values',
        base_url=BASE_URL,
        content_type='multipart/form-data',
        data={})
    assert file_post.status_code == 400
    expected = '{"errors":{"error":["Missing file in request body."]}}\n'
    assert file_post.get_data(as_text=True) == expected


def test_post_file_invalid_json(api, forecast_id):
    incorrect_file_payload = {
        'data.json': (BytesIO(b'invalid'), 'data.json', 'application/json')
    }
    file_post = api.post(
        f'/forecasts/single/{forecast_id}/values',
        base_url=BASE_URL,
        content_type='multipart/form-data',
        data=incorrect_file_payload)
    assert file_post.status_code == 400
    expected = '{"errors":{"error":["Malformed JSON."]}}\n'
    assert file_post.get_data(as_text=True) == expected


def test_post_file_invalid_mimetype(api, forecast_id):
    incorrect_file_payload = {
        'data.csv': (BytesIO(b'invalid'), 'data.xls', 'application/videogame')
    }
    file_post = api.post(
        f'/forecasts/single/{forecast_id}/values',
        base_url=BASE_URL,
        content_type='multipart/form-data',
        data=incorrect_file_payload)
    assert file_post.status_code == 400
    expected = '{"errors":{"error":["Unsupported Content-Type or MIME type."]}}\n' # noqa
    assert file_post.get_data(as_text=True) == expected


@pytest.mark.parametrize('up', [
    {'name': 'new name'},
    {},
    {'name': 'again', 'extra_parameters': 'here they are'}
])
def test_forecast_update_success(api, forecast_id, up):
    r = api.post(f'/forecasts/single/{forecast_id}/metadata',
                 base_url=BASE_URL,
                 json=up)
    assert r.status_code == 200
    assert 'Location' in r.headers


def test_forecast_update_404(api, bad_id):
    r = api.post(f'/forecasts/single/{bad_id}/metadata',
                 base_url=BASE_URL,
                 json={'name': 'new name'})
    assert r.status_code == 404


@pytest.mark.parametrize('payload,message', [
    ({'extra_parameters': 0}, '{"extra_parameters":["Not a valid string."]}'),
    ({'name': '#NOPE'}, '{"name":["Invalid characters in string."]}')
])
def test_forecast_update_bad_request(api, forecast_id, payload, message):
    r = api.post(f'/forecasts/single/{forecast_id}/metadata',
                 base_url=BASE_URL,
                 json=payload)
    assert r.status_code == 400
    assert r.get_data(as_text=True) == f'{{"errors":{message}}}\n'


@pytest.mark.parametrize('up', [
    {'name': 'new name'},
    {},
    {'name': 'again', 'extra_parameters': 'here they are'}
])
def test_cdf_forecast_update_success(api, cdf_forecast_group_id, up):
    r = api.post(f'/forecasts/cdf/{cdf_forecast_group_id}',
                 base_url=BASE_URL,
                 json=up)
    assert r.status_code == 200
    assert 'Location' in r.headers


def test_cdf_forecast_update_404(api, bad_id):
    r = api.post(f'/forecasts/cdf/{bad_id}',
                 base_url=BASE_URL,
                 json={'name': 'new name'})
    assert r.status_code == 404


@pytest.mark.parametrize('payload,message', [
    ({'extra_parameters': 0}, '{"extra_parameters":["Not a valid string."]}'),
    ({'name': '#NOPE'}, '{"name":["Invalid characters in string."]}')
])
def test_cdf_forecast_update_bad_request(api, cdf_forecast_group_id,
                                         payload, message):
    r = api.post(f'/forecasts/cdf/{cdf_forecast_group_id}',
                 base_url=BASE_URL,
                 json=payload)
    assert r.status_code == 400
    assert r.get_data(as_text=True) == f'{{"errors":{message}}}\n'


def test_post_forecast_values_empty_json(api, forecast_id):
    vals = {'values': []}
    res = api.post(f'/forecasts/single/{forecast_id}/values',
                   base_url=BASE_URL,
                   json=vals)
    assert res.status_code == 400
    assert res.json['errors'] == {
        "error": ["Posted data contained no values."],
    }


def test_post_forecast_values_empty_csv(api, forecast_id):
    res = api.post(f'/forecasts/single/{forecast_id}/values',
                   base_url=BASE_URL,
                   headers={'Content-Type': 'text/csv'},
                   data="timestamp,value\n")
    assert res.status_code == 400
    assert res.json['errors'] == {
        "error": ["Posted data contained no values."],
    }


@pytest.mark.parametrize('missing', ['timestamp', 'value'])
def test_post_forecast_values_json_missing_field(api, forecast_id, missing):
    single_value = {'timestamp': '2020-01-01T00:00Z', 'value': 0}
    single_value.pop(missing)
    vals = {'values': [single_value]}
    res = api.post(f'/forecasts/single/{forecast_id}/values',
                   base_url=BASE_URL,
                   json=vals)
    assert res.status_code == 400
    assert res.json['errors'] == {
        missing: [f'Missing "{missing}" field.'],
    }


@pytest.mark.parametrize('csv,missing', [
    ('timestamp\n2020-01-01T00:00Z', 'value'),
    ('value\n5', 'timestamp'),
])
def test_post_forecast_values_csv_missing_field(
        api, forecast_id, csv, missing):
    res = api.post(f'/forecasts/single/{forecast_id}/values',
                   base_url=BASE_URL,
                   headers={'Content-Type': 'text/csv'},
                   data=csv)
    assert res.status_code == 400
    assert res.json['errors'] == {
        missing: [f'Missing "{missing}" field.'],
    }
