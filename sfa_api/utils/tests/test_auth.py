import pytest
from json.decoder import JSONDecodeError

from sfa_api.utils import auth


@pytest.fixture()
def existing_user(mocker):
    user_check = mocker.patch('sfa_api.utils.auth.validate_user_existence')
    user_check.return_value = True
    return user_check


@pytest.fixture()
def valid_auth(app, auth_token):
    with app.test_request_context(
            headers={'Authorization': f'Bearer {auth_token}'}):
        yield


def test_verify_access_token(valid_auth, auth_token, existing_user):
    assert auth.verify_access_token()
    assert auth.current_user == 'auth0|5be343df7025406237820b85'


def test_verify_access_token_expired(app):
    old_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI6Ik5UZENSRGRFTlVNMk9FTTJNVGhCTWtRelFUSXpNRFF6TUVRd1JUZ3dNekV3T1VWR1FrRXpSUSJ9.eyJpc3MiOiJodHRwczovL3NvbGFyZm9yZWNhc3RhcmJpdGVyLmF1dGgwLmNvbS8iLCJzdWIiOiJhdXRoMHw1YmUzNDNkZjcwMjU0MDYyMzc4MjBiODUiLCJhdWQiOlsiaHR0cHM6Ly9hcGkuc29sYXJmb3JlY2FzdGFyYml0ZXIub3JnIiwiaHR0cHM6Ly9zb2xhcmZvcmVjYXN0YXJiaXRlci5hdXRoMC5jb20vdXNlcmluZm8iXSwiaWF0IjoxNTU0MjI3MDk5LCJleHAiOjE1NTQyMzc4OTksImF6cCI6ImMxNkVKbzQ4bGJUQ1FFaHFTenRHR2xteHh4bVo0elg3Iiwic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSIsImd0eSI6InBhc3N3b3JkIn0.WwV3UwX7F22SmLXWRzA7bWcrUCIN2u6e8Zwj2fEjc-d8NUBelRIC2v7nw3L-Ezg9-Ao8BTB8Ned7V5k11DmuiLzjdlOB7-4UhUZGgOGx1Vg2520JvzbljqAQqWLhqdTP2UcQwjO6ffNwTQ5rJLBxhMaUO_85FpvS9ghey3Esj_ZPPk17TZ67TtXHDBaCOr0KZxHJcY5AqRHbQ5mQ6hW6tPqMj-sIqoIhXXBt69M5KuZ0Lb4Gky49DKlPRJ9EGNTOeiNYC4FyY1kmYrRKUkcteLNmHrjCwXmg9_5pTy9xzckaGBzEN1EnaWWzmgu_IhL39CNzrPeqRwo1A-AMv4Pp2A'  # NOQA
    with app.test_request_context(
            headers={'Authorization': f'Bearer {old_token}'}):
        assert not auth.verify_access_token()


def test_verify_access_token_invalid(app):
    with app.test_request_context(
            headers={'Authorization': 'Bearer TOKEN'}):
        assert not auth.verify_access_token()


def test_verify_access_token_no_token(app):
    with app.test_request_context(
            headers={'Authorization': 'Bearer'}):
        assert not auth.verify_access_token()


def test_verify_access_token_bad_audience(app, valid_auth):
    app.config['AUTH0_AUDIENCE'] = ''
    assert not auth.verify_access_token()


def test_verify_access_token_bad_issuer(app, valid_auth):
    app.config['AUTH0_BASE_URL'] = ''
    assert not auth.verify_access_token()


def test_verify_access_token_bad_key(app, valid_auth):
    app.config['JWT_KEY'] = {}
    assert not auth.verify_access_token()


def test_requires_auth(valid_auth, existing_user):
    @auth.requires_auth
    def func():
        return 'GOOD'
    assert func() == 'GOOD'


def test_requires_auth_no_auth(app):
    @auth.requires_auth
    def func():
        return 'GOOD'

    with app.test_request_context():
        resp = func()
        assert resp.status_code == 401
        assert 'WWW-Authenticate' in resp.headers


@pytest.fixture()
def mocked_user_exists_storage(mocker):
    def fn(user_exists=True, verified=False, no_auth0=False):
        mock_storage = mocker.patch('sfa_api.utils.storage.get_storage')
        mock_storage.user_exists = mocker.Mock(return_value=user_exists)
        mock_storage.create_new_user = mocker.Mock()
        mock_storage.return_value = mock_storage

        user_info = mocker.patch('sfa_api.utils.auth.request_user_info')
        if no_auth0:
            user_info.side_effect = JSONDecodeError('error', '{}', 1)
        else:
            user_info.return_value = {'email_verified': verified}
        return (mock_storage.user_exists, user_info,
                mock_storage.create_new_user)
    return fn


@pytest.mark.parametrize('user_exists,verified,no_auth0', [
    (True, False, False),
    (False, False, True),
    (False, True, False),
    (False, False, False),
])
def test_validate_user_existence(app, mocked_user_exists_storage,
                                 user_exists, verified, no_auth0):
    exists, user_info, create_user = mocked_user_exists_storage(
        user_exists=user_exists, verified=verified, no_auth0=no_auth0)
    with app.test_request_context():
        existence = auth.validate_user_existence()
        if not user_exists:
            user_info.assert_called()
            if no_auth0:
                create_user.assert_not_called()
                assert existence is False
            if verified:
                create_user.assert_called()
                assert existence is True
            else:
                create_user.assert_not_called()
                assert existence is False
        else:
            assert existence is True
            exists.assert_called()


def test_request_user_info(sql_app, auth_token, user_id):
    ctx = sql_app.test_request_context()
    ctx.access_token = auth_token
    ctx.push()
    user_info = auth.request_user_info()
    assert user_info['name'] == 'testing@solarforecastarbiter.org'
    assert user_info['sub'] == 'auth0|5be343df7025406237820b85'
    ctx.pop()


def test_request_user_info_failure(sql_app, user_id):
    ctx = sql_app.test_request_context()
    ctx.push()
    user_info = auth.request_user_info()
    assert user_info == {}
    ctx.pop()
