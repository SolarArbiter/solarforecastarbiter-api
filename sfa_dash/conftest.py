import os
import time

import pytest


from sfa_dash import create_app
import requests


@pytest.fixture(scope='session')
def auth_token():
    token_req = requests.post(
        'https://solarforecastarbiter.auth0.com/oauth/token',
        headers={'content-type': 'application/json'},
        data=('{"grant_type": "password", '
              '"username": "testing@solarforecastarbiter.org",'
              '"password": "Thepassword123!", '
              '"audience": "https://api.solarforecastarbiter.org", '
              '"client_id": "c16EJo48lbTCQEhqSztGGlmxxxmZ4zX7"}'))
    if token_req.status_code != 200:
        pytest.skip('Cannot retrieve valid Auth0 token')
    else:
        token = token_req.json()['access_token']
        return token


@pytest.fixture()
def expired_token(auth_token):
    stored = {'access_token': auth_token, 'expires_at': time.time() - 1, 'expires_in': 10799.98034, 'id_token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI6Ik5UZENSRGRFTlVNMk9FTTJNVGhCTWtRelFUSXpNRFF6TUVRd1JUZ3dNekV3T1VWR1FrRXpSUSJ9.eyJuaWNrbmFtZSI6InRlc3RpbmciLCJuYW1lIjoidGVzdGluZ0Bzb2xhcmZvcmVjYXN0YXJiaXRlci5vcmciLCJwaWN0dXJlIjoiaHR0cHM6Ly9zLmdyYXZhdGFyLmNvbS9hdmF0YXIvY2MxMTNkZjY5NmY4ZTlmMjA2Nzc5OTQzMzUxNzRhYjY_cz00ODAmcj1wZyZkPWh0dHBzJTNBJTJGJTJGY2RuLmF1dGgwLmNvbSUyRmF2YXRhcnMlMkZ0ZS5wbmciLCJ1cGRhdGVkX2F0IjoiMjAxOS0wNC0xMlQxNzoxMjoyMi41NzhaIiwiZW1haWwiOiJ0ZXN0aW5nQHNvbGFyZm9yZWNhc3RhcmJpdGVyLm9yZyIsImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwiaXNzIjoiaHR0cHM6Ly9zb2xhcmZvcmVjYXN0YXJiaXRlci5hdXRoMC5jb20vIiwic3ViIjoiYXV0aDB8NWJlMzQzZGY3MDI1NDA2MjM3ODIwYjg1IiwiYXVkIjoiUHJFMzlBZHRHTVBJNGdLMmhSdldaMmFEUmFyZnBnN0EiLCJpYXQiOjE1NTUwODkxNzIsImV4cCI6MTU1NTEyNTE3Mn0.dS6kjf9y0w78D92ARI_3bstq8XLAM0Jj2CbPM3G7SlTJJlAbyq9UYrsBQ9yZch9GHJvpVghKyTDhgQ2NJX-TrfTQ2rgmAEbFtFwaDjoNNwhEQaXsXh-8-sQD29nvBgYI8BIOL6Odbuot-QnRyz7w-XhXdYtgRugNzeZyA-4LaNerh6u-6XWvOtKnW21xx1q-C_bYxG8-D0g_ZcthtbLUdW9GqIL8HK7XteL3UOjwiy6VumprVZRcms01-GGZv2x6-yLDBSdc6t9R-E9NfOyAh6sPt7da84OC67bovbJVpsUzpHq0wV1Zm9ieg579sNEcZwfydd2JNOmFsDOTTYr9dA', 'scope': ['openid', 'profile', 'email'], 'token_type': 'Bearer'}  # NOQA
    return stored


@pytest.fixture()
def mocked_storage(mocker, expired_token):
    class fake_storage:
        def __init__(*args, **kwargs):
            pass

        def get(self, *args):
            return expired_token

        def set(self, *args):
            pass

        def delete(self, *args):
            pass
    storage = mocker.patch('sfa_dash.SessionStorage', new=fake_storage)
    return storage


@pytest.fixture()
def app(mocked_storage):
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    return create_app('sfa_dash.config.TestConfig')
