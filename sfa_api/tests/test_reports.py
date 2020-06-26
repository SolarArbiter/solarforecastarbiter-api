from copy import deepcopy
import hashlib
import math


import pytest
from solarforecastarbiter.datamodel import (
    ALLOWED_CATEGORIES)


from sfa_api.conftest import BASE_URL
from sfa_api.schema import ALLOWED_METRICS


@pytest.fixture()
def new_report(api, report_post_json, mocked_queuing):
    def fn(rpj=report_post_json):
        res = api.post('/reports/',
                       base_url=BASE_URL,
                       json=rpj)
        return res.data.decode()
    return fn


def test_post_report(api, report_post_json, mocked_queuing):
    res = api.post('/reports/',
                   base_url=BASE_URL,
                   json=report_post_json)
    assert res.status_code == 201
    assert 'Location' in res.headers


def test_get_report(api, new_report):
    report_id = new_report()
    res = api.get(f'/reports/{report_id}',
                  base_url=BASE_URL)
    assert res.status_code == 200
    report = res.json
    assert 'report_id' in report
    assert 'provider' in report
    assert 'raw_report' in report
    assert 'status' in report
    assert 'created_at' in report
    assert 'modified_at' in report
    assert report['created_at'].endswith('+00:00')
    assert report['modified_at'].endswith('+00:00')


@pytest.fixture(
    params=['constant', 'datetime', 'timeofday', 'errorband', 'many'])
def report_post_json_cost(report_post_json, request):
    repdict = deepcopy(report_post_json)
    repdict['report_parameters']['object_pairs'][0]['cost'] = 'testcost'

    costsparams = {
        'constant': {
            'cost': 10.9,
            'net': False,
            'aggregation': 'mean'
        },
        'datetime': {
            'cost': [10.9, 11],
            'times': ['2020-04-05T00:23Z', '2020-05-12T12:33-07:00'],
            'fill': 'forward',
            'net': False,
            'aggregation': 'mean',
            'timezone': 'Etc/GMT-5'
        },
        'timeofday': {
            'cost': [10.9, 11, 33],
            'times': ['12:00', '06:33', '14:00'],
            'fill': 'backward',
            'net': True,
            'aggregation': 'sum',
            'timezone': 'Etc/GMT-5'
        },
    }
    if request.param in costsparams:
        repdict['report_parameters']['costs'] = [
            {'name': 'testcost', 'type': request.param,
             'parameters': costsparams[request.param]}
        ]
    elif request.param == 'errorband':
        repdict['report_parameters']['costs'] = [
            {'name': 'testcost', 'type': 'errorband',
             'parameters': {'bands': [
                 {'error_range': [1, 2],
                  'cost_function': 'constant',
                  'cost_function_parameters': costsparams['constant']},
                 {'error_range': ['-inf', 2],
                  'cost_function': 'constant',
                  'cost_function_parameters': costsparams['constant']},
                 {'error_range': [2, 4],
                  'cost_function': 'datetime',
                  'cost_function_parameters': costsparams['datetime']},
                 {'error_range': [3, math.inf],
                  'cost_function': 'timeofday',
                  'cost_function_parameters': costsparams['timeofday']},
             ]}}]
    elif request.param == 'many':
        repdict['report_parameters']['costs'] = [
            {'name': 'testcost', 'type': 'constant',
             'parameters': costsparams['constant']},
            {'name': 'othercost', 'type': 'timeofday',
             'parameters': costsparams['timeofday']}
        ]
    return repdict


def test_post_report_cost(api, report_post_json_cost,
                          mocked_queuing):
    res = api.post('/reports/',
                   base_url=BASE_URL,
                   json=report_post_json_cost)
    assert res.status_code == 201
    assert 'Location' in res.headers


def test_get_report_cost(api, new_report,
                         report_post_json_cost):
    report_id = new_report(report_post_json_cost)
    res = api.get(f'/reports/{report_id}',
                  base_url=BASE_URL)
    assert res.status_code == 200
    report = res.json
    assert 'report_id' in report
    assert 'provider' in report
    assert 'raw_report' in report
    assert 'status' in report
    assert 'created_at' in report
    assert 'modified_at' in report
    assert report['created_at'].endswith('+00:00')
    assert report['modified_at'].endswith('+00:00')
    assert len(report['report_parameters']['costs']) > 0


