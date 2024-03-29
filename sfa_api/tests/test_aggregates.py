import math


from copy import deepcopy
import pandas as pd
import pytest


from sfa_api.conftest import (
    BASE_URL, copy_update, variables, agg_types,
    VALID_OBS_JSON, demo_forecasts, demo_group_cdf,
    VALID_AGG_JSON, demo_aggregates)


def test_get_all_aggregates(api):
    res = api.get('/aggregates/',
                  base_url=BASE_URL)
    assert res.status_code == 200
    resp = res.get_json()
    for agg in resp:
        assert 'observations' in agg


def test_post_aggregate_success(api):
    res = api.post('/aggregates/',
                   base_url=BASE_URL,
                   json=VALID_AGG_JSON)
    assert res.status_code == 201
    assert 'Location' in res.headers


@pytest.mark.parametrize('payload,message', [
    (copy_update(VALID_AGG_JSON, 'variable', 'other'),
     f'{{"variable":["Must be one of: {variables}."]}}'),
    (copy_update(VALID_AGG_JSON, 'aggregate_type', 'cov'),
     f'{{"aggregate_type":["Must be one of: {agg_types}."]}}'),
    (copy_update(VALID_AGG_JSON, 'interval_label', 'instant'),
     '{"interval_label":["Must be one of: beginning, ending."]}'),
    ({}, '{"aggregate_type":["Missing data for required field."],"description":["Missing data for required field."],"interval_label":["Missing data for required field."],"interval_length":["Missing data for required field."],"name":["Missing data for required field."],"timezone":["Missing data for required field."],"variable":["Missing data for required field."]}'),  # NOQA
    (copy_update(VALID_AGG_JSON, 'interval_length', '61'),
     '{"interval_length":["Must be a divisor of one day."]}'),
])
def test_post_aggregate_bad_request(api, payload, message):
    res = api.post('/aggregates/',
                   base_url=BASE_URL,
                   json=payload)
    assert res.status_code == 400
    assert res.get_data(as_text=True) == f'{{"errors":{message}}}\n'


def test_get_aggregate_links(api, aggregate_id):
    res = api.get(f'/aggregates/{aggregate_id}',
                  base_url=BASE_URL)
    resp = res.get_json()
    assert 'aggregate_id' in resp
    assert '_links' in resp


def test_get_aggregate_links_404(api, missing_id):
    res = api.get(f'/aggregates/{missing_id}',
                  base_url=BASE_URL)
    assert res.status_code == 404


def test_delete_aggregate(api):
    res = api.post('/aggregates/',
                   base_url=BASE_URL,
                   json=VALID_AGG_JSON)
    assert res.status_code == 201
    new_id = res.get_data(as_text=True)
    res = api.get(f'/aggregates/{new_id}',
                  base_url=BASE_URL)
    assert res.status_code == 200
    res = api.delete(f'/aggregates/{new_id}',
                     base_url=BASE_URL)
    assert res.status_code == 204
    res = api.get(f'/aggregates/{new_id}',
                  base_url=BASE_URL)
    assert res.status_code == 404


def test_delete_aggregate_missing(api, missing_id):
    res = api.delete(f'/aggregates/{missing_id}',
                     base_url=BASE_URL)
    assert res.status_code == 404


def test_get_aggregate_metadata(api, aggregate_id):
    res = api.get(f'/aggregates/{aggregate_id}/metadata',
                  base_url=BASE_URL)
    assert res.status_code == 200
    resp = res.get_json()
    assert 'aggregate_id' in resp
    assert 'variable' in resp
    assert 'observations' in resp
    assert 'aggregate_type' in resp
    assert resp['interval_value_type'] == 'interval_mean'
    assert resp['created_at'].endswith('+00:00')
    assert resp['modified_at'].endswith('+00:00')
    assert resp['observations'][0]['created_at'].endswith('+00:00')


def test_get_aggregate_metadata_404(api, missing_id):
    res = api.get(f'/aggregates/{missing_id}/metadata',
                  base_url=BASE_URL)
    assert res.status_code == 404


