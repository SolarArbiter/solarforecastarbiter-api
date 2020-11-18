import pandas as pd
import pandas.testing as pdt
import pytest
import pytz
from werkzeug.exceptions import RequestEntityTooLarge


from sfa_api.conftest import (
    VALID_FORECAST_JSON, VALID_CDF_FORECAST_JSON, demo_forecasts)
from sfa_api.utils import request_handling
from sfa_api.utils.errors import (
    BadAPIRequest, StorageAuthError, NotFoundException)


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
    ('20190101T120000', '20190101T130000'),
    ('20190101T120000', '20190101T130000Z'),
    ('20190101T120000Z', '20190101T130000+00:00'),
    ('20190101T120000Z', '20190101T140000+01:00'),
])
def test_validate_start_end_success(app, forecast_id, start, end):
    url = f'/forecasts/single/{forecast_id}/values?start={start}&end={end}'
    with app.test_request_context(url):
        request_handling.validate_start_end()


@pytest.mark.parametrize('query,exc', [
    ('?start=20200101T0000Z', {'end'}),
    ('?end=20200101T0000Z', {'start'}),
    ('?start=20200101T0000Z&end=20210102T0000Z', {'end'}),
    ('', {'start', 'end'}),
    pytest.param('?start=20200101T0000Z&end=20200102T0000Z', {},
                 marks=pytest.mark.xfail(strict=True))
])
def test_validate_start_end_not_provided(app, forecast_id, query, exc):
    url = f'/forecasts/single/{forecast_id}/values{query}'
    with app.test_request_context(url):
        with pytest.raises(BadAPIRequest) as err:
            request_handling.validate_start_end()
        if exc:
            assert set(err.value.errors.keys()) == exc


@pytest.mark.parametrize('content_type,payload', [
    ('text/csv', ''),
    ('application/json', '{}'),
    ('application/json', '{"values": "nope"}'),
    ('text/plain', 'nope'),
])
def test_validate_parsable_fail(app, content_type, payload, forecast_id):
    url = f'/forecasts/single/{forecast_id}/values/'
    with pytest.raises(request_handling.BadAPIRequest):
        with app.test_request_context(
                url, content_type=content_type, data=payload, method='POST',
                content_length=len(payload)):
            request_handling.validate_parsable_values()


@pytest.mark.parametrize('content_type', [
    ('text/csv'),
    ('application/json'),
    ('application/json'),
])
def test_validate_parsable_fail_too_large(app, content_type, forecast_id):
    url = f'/forecasts/single/{forecast_id}/values/'
    with pytest.raises(RequestEntityTooLarge):
        with app.test_request_context(
                url, content_type=content_type, method='POST',
                content_length=17*1024*1024):
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


def test_parse_csv_windows():
    cs = '\ufeffa,b\r\n1,4\r\n2,5\r\n3,6\r\n4,7\r\n'
    test_df = request_handling.parse_csv(cs)
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


null_df = pd.DataFrame({
    'timestamp': [
        '2018-10-29T12:00:00Z',
        '2018-10-29T13:00:00Z',
        '2018-10-29T14:00:00Z',
        '2018-10-29T15:00:00Z',
    ],
    'value': [32.93, 25.17, None, None],
    'quality_flag': [0, 0, 1, 0]
})


def test_parse_csv_nan():
    test_df = request_handling.parse_csv("""
# comment line
timestamp,value,quality_flag
2018-10-29T12:00:00Z,32.93,0
2018-10-29T13:00:00Z,25.17,0
2018-10-29T14:00:00Z,,1  # this value is NaN
2018-10-29T15:00:00Z,NaN,0
""")
    pdt.assert_frame_equal(test_df, null_df)


def test_parse_json_nan():
    test_df = request_handling.parse_json("""
{"values":[
  {"timestamp": "2018-10-29T12:00:00Z", "value": 32.93, "quality_flag": 0},
  {"timestamp": "2018-10-29T13:00:00Z", "value": 25.17, "quality_flag": 0},
  {"timestamp": "2018-10-29T14:00:00Z", "value": null, "quality_flag": 1},
  {"timestamp": "2018-10-29T15:00:00Z", "value": null, "quality_flag": 0}
]}
""")
    pdt.assert_frame_equal(test_df, null_df)


