import pytest
from sfa_api import create_app


@pytest.fixture()
def api():
    app = create_app(config_name='TestingConfig')
    api = app.test_client()
    return api
