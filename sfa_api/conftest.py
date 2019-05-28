from contextlib import contextmanager
from functools import partial


from flask import _request_ctx_stack
import pytest
import pymysql
import requests


from sfa_api import create_app
from sfa_api.utils import storage_interface
from sfa_api.schema import VARIABLES, INTERVAL_VALUE_TYPES, INTERVAL_LABELS


BASE_URL = 'https://localhost'

# Strings of formatted field options for error checking
# e.g. provides "interval_mean, instantaneous, ..." so
# f'Must be one of: {interval_value_types}.' can be checked
# against the errors returned from marshmallow
variables = ', '.join(VARIABLES)
interval_value_types = ', '.join(INTERVAL_VALUE_TYPES)
interval_labels = ', '.join(INTERVAL_LABELS)


VALID_SITE_JSON = {
    "elevation": 500.0,
    "extra_parameters": '{"parameter": "value"}',
    "latitude": 42.19,
    "longitude": -122.7,
    "modeling_parameters": {
        "ac_capacity": 0.015,
        "dc_capacity": 0.015,
        "ac_loss_factor": 0,
        "dc_loss_factor": 0,
        "temperature_coefficient": -.002,
        "surface_azimuth": 180.0,
        "surface_tilt": 45.0,
        "tracking_type": "fixed"
    },
    "name": "Test Site",
    "timezone": "Etc/GMT+8",
}

VALID_FORECAST_JSON = {
    "extra_parameters": '{"instrument": "pyranometer"}',
    "name": "test forecast",
    "site_id": "123e4567-e89b-12d3-a456-426655440001",
    "variable": "ac_power",
    "interval_label": "beginning",
    "issue_time_of_day": "12:00",
    "lead_time_to_start": 60,
    "interval_length": 1,
    "run_length": 1440,
    "interval_value_type": "interval_mean",
}


VALID_OBS_JSON = {
    "extra_parameters": '{"instrument": "Ascension Technology Rotating Shadowband Pyranometer"}', # NOQA
    "name": "Ashland OR, ghi",
    "site_id": "123e4567-e89b-12d3-a456-426655440001",
    "variable": "ghi",
    "interval_label": "beginning",
    "interval_length": 1,
    "interval_value_type": "interval_mean",
    "uncertainty": 0.10,
}


VALID_CDF_FORECAST_JSON = VALID_FORECAST_JSON.copy()
VALID_CDF_FORECAST_JSON.update({
    "name": 'test cdf forecast',
    "axis": 'x',
    "constant_values": [5.0, 20.0, 50.0, 80.0, 95.0]
})

VALID_OBS_VALUE_JSON = {
    'id': '123e4567-e89b-12d3-a456-426655440000',
    'values': [
        {'quality_flag': 0,
         'timestamp': "2019-01-22T17:54:00+00:00",
         'value': 1.0},
        {'quality_flag': 0,
         'timestamp': "2019-01-22T17:55:00+00:00",
         'value': 32.0},
        {'quality_flag': 0,
         'timestamp': "2019-01-22T17:56:00+00:00",
         'value': 3.0}
    ]
}
VALID_OBS_VALUE_CSV = (
    '# observation_id: 123e4567-e89b-12d3-a456-426655440000\n'
    '# metadata: https://localhost/observations/123e4567-e89b-12d3-a456-426655440000/metadata\n' # NOQA
    'timestamp,value,quality_flag\n'
    '20190122T12:04:00+0000,52.0,0\n'
    '20190122T12:05:00+0000,73.0,0\n'
    '20190122T12:06:00+0000,42.0,0\n'
    '20190122T12:07:00+0000,12.0,0\n')
VALID_FX_VALUE_JSON = {
    'id': '123e4567-e89b-12d3-a456-426655440000',
    'values': [
        {'timestamp': "2019-01-22T17:54:00+00:00",
         'value': 1.0},
        {'timestamp': "2019-01-22T17:55:00+00:00",
         'value': 32.0},
        {'timestamp': "2019-01-22T17:56:00+00:00",
         'value': 3.0}
    ]
}
FORECAST_CSV = (
    'timestamp,value\n'
    '20190122T12:04:00+0000,7.0\n'
    '20190122T12:05:00+0000,3.0\n'
    '20190122T12:06:00+0000,13.0\n'
    '20190122T12:07:00+0000,25.0\n')

