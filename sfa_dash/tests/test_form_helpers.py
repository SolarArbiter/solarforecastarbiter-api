import pytest


from sfa_dash.blueprints.form import MetadataForm


@pytest.fixture()
def meta_form():
    return MetadataForm('forecast')


def test_flatten_dict(meta_form):
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
    out = meta_form.flatten_dict(original_dict)
    assert out == expected_out


@pytest.mark.parametrize('data,root,expected', [
    ({'time_hours': 10, 'time_minutes': 23}, 'time', '10:23'),
    ({'issue_time_hours': 5, 'issue_time_minutes': 2}, 'issue_time', '05:02'),
])
def test_parse_hhmm_field(data, root, expected, meta_form):
    assert meta_form.parse_hhmm_field(data, root) == expected


@pytest.mark.parametrize('data,root,expected', [
    ({'lead_time_number': 360,
      'lead_time_units': 'minutes'}, 'lead_time', 360),
    ({'lead_time_number': 3,
      'lead_time_units': 'hours'}, 'lead_time', 180),
    ({'lead_time_number': 2,
      'lead_time_units': 'days'}, 'lead_time', 2880),
])
def test_parse_timedelta(data, root, expected, meta_form):
    assert meta_form.parse_timedelta(data, root) == expected


def test_site_formatter(meta_form):
    pass


def test_forecast_formatter(meta_form):
    pass
