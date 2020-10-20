from copy import deepcopy
import datetime as dt


import json
import marshmallow
import pandas as pd
import pytest
import uuid


from sfa_api import schema, ma


@pytest.fixture()
def iso_schema():
    return marshmallow.Schema.from_dict({'isodt': schema.ISODateTime()})


@pytest.mark.parametrize('inp,out', [
    (dt.datetime(2019, 1, 1), '{"isodt": "2019-01-01T00:00:00+00:00"}'),
    (dt.datetime(2019, 2, 1, tzinfo=dt.timezone(dt.timedelta(hours=-2))),
     '{"isodt": "2019-02-01T00:00:00-02:00"}'),
    (dt.datetime(2019, 2, 1, tzinfo=dt.timezone.utc),
     '{"isodt": "2019-02-01T00:00:00+00:00"}')
])
def test_isodatetime_serialize(inp, out, iso_schema):
    assert iso_schema().dumps({'isodt': inp}) == out


@pytest.mark.parametrize('inp,out', [
    ("2019-01-01T00:00:00", dt.datetime(2019, 1, 1, tzinfo=dt.timezone.utc)),
    ("20190101T000000", dt.datetime(2019, 1, 1, tzinfo=dt.timezone.utc)),
    ("20190101T00:00:00", dt.datetime(2019, 1, 1, tzinfo=dt.timezone.utc)),
    ("2019-01-01T000000", dt.datetime(2019, 1, 1, tzinfo=dt.timezone.utc)),
    ("2019-01-01T00:00:00Z", dt.datetime(2019, 1, 1, tzinfo=dt.timezone.utc)),
    ("2019-01-01T06Z", dt.datetime(2019, 1, 1, 6, tzinfo=dt.timezone.utc)),
    ("20190101T000000+0800",
     dt.datetime(2019, 1, 1, tzinfo=dt.timezone(dt.timedelta(hours=8)))),
    ("2019-04-08T09:00:00+00:00",
     dt.datetime(2019, 4, 8, 9, tzinfo=dt.timezone.utc)),
    ("2019-01-01T00:00:00-07:00",
     dt.datetime(2019, 1, 1, tzinfo=dt.timezone(dt.timedelta(hours=-7)))),
])
def test_isodatetime_deserialize(inp, out, iso_schema):
    assert iso_schema().loads('{"isodt": "' + inp + '"}')['isodt'] == out


@pytest.mark.parametrize('inp', ["2019-0101T00:0000", "", "bad", "1"])
def test_isodatetime_deserialize_error(inp, iso_schema):
    with pytest.raises(marshmallow.exceptions.ValidationError):
        iso_schema().loads('{"isodt": "' + inp + '"}')['isodt']


@pytest.mark.parametrize('inp', [
    ('{"forecast": "11c20780-76ae-4b11-bef1-7a75bdc784e3",'
     '"observation": "123e4567-e89b-12d3-a456-426655440000"}'),
    ('{"forecast": "49220780-76ae-4b11-bef1-7a75bdc784e3",'
     '"aggregate": "458ffc27-df0b-11e9-b622-62adb5fd6af0"}')
])
def test_object_pair_deserialization(user, inp):
    deserialized = schema.ReportObjectPair().loads(inp)
    assert 'forecast' in deserialized
    assert (bool('observation' in deserialized) !=
            bool('aggregate' in deserialized))
    assert deserialized['reference_forecast'] is None
    assert deserialized['uncertainty'] is None
    assert deserialized['forecast_type'] == 'forecast'


@pytest.mark.parametrize('inp', [
    ('{"forecast": "11c20780-76ae-4b11-bef1-7a75bdc784e3",'
     '"observation": "123e4567-e89b-12d3-a456-426655440000",'
     '"reference_forecast": "11c20780-76ae-4b11-bef1-7a75bdc784e3"}'),
])
def test_object_pair_with_ref(inp, user):
    deserialized = schema.ReportObjectPair().loads(inp)
    assert deserialized['forecast'] == uuid.UUID("11c20780-76ae-4b11-bef1-7a75bdc784e3")  # noqa
    assert deserialized['observation'] == uuid.UUID("123e4567-e89b-12d3-a456-426655440000")  # noqa
    assert deserialized['reference_forecast'] == uuid.UUID("11c20780-76ae-4b11-bef1-7a75bdc784e3")  # noqa


