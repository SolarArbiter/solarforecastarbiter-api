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