VALID_FX_VALUE_CSV = (
    '# forecast_id: 11c20780-76ae-4b11-bef1-7a75bdc784e3\n'
    '# metadata: https://localhost/forecasts/single/11c20780-76ae-4b11-bef1-7a75bdc784e3/metadata\n' # NOQA
    f'{FORECAST_CSV}')
VALID_CDF_VALUE_CSV = (
    '# forecast_id: 633f9396-50bb-11e9-8647-d663bd873d93\n'
    '# metadata: https://localhost/forecasts/cdf/single/633f9396-50bb-11e9-8647-d663bd873d93\n' # NOQA
    f'{FORECAST_CSV}')


def copy_update(json, key, value):
    new_json = json.copy()
    new_json[key] = value
    return new_json


@contextmanager
def _make_sql_app():
    app = create_app('TestingConfig')
    with app.app_context():
        try:
            storage_interface.mysql_connection()
        except pymysql.err.OperationalError:
            pytest.skip('No connection to test database')
        else:
            yield app


@pytest.fixture(scope='module')
def sql_app():
    with _make_sql_app() as app:
        yield app


@pytest.fixture()
def sql_app_no_commit(mocker):
    with _make_sql_app() as app:
        with _make_nocommit_cursor(mocker):
            yield app


@pytest.fixture()
def sql_api(sql_app, mocker):
    api = sql_app.test_client()
    return api


@contextmanager
def _make_nocommit_cursor(mocker):
    # on release of a Pool connection, any transaction is rolled back
    # need to keep the transaction open between nocommit tests
    conn = storage_interface._make_sql_connection_partial()()
    mocker.patch.object(conn, 'close')
    mocker.patch('sfa_api.utils.storage_interface.mysql_connection',
                 return_value=conn)
    special = partial(storage_interface.get_cursor, commit=False)
    mocker.patch('sfa_api.utils.storage_interface.get_cursor', special)
    yield
    conn.rollback()


@pytest.fixture()
def nocommit_cursor(mocker, sql_app):
    with _make_nocommit_cursor(mocker) as cursor:
        yield cursor


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
def demo_app():
    app = create_app(config_name='TestingConfig')
    app.config['SFA_API_STATIC_DATA'] = True
    return app


@pytest.fixture()
def demo_api(demo_app, mocker):
    verify = mocker.patch('sfa_api.utils.auth.verify_access_token')
    verify.return_value = True
    api = demo_app.test_client()
    return api


@pytest.fixture()
def user(sql_app):
    ctx = sql_app.test_request_context()
    ctx.user = 'auth0|5be343df7025406237820b85'
    ctx.push()
    yield
    ctx.pop()


@pytest.fixture()
def invalid_user(sql_app):
    ctx = sql_app.test_request_context()
    ctx.user = 'bad'
    ctx.push()
    yield
    ctx.pop()


@pytest.fixture(params=[0, 1])
def app(request, demo_app, mocker):
    if request.param:
        yield demo_app
    else:
        # do this to avoid skipping app when no mysql
        with _make_sql_app() as sql_app:
            with _make_nocommit_cursor(mocker):
                yield sql_app


@pytest.fixture()
def api(app, mocker):
    def add_user():
        _request_ctx_stack.top.user = 'auth0|5be343df7025406237820b85'
        return True

    verify = mocker.patch('sfa_api.utils.auth.verify_access_token')
    verify.side_effect = add_user
    yield app.test_client()


@pytest.fixture()
def missing_id():
    return '7d2c3208-5243-11e9-8647-d663bd873d93'


@pytest.fixture()
def observation_id():
    return '123e4567-e89b-12d3-a456-426655440000'


@pytest.fixture()
def cdf_forecast_group_id():
    return 'ef51e87c-50b9-11e9-8647-d663bd873d93'


@pytest.fixture()
def cdf_forecast_id():
    return '633f9396-50bb-11e9-8647-d663bd873d93'


@pytest.fixture()
def forecast_id():
    return '11c20780-76ae-4b11-bef1-7a75bdc784e3'


@pytest.fixture()
def site_id():
    return 'd2018f1d-82b1-422a-8ec4-4e8b3fe92a4a'


@pytest.fixture()
def site_id_plant():
    return '123e4567-e89b-12d3-a456-426655440002'


@pytest.fixture()
def mocked_validation(mocker):
    mocked = mocker.patch('rq.Queue.enqueue')
    yield
    assert mocked.called