@pytest.mark.parametrize('payload', [
    {},
    {'name': 'new aggregate name'},
    {'description': 'is here', 'timezone': 'UTC', 'extra_parameters': 'new'}
])
def test_update_aggregate_add_obs(api, aggregate_id, payload):
    r1 = api.post('/observations/',
                  base_url=BASE_URL,
                  json=VALID_OBS_JSON)
    obs_id = r1.get_data(as_text=True)
    payload.update({'observations': [{
        'observation_id': obs_id,
        'effective_from': '2029-01-01 01:23:00Z'}]})
    res = api.post(f'/aggregates/{aggregate_id}/metadata',
                   json=payload,
                   base_url=BASE_URL)
    assert res.status_code == 200
    r2 = api.get(f'/aggregates/{aggregate_id}/metadata',
                 base_url=BASE_URL)
    assert r2.status_code == 200
    did = False
    for obs in r2.json['observations']:
        if obs['observation_id'] == obs_id:
            did = True
            assert obs['effective_from'] == (
                '2029-01-01T01:23:00+00:00')
    assert did


@pytest.mark.parametrize('payload', [
    {},
    {'name': 'new aggregate name'},
    {'description': 'is here', 'timezone': 'UTC', 'extra_parameters': 'new'},
    pytest.param({'name': 0}, marks=pytest.mark.xfail(strict=True))
])
def test_update_aggregate_no_obs(api, aggregate_id, payload):
    res = api.post(f'/aggregates/{aggregate_id}/metadata',
                   json=payload,
                   base_url=BASE_URL)
    assert res.status_code == 200
    r2 = api.get(f'/aggregates/{aggregate_id}/metadata',
                 base_url=BASE_URL)
    assert r2.status_code == 200
    res = r2.json
    for k, v in payload.items():
        assert res[k] == v


def test_update_aggregate_add_obs_404_agg(api, missing_id):
    payload = {'observations': [{
        'observation_id': '123e4567-e89b-12d3-a456-426655440000',
        'effective_from': '2019-01-01 01:23:00Z'}]}
    res = api.post(f'/aggregates/{missing_id}/metadata',
                   json=payload,
                   base_url=BASE_URL)
    assert res.status_code == 404


def test_update_aggregate_add_obs_404_obs(api, missing_id, aggregate_id):
    payload = {'observations': [{
        'observation_id': missing_id,
        'effective_from': '2019-01-01 01:23:00Z'}]}
    res = api.post(f'/aggregates/{aggregate_id}/metadata',
                   json=payload,
                   base_url=BASE_URL)
    assert res.status_code == 404


@pytest.mark.parametrize('payload,intext', [
    ({'observations': [{
        'observation_id': '123e4567-e89b-12d3-a456-426655440000',
        'effective_from': '2019-01-01 01:23:00Z'}]},
     'present and valid'),
])
def test_update_aggregate_add_obs_bad_req(api, payload, aggregate_id, intext):
    res = api.post(f'/aggregates/{aggregate_id}/metadata',
                   json=payload,
                   base_url=BASE_URL)
    assert res.status_code == 400
    assert intext in res.get_data(as_text=True)


@pytest.mark.parametrize('field,val,intext', [
    ('interval_length', 300, 'interval length is not less'),
    ('variable', 'dni', 'same variable'),
    ('interval_value_type', 'interval_min', 'interval_value_type'),
])
def test_update_aggregate_add_obs_bad_obs(api, aggregate_id, intext,
                                          field, val):
    r1 = api.post('/observations/',
                  base_url=BASE_URL,
                  json=copy_update(VALID_OBS_JSON, field, val))
    obs_id = r1.get_data(as_text=True)
    payload = {'observations': [
        {'observation_id': obs_id,
         'effective_from': '2019-01-01 01:23:00Z'}]}
    res = api.post(f'/aggregates/{aggregate_id}/metadata',
                   json=payload,
                   base_url=BASE_URL)
    assert res.status_code == 400
    assert intext in res.get_data(as_text=True)


def test_update_aggregate_add_obs_bad_many(api, aggregate_id):
    r1 = api.post('/observations/',
                  base_url=BASE_URL,
                  json=copy_update(VALID_OBS_JSON, 'interval_length', 300))
    obs_id = r1.get_data(as_text=True)
    payload = {'observations': [
        {'observation_id': obs_id,
         'effective_from': '2019-01-01 01:23:00Z'},
        {'observation_id': '123e4567-e89b-12d3-a456-426655440000',
         'effective_from': '2019-01-01 01:23:00Z'}
    ]}
    res = api.post(f'/aggregates/{aggregate_id}/metadata',
                   json=payload,
                   base_url=BASE_URL)
    assert res.status_code == 400
    assert 'present and valid' in res.get_data(as_text=True)
    assert 'interval length is not less' in res.get_data(as_text=True)


