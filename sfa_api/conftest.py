from contextlib import contextmanager
import datetime as dt
from functools import partial
from io import StringIO
import json


from flask import _request_ctx_stack
import numpy as np
import pandas as pd
import pymysql
import pytest
import pytz
import requests


from sfa_api import create_app
from sfa_api.utils import storage_interface
from sfa_api.schema import (
    VARIABLES, INTERVAL_VALUE_TYPES, INTERVAL_LABELS, AGGREGATE_TYPES)


BASE_URL = 'https://localhost'

# Strings of formatted field options for error checking
# e.g. provides "interval_mean, instantaneous, ..." so
# f'Must be one of: {interval_value_types}.' can be checked
# against the errors returned from marshmallow
variables = ', '.join(VARIABLES)
agg_types = ', '.join(AGGREGATE_TYPES)
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
        "temperature_coefficient": -.2,
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
    "interval_length": 5,
    "run_length": 1440,
    "interval_value_type": "interval_mean",
}


VALID_FORECAST_AGG_JSON = {
    "extra_parameters": '{"instrument": "pyranometer"}',
    "name": "test forecast",
    "aggregate_id": '458ffc27-df0b-11e9-b622-62adb5fd6af0',
    "variable": "ac_power",
    "interval_label": "beginning",
    "issue_time_of_day": "12:00",
    "lead_time_to_start": 60,
    "interval_length": 5,
    "run_length": 1440,
    "interval_value_type": "interval_mean",
}


VALID_OBS_JSON = {
    "extra_parameters": '{"instrument": "Ascension Technology Rotating Shadowband Pyranometer"}', # NOQA
    "name": "Weather Station, ghi",
    "site_id": "123e4567-e89b-12d3-a456-426655440001",
    "variable": "ghi",
    "interval_label": "beginning",
    "interval_length": 5,
    "interval_value_type": "interval_mean",
    "uncertainty": 0.10,
}

VALID_CDF_FORECAST_JSON = VALID_FORECAST_JSON.copy()
VALID_CDF_FORECAST_JSON.update({
    "name": 'test cdf forecast',
    "axis": 'x',
    "constant_values": [5.0, 20.0, 50.0, 80.0, 95.0]
})


VALID_CDF_FORECAST_AGG_JSON = VALID_FORECAST_AGG_JSON.copy()
VALID_CDF_FORECAST_AGG_JSON.update({
    "name": 'test cdf forecast',
    "axis": 'x',
    "constant_values": [10.0, 20.0, 50.0, 80.0, 100.0]
})


VALID_OBS_VALUE_JSON = {
    'id': '123e4567-e89b-12d3-a456-426655440000',
    'values': [
        {'quality_flag': 0,
         'timestamp': "2019-01-22T17:54:00+00:00",
         'value': 1.0},
        {'quality_flag': 0,
         'timestamp': "2019-01-22T17:59:00+00:00",
         'value': 32.0},
        {'quality_flag': 0,
         'timestamp': "2019-01-22T18:04:00+00:00",
         'value': 3.0}
    ]
}
VALID_OBS_VALUE_CSV = (
    '# observation_id: 123e4567-e89b-12d3-a456-426655440000\n'
    '# metadata: https://localhost/observations/123e4567-e89b-12d3-a456-426655440000/metadata\n' # NOQA
    'timestamp,value,quality_flag\n'
    '20190122T12:05:00+0000,52.0,0\n'
    '20190122T12:10:00+0000,73.0,0\n'
    '20190122T12:15:00+0000,42.0,0\n'
    '20190122T12:20:00+0000,12.0,0\n')
VALID_FX_VALUE_JSON = {
    'id': '123e4567-e89b-12d3-a456-426655440000',
    'values': [
        {'timestamp': "2019-01-22T17:54:00+00:00",
         'value': 1.0},
        {'timestamp': "2019-01-22T17:59:00+00:00",
         'value': 32.0},
        {'timestamp': "2019-01-22T18:04:00+00:00",
         'value': 3.0}
    ]
}
ADJ_FX_VALUE_JSON = {
    'id': '123e4567-e89b-12d3-a456-426655440000',
    'values': [
        {'timestamp': "2019-11-01T07:00:00+00:00",
         'value': 1.0},
        {'timestamp': "2019-11-01T07:05:00+00:00",
         'value': 32.0},
        {'timestamp': "2019-11-01T07:10:00+00:00",
         'value': 3.0}
    ]
}

UNSORTED_FX_VALUE_JSON = {
    'id': '123e4567-e89b-12d3-a456-426655440000',
    'values': [
        {'timestamp': "2019-01-22T17:59:00+00:00",
         'value': 32.0},
        {'timestamp': "2019-01-22T17:54:00+00:00",
         'value': 1.0},
        {'timestamp': "2019-01-22T18:04:00+00:00",
         'value': 3.0}
    ]
}
FORECAST_CSV = (
    'timestamp,value\n'
    '20190122T12:05:00+0000,7.0\n'
    '20190122T12:10:00+0000,3.0\n'
    '20190122T12:15:00+0000,13.0\n'
    '20190122T12:20:00+0000,25.0\n')

VALID_FX_VALUE_CSV = (
    '# forecast_id: 11c20780-76ae-4b11-bef1-7a75bdc784e3\n'
    '# metadata: https://localhost/forecasts/single/11c20780-76ae-4b11-bef1-7a75bdc784e3/metadata\n' # NOQA
    f'{FORECAST_CSV}')
VALID_CDF_VALUE_CSV = (
    '# forecast_id: 633f9396-50bb-11e9-8647-d663bd873d93\n'
    '# metadata: https://localhost/forecasts/cdf/single/633f9396-50bb-11e9-8647-d663bd873d93\n' # NOQA
    f'{FORECAST_CSV}')

ROLE = {
    "name": "test created role",
    "description": "testing role creation",
}

PERMISSION = {
    "action": "read",
    "applies_to_all": False,
    "description": "test created permission",
    "object_type": "observations",
}


@pytest.fixture()
def report_post_json():
    return {
        'report_parameters': {
            'name': 'NREL MIDC OASIS GHI Forecast Analysis',
            'start': "2019-04-01T07:00:00Z",
            'end': '2019-06-01T06:59:00Z',
            'metrics': ['mae', 'rmse'],
            'filters': [
                {'quality_flags': ['USER FLAGGED']}
            ],
            'categories': [
                'total',
                'date'
            ],
            'object_pairs': [
                {'observation': '123e4567-e89b-12d3-a456-426655440000',
                 'forecast': '11c20780-76ae-4b11-bef1-7a75bdc784e3'}],
        }
    }


@pytest.fixture()
def report_parameters(report_post_json):
    out = report_post_json['report_parameters'].copy()
    out['start'] = dt.datetime(2019, 4, 1, 7,
                               tzinfo=pytz.utc)
    out['end'] = dt.datetime(2019, 6, 1, 6, 59,
                             tzinfo=pytz.utc)
    return out


@pytest.fixture()
def raw_report_json():
    return {
        'generated_at': '2019-07-01T12:00:00+00:00',
        'timezone': 'Etc/GMT+8',
        'versions': [],
        'plots': None,
        'metrics': [],
        'processed_forecasts_observations': [],
        'messages': [{'step': 'dunno', 'level': 'error',
                      'message': 'FAILED', 'function': 'fcn'}],
        'data_checksum': None
    }


@pytest.fixture()
def reportid():
    return '9f290dd4-42b8-11ea-abdf-f4939feddd82'


@pytest.fixture()
def report_values():
    values = {
        'object_id': '123e4567-e89b-12d3-a456-426655440000',
        'processed_values': 'superencodedvalues'
    }
    return values


@pytest.fixture()
def report(report_parameters, raw_report_json, reportid, report_values):
    rv = report_values.copy()
    rv['id'] = 'a2b6ed14-42d0-11ea-aa3c-f4939feddd82'
    out = {
        'report_parameters': report_parameters,
        'name': report_parameters['name'],
        'report_id': reportid,
        'provider': 'Organization 1',
        'created_at': dt.datetime(2020, 1, 22, 13, 48, tzinfo=pytz.utc),
        'modified_at': dt.datetime(2020, 1, 22, 13, 50,
                                   tzinfo=pytz.utc),
        'raw_report': raw_report_json,
        'status': 'failed',
        'values': [rv]
    }
    out['raw_report']['generated_at'] = dt.datetime(2019, 7, 1, 12,
                                                    tzinfo=pytz.utc)
    return out


def copy_update(json, key, value):
    new_json = json.copy()
    new_json[key] = value
    return new_json


@pytest.fixture()
def user_id():
    return '0c90950a-7cca-11e9-a81f-54bf64606445'


@pytest.fixture()
def auth0id():
    return 'auth0|5be343df7025406237820b85'


@pytest.fixture()
def user_email():
    return 'testing@solarforecastarbiter.org'


@pytest.fixture()
def external_userid():
    return '4b436bee-8245-11e9-a81f-54bf64606445'


@pytest.fixture()
def external_auth0id():
    return 'auth0|5ceed7c8a1536b1103699501'


# User id of a permission-less unaffiliated user.
@pytest.fixture()
def unaffiliated_userid():
    return 'ef026b76-c049-11e9-9c7e-0242ac120002'


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
    return sql_app.test_client()


@pytest.fixture()
def sql_api_unauthenticated(sql_app, mocker):
    return sql_app.test_client()


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


@pytest.fixture()
def app(mocker):
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


# Forecast provided by 'Forecast Provider A', but test user does not
# have access to it.
@pytest.fixture()
def inaccessible_forecast_id():
    return 'd0dd64fc-8250-11e9-a81f-54bf64606445'


@pytest.fixture()
def site_id():
    return 'd2018f1d-82b1-422a-8ec4-4e8b3fe92a4a'


@pytest.fixture()
def site_id_plant():
    return '123e4567-e89b-12d3-a456-426655440002'


@pytest.fixture()
def aggregate_id():
    return '458ffc27-df0b-11e9-b622-62adb5fd6af0'


@pytest.fixture()
def orgid():
    return 'b76ab62e-4fe1-11e9-9e44-64006a511e6f'


@pytest.fixture()
def userid():
    return '0c90950a-7cca-11e9-a81f-54bf64606445'


@pytest.fixture()
def jobid():
    return '907a9340-0b11-11ea-9e88-f4939feddd82'


@pytest.fixture()
def mocked_queuing(mocker):
    mocked = mocker.patch('rq.Queue.enqueue',
                          autospec=True)
    yield mocked
    assert mocked.called


@pytest.fixture()
def mock_previous(mocker):
    meta = mocker.MagicMock()
    mocker.patch(
        'sfa_api.utils.storage_interface._set_previous_time',
        new=meta)
    meta.return_value = None
    return meta


@pytest.fixture()
def restrict_fx_upload(mocker):
    mocker.patch(
        'sfa_api.utils.storage_interface._set_extra_params',
        return_value='{"restrict_upload": true}')
    cut = mocker.patch(
        'sfa_api.utils.request_handling._current_utc_timestamp',
    )
    return cut