@pytest.mark.parametrize('inp', [
    ({"forecast": "11c20780-76ae-4b11-bef1-7a75bdc784e3",
      "observation": "123e4567-e89b-12d3-a456-426655440000",
      "reference_forecast": "11c20780-76ae-4b11-bef1-7a75bdc784e3",
      "uncertainty": '0.1',
      "forecast_type": "forecast"}),
])
def test_object_pair_serialization(inp):
    dumped = schema.ReportObjectPair().dumps(inp)
    out = json.loads(dumped)
    assert out == inp


@pytest.mark.parametrize('inp', [
    ({"forecast": "11c20780-76ae-4b11-bef1-7a75bdc784e3",
     "observation": "123e4567-e89b-12d3-a456-426655440000"}),
])
def test_object_pair_serialization_defaults(inp):
    dumped = schema.ReportObjectPair().dumps(inp)
    out = json.loads(dumped)
    assert out['forecast'] == inp['forecast']
    assert out['observation'] == inp['observation']
    assert out['reference_forecast'] is None
    assert out['uncertainty'] is None
    assert out['forecast_type'] == 'forecast'


base_pair_dict = {
    "forecast": "11c20780-76ae-4b11-bef1-7a75bdc784e3",
    "observation": "123e4567-e89b-12d3-a456-426655440000",
    "reference_forecast": "11c20780-76ae-4b11-bef1-7a75bdc784e3"
}


@pytest.mark.parametrize('uncertainty,exp_type', [
    (None, type(None)),
    ('observation_uncertainty', str),
    ('10.0', str),
    ('0.0', str),
    ('100.0', str),
])
def test_object_pair_with_uncertainty(uncertainty, exp_type, user):
    pair_dict = base_pair_dict.copy()
    pair_dict.update({'uncertainty': uncertainty})
    pair_json = json.dumps(pair_dict)
    deserialized = schema.ReportObjectPair().loads(pair_json)
    assert isinstance(deserialized['uncertainty'], exp_type)


@pytest.mark.parametrize('uncertainty', [
    'bad string', 10.0, '-10.0', '101.0',
])
def test_object_pair_with_invalid_uncertainty(uncertainty):
    pair_dict = base_pair_dict.copy()
    pair_dict.update({'uncertainty': uncertainty})
    pair_json = json.dumps(pair_dict)
    with pytest.raises(marshmallow.exceptions.ValidationError):
        schema.ReportObjectPair().loads(pair_json)


@pytest.mark.parametrize('forecast_type', [
    'bad string',
    'probabilistic',
    'event',
])
def test_object_pair_with_invalid_forecast_type(forecast_type):
    pair_dict = base_pair_dict.copy()
    pair_dict.update({'forecast_type': forecast_type})
    pair_json = json.dumps(pair_dict)
    with pytest.raises(marshmallow.exceptions.ValidationError):
        schema.ReportObjectPair().loads(pair_json)


@pytest.mark.parametrize('inp', [
    ('{"forecast": "11c20780-76ae-4b11-bef1-7a75bdc784e3",'
     '"observation": "123e4567-e89b-12d3-a456-426655440000",'
     '"aggregate": "458ffc27-df0b-11e9-b622-62adb5fd6af0"}'),
    ('{"forecast": "11c20780-76ae-4b11-bef1-7a75bdc784e3"}'),
    ('{"forecast": "notauuid",'
     '"aggregate": "458ffc27-df0b-11e9-b622-62adb5fd6af0"}'),
    ('{"forecast": "458ffc27-df0b-11e9-b622-62adb5fd6af0",'
     '"aggregate": "notauuid"}'),
])
def test_object_pair_test_validation(inp):
    with pytest.raises(marshmallow.exceptions.ValidationError):
        schema.ReportObjectPair().loads(inp)


@pytest.fixture()
def tseries():
    nested = marshmallow.Schema.from_dict({'cola': ma.Int(),
                                           'colb': ma.Float(),
                                           'time': ma.AwareDateTime(),
                                           })
    tseries = marshmallow.Schema.from_dict(
        {'tseries': schema.TimeseriesField(nested, many=True)})()
    return tseries