def test_update_aggregate_remove_obs(api, aggregate_id):
    payload = {'observations': [{
        'observation_id': '123e4567-e89b-12d3-a456-426655440000',
        'effective_until': '2019-01-01 01:23:00Z'}]}
    res = api.post(f'/aggregates/{aggregate_id}/metadata',
                   json=payload,
                   base_url=BASE_URL)
    assert res.status_code == 200
    r2 = api.get(f'/aggregates/{aggregate_id}/metadata',
                 base_url=BASE_URL)
    assert r2.json['observations'][0]['effective_until'] == (
        '2019-01-01T01:23:00+00:00')


def test_update_aggregate_remove_obs_404_agg(api, missing_id):
    payload = {'observations': [{
        'observation_id': '123e4567-e89b-12d3-a456-426655440000',
        'effective_until': '2019-01-01 01:23:00Z'}]}
    res = api.post(f'/aggregates/{missing_id}/metadata',
                   json=payload,
                   base_url=BASE_URL)
    assert res.status_code == 404


def test_update_aggregate_remove_obs_no_obs(api, missing_id, aggregate_id):
    payload = {'observations': [{
        'observation_id': missing_id,
        'effective_until': '2019-01-01 01:23:00Z'}]}
    res = api.post(f'/aggregates/{aggregate_id}/metadata',
                   json=payload,
                   base_url=BASE_URL)
    assert res.status_code == 200  # no effect


@pytest.mark.parametrize('payload,intext', [
    ({'observations': [{
        'observation_id': '123e4567-e89b-12d3-a456-426655440000'}]},
     'Specify one of'),
    ({'observations': [{
        'observation_id': '123e4567-e89b-12d3-a456-426655440000',
        'effective_from': 'notatime'}]},
     'Not a valid datetime'),
    ({'observations': [{
        'observation_id': '123e4567-e89b-12d3-a456-426655440000',
        'effective_until': 'notatime'}]},
     'Not a valid datetime'),
    ({'observations': [{
        'observation_id': '123e4567-e89b-12d3-a456-426655440000',
        'effective_from': '2019-01-01 00:00:00Z',
        'effective_until': '2019-01-01 00:00:00Z'}]},
     'Only specify one of'),
    ({'observations': [{
        'observation_id': '123e4567-e89b-12d3-a456-426655440000',
        'effective_until': '2050-01-01 03:14:07Z'}]},
     'Exceeds maximum'),
    ({'observations': [
        {'observation_id': '123e4567-e89b-12d3-a456-426655440000',
         'effective_from': '2019-01-01 00:00:00Z'},
        {'observation_id': '123e4567-e89b-12d3-a456-426655440000',
         'effective_until': 'notatime'}
    ]},
        '1'),
])
def test_update_aggregate_bad_req(api, aggregate_id, payload, intext):
    res = api.post(f'/aggregates/{aggregate_id}/metadata',
                   json=payload,
                   base_url=BASE_URL)
    assert res.status_code == 400
    assert intext in res.get_data(as_text=True)


def test_get_aggregate_values(api, aggregate_id, startend):
    res = api.get(f'/aggregates/{aggregate_id}/values{startend}',
                  headers={'Accept': 'application/json'},
                  base_url=BASE_URL)
    assert res.status_code == 200
    assert res.json['aggregate_id'] == aggregate_id
    assert 'values' in res.json
    assert 'timestamp' in res.json['values'][0]
    assert 'value' in res.json['values'][0]
    assert 'quality_flag' in res.json['values'][0]


def test_get_aggregate_values_startendtz(api, aggregate_id, startend):
    res = api.get(f'/aggregates/{aggregate_id}/values'
                  '?start=20190101T0000Z&end=2020-01-01T00:00:00',
                  headers={'Accept': 'application/json'},
                  base_url=BASE_URL)
    assert res.status_code == 200
    assert res.json['aggregate_id'] == aggregate_id
    assert 'values' in res.json
    assert 'timestamp' in res.json['values'][0]
    assert 'value' in res.json['values'][0]
    assert 'quality_flag' in res.json['values'][0]