@pytest.mark.parametrize('data,mimetype', [
    (csv_string, 'text/csv'),
    (csv_string, 'application/vnd.ms-excel'),
    (json_string, 'application/json')
])
def test_parse_values_success(app, data, mimetype):
    with app.test_request_context():
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
    ('20190101T1200', pd.Timestamp('20190101T1200Z')),
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


@pytest.mark.parametrize('index,interval_length,previous_time', [
    (pd.date_range(start='2019-09-01T1200Z', end='2019-09-01T1300Z',
                   freq='10min'), 10, pd.Timestamp('2019-09-01T1150Z')),
    (pd.DatetimeIndex(['2019-09-01T0000Z', '2019-09-01T0200Z',
                       '2019-09-01T0400Z']), 120, None),
    (pd.DatetimeIndex(['2019-09-01T0006Z', '2019-09-01T0011Z',
                       '2019-09-01T0016Z']),
     5,
     pd.Timestamp('2019-09-01T0001Z')),
    (pd.DatetimeIndex(['2019-09-01T0006Z', '2019-09-01T0013Z',
                       '2019-09-01T0020Z']),
     7,
     pd.Timestamp('2019-08-31T2352Z')),
    # out of order
    pytest.param(
        pd.DatetimeIndex(['2019-09-01T0013Z', '2019-09-01T0006Z',
                          '2019-09-01T0020Z']),
        7,
        pd.Timestamp('2019-08-31T2352Z'), marks=pytest.mark.xfail),
    (pd.date_range(start='2019-03-10 00:00', end='2019-03-10 05:00',
                   tz='America/Denver', freq='1h'),
     60, None),  # DST transition
    (pd.date_range(start='2019-11-03 00:00', end='2019-11-03 05:00',
                   tz='America/Denver', freq='1h'),
     60, None),  # DST transition
    (pd.DatetimeIndex(['2019-01-01T000132Z']), 33, None),
    (pd.DatetimeIndex(['2019-01-01T000132Z']), 30,
     pd.Timestamp('2018-12-01T000132Z')),
    (pd.DatetimeIndex(['2019-01-01T000132Z']), 30,
     pd.Timestamp('2019-01-02T000132Z'))
])
def test_validate_index_period(index, interval_length, previous_time):
    request_handling.validate_index_period(index, interval_length,
                                           previous_time)


def test_validate_index_empty():
    with pytest.raises(request_handling.BadAPIRequest):
        request_handling.validate_index_period(pd.DatetimeIndex([]), 10,
                                               None)


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
        request_handling.validate_index_period(index, interval_length,
                                               index[0])
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
        request_handling.validate_index_period(index, interval_length,
                                               index[0])
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
        request_handling.validate_index_period(index, interval_length,
                                               index[0])
    errs = e.value.errors['timestamp']
    assert len(errs) > 0


@pytest.mark.parametrize('index,interval_length,previous_time', [
    (pd.date_range(start='2019-09-01T1200Z', end='2019-09-01T1300Z',
                   freq='10min'), 10, pd.Timestamp('2019-09-01T1155Z')),
    (pd.DatetimeIndex(['2019-09-01T0006Z', '2019-09-01T0011Z',
                       '2019-09-01T0016Z']),
     5,
     pd.Timestamp('2019-09-01T0000Z')),
    (pd.DatetimeIndex(['2019-09-01T0006Z', '2019-09-01T0013Z',
                       '2019-09-01T0020Z']),
     7,
     pd.Timestamp('2019-09-01T0000Z')),
    (pd.DatetimeIndex(['2019-01-01T000132Z']), 30,
     pd.Timestamp('2018-12-01T000232Z')),
    (pd.DatetimeIndex(['2019-01-01T000132Z']), 30,
     pd.Timestamp('2020-12-01T000232Z'))
])
def test_validate_index_period_previous(index, interval_length, previous_time):
    with pytest.raises(request_handling.BadAPIRequest) as e:
        request_handling.validate_index_period(index, interval_length,
                                               previous_time)
    errs = e.value.errors['timestamp']
    assert len(errs) == 1
    assert 'previous time' in errs[0]


@pytest.mark.parametrize('ep,res', [
    ('{"restrict_upload": true}', True),
    ('{"restrict_upload": true, "other_key": 1}', True),
    ('{"restrict_upload" : true}', True),
    ('{"restrict_upload" : True}', True),
    ('{"restrict_upload": 1}', False),
    ('{"restrict_upload": false}', False),
    ('{"restrict_uploa": true}', False),
    ('{"upload_restrict_upload": true}', False),
])
def test__restrict_in_extra(ep, res):
    assert request_handling._restrict_in_extra(ep) is res


