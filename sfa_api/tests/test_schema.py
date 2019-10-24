import datetime as dt


import marshmallow
import pytest


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
