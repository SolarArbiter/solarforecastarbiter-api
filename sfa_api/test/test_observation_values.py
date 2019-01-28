import pandas as pd
import pytest


import sfa_api
from sfa_api import create_app


VALID_JSON = {
    'id': 'xxx-xxxx-xxxxxxxxxxxxx',
    'values': [
        {'questionable': 0,
         'timestamp': "2019-01-22T17:54:36Z",
         'value': 1},
        {'questionable': 0,
         'timestamp': "2019-01-22T17:55:36Z",
         'value': '32.96'},
        {'questionable': 0,
         'timestamp': "2019-01-22T17:56:36Z",
         'value': 3}
    ]
}
WRONG_DATE_FORMAT_JSON = {
    'values': [
        {'questionable': 0,
         'timestamp': '20-2-3T11111F',
         'value': 3},
    ]
}
NON_NUMERICAL_VALUE_JSON = {
    'values': [
        {'questionable': 0,
         'timestamp': "2019-01-22T17:56:36Z",
         'value': 'four'},
    ]
}
NON_BINARY_FLAG_JSON = {
    'values': [
        {'questionable': 'ham',
         'timestamp': "2019-01-22T17:56:36Z",
         'value': 3},
    ]
}
VALID_CSV = "#I am a header comment, I am going to be ignored\ntimestamp,value,questionable\n2018-10-29T12:04:23Z,32.93,0\n2018-10-29T12:05:23Z,32.93,0\n2018-10-29T12:06:23Z,32.93,0\n2018-10-29T12:07:23Z,32.93,0\n" # NOQA
WRONG_DATE_FORMAT_CSV = "timestamp,value,questionable\nksdfjgn,32.93,0"
NON_NUMERICAL_VALUE_CSV = "timestamp,value,questionable\n2018-10-29T12:04:23Z,fgh,0" # NOQA
NON_BINARY_FLAG_CSV = "timestamp,value,questionable\n2018-10-29T12:04:23Z,32.93,B" # NOQA


@pytest.fixture()
def app():
    app = create_app(config_name='TestingConfig')
    return app


# TODO: mock retrieval request to return a static observation for testing
def test_post_observation_balues_valid_json(app):
    with app.test_client() as api:
        r = api.post('/observations/7365da38-2ee5-46ed-bd48-c84c4cc5a6c8/values',
                     base_url='https://localhost',
                     json=VALID_JSON)
        assert r.status_code == 201


def test_post_json_storage_call(app, mocker):
    mocker.patch('sfa_api.utils.storage.store_observation_values')
    data = pd.DataFrame(VALID_JSON['values'])
    data['timestamp'] = pd.to_datetime(data['timestamp'], utc=True)
    data['value'] = pd.to_numeric(data['value'], downcast="float")
    with app.test_client() as api:
        api.get('/observations/7365da38-2ee5-46ed-bd48-c84c4cc5a6c8/values',
                base_url='https://localhost',
                json=VALID_JSON)
        sfa_api.utils.storage.store_observation_values.asser_called_with(
            obs_id='7365da38-2ee5-46ed-bd48-c84c4cc5a6c8',
            observation_df=data)


@pytest.mark.parametrize('payload',
    ['taco',
     {},
     WRONG_DATE_FORMAT_JSON,
     NON_NUMERICAL_VALUE_JSON,
     NON_BINARY_FLAG_JSON])
def test_post_observation_values_invalid_json(app, payload):
    with app.test_client() as api:
        r = api.post('/observations/7365da38-2ee5-46ed-bd48-c84c4cc5a6c8/values',
                     base_url='https://localhost',
                     json=payload)
        assert r.status_code == 400


@pytest.mark.parametrize('payload',
    ['taco',
     '',
     WRONG_DATE_FORMAT_CSV,
     NON_NUMERICAL_VALUE_CSV,
     NON_BINARY_FLAG_CSV])
def test_post_observation_values_invalid_csv(app, payload):
    with app.test_client() as api:
        r = api.post('/observations/7365da38-2ee5-46ed-bd48-c84c4cc5a6c8/values',
                     base_url='https://localhost',
                     headers={'Content-Type': 'text/csv'},
                     data=payload)
        assert r.status_code == 400


def test_post_observation_values_valid_csv(app):
    with app.test_client() as api:
        r = api.post('/observations/7365da38-2ee5-46ed-bd48-c84c4cc5a6c8/values',
                     base_url='https://localhost',
                     headers={'Content-Type': 'text/csv'},
                     data=VALID_CSV)
        assert r.status_code == 201