def test_get_report_dne(api, missing_id):
    res = api.get(f'/reports/{missing_id}',
                  base_url=BASE_URL)
    assert res.status_code == 404


@pytest.mark.parametrize('status, code', [
    ('complete', 204),
    ('failed', 204),
    ('completed', 400),
    ('invalid_status', 400),
])
def test_set_status(api, new_report, status, code):
    report_id = new_report()
    res = api.post(f'/reports/{report_id}/status/{status}',
                   base_url=BASE_URL)
    assert res.status_code == code


REPORT_VALUESET = [
    "['replace', 'with', 'real', 'data']",
]


@pytest.mark.parametrize('values', REPORT_VALUESET)
def test_post_report_values(api, new_report, values, report_post_json):
    report_id = new_report()
    object_pairs = report_post_json['report_parameters']['object_pairs']
    obj_id = object_pairs[0]['observation']
    report_values = {
        'object_id': obj_id,
        'processed_values': values,
    }
    res = api.post(f'/reports/{report_id}/values',
                   base_url=BASE_URL,
                   json=report_values)
    assert res.status_code == 201
    value_id = res.data.decode()
    values_res = api.get(
        f'/reports/{report_id}',
        base_url=BASE_URL)
    report_with_values = values_res.get_json()
    assert report_with_values['values'][0]['id'] == value_id


@pytest.mark.parametrize('values', REPORT_VALUESET[:1])
def test_post_report_values_bad_uuid(api, new_report, values):
    report_id = new_report()
    obj_id = 'bad_uuid'
    report_values = {
        'object_id': obj_id,
        'processed_values': values,
    }
    res = api.post(f'/reports/{report_id}/values',
                   base_url=BASE_URL,
                   json=report_values)
    assert res.status_code == 400
    expected = '{"errors":{"object_id":["Not a valid UUID."]}}\n'
    assert res.get_data(as_text=True) == expected


@pytest.mark.parametrize('values', REPORT_VALUESET)
def test_read_report_values(api, new_report, values, report_post_json):
    report_id = new_report()
    object_pairs = report_post_json['report_parameters']['object_pairs']
    obj_id = object_pairs[0]['observation']

    report_values = {
        'object_id': obj_id,
        'processed_values': values,
    }
    res = api.post(f'/reports/{report_id}/values',
                   base_url=BASE_URL,
                   json=report_values)
    assert res.status_code == 201
    value_id = res.data.decode()
    values_res = api.get(
        f'/reports/{report_id}/values',
        base_url=BASE_URL)
    report_values = values_res.get_json()
    assert isinstance(report_values, list)
    assert report_values[0]['id'] == value_id
    assert report_values[0]['processed_values'] == values


def test_post_raw_report(api, new_report, raw_report_json):
    report_id = new_report()
    res = api.post(f'/reports/{report_id}/raw',
                   base_url=BASE_URL,
                   json=raw_report_json)
    assert res.status_code == 204
    full_res = api.get(f'/reports/{report_id}',
                       base_url=BASE_URL)
    report_with_raw = full_res.get_json()
    assert report_with_raw['raw_report'] == raw_report_json


@pytest.mark.parametrize('chksum', [
    hashlib.sha256(b'asdf').hexdigest(),
    pytest.param('tooshort', marks=pytest.mark.xfail(strict=True)),
    pytest.param('bad??$', marks=pytest.mark.xfail(strict=True))
])
def test_post_raw_report_chksum(api, new_report, raw_report_json, chksum):
    report_id = new_report()
    post = raw_report_json
    post['data_checksum'] = chksum
    res = api.post(f'/reports/{report_id}/raw',
                   base_url=BASE_URL,
                   json=post)
    assert res.status_code == 204
    full_res = api.get(f'/reports/{report_id}',
                       base_url=BASE_URL)
    report_with_raw = full_res.get_json()
    assert report_with_raw['raw_report'] == post


