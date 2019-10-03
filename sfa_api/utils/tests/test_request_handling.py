import pandas as pd
import pandas.testing as pdt
import pytest


from sfa_api.utils import request_handling
from sfa_api.utils.errors import BadAPIRequest


@pytest.mark.parametrize('start,end', [
    ('invalid', 'invalid'),
    ('NaT', 'NaT')
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


expected_parsed_df = pd.DataFrame({
    'a': [1, 2, 3, 4],
    'b': [4, 5, 6, 7],
})
csv_string = "a,b\n1,4\n2,5\n3,6\n4,7\n"
json_string = '{"values":{"a":[1,2,3,4],"b":[4,5,6,7]}}'


def test_parse_csv_success():
    test_df = request_handling.parse_csv(csv_string)
    pdt.assert_frame_equal(test_df, expected_parsed_df)


@pytest.mark.parametrize('csv_input', [
    '',
    "a,b\n1,4\n2.56,2.45\n1,2,3\n"
])
def test_parse_csv_failure(csv_input):
    with pytest.raises(request_handling.BadAPIRequest):
        request_handling.parse_csv(csv_input)


def test_parse_json_success():
    test_df = request_handling.parse_json(json_string)
    pdt.assert_frame_equal(test_df, expected_parsed_df)


@pytest.mark.parametrize('json_input', [
    '',
    "{'a':[1,2,3]}"
])
def test_parse_json_failure(json_input):
    with pytest.raises(request_handling.BadAPIRequest):
        request_handling.parse_json(json_input)


@pytest.mark.parametrize('data,mimetype', [
    (csv_string, 'text/csv'),
    (csv_string, 'application/vnd.ms-excel'),
    (json_string, 'application/json')
])
def test_parse_values_success(data, mimetype):
    test_df = request_handling.parse_values(data, mimetype)
    pdt.assert_frame_equal(test_df, expected_parsed_df)


@pytest.mark.parametrize('data,mimetype', [
    (csv_string, 'application/fail'),
    (json_string, 'image/bmp'),
])
def test_parse_values_failure(data, mimetype):
    with pytest.raises(request_handling.BadAPIRequest):
        request_handling.parse_values(data, mimetype)


@pytest.mark.parametrize('dt_string,expected', [
    ('20190101T1200Z', pd.Timestamp('20190101T1200Z')),
    ('20190101T1200', pd.Timestamp('20190101T1200')),
    ('20190101T1200+0700', pd.Timestamp('20190101T0500Z'))
])
def test_parse_to_timestamp(dt_string, expected):
    parsed_dt = request_handling.parse_to_timestamp(dt_string)
    assert parsed_dt == expected


@pytest.mark.parametrize('dt_string', [
    'invalid datetime',
    '21454543251345234',
    '20190101T2500Z',
    'NaT',
])
def test_parse_to_timestamp_error(dt_string):
    with pytest.raises(ValueError):
        request_handling.parse_to_timestamp(dt_string)


@pytest.mark.parametrize('index,interval_length', [
    (pd.date_range(start='2019-09-01T1200Z', end='2019-09-01T1300Z',
                   freq='10min'), 10),
    (pd.DatetimeIndex(['2019-09-01T0000Z', '2019-09-01T0200Z',
                       '2019-09-01T0400Z']), 120),
    (pd.DatetimeIndex(['2019-09-01T0006Z', '2019-09-01T0011Z',
                       '2019-09-01T0016Z']), 5),
    (pd.DatetimeIndex(['2019-09-01T0006Z', '2019-09-01T0013Z',
                       '2019-09-01T0020Z']), 7),
    (pd.date_range(start='2019-03-10 00:00', end='2019-03-10 05:00',
                   tz='America/Denver', freq='1h'), 60),  # DST transition
    (pd.date_range(start='2019-11-03 00:00', end='2019-11-03 05:00',
                   tz='America/Denver', freq='1h'), 60),  # DST transition
    (pd.DatetimeIndex(['2019-01-01T000132Z']), 33)
])
def test_validate_index_period(index, interval_length):
    request_handling.validate_index_period(index, interval_length)


def test_validate_index_empty():
    with pytest.raises(request_handling.BadAPIRequest):
        request_handling.validate_index_period(pd.DatetimeIndex([]), 10)


@pytest.mark.parametrize('index,interval_length', [
    (pd.DatetimeIndex(['2019-09-01T0000Z', '2019-09-01T0200Z',
                       '2019-09-01T0300Z']), 60),
    (pd.DatetimeIndex(['2019-09-01T0000Z', '2019-09-01T0030Z',
                       '2019-09-01T0300Z']), 30),
    (pd.date_range(start='2019-09-01T1200Z', end='2019-09-01T1300Z',
                   freq='20min'), 10),
])
def test_validate_index_period_missing(index, interval_length):
    with pytest.raises(request_handling.BadAPIRequest) as e:
        request_handling.validate_index_period(index, interval_length)
    errs = e.value.errors['timestamp']
    assert len(errs) == 1
    assert 'Missing' in errs[0]


@pytest.mark.parametrize('index,interval_length', [
    (pd.DatetimeIndex(['2019-09-01T0000Z', '2019-09-01T0100Z',
                       '2019-09-01T0200Z']), 120),
    (pd.DatetimeIndex(['2019-09-01T0000Z', '2019-09-01T0030Z',
                       '2019-09-01T0045Z']), 30),
    (pd.date_range(start='2019-09-01T1200Z', end='2019-09-01T1300Z',
                   freq='5min'), 10),
])
def test_validate_index_period_extra(index, interval_length):
    with pytest.raises(request_handling.BadAPIRequest) as e:
        request_handling.validate_index_period(index, interval_length)
    errs = e.value.errors['timestamp']
    assert len(errs) == 1
    assert 'extra' in errs[0]


@pytest.mark.parametrize('index,interval_length', [
    (pd.DatetimeIndex(['2019-09-01T0000Z', '2019-09-01T0100Z',
                       '2019-09-01T0201Z']), 120),
    (pd.DatetimeIndex(['2019-09-01T0000Z', '2019-09-01T0030Z',
                       '2019-09-01T0130Z']), 30),
    (pd.date_range(start='2019-09-01T1200Z', end='2019-09-01T1305Z',
                   freq='5min'), 10),
])
def test_validate_index_period_other(index, interval_length):
    with pytest.raises(request_handling.BadAPIRequest) as e:
        request_handling.validate_index_period(index, interval_length)
    errs = e.value.errors['timestamp']
    assert len(errs) > 0