def test_timeseriesfield(tseries):
    data = pd.DataFrame({'cola': [1, 2], 'colb': [1.0, pd.NA]},
                        index=pd.DatetimeIndex(
                            [pd.Timestamp('20200401T0001Z'),
                             pd.Timestamp('20200501T0000Z')],
                            name='time'))
    out = tseries.dumps({'tseries': data})
    dict_out = json.loads(out)
    assert dict_out['tseries'] == [
        {'cola': 1, 'colb': 1.0, 'time': '2020-04-01T00:01:00Z'},
        {'cola': 2, 'colb': None, 'time': '2020-05-01T00:00:00Z'}
    ]


def test_timeseriesfield_no_index_name(tseries):
    data = pd.DataFrame({'cola': [1, 2], 'colb': [1.0, pd.NA]},
                        index=pd.DatetimeIndex(
                            [pd.Timestamp('20200401T0001Z'),
                             pd.Timestamp('20200501T0000Z')],
                            ))
    out = tseries.dumps({'tseries': data})
    dict_out = json.loads(out)
    assert dict_out['tseries'] == [
        {'cola': 1, 'colb': 1.0, 'time': None},
        {'cola': 2, 'colb': None, 'time': None}
    ]


def test_timeseriesfield_missing_col(tseries):
    data = pd.DataFrame({'cola': [1, 2]},
                        index=pd.DatetimeIndex(
                            [pd.Timestamp('20200401T0001Z'),
                             pd.Timestamp('20200501T0000Z')],
                            name='time'))
    out = tseries.dumps({'tseries': data})
    dict_out = json.loads(out)
    assert dict_out['tseries'] == [
        {'cola': 1, 'colb': None, 'time': '2020-04-01T00:01:00Z'},
        {'cola': 2, 'colb': None, 'time': '2020-05-01T00:00:00Z'}
    ]


def test_timeseriesfield_unlocalized(tseries):
    data = pd.DataFrame({'cola': [1, 2], 'colb': [1.0, pd.NA]},
                        index=pd.DatetimeIndex(
                            [pd.Timestamp('20200401T0001'),
                             pd.Timestamp('20200501T0000')],
                            name='time'))
    out = tseries.dumps({'tseries': data})
    dict_out = json.loads(out)
    assert dict_out['tseries'] == [
        {'cola': 1, 'colb': 1.0, 'time': '2020-04-01T00:01:00Z'},
        {'cola': 2, 'colb': None, 'time': '2020-05-01T00:00:00Z'}
    ]


def test_timeseriesfield_tz(tseries):
    data = pd.DataFrame({'cola': [1, 2], 'colb': [1.0, pd.NA]},
                        index=pd.DatetimeIndex(
                            [pd.Timestamp('20200401T0301'),
                             pd.Timestamp('20200501T0300')],
                            tz='MST', name='time'))
    out = tseries.dumps({'tseries': data})
    dict_out = json.loads(out)
    assert dict_out['tseries'] == [
        {'cola': 1, 'colb': 1.0, 'time': '2020-04-01T10:01:00Z'},
        {'cola': 2, 'colb': None, 'time': '2020-05-01T10:00:00Z'}
    ]


def test_timeseriesfield_notdf(tseries):
    data = pd.Series([1, 2], name='cola',
                     index=pd.DatetimeIndex(
                         [pd.Timestamp('20200401T0301Z'),
                          pd.Timestamp('20200501T0300Z')],
                         name='time'))
    with pytest.raises(AttributeError):
        tseries.dumps({'tseries': data})


def test_timeseriesfield_matches_old():
    naive = marshmallow.Schema.from_dict(
        {'tseries': ma.Nested(schema.ObservationValueSchema, many=True)})()
    tseries = marshmallow.Schema.from_dict(
        {'tseries': schema.TimeseriesField(
            schema.ObservationValueSchema, many=True)})()
    data = pd.DataFrame({'quality_flag': [0, 1], 'value': [1.0, None]},
                        index=pd.DatetimeIndex(
                            [pd.Timestamp('20200401T0301Z'),
                             pd.Timestamp('20200501T0300Z')],
                            name='timestamp'))
    tout = tseries.dumps({'tseries': data})
    ndata = data.copy()
    ndata['timestamp'] = ndata.index
    dict_values = ndata.to_dict(orient='records')
    nout = naive.dumps({'tseries': dict_values})
    # new replaces +00:00 with Z
    # and NaN with null
    assert tout == nout.replace('+00:00', 'Z').replace('NaN', 'null')