def test_get_aggregate_values_csv(api, aggregate_id, startend):
    res = api.get(f'/aggregates/{aggregate_id}/values{startend}',
                  headers={'Accept': 'text/csv'},
                  base_url=BASE_URL)
    assert res.status_code == 200
    data = res.get_data(as_text=True)
    assert aggregate_id in data
    assert 'timestamp,value,quality_flag' in data


def test_get_aggregate_values_outside_range(api, aggregate_id):
    res = api.get(f'/aggregates/{aggregate_id}/values',
                  headers={'Accept': 'application/json'},
                  base_url=BASE_URL,
                  query_string={'start': '2018-01-01T00:00:00Z',
                                'end': '2018-01-02T00:00:00Z'})
    assert res.status_code == 422
    assert res.json['errors']['values'] == [
        'No effective observations in data']


def test_get_aggregate_values_422(api, aggregate_id, startend):
    payload = {'observations': [{
        'observation_id': '123e4567-e89b-12d3-a456-426655440000',
        'effective_until': '2019-01-01 01:23:00Z'}]}
    res = api.post(f'/aggregates/{aggregate_id}/metadata',
                   json=payload,
                   base_url=BASE_URL)
    assert res.status_code == 200
    res = api.get(f'/aggregates/{aggregate_id}/values{startend}',
                  headers={'Accept': 'application/json'},
                  base_url=BASE_URL)
    assert res.status_code == 422
    assert 'missing keys 123e4567-e89b-12d3-a456-426655440000' in res.get_data(
        as_text=True)


def test_get_aggregate_values_obs_deleted(api, aggregate_id, missing_id,
                                          startend):
    res = api.delete('/observations/123e4567-e89b-12d3-a456-426655440000',
                     base_url=BASE_URL)
    assert res.status_code == 204
    res = api.get(f'/aggregates/{aggregate_id}/values{startend}',
                  headers={'Accept': 'application/json'},
                  base_url=BASE_URL)
    assert res.status_code == 422


def test_get_aggregate_values_limited_effective(api, aggregate_id, startend):
    payload = {'observations': [{
        'observation_id': '123e4567-e89b-12d3-a456-426655440000',
        'effective_until': '2019-04-17 01:23:00Z'}]}
    res = api.post(f'/aggregates/{aggregate_id}/metadata',
                   json=payload,
                   base_url=BASE_URL)
    assert res.status_code == 200
    res = api.get(f'/aggregates/{aggregate_id}/values{startend}',
                  headers={'Accept': 'application/json'},
                  base_url=BASE_URL)
    assert res.status_code == 200

    assert res.json['values'][0]['value'] is None

    # datapoint just before effective_from is None
    assert res.json['values'][6 + 24*103]['value'] is None

    # datapoint just inside/equal to effective_from is not None
    assert not math.isnan(res.json['values'][7 + 24*103]['value'])

    # datapoint just before effective_until is not null
    assert not math.isnan(res.json['values'][7 + 24*106]['value'])

    # datpoint after effective_until is null
    assert res.json['values'][8 + 24*106]['value'] is None

    assert res.json['values'][-1]['value'] is None


def test_get_aggregate_values_no_data_after_effective(api, aggregate_id):
    # https://github.com/SolarArbiter/solarforecastarbiter-api/issues/219
    # Regression test for #219, previously, requests for values after any of
    # the included observations `effective_from` was set resulted in an error.
    payload = {'observations': [{
        'observation_id': '123e4567-e89b-12d3-a456-426655440000',
        'effective_until': '2019-04-14 07:00:00Z'}, {
        'observation_id': 'b1dfe2cb-9c8e-43cd-afcf-c5a6feaf81e2',
        'effective_until': '2019-04-14 07:00:00Z'}]}
    res = api.post(f'/aggregates/{aggregate_id}/metadata',
                   json=payload,
                   base_url=BASE_URL)
    assert res.status_code == 200
    startend = '?start=2019-04-14T08:00Z&end=2019-04-17T07:00Z'
    res = api.get(f'/aggregates/{aggregate_id}/values{startend}',
                  headers={'Accept': 'application/json'},
                  base_url=BASE_URL)
    assert res.status_code == 200
    values = res.json['values']
    assert not math.isnan(values[0]['value'])
    assert not math.isnan(values[-1]['value'])


