import pytest


from sfa_dash.form_utils import utils


def test_flatten_dict():
    original_dict = {
        'a': 1,
        'b': {'z': 5,
              'y': 4,
              'x': 3},
        'c': [1, 2, 3, 4]
    }
    expected_out = {
        'a': 1,
        'z': 5,
        'y': 4,
        'x': 3,
        'c': [1, 2, 3, 4],
    }
    out = utils.flatten_dict(original_dict)
    assert out == expected_out


@pytest.mark.parametrize('data,root,expected', [
    ({'time_hours': 10, 'time_minutes': 23}, 'time', '10:23'),
    ({'issue_time_hours': 5, 'issue_time_minutes': 2}, 'issue_time', '05:02'),
])
def test_parse_hhmm_field_from_form(data, root, expected):
    assert utils.parse_hhmm_field_from_form(data, root) == expected


@pytest.mark.parametrize('expected,root,data', [
    ({'time_hours': 10, 'time_minutes': 23},
     'time', {'time': '10:23'}),
    ({'issue_time_hours': 5, 'issue_time_minutes': 2},
     'issue_time', {'issue_time': '05:02'}),
])
def test_parse_hhmm_field_from_api(data, root, expected):
    assert utils.parse_hhmm_field_from_api(data, root) == expected


@pytest.mark.parametrize('data,root,expected', [
    ({'lead_time_number': 360,
      'lead_time_units': 'minutes'}, 'lead_time', 360),
    ({'lead_time_number': 3,
      'lead_time_units': 'hours'}, 'lead_time', 180),
    ({'lead_time_number': 2,
      'lead_time_units': 'days'}, 'lead_time', 2880),
])
def test_parse_timedelta_from_form(data, root, expected):
    assert utils.parse_timedelta_from_form(data, root) == expected


@pytest.mark.parametrize('expected,root,data', [
    ({'lead_time_number': 90,
      'lead_time_units': 'minutes'}, 'lead_time', {'lead_time': 90}),
    ({'lead_time_number': 3,
      'lead_time_units': 'hours'}, 'lead_time', {'lead_time': 180}),
    ({'lead_time_number': 2,
      'lead_time_units': 'days'}, 'lead_time', {'lead_time': 2880}),
])
def test_parse_timedelta_from_api(data, root, expected):
    assert utils.parse_timedelta_from_api(data, root) == expected


@pytest.mark.parametrize('from_dict', [
    {'aggregate_id': 'someaggregateid'},
    {'site_id': 'somesiteid'},
    {'aggregate_id': 'someaggregateid', 'site_id': None},
    {'aggregate_id': None, 'site_id': 'somesiteid'},
])
def test_get_location_id(from_dict):
    assert utils.get_location_id(from_dict) == from_dict


@pytest.mark.parametrize('from_dict', [
    {'aggregate_id': 'someaggregateid', 'other_key': 1},
    {'site_id': 'somesiteid', 'name': 'hello'},
])
def test_get_location_id_only_location_keys(from_dict):
    for key in list(utils.get_location_id(from_dict).keys()):
        assert key in ['aggregate_id', 'site_id']


def test_set_location_id_no_location_key():
    assert utils.get_location_id({}) == {}
