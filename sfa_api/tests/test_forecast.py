import pandas as pd
import pytest


from sfa_api.conftest import (variables, interval_value_types, interval_labels,
                              BASE_URL, VALID_FORECAST_JSON, copy_update,
                              VALID_FX_VALUE_JSON, VALID_FX_VALUE_CSV,
                              VALID_FORECAST_AGG_JSON, UNSORTED_FX_VALUE_JSON,
                              ADJ_FX_VALUE_JSON, demo_forecasts)


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


def test_get_forecast_404(api, missing_id):
    r = api.get(f'/forecasts/single/{missing_id}',
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


def test_get_forecast_metadata_404(api, missing_id):
    r = api.get(f'/forecasts/single{missing_id}/metadata',
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


def test_get_forecast_values_404(api, missing_id, startend):
    r = api.get(f'/forecasts/single/{missing_id}/values{startend}',
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