def test_get_aggregate_values_404(api, missing_id, startend):
    res = api.get(f'/aggregates/{missing_id}/values{startend}',
                  headers={'Accept': 'application/json'},
                  base_url=BASE_URL)
    assert res.status_code == 404


def test_get_aggregate_forecasts(api, aggregate_id):
    res = api.get(f'/aggregates/{aggregate_id}/forecasts/single',
                  base_url=BASE_URL)
    assert res.status_code == 200
    assert isinstance(res.get_json(), list)
    agg_forecasts = res.get_json()
    assert len(agg_forecasts) == 2
    agg_fx = agg_forecasts[0]
    assert agg_fx['forecast_id'] in demo_forecasts
    assert agg_fx['aggregate_id'] == aggregate_id


def test_get_aggregate_forecasts_404(api, missing_id):
    res = api.get(f'/aggregates/{missing_id}/forecasts/single',
                  base_url=BASE_URL)
    assert res.status_code == 404


def test_get_aggregate_cdf_forecast_groups(api, aggregate_id):
    res = api.get(f'/aggregates/{aggregate_id}/forecasts/cdf',
                  base_url=BASE_URL)
    assert res.status_code == 200
    assert isinstance(res.get_json(), list)
    agg_cdf_forecasts = res.get_json()
    assert len(agg_cdf_forecasts) == 1
    agg_cdf = agg_cdf_forecasts[0]
    expected = list(demo_group_cdf.values())[-1]
    assert agg_cdf['forecast_id'] == expected['forecast_id']
    assert agg_cdf['aggregate_id'] == aggregate_id


def test_get_aggregate_cdf_forecasts_404(api, missing_id):
    res = api.get(f'/aggregates/{missing_id}/forecasts/cdf',
                  base_url=BASE_URL)
    assert res.status_code == 404


def test_aggregate_values_deleted_observation(api, observation_id, startend):
    r1 = api.post('/aggregates/',
                  base_url=BASE_URL,
                  json=VALID_AGG_JSON)
    assert r1.status_code == 201
    assert 'Location' in r1.headers
    aggregate_id = r1.get_data(as_text=True)

    payload = {'observations': [{
        'observation_id': observation_id,
        'effective_from': '2029-01-01 01:23:00Z'}]}
    r2 = api.post(f'/aggregates/{aggregate_id}/metadata',
                  json=payload,
                  base_url=BASE_URL)
    assert r2.status_code == 200
    r3 = api.delete(f'/observations/{observation_id}',
                    base_url=BASE_URL)
    assert r3.status_code == 204
    r4 = api.get(f'/aggregates/{aggregate_id}/values{startend}',
                 base_url=BASE_URL)
    assert r4.status_code == 422
    errors = r4.json['errors']
    assert errors['values'] == ['Deleted Observation data cannot be retrieved '
                                'to include in Aggregate']


@pytest.mark.parametrize('queryparams,label,exp1,exp2', [
    ('?start=2019-04-14T13:00Z&end=2019-04-14T14:00Z', 'beginning',
     {'timestamp': '2019-04-14T13:00:00Z', 'value': 78.30793},
     {'timestamp': '2019-04-14T14:00:00Z', 'value': 303.016}),
    ('?start=2019-04-14T13:30Z&end=2019-04-14T14:30Z', 'beginning',
     {'timestamp': '2019-04-14T13:00:00Z', 'value': 78.30793},
     {'timestamp': '2019-04-14T14:00:00Z', 'value': 303.016}),
    ('?start=2019-04-14T13:00Z&end=2019-04-14T14:00Z', 'ending',
     {'timestamp': '2019-04-14T13:00:00Z', 'value': -0.77138242},
     {'timestamp': '2019-04-14T14:00:00Z', 'value': 93.286025}),
    ('?start=2019-04-14T13:30Z&end=2019-04-14T14:30Z', 'ending',
     {'timestamp': '2019-04-14T14:00:00Z', 'value': 93.286025},
     {'timestamp': '2019-04-14T15:00:00Z', 'value': 323.98858333}),
])
def test_aggregate_values_interval_label(
        api, observation_id, label, exp1, exp2, queryparams):
    agg = deepcopy(VALID_AGG_JSON)
    agg['interval_label'] = label
    r1 = api.post('/aggregates/',
                  base_url=BASE_URL,
                  json=agg)
    assert r1.status_code == 201
    assert 'Location' in r1.headers
    aggregate_id = r1.get_data(as_text=True)

    payload = {'observations': [{
        'observation_id': observation_id,
        'effective_from': '2019-04-14 06:00:00Z'}]}
    api.post(f'/aggregates/{aggregate_id}/metadata',
             json=payload,
             base_url=BASE_URL)
    r3 = api.get(
        f'/aggregates/{aggregate_id}/values{queryparams}',
        headers={'Accept': 'application/json'},
        base_url=BASE_URL)
    values = r3.json['values']
    assert len(values) == 2
    exp1.update({'quality_flag': 0})
    exp2.update({'quality_flag': 0})
    assert values[0] == exp1
    assert values[1] == exp2


