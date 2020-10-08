import datetime as dt
import re
import time


from marshmallow.validate import Validator
from marshmallow.exceptions import ValidationError
import pytz


from sfa_api.utils.errors import StorageAuthError
from sfa_api.utils.storage import get_storage


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


def _ensure_forecast_measurement_compatibility(forecast, measurement):
    """Checks that a forecast is compatible with the measurement (observation
    or aggregate) it is compared to.

    Criteria:
    * matching variable
    * interval length of measurement is less than or equal to that of the
      forecast.
    * observations are made at the same site as the forecast
    * the forecast is made for the aggregate.

    Parameters
    ----------
    forecast: dict
    measurement: dict

    Returns
    -------
    dict
        Dictionary mapping field names to error messages. Dict will be empty
        if no issues are found.
    """
    errors = {}
    if forecast['variable'] != measurement['variable']:
        errors['variable'] = 'Must match forecast variable.'
    if forecast['interval_length'] < measurement['interval_length']:
        errors['interval_length'] = ('Must be less than or equal to '
                                     'forecast interval_length.')
    if 'site_id' in measurement:
        if forecast['site_id'] != measurement['site_id']:
            errors['site_id'] = 'Must match forecast site_id.'
    else:
        if forecast['aggregate_id'] != measurement['aggregate_id']:
            errors['aggregate_id'] = 'Must match forecast aggregate_id.'
    return errors


def _ensure_forecast_reference_compatibility(
        forecast, reference_forecast, forecast_type):
    """Checks for compatibility between a forecast and reference forecast.

    Criteria:
    * Same variable
    * Same interval length
    * Same interval label
    * Made for the same site/aggregate
    * For probabilistic forecast constant values:
      * Same axis
      * Same constant value

    Parameters
    ----------
    forecast: dict
    reference_forecast: dict
    forecast_type: str
        Type of forecast, any of the options defined in the object pair schema.

    Returns
    -------
    dict
        Dictionary mapping field names to error messages. Dict will be empty
        if no issues are found.
    """
    reference_errors = {}
    if forecast['variable'] != reference_forecast['variable']:
        reference_errors['variable'] = 'Must match forecast variable.'

    if forecast['interval_length'] != reference_forecast['interval_length']:
        reference_errors['interval_length'] = (
            'Must match forecast interval_length.')

    if forecast['interval_label'] != reference_forecast['interval_label']:
        reference_errors['interval_label'] = (
            'Must match forecast interval_label.')

    if forecast.get('aggregate_id') is not None:
        if forecast['aggregate_id'] != reference_forecast['aggregate_id']:
            reference_errors['aggregate_id'] = (
                'Must match forecast aggregate_id.')
    else:
        if forecast['site_id'] != reference_forecast['site_id']:
            reference_errors['site_id'] = 'Must match forecast site_id.'

    if forecast_type == 'probabilistic_forecast_constant_value':
        if forecast['axis'] != reference_forecast['axis']:
            reference_errors['axis'] = 'Must match forecast axis.'
        if forecast['constant_value'] != reference_forecast['constant_value']:
            reference_errors['constant_value'] = (
                'Must match forecast constant_value.')
    if forecast_type == 'probabilistic_forecast':
        if forecast['axis'] != reference_forecast['axis']:
            reference_errors['axis'] = 'Must match forecast axis.'
    return reference_errors


def ensure_pair_compatibility(data):
    """Ensures compatibility between forecast and observation/aggregate.
    Assumes that fields have been validated and required fields exist.


    Parameters
    ----------
    data: dict
        Values supplied to the marshmallow schema.

    Raises
    ------
    marshmallow.exceptions.ValidationError
        If forecast and it's observation, aggregate or reference forecast
        are not compatible.
    """
    storage = get_storage()

    errors = {}

    forecast_id = str(data['forecast'])

    observation_id = (str(data['observation'])
                      if data.get('observation') else None)

    aggregate_id = str(data['aggregate']) if data.get('aggregate') else None

    reference_forecast_id = (str(data['reference_forecast'])
                             if data.get('reference_forecast') else None)

    # determine the type of forecast in the pair
    forecast_type = data['forecast_type']

    if forecast_type == 'forecast' or forecast_type == 'event_forecast':
        forecast_loader = storage.read_forecast
    elif forecast_type == 'probabilistic_forecast':
        forecast_loader = storage.read_cdf_forecast_group
    elif forecast_type == 'probabilistic_forecast_constant_value':
        forecast_loader = storage.read_cdf_forecast
    try:
        forecast = forecast_loader(forecast_id)
    except StorageAuthError:
        raise ValidationError({'forecast': 'Does not exist.'})

    observation = None
    aggregate = None
    reference_forecast = None

    if observation_id is not None:
        try:
            observation = storage.read_observation(observation_id)
        except StorageAuthError:
            obs_errors = 'Does not exist.'
        else:
            obs_errors = _ensure_forecast_measurement_compatibility(
                forecast, observation)
        if obs_errors:
            errors['observation'] = obs_errors

    if aggregate_id is not None:
        try:
            aggregate = storage.read_aggregate(aggregate_id)
        except StorageAuthError:
            agg_errors = 'Does not exist.'
        else:
            agg_errors = _ensure_forecast_measurement_compatibility(
                forecast, aggregate)
        if agg_errors:
            errors['aggregate'] = agg_errors

    if reference_forecast_id is not None:
        try:
            reference_forecast = forecast_loader(reference_forecast_id)
        except StorageAuthError:
            reference_errors = 'Does not exist.'
        else:
            reference_errors = _ensure_forecast_reference_compatibility(
                forecast, reference_forecast, forecast_type)
        if reference_errors:
            errors['reference_forecast'] = reference_errors

    if errors:
        raise ValidationError(errors)
