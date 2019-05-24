import pytest


from flask import _request_ctx_stack


from sfa_api.conftest import BASE_URL


@pytest.fixture()
def api(sql_app, mocker):
    def add_user():
        _request_ctx_stack.top.user = 'auth0|5be343df7025406237820b85'
        return True

    verify = mocker.patch('sfa_api.utils.auth.verify_access_token')
    verify.side_effect = add_user
    yield sql_app.test_client()
