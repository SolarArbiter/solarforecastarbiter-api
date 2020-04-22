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
    filter(lambda x: 'GMT' in x or 'UTC' in x, pytz.all_timezones))


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


class UncertaintyValidator(Validator):
    """Ensures value is None, 'observation_uncertainty' or a quoted float.
    """
    def __call__(self, value):
        if value is not None:
            if value != "observation_uncertainty":
                try:
                    float_value = float(value)
                except ValueError:
                    raise ValidationError(
                        "Invalid uncertainty value. Must be one of: null, "
                        "'observation_uncertainty' or a quoted float value "
                        "from 0.0 to 100.0.")
                else:
                    if float_value > 100:
                        raise ValidationError(
                            "Unvertainty percentage must be less than or "
                            "equal to 100.0.")
                    if float_value < 0:
                        raise ValidationError(
                            "Unvertainty percentage must be greater than or "
                            "equal to 0.0.")
        return value


def validate_if_event(schema, data, **kwargs):
    """Checks for an event variable or interval label and ensures they are
    the same.

    This function is in the form of a marshmallow schema-level validator, which
    is typically implemented as a decorated method but is instead placed here
    to allow reuse.

    Parameters
    ----------
    schema: marshmallow.Schema
        The schema to validate.
    data: dict
        The data being used to instantiate the schema class.

    Raises
    ------
    marshmallow.ValidationError
        If either `variable` or `interval_label` are set to 'event' and the
        other does not match.
    """
    variable = data.get('variable')
    interval_label = data.get('interval_label')
    if(variable == 'event' or interval_label == 'event'):
        if (variable != interval_label):
            raise ValidationError({
                'events': ["Both interval_label and variable must be set to "
                           "'event'."]})