demo_sites = {
    '123e4567-e89b-12d3-a456-426655440001': {
        "elevation": 595.0,
        "extra_parameters": (
            '{"network_api_abbreviation": "AS","network": "University of Oregon SRML","network_api_id": "94040"}' # NOQA
        ),
        "latitude": 42.19,
        "longitude": -122.7,
        "modeling_parameters": {
            "ac_capacity": None,
            "ac_loss_factor": None,
            "axis_azimuth": None,
            "axis_tilt": None,
            "backtrack": None,
            "dc_capacity": None,
            "dc_loss_factor": None,
            "ground_coverage_ratio": None,
            "max_rotation_angle": None,
            "surface_azimuth": None,
            "surface_tilt": None,
            "temperature_coefficient": None,
            "tracking_type": None
        },
        "name": "Weather Station",
        "provider": "Organization 1",
        "timezone": "Etc/GMT+8",
        "site_id": '123e4567-e89b-12d3-a456-426655440001',
        "created_at": pytz.utc.localize(dt.datetime(2019, 3, 1, 11, 44, 38)),
        "modified_at": pytz.utc.localize(dt.datetime(2019, 3, 1, 11, 44, 38))
    },
    'd2018f1d-82b1-422a-8ec4-4e8b3fe92a4a': {
        "elevation": 786.0,
        "extra_parameters": '{"network": "NREL MIDC"}',
        "latitude": 32.22969,
        "longitude": -110.95534,
        "modeling_parameters": {
            "ac_capacity": None,
            "ac_loss_factor": None,
            "axis_azimuth": None,
            "axis_tilt": None,
            "backtrack": None,
            "dc_capacity": None,
            "dc_loss_factor": None,
            "ground_coverage_ratio": None,
            "max_rotation_angle": None,
            "surface_azimuth": None,
            "surface_tilt": None,
            "temperature_coefficient": None,
            "tracking_type": None
        },
        "name": "Weather Station 1",
        "provider": "Organization 1",
        "timezone": "America/Phoenix",
        "site_id": 'd2018f1d-82b1-422a-8ec4-4e8b3fe92a4a',
        "created_at": pytz.utc.localize(dt.datetime(2019, 3, 1, 11, 44, 44)),
        "modified_at": pytz.utc.localize(dt.datetime(2019, 3, 1, 11, 44, 44))
    },
    '123e4567-e89b-12d3-a456-426655440002': {
        "elevation": 786.0,
        "extra_parameters": "",
        "latitude": 43.73403,
        "longitude": -96.62328,
        "modeling_parameters": {
            "ac_capacity": 0.015,
            "ac_loss_factor": 0.0,
            "axis_azimuth": None,
            "axis_tilt": None,
            "backtrack": None,
            "dc_capacity": 0.015,
            "dc_loss_factor": 0.0,
            "ground_coverage_ratio": None,
            "max_rotation_angle": None,
            "surface_azimuth": 180.0,
            "surface_tilt": 45.0,
            "temperature_coefficient": -.2,
            "tracking_type": "fixed"
        },
        "name": "Power Plant 1",
        "provider": "Organization 1",
        "timezone": "Etc/GMT+6",
        "site_id": '123e4567-e89b-12d3-a456-426655440002',
        "created_at": pytz.utc.localize(dt.datetime(2019, 3, 1, 11, 44, 46)),
        "modified_at": pytz.utc.localize(dt.datetime(2019, 3, 1, 11, 44, 46))
    }
}


demo_observations = {
    "123e4567-e89b-12d3-a456-426655440000": {
        "extra_parameters": (
            '{"instrument": "Ascension Technology Rotating Shadowband Pyranometer",'  # NOQA
            ' "network": "UO SRML"}'
        ),
        "name": "GHI Instrument 1",
        "observation_id": "123e4567-e89b-12d3-a456-426655440000",
        "provider": "Organization 1",
        "site_id": "123e4567-e89b-12d3-a456-426655440001",
        "variable": "ghi",
        "interval_value_type": "interval_mean",
        "interval_label": "beginning",
        "interval_length": 5,
        "uncertainty": 0.10,
        "created_at": pytz.utc.localize(dt.datetime(2019, 3, 1, 12, 1, 39)),
        "modified_at": pytz.utc.localize(dt.datetime(2019, 3, 1, 12, 1, 39))
    },
    "9cfa4aa2-7d0f-4f6f-a1c1-47f75e1d226f": {
        "extra_parameters": (
            '{"instrument": "Ascension Technology Rotating Shadowband Pyranometer",'  # NOQA
            ' "network": "UO SRML"}'
        ),
        "name": "DHI Instrument 1",
        "observation_id": "9cfa4aa2-7d0f-4f6f-a1c1-47f75e1d226f",
        "provider": "Organization 1",
        "site_id": "123e4567-e89b-12d3-a456-426655440001",
        "variable": "dhi",
        "interval_value_type": "interval_mean",
        "interval_label": "beginning",
        "interval_length": 5,
        "uncertainty": 0.10,
        "created_at": pytz.utc.localize(dt.datetime(2019, 3, 1, 12, 1, 43)),
        "modified_at": pytz.utc.localize(dt.datetime(2019, 3, 1, 12, 1, 43))
    },
    "9ce9715c-bd91-47b7-989f-50bb558f1eb9": {
        "extra_parameters": (
            '{"instrument": "Ascension Technology Rotating Shadowband Pyranometer",' # NOQA
            ' "network": "UO SRML"}'
        ),
        "name": "DNI Instrument 2",
        "observation_id": "9ce9715c-bd91-47b7-989f-50bb558f1eb9",
        "provider": "Organization 1",
        "site_id": "123e4567-e89b-12d3-a456-426655440001",
        "variable": "dni",
        "interval_value_type": "interval_mean",
        "interval_label": "beginning",
        "interval_length": 5,
        "uncertainty": 0.10,
        "created_at": pytz.utc.localize(dt.datetime(2019, 3, 1, 12, 1, 48)),
        "modified_at": pytz.utc.localize(dt.datetime(2019, 3, 1, 12, 1, 48))
    },
    "e0da0dea-9482-4073-84de-f1b12c304d23": {
        "extra_parameters": (
            '{"instrument": "Kipp & Zonen CMP 22 Pyranometer",'
            ' "network": "UO SRML"}'
        ),
        "name": "GHI Instrument 2",
        "observation_id": "e0da0dea-9482-4073-84de-f1b12c304d23",
        "provider": "Organization 1",
        "site_id": "d2018f1d-82b1-422a-8ec4-4e8b3fe92a4a",
        "variable": "ghi",
        "interval_value_type": "interval_mean",
        "interval_label": "beginning",
        "interval_length": 5,
        "uncertainty": 0.10,
        "created_at": pytz.utc.localize(dt.datetime(2019, 3, 1, 12, 1, 55)),
        "modified_at": pytz.utc.localize(dt.datetime(2019, 3, 1, 12, 1, 55))
    },
    "b1dfe2cb-9c8e-43cd-afcf-c5a6feaf81e2": {
        "extra_parameters": (
            '{"instrument": "Kipp & Zonen CMP 22 Pyranometer",'
            ' "network": "NOAA"}'
        ),
        "name": "Sioux Falls, ghi",
        "observation_id": "b1dfe2cb-9c8e-43cd-afcf-c5a6feaf81e2",
        "provider": "Organization 1",
        "site_id": "d2018f1d-82b1-422a-8ec4-4e8b3fe92a4a",
        "variable": "ghi",
        "interval_value_type": "interval_mean",
        "interval_label": "beginning",
        "interval_length": 5,
        "uncertainty": 0.10,
        "created_at": pytz.utc.localize(dt.datetime(2019, 3, 1, 12, 2, 38)),
        "modified_at": pytz.utc.localize(dt.datetime(2019, 3, 1, 12, 2, 38))
    },
    '991d15ce-7f66-11ea-96ae-0242ac150002': {
        'name': 'Weather Station Event Observation',
        'variable': 'event',
        'interval_value_type': 'instantaneous',
        'interval_length': 5.0,
        'interval_label': 'event',
        'site_id': '123e4567-e89b-12d3-a456-426655440001',
        'uncertainty': 1.0,
        'observation_id': '991d15ce-7f66-11ea-96ae-0242ac150002',
        'provider': 'Organization 1',
        'created_at': pytz.utc.localize(dt.datetime(2019, 4, 14, 7, 00, 00)),
        'modified_at': pytz.utc.localize(dt.datetime(2019, 4, 14, 7, 00, 00)),
        'extra_parameters': ''}
}


demo_forecasts = {
    '11c20780-76ae-4b11-bef1-7a75bdc784e3': {
        "extra_parameters": "",
        "forecast_id": "11c20780-76ae-4b11-bef1-7a75bdc784e3",
        "name": "DA GHI",
        "provider": "Organization 1",
        "site_id": "123e4567-e89b-12d3-a456-426655440001",
        "aggregate_id": None,
        "variable": "ghi",
        "issue_time_of_day": "06:00",
        "interval_length": 5,
        "run_length": 1440,
        "interval_label": "beginning",
        "lead_time_to_start": 60,
        "interval_value_type": "interval_mean",
        "created_at": pytz.utc.localize(dt.datetime(2019, 3, 1, 11, 55, 37)),
        "modified_at": pytz.utc.localize(dt.datetime(2019, 3, 1, 11, 55, 37))
    },
    'f8dd49fa-23e2-48a0-862b-ba0af6dec276': {
        "extra_parameters": "",
        "forecast_id": "f8dd49fa-23e2-48a0-862b-ba0af6dec276",
        "name": "HA Power",
        "provider": "Organization 1",
        "site_id": "123e4567-e89b-12d3-a456-426655440002",
        "aggregate_id": None,
        "variable": "ac_power",
        "issue_time_of_day": "12:00",
        "run_length": 60,
        "interval_length": 1,
        "interval_label": "beginning",
        "lead_time_to_start": 60,
        "interval_value_type": "interval_mean",
        "created_at": pytz.utc.localize(dt.datetime(2019, 3, 1, 11, 55, 38)),
        "modified_at": pytz.utc.localize(dt.datetime(2019, 3, 1, 11, 55, 38))
    },
    '39220780-76ae-4b11-bef1-7a75bdc784e3': {
        "extra_parameters": "",
        "forecast_id": "39220780-76ae-4b11-bef1-7a75bdc784e3",
        "name": "GHI Aggregate FX",
        "provider": "Organization 1",
        "site_id": None,
        "aggregate_id": "458ffc27-df0b-11e9-b622-62adb5fd6af0",
        "variable": "ghi",
        "issue_time_of_day": "06:00",
        "run_length": 1440,
        "interval_length": 5,
        "interval_label": "beginning",
        "lead_time_to_start": 60,
        "interval_value_type": "interval_mean",
        "created_at": pytz.utc.localize(dt.datetime(2019, 3, 1, 11, 55, 37)),
        "modified_at": pytz.utc.localize(dt.datetime(2019, 3, 1, 11, 55, 37))
    },
    '49220780-76ae-4b11-bef1-7a75bdc784e3': {
        "extra_parameters": "",
        "forecast_id": "49220780-76ae-4b11-bef1-7a75bdc784e3",
        "name": "GHI Aggregate FX 60",
        "provider": "Organization 1",
        "site_id": None,
        "aggregate_id": "458ffc27-df0b-11e9-b622-62adb5fd6af0",
        "variable": "ghi",
        "issue_time_of_day": "00:00",
        "run_length": 1440,
        "interval_length": 60,
        "interval_label": "beginning",
        "lead_time_to_start": 0,
        "interval_value_type": "interval_mean",
        "created_at": pytz.utc.localize(dt.datetime(2019, 3, 1, 11, 55, 37)),
        "modified_at": pytz.utc.localize(dt.datetime(2019, 3, 1, 11, 55, 37))
    },
    '24cbae4e-7ea6-11ea-86b1-0242ac150002': {
        'name': 'Weather Station Event Forecast',
        'issue_time_of_day': '05:00',
        'lead_time_to_start': 60.0,
        'interval_length': 5.0,
        'run_length': 60.0,
        'interval_label': 'event',
        'interval_value_type': 'instantaneous',
        'variable': 'event',
        'forecast_id': '24cbae4e-7ea6-11ea-86b1-0242ac150002',
        'site_id': '123e4567-e89b-12d3-a456-426655440001',
        'aggregate_id': None,
        'provider': 'Organization 1',
        'extra_parameters': '',
        'created_at': pytz.utc.localize(dt.datetime(2019, 4, 14, 7, 00, 00)),
        'modified_at': pytz.utc.localize(dt.datetime(2019, 4, 14, 7, 00, 00)),
    }
}


