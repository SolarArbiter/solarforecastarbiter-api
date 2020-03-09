# Centralized definitions for injecting reusable variables
# into templates. Variables should be added to the dict returned by
# the template_variables function.

import pytz

import sfa_dash
from sfa_dash import filters
from solarforecastarbiter.datamodel import (
    ALLOWED_CATEGORIES, ALLOWED_DETERMINISTIC_METRICS)


TIMEZONES = pytz.country_timezones('US') + list(
    filter(lambda x: 'GMT' in x, pytz.all_timezones))


VARIABLE_OPTIONS = {key: f'{value} ({filters.api_varname_to_units(key)})'
                    for key, value in filters.variable_mapping.items()}

DEFAULT_VARIABLE = 'ghi'


TIMEZONE_OPTIONS = {tz: tz.replace('_', ' ') for tz in TIMEZONES}


DEFAULT_METRICS = ['mae', 'mbe', 'rmse']


ALLOWED_QUALITY_FLAGS = {
    'USER FLAGGED': 1,
    'NIGHTTIME': 16,
}


def template_variables():
    return {
        'dashboard_version': sfa_dash.__version__,
        'variable_options': VARIABLE_OPTIONS,
        'default_variable': DEFAULT_VARIABLE,
        'timezone_options': TIMEZONE_OPTIONS,
        'metric_categories': ALLOWED_CATEGORIES,
        'deterministic_metrics': ALLOWED_DETERMINISTIC_METRICS,
        'default_metrics': DEFAULT_METRICS,
        'quality_flags': ALLOWED_QUALITY_FLAGS
    }
