import datetime as dt


import json
import marshmallow
import pytest
import uuid


from sfa_api import schema


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
    ("2019-04-08T09:00:00+00:00",
     dt.datetime(2019, 4, 8, 9, tzinfo=dt.timezone.utc)),
    ("2019-01-01T00:00:00-07:00",
     dt.datetime(2019, 1, 1, tzinfo=dt.timezone(dt.timedelta(hours=-7)))),
])
def test_isodatetime_deserialize(inp, out, iso_schema):
    assert iso_schema().loads('{"isodt": "' + inp + '"}')['isodt'] == out


@pytest.mark.parametrize('inp', [
    ('{"forecast": "11c20780-76ae-4b11-bef1-7a75bdc784e3",'
     '"observation": "123e4567-e89b-12d3-a456-426655440000"}'),
    ('{"forecast": "11c20780-76ae-4b11-bef1-7a75bdc784e3",'
     '"aggregate": "458ffc27-df0b-11e9-b622-62adb5fd6af0"}')
])
def test_object_pair_deserialization(inp):
    deserialized = schema.ReportObjectPair().loads(inp)
    assert 'forecast' in deserialized
    assert (bool('observation' in deserialized) !=
            bool('aggregate' in deserialized))
    assert deserialized['reference_forecast'] is None
    assert deserialized['uncertainty'] is None


@pytest.mark.parametrize('inp', [
    ('{"forecast": "11c20780-76ae-4b11-bef1-7a75bdc784e3",'
     '"observation": "123e4567-e89b-12d3-a456-426655440000",'
     '"reference_forecast": "11c20780-76ae-4b11-bef1-7a75bdc784e3"}'),
])
def test_object_pair_with_ref(inp):
    deserialized = schema.ReportObjectPair().loads(inp)
    assert deserialized['forecast'] == uuid.UUID("11c20780-76ae-4b11-bef1-7a75bdc784e3")  # noqa
    assert deserialized['observation'] == uuid.UUID("123e4567-e89b-12d3-a456-426655440000")  # noqa
    assert deserialized['reference_forecast'] == uuid.UUID("11c20780-76ae-4b11-bef1-7a75bdc784e3")  # noqa


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
def test_object_pair_with_uncertainty(uncertainty, exp_type):
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