demo_single_cdf = {
    '633f9396-50bb-11e9-8647-d663bd873d93': {
        "forecast_id": '633f9396-50bb-11e9-8647-d663bd873d93',
        "constant_value": 5.0,
        "parent": 'ef51e87c-50b9-11e9-8647-d663bd873d93',
    },
    '633f9864-50bb-11e9-8647-d663bd873d93': {
        "forecast_id": '633f9864-50bb-11e9-8647-d663bd873d93',
        "constant_value": 20.0,
        "parent": 'ef51e87c-50b9-11e9-8647-d663bd873d93',
    },
    '633f9b2a-50bb-11e9-8647-d663bd873d93': {
        "forecast_id": '633f9b2a-50bb-11e9-8647-d663bd873d93',
        "constant_value": 50.0,
        "parent": 'ef51e87c-50b9-11e9-8647-d663bd873d93',
    },
    '633f9d96-50bb-11e9-8647-d663bd873d93': {
        "forecast_id": '633f9d96-50bb-11e9-8647-d663bd873d93',
        "constant_value": 80.0,
        "parent": 'ef51e87c-50b9-11e9-8647-d663bd873d93',
    },
    '633fa548-50bb-11e9-8647-d663bd873d93': {
        "forecast_id": '633fa548-50bb-11e9-8647-d663bd873d93',
        "constant_value": 95.0,
        "parent": 'ef51e87c-50b9-11e9-8647-d663bd873d93',
    },
    '633fa94e-50bb-11e9-8647-d663bd873d93': {
        "forecast_id": '633fa94e-50bb-11e9-8647-d663bd873d93',
        "constant_value": 0.0,
        "parent": '058b182a-50ba-11e9-8647-d663bd873d93',
    },
    '633fabec-50bb-11e9-8647-d663bd873d93': {
        "forecast_id": '633fabec-50bb-11e9-8647-d663bd873d93',
        "constant_value": 5.0,
        "parent": '058b182a-50ba-11e9-8647-d663bd873d93',

    },
    '633fae62-50bb-11e9-8647-d663bd873d93': {
        "forecast_id": '633fae62-50bb-11e9-8647-d663bd873d93',
        "constant_value": 10.0,
        "parent": '058b182a-50ba-11e9-8647-d663bd873d93',
    },
    '633fb114-50bb-11e9-8647-d663bd873d93': {
        "forecast_id": '633fb114-50bb-11e9-8647-d663bd873d93',
        "constant_value": 15.0,
        "parent": '058b182a-50ba-11e9-8647-d663bd873d93',
    },
    '633fb3a8-50bb-11e9-8647-d663bd873d93': {
        "forecast_id": '633fb3a8-50bb-11e9-8647-d663bd873d93',
        "constant_value": 20.0,
        "parent": '058b182a-50ba-11e9-8647-d663bd873d93',
    },
    '733f9396-50bb-11e9-8647-d663bd873d93': {
        "forecast_id": '733f9396-50bb-11e9-8647-d663bd873d93',
        "constant_value": 10.0,
        "parent": 'f6b620ca-f743-11e9-a34f-f4939feddd82'
    },
    '733f9864-50bb-11e9-8647-d663bd873d93': {
        "forecast_id": '733f9864-50bb-11e9-8647-d663bd873d93',
        "constant_value": 20.0,
        "parent": 'f6b620ca-f743-11e9-a34f-f4939feddd82'
    },
    '733f9b2a-50bb-11e9-8647-d663bd873d93': {
        "forecast_id": '733f9b2a-50bb-11e9-8647-d663bd873d93',
        "constant_value": 50.0,
        "parent": 'f6b620ca-f743-11e9-a34f-f4939feddd82'
    },
    '733f9d96-50bb-11e9-8647-d663bd873d93': {
        "forecast_id": '733f9d96-50bb-11e9-8647-d663bd873d93',
        "constant_value": 80.0,
        "parent": 'f6b620ca-f743-11e9-a34f-f4939feddd82'
    },
    '733fa548-50bb-11e9-8647-d663bd873d93': {
        "forecast_id": '733fa548-50bb-11e9-8647-d663bd873d93',
        "constant_value": 100.0,
        "parent": 'f6b620ca-f743-11e9-a34f-f4939feddd82'
    },
}


def _get_constant_values(fxid):
    out = demo_single_cdf[fxid].copy()
    del out['parent']
    return out


demo_group_cdf = {
    'ef51e87c-50b9-11e9-8647-d663bd873d93': {
        "forecast_id": "ef51e87c-50b9-11e9-8647-d663bd873d93",
        "name": "DA GHI",
        "extra_parameters": "",
        "provider": "Organization 1",
        "site_id": "123e4567-e89b-12d3-a456-426655440001",
        "aggregate_id": None,
        "variable": "ghi",
        "issue_time_of_day": "06:00",
        "interval_length": 5,
        "run_length": 1440,
        "interval_label": "beginning",
        "lead_time_to_start": 60,
        "interval_value_type": "interval_mean",
        "axis": "y",
        "constant_values": [
            _get_constant_values('633f9396-50bb-11e9-8647-d663bd873d93'),
            _get_constant_values('633f9864-50bb-11e9-8647-d663bd873d93'),
            _get_constant_values('633f9b2a-50bb-11e9-8647-d663bd873d93'),
            _get_constant_values('633f9d96-50bb-11e9-8647-d663bd873d93'),
            _get_constant_values('633fa548-50bb-11e9-8647-d663bd873d93')],
        "created_at": pytz.utc.localize(dt.datetime(2019, 3, 2, 14, 55, 37)),
        "modified_at": pytz.utc.localize(dt.datetime(2019, 3, 2, 14, 55, 37))
    },
    '058b182a-50ba-11e9-8647-d663bd873d93': {
        "forecast_id": "058b182a-50ba-11e9-8647-d663bd873d93",
        "name": "HA Power",
        "extra_parameters": "",
        "provider": "Organization 1",
        "site_id": "123e4567-e89b-12d3-a456-426655440002",
        "aggregate_id": None,
        "variable": "ac_power",
        "issue_time_of_day": "12:00",
        "run_length": 60,
        "interval_length": 1,
        "interval_label": "beginning",
        "lead_time_to_start": 60,
        "interval_value_type": "interval_mean",
        "axis": "x",
        "constant_values": [
            _get_constant_values('633fb3a8-50bb-11e9-8647-d663bd873d93'),
            _get_constant_values('633fb114-50bb-11e9-8647-d663bd873d93'),
            _get_constant_values('633fae62-50bb-11e9-8647-d663bd873d93'),
            _get_constant_values('633fabec-50bb-11e9-8647-d663bd873d93'),
            _get_constant_values('633fa94e-50bb-11e9-8647-d663bd873d93')],
        "created_at": pytz.utc.localize(dt.datetime(2019, 3, 2, 14, 55, 38)),
        "modified_at": pytz.utc.localize(dt.datetime(2019, 3, 2, 14, 55, 38))
    },
    'f6b620ca-f743-11e9-a34f-f4939feddd82': {
        "forecast_id": "f6b620ca-f743-11e9-a34f-f4939feddd82",
        "name": "GHI Aggregate CDF FX",
        "extra_parameters": "",
        "provider": "Organization 1",
        "site_id": None,
        "aggregate_id": "458ffc27-df0b-11e9-b622-62adb5fd6af0",
        "variable": "ghi",
        "issue_time_of_day": "06:00",
        "interval_length": 5,
        "run_length": 1440,
        "interval_label": "beginning",
        "lead_time_to_start": 60,
        "interval_value_type": "interval_mean",
        "axis": "y",
        "constant_values": [
            _get_constant_values('733f9396-50bb-11e9-8647-d663bd873d93'),
            _get_constant_values('733f9864-50bb-11e9-8647-d663bd873d93'),
            _get_constant_values('733f9b2a-50bb-11e9-8647-d663bd873d93'),
            _get_constant_values('733f9d96-50bb-11e9-8647-d663bd873d93'),
            _get_constant_values('733fa548-50bb-11e9-8647-d663bd873d93')],
        "created_at": pytz.utc.localize(dt.datetime(2019, 3, 2, 14, 55, 38)),
        "modified_at": pytz.utc.localize(dt.datetime(2019, 3, 2, 14, 55, 38))
    }
}


ca = dt.datetime(2019, 9, 25, 0, 0, tzinfo=dt.timezone.utc)
ef = dt.datetime(2019, 1, 1, 0, 0, tzinfo=dt.timezone.utc)
demo_aggregates = {
    "458ffc27-df0b-11e9-b622-62adb5fd6af0": {
        "aggregate_id": "458ffc27-df0b-11e9-b622-62adb5fd6af0",
        "name": "Test Aggregate ghi",
        "provider": "Organization 1",
        "variable": "ghi",
        "interval_label": "ending",
        "interval_length": 60,
        "interval_value_type": "interval_mean",
        "aggregate_type": "mean",
        "extra_parameters": "extra",
        "description": "ghi agg",
        "timezone": "America/Denver",
        "created_at": dt.datetime(2019, 9, 24, 12, 0, tzinfo=dt.timezone.utc),
        "modified_at": dt.datetime(2019, 9, 24, 12, 0, tzinfo=dt.timezone.utc),
        "observations": [
            {"observation_id": "123e4567-e89b-12d3-a456-426655440000",
             "created_at": ca,
             "effective_from": ef,
             "observation_deleted_at": None,
             "effective_until": None},
            {"observation_id": "e0da0dea-9482-4073-84de-f1b12c304d23",
             "created_at": ca,
             "effective_from": ef,
             "observation_deleted_at": None,
             "effective_until": None},
            {"observation_id": "b1dfe2cb-9c8e-43cd-afcf-c5a6feaf81e2",
             "created_at": ca,
             "effective_from": ef,
             "observation_deleted_at": None,
             "effective_until": None},
        ]
    },
    "d3d1e8e5-df1b-11e9-b622-62adb5fd6af0": {
        "aggregate_id": "d3d1e8e5-df1b-11e9-b622-62adb5fd6af0",
        "name": "Test Aggregate dni",
        "provider": "Organization 1",
        "variable": "dni",
        "interval_label": "ending",
        "interval_length": 60,
        "interval_value_type": "interval_mean",
        "aggregate_type": "mean",
        "extra_parameters": "extra",
        "description": "dni agg",
        "timezone": "America/Denver",
        "created_at": dt.datetime(2019, 9, 24, 12, 0, tzinfo=dt.timezone.utc),
        "modified_at": dt.datetime(2019, 9, 24, 12, 0, tzinfo=dt.timezone.utc),
        "observations": [
            {"observation_id": "95890740-824f-11e9-a81f-54bf64606445",
             "created_at": ca,
             "observation_deleted_at": None,
             "effective_from": ef,
             "effective_until": None},
            {"observation_id": "9ce9715c-bd91-47b7-989f-50bb558f1eb9",
             "created_at": ca,
             "observation_deleted_at": None,
             "effective_from": ef,
             "effective_until": None}
        ]
    }
}


