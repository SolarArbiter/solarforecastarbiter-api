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
])
def test_display_timedelta(minutes, expected):
    assert filters.display_timedelta(minutes) == expected


@pytest.mark.paramtrize('minutes', [-1, 0])
def test_display_timedelta_failure():
    with pytest.raises(ValueError):
        filters.display_timedelta(0)
