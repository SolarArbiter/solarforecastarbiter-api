import datetime as dt
import re
import time


from marshmallow.validate import Validator
from marshmallow.exceptions import ValidationError
import pytz


class TimeFormat(Validator):
    """Validates Time is in correct format"""
    def __init__(self, time_format):
        self.time_format = time_format

    def __call__(self, value):
        try:
            time.strptime(value, self.time_format)
        except ValueError:
            raise ValidationError(f'Time not in {self.time_format} format.')
        return value


class UserstringValidator(Validator):
    """
    Validates a string the user provides does not include invalid characters.
    Currently must only match word characters (letters, numbers, underscore),
    space, comma, apostrophe, hyphen, and parentheses. Must also have some word
    characters.
    """
    def __init__(self):
        self.compiled_re = re.compile(
            "^(?!\\W+$)(?![_ ',\\-\\(\\)]+$)[\\w ',\\-\\(\\)]+$")

    def __call__(self, value):
        match = self.compiled_re.match(value)
        if match is None or match[0] != value:
            raise ValidationError('Invalid characters in string.')
        return value


ALLOWED_TIMEZONES = pytz.country_timezones('US') + list(
    filter(lambda x: 'GMT' in x, pytz.all_timezones))


class TimezoneValidator(Validator):
    def __call__(self, value):
        if value not in ALLOWED_TIMEZONES:
            raise ValidationError('Invalid timezone.')
        return value


MAX_SQL_TIME = dt.datetime(2038, 1, 19, 3, 14, 7, 0, tzinfo=pytz.utc)
MIN_SQL_TIME = dt.datetime(1970, 1, 1, 0, 0, 1, 0, tzinfo=pytz.utc)


class TimeLimitValidator(Validator):
    """
    Ensures a DateTime is not outside the range of allowed for MySQL TIMESTAMP
    objects
    """
    def __call__(self, value):
        if value.tzinfo is not None:
            testval = value.astimezone(pytz.utc)
        else:
            testval = pytz.utc.localize(value)
        if testval > MAX_SQL_TIME:
            raise ValidationError(
                f'Exceeds maximum allowed timestamp of {MAX_SQL_TIME}')
        elif testval < MIN_SQL_TIME:
            raise ValidationError(
                f'Less than minimum allowed timestamp of {MIN_SQL_TIME}')
        return value