def generate_randoms(freq):
    """Generates two days worth of random noisy data.

    Parameters
    ----------
    freq: int
        The "interval length" of the data to produce in minutes.
        options: 1 or 5

    Returns
    -------
    Dataframe
        Dataframe with datetimeindex, values and quality_flag
        columns.

    Notes
    -----
    Won't throw an error if you try to use a freq of other
    than 1 or 5 but will provide you values as though
    you selected 5.
    """
    if freq == 1:
        length = 4320
    elif freq == 5:
        length = 864
    else:
        # assume 60 min
        length = 72
    index = pd.date_range(start=pd.Timestamp('20190414T07:00'),
                          periods=length, freq=f'{freq}min', tz='UTC')
    values = np.random.normal(50, 5, size=length)
    quality_flags = np.random.randint(11, size=length)
    return index, values, quality_flags


demo_file_variables = ['ghi', 'dni', 'dhi']


@pytest.fixture()
def obs_vals():
    index, values, quality = generate_randoms(freq=5)
    data = {
        'value': values,
        'quality_flag': quality}
    obs_df = pd.DataFrame(index=index, data=data)
    obs_df.index.name = 'timestamp'
    return obs_df


@pytest.fixture()
def fx_vals():
    index, values, quality = generate_randoms(freq=5)
    data = {
        'value': values}
    fx_df = pd.DataFrame(index=index, data=data)
    fx_df.index.name = 'timestamp'
    return fx_df


