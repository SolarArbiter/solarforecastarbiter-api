from marshmallow.exceptions import ValidationError
import pytest


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
    "apostrophe '", 'site_99'
])
def test_userstring(thestring):
    assert validators.UserstringValidator()(
        thestring) == thestring


@pytest.mark.parametrize('thestring', [
    '<script>bac</script>', '<', ';delete',
    'site:a:b', 'site+1', 'site\\G',
    'site\n', '', ' ', "'", "'   ", '_'
])
def test_invalid_userstring(thestring):
    with pytest.raises(ValidationError):
        validators.UserstringValidator()(thestring)
