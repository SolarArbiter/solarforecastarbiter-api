import os

import pytest

from sfa_api import create_app



@pytest.fixture()
def app():
    if not os.getenv('SFA_API_STATIC_DATA'):
        os.environ['SFA_API_STATIC_DATA'] = 'true'
    app = create_app(config_name='TestingConfig')
    return app


@pytest.fixture()
def api(app):
    api = app.test_client()
    return api


@pytest.fixture()
def missing_id():
    return '7d2c3208-5243-11e9-8647-d663bd873d93'


@pytest.fixture()
def observation_id():
    return '123e4567-e89b-12d3-a456-426655440000'


@pytest.fixture()
def missing_observation_id():
    return '123e4567-e89b-12d3-a456-426655440007'


@pytest.fixture()
def cdf_forecast_group_id():
    return 'ef51e87c-50b9-11e9-8647-d663bd873d93'


@pytest.fixture()
def cdf_forecast_id():
    return '633f9396-50bb-11e9-8647-d663bd873d93'


@pytest.fixture()
def forecast_id():
    return 'f8dd49fa-23e2-48a0-862b-ba0af6dec276'


@pytest.fixture()
def missing_forecast_id():
    return 'f8dd49fa-23e2-48a0-862b-ba0afaaaaaa6'


@pytest.fixture()
def site_id():
    return 'd2018f1d-82b1-422a-8ec4-4e8b3fe92a4a'


@pytest.fixture()
def site_id_plant():
    return '123e4567-e89b-12d3-a456-426655440002'


@pytest.fixture()
def missing_site_id():
    return '123e4567-e89b-12d3-a456-000055440002'