@pytest.fixture(scope="module")
def ghi_obs_vals():
    ghi_csv = """
timestamp,value,quality_flag
2019-04-14T07:00:00+00:00,-2.58981,0
2019-04-14T07:05:00+00:00,-2.59598,0
2019-04-14T07:10:00+00:00,-2.95363,0
2019-04-14T07:15:00+00:00,-2.58983,0
2019-04-14T07:20:00+00:00,-2.5897900000000003,0
2019-04-14T07:25:00+00:00,-2.65143,0
2019-04-14T07:30:00+00:00,-2.58363,0
2019-04-14T07:35:00+00:00,-2.9351,0
2019-04-14T07:40:00+00:00,-2.5897799999999997,0
2019-04-14T07:45:00+00:00,-2.58975,0
2019-04-14T07:50:00+00:00,-2.58976,0
2019-04-14T07:55:00+00:00,-2.5836,0
2019-04-14T08:00:00+00:00,-2.63912,0
2019-04-14T08:05:00+00:00,-2.87963,0
2019-04-14T08:10:00+00:00,-2.58983,0
2019-04-14T08:15:00+00:00,-2.5897799999999997,0
2019-04-14T08:20:00+00:00,-2.21981,0
2019-04-14T08:25:00+00:00,-2.0163599999999997,0
2019-04-14T08:30:00+00:00,-2.5897900000000003,0
2019-04-14T08:35:00+00:00,-2.58986,0
2019-04-14T08:40:00+00:00,-2.5899,0
2019-04-14T08:45:00+00:00,-2.46659,0
2019-04-14T08:50:00+00:00,-2.54677,0
2019-04-14T08:55:00+00:00,-2.33095,0
2019-04-14T09:00:00+00:00,-2.07193,0
2019-04-14T09:05:00+00:00,-2.3679200000000002,0
2019-04-14T09:10:00+00:00,-2.2137599999999997,0
2019-04-14T09:15:00+00:00,-2.5899799999999997,0
2019-04-14T09:20:00+00:00,-2.368,0
2019-04-14T09:25:00+00:00,-2.59004,0
2019-04-14T09:30:00+00:00,-2.5838900000000002,0
2019-04-14T09:35:00+00:00,-2.59002,0
2019-04-14T09:40:00+00:00,-2.59003,0
2019-04-14T09:45:00+00:00,-2.46049,0
2019-04-14T09:50:00+00:00,-2.21995,0
2019-04-14T09:55:00+00:00,-2.2384,0
2019-04-14T10:00:00+00:00,-2.15828,0
2019-04-14T10:05:00+00:00,-2.59001,0
2019-04-14T10:10:00+00:00,-2.22008,0
2019-04-14T10:15:00+00:00,-2.22011,0
2019-04-14T10:20:00+00:00,-2.34346,0
2019-04-14T10:25:00+00:00,-2.22012,0
2019-04-14T10:30:00+00:00,-2.2200900000000003,0
2019-04-14T10:35:00+00:00,-2.26943,0
2019-04-14T10:40:00+00:00,-2.22627,0
2019-04-14T10:45:00+00:00,-1.94259,0
2019-04-14T10:50:00+00:00,-2.21394,0
2019-04-14T10:55:00+00:00,-2.20161,0
2019-04-14T11:00:00+00:00,-2.18928,0
2019-04-14T11:05:00+00:00,-2.25712,0
2019-04-14T11:10:00+00:00,-2.3496200000000003,0
2019-04-14T11:15:00+00:00,-2.01661,0
2019-04-14T11:20:00+00:00,-2.20778,0
2019-04-14T11:25:00+00:00,-1.99194,0
2019-04-14T11:30:00+00:00,-1.8501,0
2019-04-14T11:35:00+00:00,-1.86243,0
2019-04-14T11:40:00+00:00,-2.1461099999999997,0
2019-04-14T11:45:00+00:00,-1.88093,0
2019-04-14T11:50:00+00:00,-1.8501,0
2019-04-14T11:55:00+00:00,-2.21395,0
2019-04-14T12:00:00+00:00,-2.07211,0
2019-04-14T12:05:00+00:00,-1.8562599999999998,0
2019-04-14T12:10:00+00:00,-2.33112,0
2019-04-14T12:15:00+00:00,-2.56547,0
2019-04-14T12:20:00+00:00,-2.5593,0
2019-04-14T12:25:00+00:00,-2.18928,0
2019-04-14T12:30:00+00:00,-2.1461099999999997,0
2019-04-14T12:35:00+00:00,-1.8501,0
2019-04-14T12:40:00+00:00,-1.8501,0
2019-04-14T12:45:00+00:00,-1.11006,0
2019-04-14T12:50:00+00:00,0.370021,0
2019-04-14T12:55:00+00:00,2.81833,0
2019-04-14T13:00:00+00:00,6.01286,0
2019-04-14T13:05:00+00:00,14.8625,0
2019-04-14T13:10:00+00:00,25.0627,0
2019-04-14T13:15:00+00:00,36.0769,0
2019-04-14T13:20:00+00:00,49.3668,0
2019-04-14T13:25:00+00:00,64.1798,0
2019-04-14T13:30:00+00:00,80.7814,0
2019-04-14T13:35:00+00:00,98.1722,0
2019-04-14T13:40:00+00:00,116.131,0
2019-04-14T13:45:00+00:00,134.749,0
2019-04-14T13:50:00+00:00,152.97799999999998,0
2019-04-14T13:55:00+00:00,161.322,0
2019-04-14T14:00:00+00:00,185.75,0
2019-04-14T14:05:00+00:00,212.2,0
2019-04-14T14:10:00+00:00,232.768,0
2019-04-14T14:15:00+00:00,253.32299999999998,0
2019-04-14T14:20:00+00:00,271.79200000000003,0
2019-04-14T14:25:00+00:00,292.827,0
2019-04-14T14:30:00+00:00,314.072,0
2019-04-14T14:35:00+00:00,331.245,0
2019-04-14T14:40:00+00:00,354.673,0
2019-04-14T14:45:00+00:00,374.912,0
2019-04-14T14:50:00+00:00,395.663,0
2019-04-14T14:55:00+00:00,416.967,0
2019-04-14T15:00:00+00:00,437.421,0
2019-04-14T15:05:00+00:00,458.991,0
2019-04-14T15:10:00+00:00,482.281,0
2019-04-14T15:15:00+00:00,479.139,0
2019-04-14T15:20:00+00:00,508.588,0
2019-04-14T15:25:00+00:00,535.8969999999999,0
2019-04-14T15:30:00+00:00,553.289,0
2019-04-14T15:35:00+00:00,571.726,0
2019-04-14T15:40:00+00:00,590.8,0
2019-04-14T15:45:00+00:00,597.552,0
2019-04-14T15:50:00+00:00,625.388,0
2019-04-14T15:55:00+00:00,642.813,0
2019-04-14T16:00:00+00:00,659.5160000000001,0
2019-04-14T16:05:00+00:00,676.591,0
2019-04-14T16:10:00+00:00,693.842,0
2019-04-14T16:15:00+00:00,710.203,0
2019-04-14T16:20:00+00:00,725.822,0
2019-04-14T16:25:00+00:00,742.3810000000001,0
2019-04-14T16:30:00+00:00,758.559,0
2019-04-14T16:35:00+00:00,774.2180000000001,0
2019-04-14T16:40:00+00:00,789.38,0
2019-04-14T16:45:00+00:00,804.44,0
2019-04-14T16:50:00+00:00,819.814,0
2019-04-14T16:55:00+00:00,834.556,0
2019-04-14T17:00:00+00:00,848.2639999999999,0
2019-04-14T17:05:00+00:00,861.556,0
2019-04-14T17:10:00+00:00,874.9169999999999,0
2019-04-14T17:15:00+00:00,887.265,0
2019-04-14T17:20:00+00:00,899.135,0
2019-04-14T17:25:00+00:00,914.666,0
2019-04-14T17:30:00+00:00,928.618,0
2019-04-14T17:35:00+00:00,951.102,0
2019-04-14T17:40:00+00:00,890.1210000000001,0
2019-04-14T17:45:00+00:00,728.257,0
2019-04-14T17:50:00+00:00,661.2189999999999,0
2019-04-14T17:55:00+00:00,991.305,0
2019-04-14T18:00:00+00:00,974.33,0
2019-04-14T18:05:00+00:00,999.362,0
2019-04-14T18:10:00+00:00,944.8510000000001,0
2019-04-14T18:15:00+00:00,715.2760000000001,0
2019-04-14T18:20:00+00:00,945.5980000000001,0
2019-04-14T18:25:00+00:00,967.4939999999999,0
2019-04-14T18:30:00+00:00,1038.75,0
2019-04-14T18:35:00+00:00,1035.99,0
2019-04-14T18:40:00+00:00,1038.4,0
2019-04-14T18:45:00+00:00,1039.57,0
2019-04-14T18:50:00+00:00,929.263,0
2019-04-14T18:55:00+00:00,947.2260000000001,0
2019-04-14T19:00:00+00:00,952.812,0
2019-04-14T19:05:00+00:00,1056.66,0
2019-04-14T19:10:00+00:00,1084.52,0
2019-04-14T19:15:00+00:00,1080.25,0
2019-04-14T19:20:00+00:00,1067.63,0
2019-04-14T19:25:00+00:00,1063.64,0
2019-04-14T19:30:00+00:00,1046.98,0
2019-04-14T19:35:00+00:00,1049.83,0
2019-04-14T19:40:00+00:00,983.454,0
2019-04-14T19:45:00+00:00,953.0,0
2019-04-14T19:50:00+00:00,973.1189999999999,0
2019-04-14T19:55:00+00:00,1031.86,0
2019-04-14T20:00:00+00:00,893.164,0
2019-04-14T20:05:00+00:00,966.245,0
2019-04-14T20:10:00+00:00,1019.2,0
2019-04-14T20:15:00+00:00,976.79,0
2019-04-14T20:20:00+00:00,901.305,0
2019-04-14T20:25:00+00:00,945.3939999999999,0
2019-04-14T20:30:00+00:00,989.505,0
2019-04-14T20:35:00+00:00,1043.08,0
2019-04-14T20:40:00+00:00,843.58,0
2019-04-14T20:45:00+00:00,943.299,0
2019-04-14T20:50:00+00:00,893.836,0
2019-04-14T20:55:00+00:00,866.0110000000001,0
2019-04-14T21:00:00+00:00,811.8969999999999,0
2019-04-14T21:05:00+00:00,840.812,0
2019-04-14T21:10:00+00:00,757.7389999999999,0
2019-04-14T21:15:00+00:00,899.6519999999999,0
2019-04-14T21:20:00+00:00,909.35,0
2019-04-14T21:25:00+00:00,954.7180000000001,0
2019-04-14T21:30:00+00:00,894.877,0
2019-04-14T21:35:00+00:00,891.1339999999999,0
2019-04-14T21:40:00+00:00,871.166,0
2019-04-14T21:45:00+00:00,872.8610000000001,0
2019-04-14T21:50:00+00:00,844.846,0
2019-04-14T21:55:00+00:00,837.497,0
2019-04-14T22:00:00+00:00,766.3919999999999,0
2019-04-14T22:05:00+00:00,810.61,0
2019-04-14T22:10:00+00:00,776.055,0
2019-04-14T22:15:00+00:00,745.7360000000001,0
2019-04-14T22:20:00+00:00,722.574,0
2019-04-14T22:25:00+00:00,752.806,0
2019-04-14T22:30:00+00:00,721.926,0
2019-04-14T22:35:00+00:00,694.8430000000001,0
2019-04-14T22:40:00+00:00,684.0169999999999,0
2019-04-14T22:45:00+00:00,666.4830000000001,0
2019-04-14T22:50:00+00:00,632.129,0
2019-04-14T22:55:00+00:00,580.055,0
2019-04-14T23:00:00+00:00,458.814,0
2019-04-14T23:05:00+00:00,615.59,0
2019-04-14T23:10:00+00:00,619.446,0
2019-04-14T23:15:00+00:00,592.008,0
2019-04-14T23:20:00+00:00,437.16900000000004,0
2019-04-14T23:25:00+00:00,514.895,0
2019-04-14T23:30:00+00:00,342.56,0
2019-04-14T23:35:00+00:00,567.229,0
2019-04-14T23:40:00+00:00,521.059,0
2019-04-14T23:45:00+00:00,475.625,0
2019-04-14T23:50:00+00:00,286.94,0
2019-04-14T23:55:00+00:00,430.19,0
2019-04-15T00:00:00+00:00,181.178,0
2019-04-15T00:05:00+00:00,246.452,0
2019-04-15T00:10:00+00:00,123.838,0
2019-04-15T00:15:00+00:00,134.411,0
2019-04-15T00:20:00+00:00,178.725,0
2019-04-15T00:25:00+00:00,222.75099999999998,0
2019-04-15T00:30:00+00:00,122.815,0
2019-04-15T00:35:00+00:00,120.95200000000001,0
2019-04-15T00:40:00+00:00,215.28599999999997,0
2019-04-15T00:45:00+00:00,182.082,0
2019-04-15T00:50:00+00:00,112.78399999999999,0
2019-04-15T00:55:00+00:00,99.9878,0
2019-04-15T01:00:00+00:00,95.6318,0
2019-04-15T01:05:00+00:00,98.37,0
2019-04-15T01:10:00+00:00,65.9311,0
2019-04-15T01:15:00+00:00,54.4334,0
2019-04-15T01:20:00+00:00,69.2061,0
2019-04-15T01:25:00+00:00,57.6223,0
2019-04-15T01:30:00+00:00,27.152,0
2019-04-15T01:35:00+00:00,15.2969,0
2019-04-15T01:40:00+00:00,7.52508,0
2019-04-15T01:45:00+00:00,3.06547,0
2019-04-15T01:50:00+00:00,0.370076,0
2019-04-15T01:55:00+00:00,-1.11022,0
2019-04-15T02:00:00+00:00,-1.8503,0
2019-04-15T02:05:00+00:00,-2.6026700000000003,0
2019-04-15T02:10:00+00:00,-2.9603,0
2019-04-15T02:15:00+00:00,-3.31795,0
2019-04-15T02:20:00+00:00,-3.3302300000000002,0
2019-04-15T02:25:00+00:00,-3.3302099999999997,0
2019-04-15T02:30:00+00:00,-3.3302300000000002,0
2019-04-15T02:35:00+00:00,-3.19462,0
2019-04-15T02:40:00+00:00,-3.70025,0
2019-04-15T02:45:00+00:00,-3.8913900000000003,0
2019-04-15T02:50:00+00:00,-3.5152099999999997,0
2019-04-15T02:55:00+00:00,-3.54601,0
2019-04-15T03:00:00+00:00,-3.48432,0
2019-04-15T03:05:00+00:00,-3.33015,0
2019-04-15T03:10:00+00:00,-3.33015,0
2019-04-15T03:15:00+00:00,-3.1760200000000003,0
2019-04-15T03:20:00+00:00,-3.3302400000000003,0
2019-04-15T03:25:00+00:00,-2.9725599999999996,0
2019-04-15T03:30:00+00:00,-2.9664,0
2019-04-15T03:35:00+00:00,-2.59022,0
2019-04-15T03:40:00+00:00,-2.96026,0
2019-04-15T03:45:00+00:00,-3.0836,0
2019-04-15T03:50:00+00:00,-3.33029,0
2019-04-15T03:55:00+00:00,-3.3302199999999997,0
2019-04-15T04:00:00+00:00,-3.33016,0
2019-04-15T04:05:00+00:00,-3.2933,0
2019-04-15T04:10:00+00:00,-2.96029,0
2019-04-15T04:15:00+00:00,-2.96038,0
2019-04-15T04:20:00+00:00,-2.91717,0
2019-04-15T04:25:00+00:00,-2.59643,0
2019-04-15T04:30:00+00:00,-2.59025,0
2019-04-15T04:35:00+00:00,-2.59023,0
2019-04-15T04:40:00+00:00,-2.59016,0
2019-04-15T04:45:00+00:00,-2.7258299999999998,0
2019-04-15T04:50:00+00:00,-2.99723,0
2019-04-15T04:55:00+00:00,-2.96025,0
2019-04-15T05:00:00+00:00,-3.07743,0
2019-04-15T05:05:00+00:00,-3.39195,0
2019-04-15T05:10:00+00:00,-3.36734,0
2019-04-15T05:15:00+00:00,-3.3303599999999998,0
2019-04-15T05:20:00+00:00,-3.3303800000000003,0
2019-04-15T05:25:00+00:00,-3.18854,0
2019-04-15T05:30:00+00:00,-3.3242300000000005,0
2019-04-15T05:35:00+00:00,-2.9603599999999997,0
2019-04-15T05:40:00+00:00,-2.96037,0
2019-04-15T05:45:00+00:00,-2.95419,0
2019-04-15T05:50:00+00:00,-2.96035,0
2019-04-15T05:55:00+00:00,-2.9603599999999997,0
2019-04-15T06:00:00+00:00,-3.09606,0
2019-04-15T06:05:00+00:00,-2.9603599999999997,0
2019-04-15T06:10:00+00:00,-2.9603200000000003,0
2019-04-15T06:15:00+00:00,-2.96029,0
2019-04-15T06:20:00+00:00,-2.96028,0
2019-04-15T06:25:00+00:00,-2.59024,0
2019-04-15T06:30:00+00:00,-2.59023,0
2019-04-15T06:35:00+00:00,-2.59017,0
2019-04-15T06:40:00+00:00,-2.5901400000000003,0
2019-04-15T06:45:00+00:00,-2.59009,0
2019-04-15T06:50:00+00:00,-2.59008,0
2019-04-15T06:55:00+00:00,-2.59001,0
2019-04-15T07:00:00+00:00,-2.5899900000000002,0
2019-04-15T07:05:00+00:00,-2.62702,0
2019-04-15T07:10:00+00:00,-2.5899900000000002,0
2019-04-15T07:15:00+00:00,-2.58996,0
2019-04-15T07:20:00+00:00,-2.5899400000000004,0
2019-04-15T07:25:00+00:00,-2.58995,0
2019-04-15T07:30:00+00:00,-2.5899099999999997,0
2019-04-15T07:35:00+00:00,-2.5899,0
2019-04-15T07:40:00+00:00,-2.58992,0
2019-04-15T07:45:00+00:00,-2.58993,0
2019-04-15T07:50:00+00:00,-2.58995,0
2019-04-15T07:55:00+00:00,-2.58995,0
2019-04-15T08:00:00+00:00,-2.9291,0
2019-04-15T08:05:00+00:00,-2.95992,0
2019-04-15T08:10:00+00:00,-2.95991,0
2019-04-15T08:15:00+00:00,-3.07707,0
2019-04-15T08:20:00+00:00,-2.9599,0
2019-04-15T08:25:00+00:00,-2.68859,0
2019-04-15T08:30:00+00:00,-2.60227,0
2019-04-15T08:35:00+00:00,-2.67009,0
2019-04-15T08:40:00+00:00,-2.58993,0
2019-04-15T08:45:00+00:00,-2.58992,0
2019-04-15T08:50:00+00:00,-2.58989,0
2019-04-15T08:55:00+00:00,-2.58988,0
2019-04-15T09:00:00+00:00,-2.58988,0
2019-04-15T09:05:00+00:00,-2.58989,0
2019-04-15T09:10:00+00:00,-2.9598400000000002,0
2019-04-15T09:15:00+00:00,-2.91663,0
2019-04-15T09:20:00+00:00,-2.58977,0
2019-04-15T09:25:00+00:00,-2.54041,0
2019-04-15T09:30:00+00:00,-2.25062,0
2019-04-15T09:35:00+00:00,-2.30618,0
2019-04-15T09:40:00+00:00,-2.58982,0
2019-04-15T09:45:00+00:00,-2.58986,0
2019-04-15T09:50:00+00:00,-2.58987,0
2019-04-15T09:55:00+00:00,-2.57755,0
2019-04-15T10:00:00+00:00,-2.58989,0
2019-04-15T10:05:00+00:00,-2.58985,0
2019-04-15T10:10:00+00:00,-2.5897900000000003,0
2019-04-15T10:15:00+00:00,-2.31846,0
2019-04-15T10:20:00+00:00,-2.5897799999999997,0
2019-04-15T10:25:00+00:00,-2.58976,0
2019-04-15T10:30:00+00:00,-2.58974,0
2019-04-15T10:35:00+00:00,-2.44176,0
2019-04-15T10:40:00+00:00,-2.57742,0
2019-04-15T10:45:00+00:00,-2.56506,0
2019-04-15T10:50:00+00:00,-2.42942,0
2019-04-15T10:55:00+00:00,-2.2938,0
2019-04-15T11:00:00+00:00,-2.5342599999999997,0
2019-04-15T11:05:00+00:00,-2.3122700000000003,0
2019-04-15T11:10:00+00:00,-2.21975,0
2019-04-15T11:15:00+00:00,-2.20126,0
2019-04-15T11:20:00+00:00,-2.35545,0
2019-04-15T11:25:00+00:00,-2.58973,0
2019-04-15T11:30:00+00:00,-2.58974,0
2019-04-15T11:35:00+00:00,-2.58976,0
2019-04-15T11:40:00+00:00,-2.7069400000000003,0
2019-04-15T11:45:00+00:00,-2.58983,0
2019-04-15T11:50:00+00:00,-2.58986,0
2019-04-15T11:55:00+00:00,-2.58986,0
2019-04-15T12:00:00+00:00,-2.58982,0
2019-04-15T12:05:00+00:00,-2.5898,0
2019-04-15T12:10:00+00:00,-2.34317,0
2019-04-15T12:15:00+00:00,-2.2199,0
2019-04-15T12:20:00+00:00,-2.13352,0
2019-04-15T12:25:00+00:00,-2.2938099999999997,0
2019-04-15T12:30:00+00:00,-2.27527,0
2019-04-15T12:35:00+00:00,-2.55277,0
2019-04-15T12:40:00+00:00,-2.24453,0
2019-04-15T12:45:00+00:00,-1.2333,0
2019-04-15T12:50:00+00:00,1.51696,0
2019-04-15T12:55:00+00:00,3.3299300000000005,0
2019-04-15T13:00:00+00:00,5.33415,0
2019-04-15T13:05:00+00:00,12.8762,0
2019-04-15T13:10:00+00:00,28.0401,0
2019-04-15T13:15:00+00:00,25.3819,0
2019-04-15T13:20:00+00:00,33.9907,0
2019-04-15T13:25:00+00:00,40.2998,0
2019-04-15T13:30:00+00:00,46.7991,0
2019-04-15T13:35:00+00:00,55.1116,0
2019-04-15T13:40:00+00:00,65.0373,0
2019-04-15T13:45:00+00:00,90.2805,0
2019-04-15T13:50:00+00:00,107.291,0
2019-04-15T13:55:00+00:00,91.751,0
2019-04-15T14:00:00+00:00,93.0265,0
2019-04-15T14:05:00+00:00,119.853,0
2019-04-15T14:10:00+00:00,275.908,0
2019-04-15T14:15:00+00:00,259.889,0
2019-04-15T14:20:00+00:00,297.738,0
2019-04-15T14:25:00+00:00,320.35900000000004,0
2019-04-15T14:30:00+00:00,330.24800000000005,0
2019-04-15T14:35:00+00:00,340.918,0
2019-04-15T14:40:00+00:00,315.414,0
2019-04-15T14:45:00+00:00,323.96299999999997,0
2019-04-15T14:50:00+00:00,391.41,0
2019-04-15T14:55:00+00:00,428.966,0
2019-04-15T15:00:00+00:00,452.981,0
2019-04-15T15:05:00+00:00,436.892,0
2019-04-15T15:10:00+00:00,501.43800000000005,0
2019-04-15T15:15:00+00:00,361.515,0
2019-04-15T15:20:00+00:00,517.174,0
2019-04-15T15:25:00+00:00,553.139,0
2019-04-15T15:30:00+00:00,532.0880000000001,0
2019-04-15T15:35:00+00:00,602.265,0
2019-04-15T15:40:00+00:00,542.089,0
2019-04-15T15:45:00+00:00,619.884,0
2019-04-15T15:50:00+00:00,640.026,0
2019-04-15T15:55:00+00:00,615.5459999999999,0
2019-04-15T16:00:00+00:00,535.669,0
2019-04-15T16:05:00+00:00,663.263,0
2019-04-15T16:10:00+00:00,696.176,0
2019-04-15T16:15:00+00:00,709.57,0
2019-04-15T16:20:00+00:00,720.297,0
2019-04-15T16:25:00+00:00,741.4789999999999,0
2019-04-15T16:30:00+00:00,756.16,0
2019-04-15T16:35:00+00:00,772.105,0
2019-04-15T16:40:00+00:00,787.586,0
2019-04-15T16:45:00+00:00,803.993,0
2019-04-15T16:50:00+00:00,816.363,0
2019-04-15T16:55:00+00:00,830.944,0
2019-04-15T17:00:00+00:00,848.325,0
2019-04-15T17:05:00+00:00,862.183,0
2019-04-15T17:10:00+00:00,844.135,0
2019-04-15T17:15:00+00:00,876.2289999999999,0
2019-04-15T17:20:00+00:00,889.044,0
2019-04-15T17:25:00+00:00,902.704,0
2019-04-15T17:30:00+00:00,912.7310000000001,0
2019-04-15T17:35:00+00:00,923.09,0
2019-04-15T17:40:00+00:00,933.9680000000001,0
2019-04-15T17:45:00+00:00,943.538,0
2019-04-15T17:50:00+00:00,951.5260000000001,0
2019-04-15T17:55:00+00:00,961.005,0
2019-04-15T18:00:00+00:00,967.9910000000001,0
2019-04-15T18:05:00+00:00,977.7189999999999,0
2019-04-15T18:10:00+00:00,984.003,0
2019-04-15T18:15:00+00:00,991.053,0
2019-04-15T18:20:00+00:00,998.3510000000001,0
2019-04-15T18:25:00+00:00,1011.07,0
2019-04-15T18:30:00+00:00,1023.55,0
2019-04-15T18:35:00+00:00,956.725,0
2019-04-15T18:40:00+00:00,673.852,0
2019-04-15T18:45:00+00:00,869.235,0
2019-04-15T18:50:00+00:00,1059.85,0
2019-04-15T18:55:00+00:00,923.8989999999999,0
2019-04-15T19:00:00+00:00,1023.12,0
2019-04-15T19:05:00+00:00,1054.61,0
2019-04-15T19:10:00+00:00,1021.47,0
2019-04-15T19:15:00+00:00,960.933,0
2019-04-15T19:20:00+00:00,1037.77,0
2019-04-15T19:25:00+00:00,885.221,0
2019-04-15T19:30:00+00:00,1037.18,0
2019-04-15T19:35:00+00:00,1032.81,0
2019-04-15T19:40:00+00:00,1024.12,0
2019-04-15T19:45:00+00:00,1030.9,0
2019-04-15T19:50:00+00:00,1035.2,0
2019-04-15T19:55:00+00:00,1031.66,0
2019-04-15T20:00:00+00:00,1029.01,0
2019-04-15T20:05:00+00:00,1030.1,0
2019-04-15T20:10:00+00:00,1022.15,0
2019-04-15T20:15:00+00:00,1040.45,0
2019-04-15T20:20:00+00:00,1013.47,0
2019-04-15T20:25:00+00:00,1044.57,0
2019-04-15T20:30:00+00:00,1046.76,0
2019-04-15T20:35:00+00:00,994.2539999999999,0
2019-04-15T20:40:00+00:00,1000.12,0
2019-04-15T20:45:00+00:00,979.342,0
2019-04-15T20:50:00+00:00,963.86,0
2019-04-15T20:55:00+00:00,954.6339999999999,0
2019-04-15T21:00:00+00:00,945.7539999999999,0
2019-04-15T21:05:00+00:00,932.436,0
2019-04-15T21:10:00+00:00,926.655,0
2019-04-15T21:15:00+00:00,912.58,0
2019-04-15T21:20:00+00:00,885.745,0
2019-04-15T21:25:00+00:00,890.035,0
2019-04-15T21:30:00+00:00,881.33,0
2019-04-15T21:35:00+00:00,873.1110000000001,0
2019-04-15T21:40:00+00:00,862.566,0
2019-04-15T21:45:00+00:00,848.862,0
2019-04-15T21:50:00+00:00,837.1339999999999,0
2019-04-15T21:55:00+00:00,823.7389999999999,0
2019-04-15T22:00:00+00:00,787.9630000000001,0
2019-04-15T22:05:00+00:00,769.363,0
2019-04-15T22:10:00+00:00,741.2410000000001,0
2019-04-15T22:15:00+00:00,722.4060000000001,0
2019-04-15T22:20:00+00:00,743.5419999999999,0
2019-04-15T22:25:00+00:00,707.926,0
2019-04-15T22:30:00+00:00,598.981,0
2019-04-15T22:35:00+00:00,527.816,0
2019-04-15T22:40:00+00:00,384.231,0
2019-04-15T22:45:00+00:00,394.772,0
2019-04-15T22:50:00+00:00,343.18300000000005,0
2019-04-15T22:55:00+00:00,365.339,0
2019-04-15T23:00:00+00:00,316.932,0
2019-04-15T23:05:00+00:00,311.01,0
2019-04-15T23:10:00+00:00,269.47700000000003,0
2019-04-15T23:15:00+00:00,266.522,0
2019-04-15T23:20:00+00:00,323.63,0
2019-04-15T23:25:00+00:00,260.445,0
2019-04-15T23:30:00+00:00,300.435,0
2019-04-15T23:35:00+00:00,240.81400000000002,0
2019-04-15T23:40:00+00:00,261.992,0
2019-04-15T23:45:00+00:00,248.27200000000002,0
2019-04-15T23:50:00+00:00,373.164,0
2019-04-15T23:55:00+00:00,338.93,0
2019-04-16T00:00:00+00:00,447.551,0
2019-04-16T00:05:00+00:00,425.18,0
2019-04-16T00:10:00+00:00,253.859,0
2019-04-16T00:15:00+00:00,250.486,0
2019-04-16T00:20:00+00:00,182.83,0
2019-04-16T00:25:00+00:00,157.441,0
2019-04-16T00:30:00+00:00,160.778,0
2019-04-16T00:35:00+00:00,136.722,0
2019-04-16T00:40:00+00:00,116.979,0
2019-04-16T00:45:00+00:00,95.4898,0
2019-04-16T00:50:00+00:00,99.1536,0
2019-04-16T00:55:00+00:00,81.5057,0
2019-04-16T01:00:00+00:00,76.2751,0
2019-04-16T01:05:00+00:00,98.7015,0
2019-04-16T01:10:00+00:00,138.364,0
2019-04-16T01:15:00+00:00,79.304,0
2019-04-16T01:20:00+00:00,42.3035,0
2019-04-16T01:25:00+00:00,30.6648,0
2019-04-16T01:30:00+00:00,29.0972,0
2019-04-16T01:35:00+00:00,21.0981,0
2019-04-16T01:40:00+00:00,11.9581,0
2019-04-16T01:45:00+00:00,6.61729,0
2019-04-16T01:50:00+00:00,1.87484,0
2019-04-16T01:55:00+00:00,0.080174,0
2019-04-16T02:00:00+00:00,-1.85017,0
2019-04-16T02:05:00+00:00,-2.59026,0
2019-04-16T02:10:00+00:00,-2.95407,0
2019-04-16T02:15:00+00:00,-2.9601900000000003,0
2019-04-16T02:20:00+00:00,-2.9601599999999997,0
2019-04-16T02:25:00+00:00,-2.9108099999999997,0
2019-04-16T02:30:00+00:00,-2.96015,0
2019-04-16T02:35:00+00:00,-2.9601599999999997,0
2019-04-16T02:40:00+00:00,-2.9601599999999997,0
2019-04-16T02:45:00+00:00,-2.88618,0
2019-04-16T02:50:00+00:00,-2.94785,0
2019-04-16T02:55:00+00:00,-2.96017,0
2019-04-16T03:00:00+00:00,-2.9602,0
2019-04-16T03:05:00+00:00,-2.85538,0
2019-04-16T03:10:00+00:00,-2.59021,0
2019-04-16T03:15:00+00:00,-2.5902,0
2019-04-16T03:20:00+00:00,-2.59022,0
2019-04-16T03:25:00+00:00,-2.59024,0
2019-04-16T03:30:00+00:00,-2.59024,0
2019-04-16T03:35:00+00:00,-2.60258,0
2019-04-16T03:40:00+00:00,-2.65192,0
2019-04-16T03:45:00+00:00,-2.70745,0
2019-04-16T03:50:00+00:00,-2.63959,0
2019-04-16T03:55:00+00:00,-2.84312,0
2019-04-16T04:00:00+00:00,-2.8307700000000002,0
2019-04-16T04:05:00+00:00,-2.82457,0
2019-04-16T04:10:00+00:00,-2.96026,0
2019-04-16T04:15:00+00:00,-2.96027,0
2019-04-16T04:20:00+00:00,-2.96025,0
2019-04-16T04:25:00+00:00,-2.9664,0
2019-04-16T04:30:00+00:00,-2.96017,0
2019-04-16T04:35:00+00:00,-2.96015,0
2019-04-16T04:40:00+00:00,-2.96017,0
2019-04-16T04:45:00+00:00,-2.92315,0
2019-04-16T04:50:00+00:00,-2.83682,0
2019-04-16T04:55:00+00:00,-2.94789,0
2019-04-16T05:00:00+00:00,-2.96027,0
2019-04-16T05:05:00+00:00,-2.96026,0
2019-04-16T05:10:00+00:00,-2.95411,0
2019-04-16T05:15:00+00:00,-2.88632,0
2019-04-16T05:20:00+00:00,-2.83701,0
2019-04-16T05:25:00+00:00,-2.9048599999999998,0
2019-04-16T05:30:00+00:00,-2.9603200000000003,0
2019-04-16T05:35:00+00:00,-2.60875,0
2019-04-16T05:40:00+00:00,-2.59026,0
2019-04-16T05:45:00+00:00,-2.69508,0
2019-04-16T05:50:00+00:00,-2.86777,0
2019-04-16T05:55:00+00:00,-2.69506,0
2019-04-16T06:00:00+00:00,-2.59021,0
2019-04-16T06:05:00+00:00,-2.59023,0
2019-04-16T06:10:00+00:00,-2.59022,0
2019-04-16T06:15:00+00:00,-2.59022,0
2019-04-16T06:20:00+00:00,-2.59024,0
2019-04-16T06:25:00+00:00,-2.59023,0
2019-04-16T06:30:00+00:00,-2.59022,0
2019-04-16T06:35:00+00:00,-2.59022,0
2019-04-16T06:40:00+00:00,-2.59023,0
2019-04-16T06:45:00+00:00,-2.59024,0
2019-04-16T06:50:00+00:00,-2.58405,0
2019-04-16T06:55:00+00:00,-2.59019,0
2019-04-16T07:00:00+00:00,-2.59015,0
2019-04-16T07:05:00+00:00,-2.58393,0
2019-04-16T07:10:00+00:00,-2.47913,0
2019-04-16T07:15:00+00:00,-2.54083,0
2019-04-16T07:20:00+00:00,-2.34964,0
2019-04-16T07:25:00+00:00,-2.26333,0
2019-04-16T07:30:00+00:00,-2.57167,0
2019-04-16T07:35:00+00:00,-2.59013,0
2019-04-16T07:40:00+00:00,-2.22627,0
2019-04-16T07:45:00+00:00,-2.26326,0
2019-04-16T07:50:00+00:00,-2.22625,0
2019-04-16T07:55:00+00:00,-2.59008,0
2019-04-16T08:00:00+00:00,-2.5284,0
2019-04-16T08:05:00+00:00,-2.58391,0
2019-04-16T08:10:00+00:00,-2.59001,0
2019-04-16T08:15:00+00:00,-2.59006,0
2019-04-16T08:20:00+00:00,-2.23239,0
2019-04-16T08:25:00+00:00,-2.28786,0
2019-04-16T08:30:00+00:00,-2.33102,0
2019-04-16T08:35:00+00:00,-2.30017,0
2019-04-16T08:40:00+00:00,-2.33714,0
2019-04-16T08:45:00+00:00,-2.27547,0
2019-04-16T08:50:00+00:00,-2.23227,0
2019-04-16T08:55:00+00:00,-2.25694,0
2019-04-16T09:00:00+00:00,-2.36794,0
2019-04-16T09:05:00+00:00,-2.28163,0
2019-04-16T09:10:00+00:00,-2.5899400000000004,0
2019-04-16T09:15:00+00:00,-2.55295,0
2019-04-16T09:20:00+00:00,-2.58995,0
2019-04-16T09:25:00+00:00,-2.58996,0
2019-04-16T09:30:00+00:00,-2.58995,0
2019-04-16T09:35:00+00:00,-1.86847,0
2019-04-16T09:40:00+00:00,-1.8499700000000001,0
2019-04-16T09:45:00+00:00,-2.58997,0
2019-04-16T09:50:00+00:00,-2.58997,0
2019-04-16T09:55:00+00:00,-2.58995,0
2019-04-16T10:00:00+00:00,-2.58993,0
2019-04-16T10:05:00+00:00,-2.5899,0
2019-04-16T10:10:00+00:00,-2.5899,0
2019-04-16T10:15:00+00:00,-2.54675,0
2019-04-16T10:20:00+00:00,-2.2816099999999997,0
2019-04-16T10:25:00+00:00,-2.58993,0
2019-04-16T10:30:00+00:00,-2.58993,0
2019-04-16T10:35:00+00:00,-2.8551,0
2019-04-16T10:40:00+00:00,-2.58992,0
2019-04-16T10:45:00+00:00,-2.22611,0
2019-04-16T10:50:00+00:00,-2.37412,0
2019-04-16T10:55:00+00:00,-2.58995,0
2019-04-16T11:00:00+00:00,-3.08324,0
2019-04-16T11:05:00+00:00,-3.23739,0
2019-04-16T11:10:00+00:00,-3.08324,0
2019-04-16T11:15:00+00:00,-2.58989,0
2019-04-16T11:20:00+00:00,-2.50968,0
2019-04-16T11:25:00+00:00,-2.51578,0
2019-04-16T11:30:00+00:00,-2.41095,0
2019-04-16T11:35:00+00:00,-2.3185,0
2019-04-16T11:40:00+00:00,-2.1705200000000002,0
2019-04-16T11:45:00+00:00,-2.50964,0
2019-04-16T11:50:00+00:00,-2.5898,0
2019-04-16T11:55:00+00:00,-2.58977,0
2019-04-16T12:00:00+00:00,-2.58973,0
2019-04-16T12:05:00+00:00,-2.58356,0
2019-04-16T12:10:00+00:00,-2.18894,0
2019-04-16T12:15:00+00:00,-2.09028,0
2019-04-16T12:20:00+00:00,-1.84982,0
2019-04-16T12:25:00+00:00,-1.9115099999999998,0
2019-04-16T12:30:00+00:00,-2.07183,0
2019-04-16T12:35:00+00:00,-2.21366,0
2019-04-16T12:40:00+00:00,-1.8498299999999999,0
2019-04-16T12:45:00+00:00,-0.653601,0
2019-04-16T12:50:00+00:00,2.61437,0
2019-04-16T12:55:00+00:00,4.0572,0
2019-04-16T13:00:00+00:00,7.22663,0
2019-04-16T13:05:00+00:00,17.3453,0
2019-04-16T13:10:00+00:00,32.329,0
2019-04-16T13:15:00+00:00,49.1626,0
2019-04-16T13:20:00+00:00,64.7622,0
2019-04-16T13:25:00+00:00,83.6739,0
2019-04-16T13:30:00+00:00,92.5838,0
2019-04-16T13:35:00+00:00,90.1717,0
2019-04-16T13:40:00+00:00,112.14399999999999,0
2019-04-16T13:45:00+00:00,164.34799999999998,0
2019-04-16T13:50:00+00:00,234.75599999999997,0
2019-04-16T13:55:00+00:00,246.387,0
2019-04-16T14:00:00+00:00,272.242,0
2019-04-16T14:05:00+00:00,271.619,0
2019-04-16T14:10:00+00:00,286.362,0
2019-04-16T14:15:00+00:00,237.521,0
2019-04-16T14:20:00+00:00,200.06799999999998,0
2019-04-16T14:25:00+00:00,93.2373,0
2019-04-16T14:30:00+00:00,90.6478,0
2019-04-16T14:35:00+00:00,94.2381,0
2019-04-16T14:40:00+00:00,104.932,0
2019-04-16T14:45:00+00:00,120.898,0
2019-04-16T14:50:00+00:00,130.222,0
2019-04-16T14:55:00+00:00,141.884,0
2019-04-16T15:00:00+00:00,216.80200000000002,0
2019-04-16T15:05:00+00:00,288.144,0
2019-04-16T15:10:00+00:00,524.619,0
2019-04-16T15:15:00+00:00,547.526,0
2019-04-16T15:20:00+00:00,140.826,0
2019-04-16T15:25:00+00:00,354.62800000000004,0
2019-04-16T15:30:00+00:00,466.901,0
2019-04-16T15:35:00+00:00,594.6519999999999,0
2019-04-16T15:40:00+00:00,441.285,0
2019-04-16T15:45:00+00:00,539.64,0
2019-04-16T15:50:00+00:00,639.173,0
2019-04-16T15:55:00+00:00,642.967,0
2019-04-16T16:00:00+00:00,658.3919999999999,0
2019-04-16T16:05:00+00:00,679.262,0
2019-04-16T16:10:00+00:00,699.2760000000001,0
2019-04-16T16:15:00+00:00,726.8710000000001,0
2019-04-16T16:20:00+00:00,751.487,0
2019-04-16T16:25:00+00:00,771.829,0
2019-04-16T16:30:00+00:00,728.345,0
2019-04-16T16:35:00+00:00,750.4680000000001,0
2019-04-16T16:40:00+00:00,807.5239999999999,0
2019-04-16T16:45:00+00:00,706.362,0
2019-04-16T16:50:00+00:00,850.466,0
2019-04-16T16:55:00+00:00,940.403,0
2019-04-16T17:00:00+00:00,802.26,0
2019-04-16T17:05:00+00:00,891.529,0
2019-04-16T17:10:00+00:00,289.269,0
2019-04-16T17:15:00+00:00,798.425,0
2019-04-16T17:20:00+00:00,269.858,0
2019-04-16T17:25:00+00:00,329.37,0
2019-04-16T17:30:00+00:00,898.745,0
2019-04-16T17:35:00+00:00,766.643,0
2019-04-16T17:40:00+00:00,1005.39,0
2019-04-16T17:45:00+00:00,887.747,0
2019-04-16T17:50:00+00:00,733.038,0
2019-04-16T17:55:00+00:00,961.1410000000001,0
2019-04-16T18:00:00+00:00,985.0110000000001,0
2019-04-16T18:05:00+00:00,1027.04,0
2019-04-16T18:10:00+00:00,1020.3,0
2019-04-16T18:15:00+00:00,995.9,0
2019-04-16T18:20:00+00:00,1006.89,0
2019-04-16T18:25:00+00:00,1026.46,0
2019-04-16T18:30:00+00:00,1027.81,0
2019-04-16T18:35:00+00:00,1048.59,0
2019-04-16T18:40:00+00:00,1115.36,0
2019-04-16T18:45:00+00:00,1084.52,0
2019-04-16T18:50:00+00:00,1106.36,0
2019-04-16T18:55:00+00:00,1155.42,0
2019-04-16T19:00:00+00:00,794.558,0
2019-04-16T19:05:00+00:00,1197.29,0
2019-04-16T19:10:00+00:00,350.171,0
2019-04-16T19:15:00+00:00,580.599,0
2019-04-16T19:20:00+00:00,1228.67,0
2019-04-16T19:25:00+00:00,1266.43,0
2019-04-16T19:30:00+00:00,1223.9,0
2019-04-16T19:35:00+00:00,1106.54,0
2019-04-16T19:40:00+00:00,1122.57,0
2019-04-16T19:45:00+00:00,1152.58,0
2019-04-16T19:50:00+00:00,719.179,0
2019-04-16T19:55:00+00:00,447.056,0
2019-04-16T20:00:00+00:00,402.275,0
2019-04-16T20:05:00+00:00,595.24,0
2019-04-16T20:10:00+00:00,1173.89,0
2019-04-16T20:15:00+00:00,580.9540000000001,0
2019-04-16T20:20:00+00:00,375.871,0
2019-04-16T20:25:00+00:00,1242.88,0
2019-04-16T20:30:00+00:00,503.10900000000004,0
2019-04-16T20:35:00+00:00,1153.81,0
2019-04-16T20:40:00+00:00,1154.69,0
2019-04-16T20:45:00+00:00,489.097,0
2019-04-16T20:50:00+00:00,401.384,0
2019-04-16T20:55:00+00:00,545.076,0
2019-04-16T21:00:00+00:00,267.79,0
2019-04-16T21:05:00+00:00,196.813,0
2019-04-16T21:10:00+00:00,265.881,0
2019-04-16T21:15:00+00:00,231.655,0
2019-04-16T21:20:00+00:00,296.884,0
2019-04-16T21:25:00+00:00,308.718,0
2019-04-16T21:30:00+00:00,251.62900000000002,0
2019-04-16T21:35:00+00:00,254.757,0
2019-04-16T21:40:00+00:00,311.839,0
2019-04-16T21:45:00+00:00,304.407,0
2019-04-16T21:50:00+00:00,367.164,0
2019-04-16T21:55:00+00:00,311.964,0
2019-04-16T22:00:00+00:00,324.35400000000004,0
2019-04-16T22:05:00+00:00,387.246,0
2019-04-16T22:10:00+00:00,279.862,0
2019-04-16T22:15:00+00:00,164.74900000000002,0
2019-04-16T22:20:00+00:00,117.959,0
2019-04-16T22:25:00+00:00,139.999,0
2019-04-16T22:30:00+00:00,133.882,0
2019-04-16T22:35:00+00:00,98.0075,0
2019-04-16T22:40:00+00:00,82.1886,0
2019-04-16T22:45:00+00:00,93.1478,0
2019-04-16T22:50:00+00:00,102.325,0
2019-04-16T22:55:00+00:00,151.645,0
2019-04-16T23:00:00+00:00,137.683,0
2019-04-16T23:05:00+00:00,243.864,0
2019-04-16T23:10:00+00:00,208.706,0
2019-04-16T23:15:00+00:00,121.73,0
2019-04-16T23:20:00+00:00,107.057,0
2019-04-16T23:25:00+00:00,43.7813,0
2019-04-16T23:30:00+00:00,48.154,0
2019-04-16T23:35:00+00:00,63.4735,0
2019-04-16T23:40:00+00:00,54.4389,0
2019-04-16T23:45:00+00:00,69.6048,0
2019-04-16T23:50:00+00:00,68.4514,0
2019-04-16T23:55:00+00:00,65.0645,0
2019-04-17T00:00:00+00:00,71.5086,0
2019-04-17T00:05:00+00:00,139.45600000000002,0
2019-04-17T00:10:00+00:00,173.799,0
2019-04-17T00:15:00+00:00,170.15400000000002,0
2019-04-17T00:20:00+00:00,115.132,0
2019-04-17T00:25:00+00:00,75.0135,0
2019-04-17T00:30:00+00:00,63.6482,0
2019-04-17T00:35:00+00:00,95.7993,0
2019-04-17T00:40:00+00:00,43.5426,0
2019-04-17T00:45:00+00:00,37.5979,0
2019-04-17T00:50:00+00:00,71.2115,0
2019-04-17T00:55:00+00:00,53.3279,0
2019-04-17T01:00:00+00:00,32.997,0
2019-04-17T01:05:00+00:00,16.6621,0
2019-04-17T01:10:00+00:00,7.67766,0
2019-04-17T01:15:00+00:00,4.32305,0
2019-04-17T01:20:00+00:00,3.5645599999999997,0
2019-04-17T01:25:00+00:00,2.1276599999999997,0
2019-04-17T01:30:00+00:00,3.36729,0
2019-04-17T01:35:00+00:00,1.8378400000000001,0
2019-04-17T01:40:00+00:00,0.7339,0
2019-04-17T01:45:00+00:00,-0.104843,0
2019-04-17T01:50:00+00:00,-0.740074,0
2019-04-17T01:55:00+00:00,-1.4801600000000001,0
2019-04-17T02:00:00+00:00,-1.8501900000000002,0
2019-04-17T02:05:00+00:00,-1.65283,0
2019-04-17T02:10:00+00:00,-2.59021,0
2019-04-17T02:15:00+00:00,-2.96022,0
2019-04-17T02:20:00+00:00,-2.45443,0
2019-04-17T02:25:00+00:00,-1.85005,0
2019-04-17T02:30:00+00:00,-1.8500299999999998,0
2019-04-17T02:35:00+00:00,-1.85,0
2019-04-17T02:40:00+00:00,-2.20764,0
2019-04-17T02:45:00+00:00,-1.8499700000000001,0
2019-04-17T02:50:00+00:00,-1.6402900000000002,0
2019-04-17T02:55:00+00:00,-1.85612,0
2019-04-17T03:00:00+00:00,-1.8499700000000001,0
2019-04-17T03:05:00+00:00,-1.81913,0
2019-04-17T03:10:00+00:00,-1.67113,0
2019-04-17T03:15:00+00:00,-1.84995,0
2019-04-17T03:20:00+00:00,-1.8067900000000001,0
2019-04-17T03:25:00+00:00,-1.8499599999999998,0
2019-04-17T03:30:00+00:00,-1.9856200000000002,0
2019-04-17T03:35:00+00:00,-2.95995,0
2019-04-17T03:40:00+00:00,-2.34331,0
2019-04-17T03:45:00+00:00,-1.51698,0
2019-04-17T03:50:00+00:00,-2.33712,0
2019-04-17T03:55:00+00:00,-4.82225,0
2019-04-17T04:00:00+00:00,-3.9835,0
2019-04-17T04:05:00+00:00,-2.30004,0
2019-04-17T04:10:00+00:00,-2.2198,0
2019-04-17T04:15:00+00:00,-2.90423,0
2019-04-17T04:20:00+00:00,-3.32355,0
2019-04-17T04:25:00+00:00,-2.8610700000000002,0
2019-04-17T04:30:00+00:00,-2.5897900000000003,0
2019-04-17T04:35:00+00:00,-2.21365,0
2019-04-17T04:40:00+00:00,-2.78091,0
2019-04-17T04:45:00+00:00,-3.3296900000000003,0
2019-04-17T04:50:00+00:00,-3.5455,0
2019-04-17T04:55:00+00:00,-2.9597599999999997,0
2019-04-17T05:00:00+00:00,-3.3112,0
2019-04-17T05:05:00+00:00,-2.5898,0
2019-04-17T05:10:00+00:00,-2.58981,0
2019-04-17T05:15:00+00:00,-2.5897799999999997,0
2019-04-17T05:20:00+00:00,-2.5897799999999997,0
2019-04-17T05:25:00+00:00,-1.85601,0
2019-04-17T05:30:00+00:00,-1.8498299999999999,0
2019-04-17T05:35:00+00:00,-1.84981,0
2019-04-17T05:40:00+00:00,-1.84981,0
2019-04-17T05:45:00+00:00,-1.84978,0
2019-04-17T05:50:00+00:00,-1.84978,0
2019-04-17T05:55:00+00:00,-1.8497700000000001,0
2019-04-17T06:00:00+00:00,-1.76964,0
2019-04-17T06:05:00+00:00,-1.51683,0
2019-04-17T06:10:00+00:00,-1.15921,0
2019-04-17T06:15:00+00:00,-1.49834,0
2019-04-17T06:20:00+00:00,-1.51068,0
2019-04-17T06:25:00+00:00,-1.1961899999999999,0
2019-04-17T06:30:00+00:00,-1.84981,0
2019-04-17T06:35:00+00:00,-1.8498700000000001,0
2019-04-17T06:40:00+00:00,-2.18287,0
2019-04-17T06:45:00+00:00,-1.91156,0
2019-04-17T06:50:00+00:00,-1.84988,0
2019-04-17T06:55:00+00:00,-1.8498599999999998,0
"""
    obs_df = pd.read_csv(StringIO(ghi_csv))
    obs_df = obs_df.set_index('timestamp')
    obs_df.index = pd.to_datetime(obs_df.index)
    obs_df.index.name = 'timestamp'
    return obs_df


