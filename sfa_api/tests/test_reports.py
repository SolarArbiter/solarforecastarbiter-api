import pytest


from copy import deepcopy
from flask import _request_ctx_stack
import json
from sfa_api.conftest import BASE_URL, REPORT_POST_JSON


@pytest.fixture()
def api(sql_app_no_commit, mocker):
    def add_user():
        _request_ctx_stack.top.user = 'auth0|5be343df7025406237820b85'
        return True
    verify = mocker.patch('sfa_api.utils.auth.verify_access_token')
    verify.side_effect = add_user
    yield sql_app_no_commit.test_client()


@pytest.fixture()
def report_json():
    return REPORT_POST_JSON


@pytest.fixture()
def new_report(api, report_json):
    def fn():
        res = api.post('/reports/',
                       base_url=BASE_URL,
                       json=report_json)
        return res.data.decode()
    return fn


def test_post_report(api, report_json):
    res = api.post('/reports/',
                   base_url=BASE_URL,
                   json=REPORT_POST_JSON)
    assert res.status_code == 201
    assert 'Location' in res.headers


def test_get_report(api, new_report):
    report_id = new_report()
    res = api.get(f'/reports/{report_id}',
                  base_url=BASE_URL)
    assert res.status_code == 200


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
def test_post_report_values(api, new_report, values):
    report_id = new_report()
    # TODO: fix with final format
    obj_id = REPORT_POST_JSON['report_parameters']['object_pairs'][0][0]
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


def test_post_metrics(api, new_report):
    report_id = new_report()
    # TODO: fix with final format
    payload = { 
        'metrics' : {'MAE': 'data', 'RMSE': 'data'},
        'raw_report': '<p>hello</p>',
    }
    res = api.post(f'/reports/{report_id}/metrics',
                   base_url=BASE_URL,
                   json=payload)
    assert res.status_code == 204
    metrics_res = api.get(f'/reports/{report_id}',
                          base_url=BASE_URL)
    report_with_metrics = metrics_res.get_json()
    assert json.loads(report_with_metrics['metrics']) == payload['metrics']
    assert report_with_metrics['raw_report'] == payload['raw_report']


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
    assert len(reports_list) == 3


@pytest.mark.parametrize('key,value,error', [
    ('start', 'invalid_date',
     '["Not a valid datetime."]'),
    ('end', 'invalid_date',
     '["Not a valid datetime."]'),
    ('object_pairs', '[("wrongtuple"),()]',
     '["Not a valid list."]'),
    ('filters', 'not a list',
     '["Not a valid list."]'),
    ('metrics', ["bad"],
     '{"0":["Must be one of: MAE, RMSE."]}'),
])
def test_post_report_invalid_report_params(
        api, key, value, error, report_json):
    payload = deepcopy(report_json)
    payload['report_parameters'][key] = value
    res = api.post('/reports/', base_url=BASE_URL, json=payload)
    assert res.status_code == 400
    expected = ('{"errors":{"report_parameters":[{"%s":%s}]}}\n' %
                (key, error))
    assert res.get_data(as_text=True) == expected


def test_post_report_values_invalid_params(api):
    # add tests after format is decided
    pass