@pytest.mark.parametrize('json,error', [
    ('{"description": "<script>console.log();</script>", "action": "read",'
     '"object_type": "observations", "applies_to_all": false}',
     'Invalid characters in string.'),
    ('{"description": "' + ('a'*65) + '", "action": "read",'
     '"object_type": "observations", "applies_to_all": false}',
     'Longer than maximum length 64.'),
    ('{"description": "!!!", "action": "read",'
     '"object_type": "observations", "applies_to_all": false}',
     'Invalid characters in string.'),
])
def test_permission_description_validation(json, error):
    with pytest.raises(marshmallow.exceptions.ValidationError) as E:
        schema.PermissionPostSchema().loads(json)
    assert E.value.messages['description'] == [error]


def test_report_deserialize_defaults(report_post_json, user):
    report_dict = deepcopy(report_post_json)
    report_dict['report_parameters'].pop('filters')
    report_json = json.dumps(report_dict)
    report = schema.ReportPostSchema().loads(report_json)
    params = report['report_parameters']
    assert params['forecast_fill_method'] == 'drop'
    assert params['filters'] == []
    assert params['costs'] == []


def test_report_serialize_missing(report_post_json, user):
    report_dict = deepcopy(report_post_json)
    report_dict['report_parameters'].pop('filters')
    report_json = schema.ReportSchema().dumps(report_dict)
    params = json.loads(report_json)['report_parameters']
    assert params['forecast_fill_method'] == 'drop'
    assert params['filters'] == []
    assert params['costs'] == []


@pytest.fixture(params=[None, 'fixed', 'single_axis'])
def modeling_params(request):
    if request.param is None:
        return {
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
        }
    elif request.param == 'fixed':
        return {
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
        }
    elif request.param == 'single_axis':
        return {
            "ac_capacity": 0.015,
            "ac_loss_factor": 0.0,
            "axis_azimuth": 180,
            "axis_tilt": 0,
            "backtrack": False,
            "dc_capacity": 0.015,
            "dc_loss_factor": 0.0,
            "ground_coverage_ratio": 1,
            "max_rotation_angle": 2,
            "surface_azimuth": None,
            "surface_tilt": None,
            "temperature_coefficient": -.2,
            "tracking_type": "single_axis"
        }


@pytest.fixture()
def mp_schema():
    return marshmallow.Schema.from_dict(
        {'modeling_params': schema.ModelingParametersField()})


def test_modeling_parameters_serialization(modeling_params, mp_schema):
    mp = {k: v for k, v in modeling_params.items() if v is not None}
    out = mp_schema().dump({'modeling_params': mp})
    assert out['modeling_params'] == modeling_params


def test_modeling_parameters_deserialization(modeling_params, mp_schema):
    mp = {k: v for k, v in modeling_params.items() if v is not None}
    out = mp_schema().load({'modeling_params': mp})
    assert out['modeling_params'] == modeling_params


def test_modeling_parameters_deserialization_fail(modeling_params, mp_schema):
    mp = {k: v for k, v in modeling_params.items() if v is not None}
    mp['surface_tilt'] = 0
    mp['axis_azimuth'] = 0
    with pytest.raises(marshmallow.exceptions.ValidationError):
        mp_schema().load({'modeling_params': mp})


@pytest.mark.parametrize('mp', [
    {},
    pytest.param(
        {'tracking_type': None}, marks=pytest.mark.xfail(strict=True)),
])
def test_site_update_modeling_params(mp):
    _mp = {
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
        "tracking_type": 'noupdate'
    }

    out = schema.SiteUpdateSchema().load({'name': 'new'})
    assert out == {'name': 'new', 'modeling_parameters': _mp}
    out = schema.SiteUpdateSchema().load({'modeling_parameters': mp})
    assert out['modeling_parameters'] == {**_mp, 'tracking_type': None}


@pytest.mark.parametrize('params', [
    {'extra_parameters': 'newextra'},
    {'uncertainty': None, 'name': 'newname'}
])
def test_observation_update(params):
    out = schema.ObservationUpdateSchema().load(params)
    for k, v in params.items():
        assert out[k] == v
    if 'uncertainty' in params and params['uncertainty'] is None:
        assert out['null_uncertainty']
    else:
        assert not out['null_uncertainty']
