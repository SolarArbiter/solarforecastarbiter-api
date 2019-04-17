import pytest
from oauthlib.oauth2.rfc6749.errors import InvalidClientIdError


@pytest.fixture()
def no_refresh_token(mocker):
    ref = mocker.patch(
        'requests_oauthlib.oauth2_session.OAuth2Session.refresh_token')
    return ref


def test_token_refresh_invalid_clientid_error(app, mocker, no_refresh_token):
    """Test redirect to login when refreshing an expired token fails with
    InvalidClientIdError"""
    no_refresh_token.side_effect = InvalidClientIdError
    handler = mocker.patch('sfa_dash.error_handlers.bad_oauth_token')
    with app.test_client() as webapp:
        get = webapp.get('/observations/', base_url='http://localhost',
                         follow_redirects=False)
    assert get.status_code == 302
    assert get.headers['Location'] == 'http://localhost/login/auth0'
    handler.assert_called
