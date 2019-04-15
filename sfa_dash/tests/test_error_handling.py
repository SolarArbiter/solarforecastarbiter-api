import pytest


from oauthlib.oauth2.rfc6749.errors import InvalidClientIdError


@pytest.fixture()
def mocked_get(mocker):
    get = mocker.patch('sfa_dash.api_interface.get_request')
    get.side_effect = InvalidClientIdError()
    return get


def test_token_refresh_error(app, mocked_storage):
    with app.test_client() as webapp:
        req = webapp.get('/observations/')
    assert req.status_code == 302


def test_token_refresh_error_handler_called(app, mocked_storage, mocker):
    handler = mocker.patch('sfa_dash.error_handlers.no_refresh_token')
    with app.test_client() as webapp:
        get = webapp.get('/observations/', base_url='http://localhost')
    assert get.status_code == 302
    handler.assert_called
