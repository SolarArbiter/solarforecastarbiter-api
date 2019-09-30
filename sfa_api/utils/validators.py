import re
import time


from marshmallow.validate import Validator
from marshmallow.exceptions import ValidationError


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
