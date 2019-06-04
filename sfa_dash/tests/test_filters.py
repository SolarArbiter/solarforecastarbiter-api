import pytest


from sfa_dash import filters


@pytest.mark.parametrize('minutes,expected', [
    (1500, '1 day 1 hour'),
    (1501, '1 day 1 hour 1 minute'),
    (3002, '2 days 2 hours 2 minutes'),
    (4320, '3 days'),
    (1440, '1 day'),
    (300, '5 hours'),
    (60, '1 hour'),
    (30, '30 minutes'),
    (1, '1 minute'),
    (0, '0 minutes')
])
def test_display_timedelta(minutes, expected):
    assert filters.display_timedelta(minutes) == expected


@pytest.mark.parametrize('minutes', [-1, -2])
def test_display_timedelta_failure(minutes):
    with pytest.raises(ValueError):
        filters.display_timedelta(minutes)