@pytest.fixture
def new_role(api):
    def fn(**kwargs):
        role_json = ROLE.copy()
        role_json.update(kwargs)
        role = api.post(f'/roles/', BASE_URL, json=role_json)
        role_id = role.data.decode('utf-8')
        return role_id
    return fn


@pytest.fixture
def new_observation(api):
    def fn():
        obs = api.post(f'/observations/', BASE_URL, json=VALID_OBS_JSON)
        obs_id = obs.data.decode('utf-8')
        return obs_id
    return fn


@pytest.fixture
def new_forecast(api):
    def fn():
        fx = api.post(f'/forecasts/single/', BASE_URL,
                      json=VALID_FORECAST_JSON)
        fx_id = fx.data.decode('utf-8')
        return fx_id
    return fn


@pytest.fixture
def new_perm(api):
    def fn(**kwargs):
        perm_json = PERMISSION.copy()
        perm_json.update(kwargs)
        perm = api.post(f'/permissions/', BASE_URL, json=perm_json)
        perm_id = perm.data.decode('utf-8')
        return perm_id
    return fn


@pytest.fixture
def current_roles(api):
    roles_req = api.get('/roles/', BASE_URL)
    return [role['role_id'] for role in roles_req.json]


@pytest.fixture
def current_role(api, current_roles):
    return current_roles[0]


