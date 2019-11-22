import re


import pytest
from redis import Redis
import requests


from sfa_api.utils import auth0_info


@pytest.fixture()
def running_app(app):
    with app.app_context():
        yield app


def test_token_redis_connection(running_app):
    r = auth0_info.token_redis_connection()
    assert isinstance(r, Redis)


def test_get_fresh_auth0_management_token(running_app, requests_mock):
    mocked = requests_mock.register_uri(
        'POST', 'https://solarforecastarbiter.auth0.com/oauth/token',
        content=b'{"access_token": "token"}')
    token = auth0_info.get_fresh_auth0_management_token()
    assert token == 'token'
    hist = mocked.request_history
    assert len(hist) == 1
    req_json = hist[0].json()
    assert req_json['grant_type'] == 'client_credentials'
    for k in ('client_id', 'client_secret', 'audience'):
        assert k in req_json


@pytest.mark.parametrize('empty', (
    'AUTH0_CLIENT_ID', 'AUTH0_CLIENT_SECRET',
    'AUTH0_CLIENT_ID,AUTH0_CLIENT_SECRET'))
def test_get_fresh_auth0_management_token_config_fail(
        running_app, empty):
    for k in empty.split(','):
        running_app.config[k] = ''
    with pytest.raises(ValueError):
        auth0_info.get_fresh_auth0_management_token()


def test_get_fresh_auth0_management_token_http_err(running_app, requests_mock):
    requests_mock.register_uri(
        'POST', 'https://solarforecastarbiter.auth0.com/oauth/token',
        status_code=401)
    with pytest.raises(requests.HTTPError):
        auth0_info.get_fresh_auth0_management_token()


def test_check_if_token_is_valid_none(running_app):
    assert auth0_info.check_if_token_is_valid(None) is None


def test_check_if_token_is_valid_true(running_app, mocker):
    mocker.patch('sfa_api.utils.auth0_info.jwt.decode')
    assert auth0_info.check_if_token_is_valid('token')


def test_check_if_token_is_valid_fail(running_app):
    assert not auth0_info.check_if_token_is_valid('token')


def test_check_if_token_is_valid_bad_audience(running_app, auth_token):
    assert not auth0_info.check_if_token_is_valid(auth_token)


def test_auth0_token_in_redis(running_app, mocker):
    r = auth0_info.token_redis_connection()
    r.set('auth0_token', 'thetoken')
    mocker.patch('sfa_api.utils.auth0_info.check_if_token_is_valid',
                 return_value=True)
    assert auth0_info.auth0_token() == 'thetoken'


def test_auth0_token_not_in_redis(running_app, mocker):
    mocker.patch(
        'sfa_api.utils.auth0_info.get_fresh_auth0_management_token',
        return_value='atoken')
    assert auth0_info.auth0_token() == 'atoken'
    r = auth0_info.token_redis_connection()
    r.get('auth0_token') == 'atoken'


@pytest.mark.parametrize('se', [ValueError, requests.HTTPError])
def test_auth0_token_no_fresh(running_app, mocker, se):
    log = mocker.patch('sfa_api.utils.auth0_info.logger.error')
    mocker.patch(
        'sfa_api.utils.auth0_info.get_fresh_auth0_management_token',
        side_effect=se)
    assert auth0_info.auth0_token() is None
    r = auth0_info.token_redis_connection()
    r.get('auth0_token') is None
    assert log.called


@pytest.mark.parametrize('val', [
    'no', 'auth0other',
    pytest.param('auth0|4882lxjlsd0', marks=pytest.mark.xfail)
])
def test__verify_auth0_id(val):
    with pytest.raises(ValueError):
        auth0_info._verify_auth0_id(val)


@pytest.fixture()
def auth0id():
    return 'auth0|5be343df7025406237820b85'


@pytest.fixture()
def email():
    return 'testing@solarforecastarbiter.org'


@pytest.fixture()
def email_in_redis(auth0id, email, running_app):
    r = auth0_info.token_redis_connection()
    r.set(auth0id, email)
    r.set(email, auth0id)


@pytest.fixture()
def token_set(running_app, mocker):
    mocker.patch('sfa_api.utils.auth0_info.auth0_token',
                 return_value='token')


def test_get_email_of_user(
        running_app, auth0id, email, requests_mock, token_set):
    requests_mock.register_uri(
        'GET',
        re.compile(running_app.config['AUTH0_BASE_URL'] + '/.*'),
        content=f'{{"email": "{email}"}}'.encode())
    out = auth0_info.get_email_of_user(auth0id)
    assert out == email
    r = auth0_info.token_redis_connection()
    assert r.get(auth0id) == email
    assert 90000 > r.ttl(auth0id) > 80000


def test_get_email_of_user_in_redis(running_app, auth0id, email,
                                    email_in_redis, token_set):
    assert auth0_info.get_email_of_user(auth0id) == email


def test_get_email_of_user_bad_id(running_app):
    with pytest.raises(ValueError):
        auth0_info.get_email_of_user('badid')


def test_get_email_of_user_http_err(running_app, auth0id,
                                    requests_mock, token_set):
    requests_mock.register_uri(
        'GET',
        re.compile(running_app.config['AUTH0_BASE_URL'] + '/.*'),
        status_code=401)
    out = auth0_info.get_email_of_user(auth0id)
    assert out == 'Unable to retrieve'