@pytest.mark.parametrize('label,expected', [
    ('beginning', {'timestamp': '2019-04-14T13:00:00Z', 'value': 78.30793}),
    ('ending', {'timestamp': '2019-04-14T14:00:00Z', 'value': 93.286025}),
])
def test_aggregate_values_inside_interval(
        api, observation_id, label, expected):
    # Ensure that a request for data inside an interval returns the whole
    # interval that contains that data.
    agg = deepcopy(VALID_AGG_JSON)
    agg['interval_label'] = label
    r1 = api.post('/aggregates/',
                  base_url=BASE_URL,
                  json=agg)
    assert r1.status_code == 201
    assert 'Location' in r1.headers
    aggregate_id = r1.get_data(as_text=True)

    payload = {'observations': [{
        'observation_id': observation_id,
        'effective_from': '2019-04-14 06:00:00Z'}]}
    api.post(f'/aggregates/{aggregate_id}/metadata',
             json=payload,
             base_url=BASE_URL)
    r3 = api.get(
        f'/aggregates/{aggregate_id}/values'
        '?start=2019-04-14T13:30Z&end=2019-04-14T13:59Z',
        headers={'Accept': 'application/json'},
        base_url=BASE_URL)
    values = r3.json['values']
    expected.update({'quality_flag': 0})
    assert len(values) == 1
    assert values[0] == expected


def test_aggregate_delete_obs(api, aggregate_id):
    obsid = '123e4567-e89b-12d3-a456-426655440000'
    r1 = api.get(f'/aggregates/{aggregate_id}/metadata',
                 base_url=BASE_URL)
    allobs = [o['observation_id'] for o in r1.json['observations']]
    assert obsid in allobs

    res = api.delete(f'/aggregates/{aggregate_id}/observations/{obsid}',
                     base_url=BASE_URL)
    assert res.status_code == 204

    r2 = api.get(f'/aggregates/{aggregate_id}/metadata',
                 base_url=BASE_URL)
    allobs = [o['observation_id'] for o in r2.json['observations']]
    assert obsid not in allobs


def test_aggregate_delete_obs_404_agg(api, missing_id):
    obsid = '123e4567-e89b-12d3-a456-426655440000'
    res = api.delete(f'/aggregates/{missing_id}/observations/{obsid}',
                     base_url=BASE_URL)
    assert res.status_code == 404


def test_aggregate_delete_obs_no_obs(api, missing_id, aggregate_id):
    res = api.delete(f'/aggregates/{aggregate_id}/observations/{missing_id}',
                     base_url=BASE_URL)
    assert res.status_code == 204  # no effect


def test_get_aggregate_values_all_none(api, aggregate_id):
    """Ensure that Null values are computed correctly. Regression test for
    GH 296
    """
    start = '20190101T0000Z'
    end = '20190201T0000Z'
    agg = demo_aggregates[aggregate_id]
    obs_data = pd.DataFrame(
        index=pd.date_range(start, end, freq='5T'),
        data={'value': None, 'quality_flag': 0},
    )
    obs_data['timestamp'] = obs_data.index.strftime('%Y%m%dT%H%MZ')
    value_payload = {'values': obs_data.to_dict(orient='records', )}
    for obs in agg['observations']:
        api.post(
            f'/observations/{obs["observation_id"]}/values?donotvalidate=true',
            base_url=BASE_URL,
            json=value_payload
        )
    res = api.get(f'/aggregates/{aggregate_id}/values?start={start}&end={end}',
                  headers={'Accept': 'application/json'},
                  base_url=BASE_URL)

    assert res.status_code == 200
    assert res.json['aggregate_id'] == aggregate_id
    values = res.json['values']
    for val in values:
        assert val['value'] is None