@pytest.fixture
def remove_perms_from_current_role(api, current_role):
    def fn(action, object_type):
        perm_req = api.get('/permissions/', BASE_URL)
        perms = perm_req.json
        to_remove = [perm['permission_id'] for perm in perms
                     if perm['object_type'] == object_type
                     and perm['action'] == action]
        for perm_id in to_remove:
            api.delete(f'/roles/{current_role}/permissions/{perm_id}',
                       BASE_URL)
    return fn


@pytest.fixture
def remove_all_perms(api, current_roles):
    def fn(action, object_type):
        perm_req = api.get('/permissions/', BASE_URL)
        perms = perm_req.json
        to_remove = [perm['permission_id'] for perm in perms
                     if perm['object_type'] == object_type
                     and perm['action'] == action]
        for role_id in current_roles:
            for perm_id in to_remove:
                api.delete(f'/roles/{role_id}/permissions/{perm_id}',
                           BASE_URL)
    return fn


@pytest.fixture
def random_post_payload():
    def fn(npts, mimetype, include_flags=True):
        idx = pd.date_range(
            start=pd.to_datetime('2017-01-01T00:00Z'),
            periods=npts,
            freq='1min'
        )
        data = {'value': np.random.uniform(0, 999.9, size=idx.size)}
        if include_flags:
            data['quality_flags'] = 0
        df = pd.DataFrame(data=data, index=idx)
        if mimetype == 'application/json':
            value_string = json.dumps({
                'values': df.to_dict(orient='records')
            })
        else:
            value_string = df.to_csv(index=False)
        return value_string
    return fn