def test_list_user_emails(running_app, auth0id, email,
                          requests_mock, token_set,
                          email_in_redis):
    requests_mock.register_uri(
        'GET',
        re.compile(running_app.config['AUTH0_BASE_URL'] + '/.*'),
        [{'content': b'{"email": "second"}'},
         {'content': b'{"email": "third"}'},
         {'content': b'', 'status_code': 401}]
    )
    ids = [auth0id, 'auth0|one', 'auth0|ooasdd', 'auth0|what']
    out = auth0_info.list_user_emails(ids)
    assert set(out.values()) == {
        email, 'second', 'third', 'Unable to retrieve'}


def test_list_user_emails_invalid(running_app, auth0id):
    ids = [auth0id, 'auth0|one', 'auth0|ooasdd', 'auth0|what',
           'bad']
    with pytest.raises(ValueError):
        auth0_info.list_user_emails(ids)


def test_get_auth0_id_of_user(
        running_app, auth0id, email, requests_mock, token_set):
    requests_mock.register_uri(
        'GET',
        re.compile(running_app.config['AUTH0_BASE_URL'] + '/.*'),
        content=f'[{{"user_id": "{auth0id}"}}]'.encode())
    out = auth0_info.get_auth0_id_of_user(email)
    assert out == auth0id
    r = auth0_info.token_redis_connection()
    assert r.get(email) == auth0id
    assert 90000 > r.ttl(email) > 80000


def test_get_auth0_id_of_user_in_redis(running_app, auth0id, email,
                                       email_in_redis, token_set):
    assert auth0_info.get_auth0_id_of_user(email) == auth0id


def test_get_auth0_id_of_user_http_err(running_app, email,
                                       requests_mock, token_set):
    requests_mock.register_uri(
        'GET',
        re.compile(running_app.config['AUTH0_BASE_URL'] + '/.*'),
        status_code=401)
    out = auth0_info.get_auth0_id_of_user(email)
    assert out == 'Unable to retrieve'


def test_get_auth0_id_of_user_empty(running_app, email,
                                    requests_mock, token_set):
    requests_mock.register_uri(
        'GET',
        re.compile(running_app.config['AUTH0_BASE_URL'] + '/.*'),
        content=b'[]')
    out = auth0_info.get_auth0_id_of_user(email)
    assert out == 'Unable to retrieve'


def test_random_password():
    p1 = auth0_info.random_password()
    p2 = auth0_info.random_password()
    assert p1 != p2
    assert 32 <= len(p1) <= 48
    assert 32 <= len(p2) <= 48


def test_create_user(running_app, requests_mock, token_set):
    mocked = requests_mock.register_uri(
        'POST', re.compile(running_app.config['AUTH0_BASE_URL'] + '/.*'),
        content=b'{"user_id": "auth0|theuser"}')
    out = auth0_info.create_user('anemail', 'password')
    assert out == 'auth0|theuser'
    hist = mocked.request_history
    assert len(hist) == 1
    req_json = hist[0].json()
    assert req_json['email'] == 'anemail'
    assert req_json['password'] == 'password'
    assert not req_json['email_verified']


def test_create_user_fail(running_app, requests_mock, token_set):
    requests_mock.register_uri(
        'POST', re.compile(running_app.config['AUTH0_BASE_URL'] + '/.*'),
        status_code=400)
    with pytest.raises(requests.HTTPError):
        auth0_info.create_user('anemail', 'password')


def test_get_refresh_token(running_app, requests_mock, token_set):
    mocked = requests_mock.register_uri(
        'POST', re.compile(running_app.config['AUTH0_BASE_URL'] + '/.*'),
        content=b'{"refresh_token": "token"}')
    out = auth0_info.get_refresh_token('anemail', 'password')
    assert out == 'token'
    hist = mocked.request_history
    assert len(hist) == 1
    req_json = hist[0].json()
    assert req_json['username'] == 'anemail'
    assert req_json['password'] == 'password'
    assert req_json['scope'] == 'offline_access'


def test_get_refresh_token_fail(running_app, requests_mock, token_set):
    requests_mock.register_uri(
        'POST', re.compile(running_app.config['AUTH0_BASE_URL'] + '/.*'),
        status_code=400)
    with pytest.raises(requests.HTTPError):
        auth0_info.get_refresh_token('anemail', 'password')


def test_exchange_refresh_token(running_app, requests_mock, token_set):
    mocked = requests_mock.register_uri(
        'POST', re.compile(running_app.config['AUTH0_BASE_URL'] + '/.*'),
        content=b'{"access_token": "acctoken"}')
    out = auth0_info.exchange_refresh_token('thetoken')
    assert out == 'acctoken'
    hist = mocked.request_history
    assert len(hist) == 1
    req_json = hist[0].json()
    assert req_json['grant_type'] == 'refresh_token'
    assert req_json['refresh_token'] == 'thetoken'


def test_exchange_refresh_token_fail(running_app, requests_mock, token_set):
    requests_mock.register_uri(
        'POST', re.compile(running_app.config['AUTH0_BASE_URL'] + '/.*'),
        status_code=400)
    with pytest.raises(requests.HTTPError):
        auth0_info.exchange_refresh_token('token')
