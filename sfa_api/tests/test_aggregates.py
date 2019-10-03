from flask import _request_ctx_stack
import pytest


from sfa_api.conftest import BASE_URL


@pytest.fixture()
def api(sql_app_no_commit, mocker):
    def add_user():
        _request_ctx_stack.top.user = 'auth0|5be343df7025406237820b85'
        return True
    verify = mocker.patch('sfa_api.utils.auth.verify_access_token')
    verify.side_effect = add_user
    yield sql_app_no_commit.test_client()


@pytest.fixture()
def agg_json():
    return {
        "name": "Test Aggregate ghi",
        "variable": "ghi",
        "interval_label": "ending",
        "interval_length": 60,
        "aggregate_type": "sum",
        "extra_parameters": "extra",
        "description": "ghi agg",
        "timezone": "America/Denver"
    }


def test_post_aggregate_success(api, agg_json):
    res = api.post('/aggregates/',
                   base_url=BASE_URL,
                   json=agg_json)
    assert res.status_code == 201
    # assert 'Location' in res.headers


def test_get_all_aggregates(api):
    res = api.get('/aggregates/',
                  base_url=BASE_URL)
    assert res.status_code == 200
    resp = res.get_json()
    for agg in resp:
        assert 'observations' in agg


def test_get_aggregate_metadata(api, aggregate_id):
    res = api.get(f'/aggregates/{aggregate_id}/metadata',
                  base_url=BASE_URL)
    assert res.status_code == 200
    resp = res.get_json()
    assert 'aggregate_id' in resp
    assert 'variable' in resp
    assert 'observations' in resp