def test__current_utc_timestamp():
    t = request_handling._current_utc_timestamp()
    assert isinstance(t, pd.Timestamp)
    assert t.tzinfo == pytz.utc


def test_restrict_upload_window_noop():
    assert request_handling.restrict_forecast_upload_window(
        '', None, None) is None


@pytest.mark.parametrize('now,first', [
    (pd.Timestamp('2019-11-01T11:59Z'), pd.Timestamp('2019-11-01T13:00Z')),
    (pd.Timestamp('2019-11-01T12:00Z'), pd.Timestamp('2019-11-01T13:00Z')),
    (pd.Timestamp('2019-11-01T00:00Z'), pd.Timestamp('2019-11-01T13:00Z')),
    (pd.Timestamp('2019-11-01T12:01Z'), pd.Timestamp('2019-11-02T13:00Z')),
])
def test_restrict_upload_window(mocker, now, first):
    fxd = VALID_FORECAST_JSON.copy()
    ep = '{"restrict_upload": true}'
    mocker.patch(
        'sfa_api.utils.request_handling._current_utc_timestamp',
        return_value=now)
    request_handling.restrict_forecast_upload_window(ep, lambda: fxd, first)


@pytest.mark.parametrize('now,first', [
    (pd.Timestamp('2019-11-01T11:59Z'), pd.Timestamp('2019-11-01T13:00Z')),
    (pd.Timestamp('2019-11-01T12:00Z'), pd.Timestamp('2019-11-01T13:00Z')),
    # as currently and previously (pre-rc1) implemented in core, midnight is a
    # valid forecast init time even if doesn't start until mid-day
    # pre-rc1 did not 11/1 00:00, but would include 11/2 00:00 in issue times
    (pd.Timestamp('2019-11-01T00:00Z'), pd.Timestamp('2019-11-01T01:00Z')),
    (pd.Timestamp('2019-11-01T22:01Z'), pd.Timestamp('2019-11-02T00:00Z')),
    (pd.Timestamp('2019-11-01T23:20Z'), pd.Timestamp('2019-11-02T01:00Z'))
])
def test_restrict_upload_window_freq(mocker, now, first):
    fxd = demo_forecasts['f8dd49fa-23e2-48a0-862b-ba0af6dec276'].copy()
    ep = '{"restrict_upload": true}'
    mocker.patch(
        'sfa_api.utils.request_handling._current_utc_timestamp',
        return_value=now)
    request_handling.restrict_forecast_upload_window(ep, lambda: fxd, first)


def test_restrict_upload_window_cdf_dict(mocker):
    now = pd.Timestamp('2019-11-01T11:59Z')
    first = pd.Timestamp('2019-11-01T13:00Z')
    fxd = VALID_CDF_FORECAST_JSON.copy()
    ep = '{"restrict_upload": true}'
    mocker.patch(
        'sfa_api.utils.request_handling._current_utc_timestamp',
        return_value=now)
    request_handling.restrict_forecast_upload_window(ep, lambda: fxd, first)


def test_restrict_upload_window_cant_get(mocker):
    now = pd.Timestamp('2019-11-01T11:59Z')
    first = pd.Timestamp('2019-11-01T13:00Z')

    ep = '{"restrict_upload": true}'
    mocker.patch(
        'sfa_api.utils.request_handling._current_utc_timestamp',
        return_value=now)
    get = mocker.MagicMock(side_effect=StorageAuthError)
    with pytest.raises(NotFoundException):
        request_handling.restrict_forecast_upload_window(ep, get, first)


@pytest.mark.parametrize('now,first', [
    (pd.Timestamp('2019-11-01T11:59Z'), pd.Timestamp('2019-11-01T14:00Z')),
    (pd.Timestamp('2019-11-01T12:00:00.000001Z'),
     pd.Timestamp('2019-11-01T13:00Z')),
    (pd.Timestamp('2019-11-01T11:59Z'), pd.Timestamp('2019-11-02T13:00Z')),
])
def test_restrict_upload_window_bad(mocker, now, first):
    fxd = VALID_FORECAST_JSON.copy()
    ep = '{"restrict_upload": true}'
    mocker.patch(
        'sfa_api.utils.request_handling._current_utc_timestamp',
        return_value=now)
    with pytest.raises(BadAPIRequest) as err:
        request_handling.restrict_forecast_upload_window(
            ep, lambda: fxd, first)
    assert 'only accepting' in err.value.errors['issue_time'][0]


