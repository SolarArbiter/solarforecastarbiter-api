import pytest
import requests


from sfa_api.utils import auth


@pytest.fixture()
def valid_auth(app, auth_token):
    with app.test_request_context(
            headers={'Authorization': f'Bearer {auth_token}'}):
        yield


def test_verify_access_token(valid_auth, auth_token):
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


def test_verify_access_token_bad_audience(app, valid_auth):
    app.config['AUTH0_AUDIENCE'] = ''
    assert not auth.verify_access_token()


def test_verify_access_token_bad_issuer(app, valid_auth):
    app.config['AUTH0_BASE_URL'] = ''
    assert not auth.verify_access_token()


def test_verify_access_token_bad_key(app, valid_auth):
    app.config['JWT_KEY'] = {}
    assert not auth.verify_access_token()


def test_requires_auth(valid_auth):
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
