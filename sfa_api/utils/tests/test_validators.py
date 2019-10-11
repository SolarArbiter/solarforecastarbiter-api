import datetime as dt


from marshmallow.exceptions import ValidationError
import pytest
import pytz


from sfa_api.utils import validators


@pytest.mark.parametrize('thetime', [
    '09:00', '9:00', '00:00'
])
def test_time_format(thetime):
    assert validators.TimeFormat('%H:%M')(thetime) == thetime


@pytest.mark.parametrize('bad', [
    '25:00', '00:00:00', 'ab:cd', '10:88'
])
def test_time_format_fail(bad):
    with pytest.raises(ValidationError):
        validators.TimeFormat('%H:%M')(bad)


@pytest.mark.parametrize('thestring', [
    'mysite', 'Site 1', 'A really long but otherwise OK site',
    "apostrophe '", 'site_99', 'site tucson, az',
    "Test (site)", 'w,', 'test-hyphen'
])
def test_userstring(thestring):
    assert validators.UserstringValidator()(
        thestring) == thestring


@pytest.mark.parametrize('thestring', [
    '<script>bac</script>', '<', ';delete',
    'site:a:b', 'site+1', 'site\\G',
    'site\n', '', ' ', "'", "'   ", '_', ',',
    ',_', '()', "'()',", "(){ :|:& };"
])
def test_invalid_userstring(thestring):
    with pytest.raises(ValidationError):
        validators.UserstringValidator()(thestring)


@pytest.mark.parametrize('tz', [
    'America/Phoenix',
    'Etc/GMT+7'
])
def test_timezonevalidator(tz):
    assert validators.TimezoneValidator()(tz) == tz


@pytest.mark.parametrize('tz', ['PDT', 'Germany/Berlin'])
def test_timezonevalidator_fail(tz):
    with pytest.raises(ValidationError):
        validators.TimezoneValidator()(tz)


@pytest.mark.parametrize('time_', [
    dt.datetime(2019, 1, 1, 12, 3, tzinfo=pytz.timezone('MST')),
    dt.datetime(2019, 1, 1, 12, 3),
    dt.datetime(1969, 12, 31, 17, 0, 1, tzinfo=pytz.timezone('MST')),
])
def test_timelimit_validator(time_):
    assert validators.TimeLimitValidator()(time_) == time_


@pytest.mark.parametrize('time_', [
    dt.datetime(2049, 1, 1, 12, 3),
    dt.datetime(1969, 12, 31, 14, 0, 1, tzinfo=pytz.timezone('MST')),
])
def test_timelimit_validator_fail(time_):
    with pytest.raises(ValidationError):
        validators.TimeLimitValidator()(time_)
