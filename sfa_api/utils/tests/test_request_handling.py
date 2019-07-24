import pandas as pd
import pytest


from sfa_api.utils import request_handling
from sfa_api.utils.errors import BadAPIRequest


@pytest.mark.parametrize('start,end', [
    ('invalid', 'invalid')
])
def test_validate_start_end_fail(app, forecast_id, start, end):
    url = f'/forecasts/single/{forecast_id}/values?start={start}&end={end}'
    with pytest.raises(request_handling.BadAPIRequest):
        with app.test_request_context(url):
            request_handling.validate_start_end()


@pytest.mark.parametrize('start,end', [
    ('20190101T120000Z', '20190101T130000Z'),
])
def test_validate_start_end_success(app, forecast_id, start, end):
    url = f'/forecasts/single/{forecast_id}/values?start={start}&end={end}'
    with app.test_request_context(url):
        request_handling.validate_start_end()


@pytest.mark.parametrize('content_type,payload', [
    ('text/csv', ''),
    ('application/json', '{}'),
    ('application/json', '{"values": "nope"}'),
    ('text/plain', 'nope'),
])
def test_validate_parsable_fail(app, content_type, payload, forecast_id):
    url = f'/forecasts/single/{forecast_id}/values/'
    with pytest.raises(request_handling.BadAPIRequest):
        with app.test_request_context(url, content_type=content_type,
                                      data=payload, method='POST'):
            request_handling.validate_parsable_values()


@pytest.mark.parametrize('content_type,payload', [
    ('text/csv', 'timestamp,value\n2019-01-01T12:00:00Z,5'),
    ('application/json', ('{"values":[{"timestamp": "2019-01-01T12:00:00Z",'
                          '"value": 5}]}')),
])
def test_validate_parsable_success(app, content_type, payload, forecast_id):
    with app.test_request_context(f'/forecasts/single/{forecast_id}/values/',
                                  content_type=content_type, data=payload,
                                  method='POST'):
        request_handling.validate_parsable_values()


def test_validate_observation_values():
    df = pd.DataFrame({'value': [0.1, '.2'],
                       'quality_flag': [0.0, 1],
                       'timestamp': ['20190101T0000Z',
                                     '2019-01-01T03:00:00+07:00']})
    request_handling.validate_observation_values(df)


def test_validate_observation_values_bad_value():
    df = pd.DataFrame({'value': [0.1, 's.2'],
                       'quality_flag': [0.0, 1],
                       'timestamp': ['20190101T0000Z',
                                     '2019-01-01T03:00:00+07:00']})
    with pytest.raises(BadAPIRequest) as e:
        request_handling.validate_observation_values(df)
    assert 'value' in e.value.errors


def test_validate_observation_values_no_value():
    df = pd.DataFrame({'quality_flag': [0.0, 1],
                       'timestamp': ['20190101T0000Z',
                                     '2019-01-01T03:00:00+07:00']})
    with pytest.raises(BadAPIRequest) as e:
        request_handling.validate_observation_values(df)
    assert 'value' in e.value.errors


def test_validate_observation_values_bad_timestamp():
    df = pd.DataFrame({'value': [0.1, '.2'],
                       'quality_flag': [0.0, 1],
                       'timestamp': ['20190101T008Z',
                                     '2019-01-01T03:00:00+07:00']})
    with pytest.raises(BadAPIRequest) as e:
        request_handling.validate_observation_values(df)
    assert 'timestamp' in e.value.errors


def test_validate_observation_values_no_timestamp():
    df = pd.DataFrame({
        'value': [0.1, '.2'], 'quality_flag': [0.0, 1]})
    with pytest.raises(BadAPIRequest) as e:
        request_handling.validate_observation_values(df)
    assert 'timestamp' in e.value.errors


@pytest.mark.parametrize('quality', [
    [1, .1],
    [1, '0.9'],
    [2, 0],
    ['ham', 0]
])
def test_validate_observation_values_bad_quality(quality):
    df = pd.DataFrame({'value': [0.1, .2],
                       'quality_flag': quality,
                       'timestamp': ['20190101T008Z',
                                     '2019-01-01T03:00:00+07:00']})
    with pytest.raises(BadAPIRequest) as e:
        request_handling.validate_observation_values(df)
    assert 'quality_flag' in e.value.errors


def test_validate_observation_values_no_quality():
    df = pd.DataFrame({'value': [0.1, '.2'],
                       'timestamp': ['20190101T008Z',
                                     '2019-01-01T03:00:00+07:00']})
    with pytest.raises(BadAPIRequest) as e:
        request_handling.validate_observation_values(df)
    assert 'quality_flag' in e.value.errors


def test_parse_csv():
    pass


def test_parse_json():
    pass
