import os

import pytest

from sfa_api import create_app


@pytest.fixture()
def api():
    if not os.getenv('SFA_API_STATIC_DATA'):
        os.environ['SFA_API_STATIC_DATA'] = 'true'
    app = create_app(config_name='TestingConfig')
    api = app.test_client()
    return api
