import math


import pytest


from sfa_api.conftest import (
    BASE_URL, copy_update, variables, agg_types,
    VALID_OBS_JSON)


AGG_JSON = {
        "name": "Test Aggregate ghi",
        "variable": "ghi",
        "interval_label": "ending",
        "interval_length": 60,
        "aggregate_type": "sum",
        "extra_parameters": "extra",
        "description": "ghi agg",
        "timezone": "America/Denver"
    }


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
                   json=AGG_JSON)
    assert res.status_code == 201
    assert 'Location' in res.headers


@pytest.mark.parametrize('payload,message', [
    (copy_update(AGG_JSON, 'variable', 'other'),
     f'{{"variable":["Must be one of: {variables}."]}}'),
    (copy_update(AGG_JSON, 'aggregate_type', 'cov'),
     f'{{"aggregate_type":["Must be one of: {agg_types}."]}}'),
    (copy_update(AGG_JSON, 'interval_label', 'instant'),
     '{"interval_label":["Must be one of: beginning, ending."]}'),
    ({}, '{"aggregate_type":["Missing data for required field."],"description":["Missing data for required field."],"interval_label":["Missing data for required field."],"interval_length":["Missing data for required field."],"name":["Missing data for required field."],"timezone":["Missing data for required field."],"variable":["Missing data for required field."]}')  # NOQA
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
                   json=AGG_JSON)
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


def test_update_aggregate_add_obs(api, aggregate_id):
    r1 = api.post('/observations/',
                  base_url=BASE_URL,
                  json=VALID_OBS_JSON)
    obs_id = r1.get_data(as_text=True)
    payload = {'observations': [{
        'observation_id': obs_id,
        'effective_from': '2029-01-01 01:23:00Z'}]}
    res = api.post(f'/aggregates/{aggregate_id}/metadata',
                   json=payload,
                   base_url=BASE_URL)
    assert res.status_code == 200
    r2 = api.get(f'/aggregates/{aggregate_id}/metadata',
                 base_url=BASE_URL)
    did = False
    for obs in r2.json['observations']:
        if obs['observation_id'] == obs_id:
            did = True
            assert obs['effective_from'] == (
                '2029-01-01T01:23:00+00:00')
    assert did


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
    ({}, '"observations":["Missing data for required field."]')
])
def test_update_aggregate_bad_req(api, aggregate_id, payload, intext):
    res = api.post(f'/aggregates/{aggregate_id}/metadata',
                   json=payload,
                   base_url=BASE_URL)
    assert res.status_code == 400
    assert intext in res.get_data(as_text=True)


def test_get_aggregate_values(api, aggregate_id):
    res = api.get(f'/aggregates/{aggregate_id}/values',
                  headers={'Accept': 'application/json'},
                  base_url=BASE_URL)
    assert res.status_code == 200
    assert res.json['aggregate_id'] == aggregate_id
    assert 'values' in res.json
    assert 'timestamp' in res.json['values'][0]
    assert 'value' in res.json['values'][0]
    assert 'quality_flag' in res.json['values'][0]


def test_get_aggregate_values_csv(api, aggregate_id):
    res = api.get(f'/aggregates/{aggregate_id}/values',
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


def test_get_aggregate_values_422(api, aggregate_id):
    payload = {'observations': [{
        'observation_id': '123e4567-e89b-12d3-a456-426655440000',
        'effective_until': '2019-01-01 01:23:00Z'}]}
    res = api.post(f'/aggregates/{aggregate_id}/metadata',
                   json=payload,
                   base_url=BASE_URL)
    assert res.status_code == 200
    res = api.get(f'/aggregates/{aggregate_id}/values',
                  headers={'Accept': 'application/json'},
                  base_url=BASE_URL)
    assert res.status_code == 422
    assert 'missing keys 123e4567-e89b-12d3-a456-426655440000' in res.get_data(
        as_text=True)


def test_get_aggregate_values_obs_deleted(api, aggregate_id, missing_id):
    res = api.delete('/observations/123e4567-e89b-12d3-a456-426655440000',
                     base_url=BASE_URL)
    assert res.status_code == 204
    res = api.get(f'/aggregates/{aggregate_id}/values',
                  headers={'Accept': 'application/json'},
                  base_url=BASE_URL)
    assert res.status_code == 422


def test_get_aggregate_values_limited_effective(api, aggregate_id):
    payload = {'observations': [{
        'observation_id': '123e4567-e89b-12d3-a456-426655440000',
        'effective_until': '2019-04-17 01:23:00Z'}]}
    res = api.post(f'/aggregates/{aggregate_id}/metadata',
                   json=payload,
                   base_url=BASE_URL)
    assert res.status_code == 200
    res = api.get(f'/aggregates/{aggregate_id}/values',
                  headers={'Accept': 'application/json'},
                  base_url=BASE_URL)
    assert res.status_code == 200
    assert not math.isnan(res.json['values'][-1]['value'])


def test_get_aggregate_values_404(api, missing_id):
    res = api.get(f'/aggregates/{missing_id}/values',
                  headers={'Accept': 'application/json'},
                  base_url=BASE_URL)
    assert res.status_code == 404


def test_get_aggregate_forecasts(api, aggregate_id):
    res = api.get(f'/aggregates/{aggregate_id}/forecasts/single',
                  base_url=BASE_URL)
    assert res.status_code == 200
    assert isinstance(res.get_json(), list)


def test_get_aggregate_cdf_forecast_groups(api, aggregate_id):
    res = api.get(f'/aggregates/{aggregate_id}/forecasts/cdf',
                  base_url=BASE_URL)
    assert res.status_code == 200
    assert isinstance(res.get_json(), list)