@pytest.mark.parametrize('now,first,label', [
    (pd.Timestamp('2019-11-01T11:59Z'), pd.Timestamp('2019-11-01T13:00Z'),
     'beginning'),
    (pd.Timestamp('2019-11-01T11:59Z'), pd.Timestamp('2019-11-01T13:00Z'),
     'instant'),
    (pd.Timestamp('2019-11-01T12:00Z'), pd.Timestamp('2019-11-01T13:05Z'),
     'ending'),
    pytest.param(
        pd.Timestamp('2019-11-01T11:59Z'), pd.Timestamp('2019-11-01T13:00Z'),
        'ending', marks=pytest.mark.xfail
    ),
])
def test_restrict_upload_interval_label(mocker, now, first, label):
    fxd = VALID_FORECAST_JSON.copy()
    fxd['interval_label'] = label
    ep = '{"restrict_upload": true}'
    mocker.patch(
        'sfa_api.utils.request_handling._current_utc_timestamp',
        return_value=now)
    request_handling.restrict_forecast_upload_window(ep, lambda: fxd, first)


@pytest.mark.parametrize('mimetype', [
    'text/csv',
    'application/vnd.ms-excel',
    'application/json'
])
def test_parse_values_too_much_data(app, random_post_payload, mimetype):
    with app.test_request_context():
        data = random_post_payload(
            app.config.get('MAX_POST_DATAPOINTS') + 1,
            mimetype
        )
        with pytest.raises(request_handling.BadAPIRequest):
            request_handling.parse_values(data, mimetype)


@pytest.mark.parametrize('lat,lon,exc', [
    ('str', -110, {'latitude': ['Must be a float']}),
    (32, 'str', {'longitude': ['Must be a float']}),
    ('str', 'str', {'longitude': ['Must be a float'],
                    'latitude': ['Must be a float']}),
    (-110, -110, {'latitude': ['Must be within [-90, 90].']}),
    (-110, -181, {'latitude': ['Must be within [-90, 90].'],
                  'longitude': ['Must be within (-180, 180].']}),
    (None, -181, {'latitude': ['Must provide a latitude'],
                  'longitude': ['Must be within (-180, 180].']}),
    (32, None, {'longitude': ['Must provide a longitude']}),
])
def test_validate_latitude_longitude_fail(app, lat, lon, exc):
    url = '/climatezones/search?'
    if lat is not None:
        url += f'latitude={lat}&'
    if lon is not None:
        url += f'longitude={lon}'
    with pytest.raises(request_handling.BadAPIRequest) as err:
        with app.test_request_context(url):
            request_handling.validate_latitude_longitude()
    assert err.value.errors == exc


@pytest.mark.parametrize('lat,lon', [
    (32, -110),
    (0, 0),
    (-20, 170),
    (-.01, 20.8)
])
def test_validate_latitude_longitude_success(app, lat, lon):
    url = f'/climatezones/search?latitude={lat}&longitude={lon}'
    with app.test_request_context(url):
        request_handling.validate_latitude_longitude()


@pytest.mark.parametrize('data', [
    pd.DataFrame({'value': []}),
    pd.DataFrame({'value': [0, 0, 0]}),
    pd.DataFrame({'value': [0.0, 1.0, 0.0]}, index=pd.date_range(
        start='now', freq='5min', periods=3)),
    pd.DataFrame({'value': [1, 0, 1], 'other': ['a', 'b', 'c']})
])
def test_validate_event_data_ok(data):
    request_handling.validate_event_data(data)


@pytest.mark.parametrize('data,exp', [
    (pd.DataFrame({'value': [1, 2, 0]}), [1]),
    (pd.DataFrame({'value': [2, 2, 2, 2]}), [0, 1, 2, 3]),
    (pd.DataFrame({'value': ['a', 1.0, 0.0, 99]}, index=pd.date_range(
        start='now', freq='5min', periods=4)), [0, 3])
])
def test_validate_event_data_bad(data, exp):
    with pytest.raises(request_handling.BadAPIRequest) as err:
        request_handling.validate_event_data(data)
    locs = [
        int(x) for x in
        err.value.errors['value'][0].split('locations ')[1].split(',')
    ]
    assert exp == locs