def test_delete_report(api, new_report):
    report_id = new_report()
    res = api.get(f'/reports/{report_id}',
                  base_url=BASE_URL)
    assert res.status_code == 200
    delete = api.delete(f'/reports/{report_id}',
                        base_url=BASE_URL)
    assert delete.status_code == 204
    res = api.get(f'/reports/{report_id}',
                  base_url=BASE_URL)
    assert res.status_code == 404


def test_list_reports(api, new_report):
    new_report()
    new_report()
    new_report()
    reports = api.get('/reports/', base_url=BASE_URL)
    reports_list = reports.get_json()
    # one more as test already in db
    assert len(reports_list) == 4


metrics_list = ", ".join(list(ALLOWED_METRICS.keys()))
categories_list = ", ".join(list(ALLOWED_CATEGORIES.keys()))


@pytest.mark.parametrize('key,value,error', [
    ('name', 'r' * 70, '["Longer than maximum length 64."]'),
    ('start', 'invalid_date',
     '["Not a valid datetime."]'),
    ('end', 'invalid_date',
     '["Not a valid datetime."]'),
    ('object_pairs', '[{"wrongtuple"},{}]',
     '["Invalid type."]'),
    ('object_pairs', [{"observation": "x", "forecast": "y"}],
     '{"0":{"forecast":["Not a valid UUID."],'
     '"observation":["Not a valid UUID."]}}'),
    ('object_pairs', [{"observation": "123e4567-e89b-12d3-a456-426655440000",
                       "forecast": "123e4567-e89b-12d3-a456-426655440000",
                       "aggregate": "123e4567-e89b-12d3-a456-426655440000"}],
     '{"0":{"_schema":["Only specify one of observation or aggregate"]}}'),
    ('object_pairs', [{"forecast": "123e4567-e89b-12d3-a456-426655440000"}],
     '{"0":{"_schema":["Specify one of observation or aggregate"]}}'),
    ('filters', 'not a list',
     '["Not a valid list."]'),
    ('metrics', ["bad"],
        f'{{"0":["Must be one of: {metrics_list}."]}}'),
    ('categories', ["bad"],
        f'{{"0":["Must be one of: {categories_list}."]}}'),
    ('object_pairs', [{"observation": "123e4567-e89b-12d3-a456-426655440000",
                       "forecast": "123e4567-e89b-12d3-a456-426655440000",
                       "cost": "nocost"}],
     '{"0":{"cost":["Must specify a \'cost\' that is present in report parameters \'costs\'"]}}'),  # NOQA: E501
    ('metrics', ['mae', 'cost'],
     '["Must specify \'costs\' parameters to calculate cost metric"]')
])
def test_post_report_invalid_report_params(
        api, key, value, error, report_post_json):
    payload = deepcopy(report_post_json)
    payload['report_parameters'][key] = value
    res = api.post('/reports/', base_url=BASE_URL, json=payload)
    assert res.status_code == 400
    expected = ('{"errors":{"report_parameters":[{"%s":%s}]}}\n' %
                (key, error))
    assert res.get_data(as_text=True) == expected


def test_recompute(api, new_report):
    report_id = new_report()
    res = api.get(f'/reports/{report_id}/recompute', base_url=BASE_URL)
    assert res.status_code == 200
    assert res.data.decode('utf-8') == report_id
    assert 'Location' in res.headers


def test_recompute_report_dne(api, missing_id):
    res = api.get(f'/reports/{missing_id}/recompute', base_url=BASE_URL)
    assert res.status_code == 404


def test_recompute_report_no_update(api, new_report, remove_all_perms):
    report_id = new_report()
    remove_all_perms('update', 'reports')
    res = api.get(f'/reports/{report_id}/recompute', base_url=BASE_URL)
    assert res.status_code == 404


def test_post_report_alt_url(api, report_post_json, mocked_queuing,
                             mocker, app):
    mocker.patch.dict(app.config, {'JOB_BASE_URL': 'http://0.0.0.1'})
    res = api.post('/reports/',
                   base_url=BASE_URL,
                   json=report_post_json)
    assert res.status_code == 201
    assert 'Location' in res.headers
    assert mocked_queuing.call_args[1]['base_url'] == 'http://0.0.0.1'
