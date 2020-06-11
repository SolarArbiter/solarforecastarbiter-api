# Centralized definitions for injecting reusable variables
# into templates. Variables should be added to the dict returned by
# the template_variables function.

import pytz
from flask import g, request, current_app

import sfa_dash
from sfa_dash import filters
from solarforecastarbiter.datamodel import (
    ALLOWED_CATEGORIES,
    ALLOWED_DETERMINISTIC_METRICS,
    ALLOWED_EVENT_METRICS,
    ALLOWED_PROBABILISTIC_METRICS,
    ALLOWED_VARIABLES,
    COMMON_NAMES,
)

TIMEZONES = pytz.country_timezones('US') + list(
    filter(lambda x: 'GMT' in x, pytz.all_timezones))


VARIABLE_OPTIONS = {key: f'{value} ({filters.api_varname_to_units(key)})'
                    for key, value in filters.variable_mapping.items()}

DEFAULT_VARIABLE = 'ghi'


TIMEZONE_OPTIONS = {tz: tz.replace('_', ' ') for tz in TIMEZONES}


DEFAULT_METRICS = ['mae', 'mbe', 'rmse']

DEFAULT_CATEGORIES = ['total', 'year', 'month', 'hour', 'date']

ALL_METRICS = {}
ALL_METRICS.update(ALLOWED_DETERMINISTIC_METRICS)
ALL_METRICS.update(ALLOWED_EVENT_METRICS)
ALL_METRICS.update(ALLOWED_PROBABILISTIC_METRICS)

ALLOWED_QUALITY_FLAGS = {
    'USER FLAGGED': 'USER FLAGGED',
    'NIGHTTIME': 'NIGHTTIME',
    'CLEARSKY': 'CLEARSKY (GHI only)',
    'LIMITS EXCEEDED': 'LIMITS EXCEEDED',
    'STALE VALUES': 'STALE VALUES (includes fixed values at nighttime)',
    'DAYTIME STALE VALUES': 'DAYTIME STALE VALUES',
    'INTERPOLATED VALUES':
        'INTERPOLATED VALUES (includes fixed values at nighttime)',
    'DAYTIME INTERPOLATED VALUES': 'DAYTIME INTERPOLATED VALUES'
}


def is_allowed(action):
    """Returns if the action is allowed or not on the current object.

    Parameters
    ----------
    action: str
        The action to query for permission.

    Returns
    -------
    bool
        If the action is allowed or not.
    """
    allowed = getattr(g, 'allowed_actions', [])
    return action in allowed


def parse_quality_flags(form_dict):
    """Parses quality flag filter values out of a parsed form_data
    dictionary. This is necessary because filters are presented as a list
    of dicts where a key designates filter type.

    Parameters
    ----------
    form_dict: dict
        The api payload parsed from form data in the form of a dictionary.

    Returns
    -------
    list
        List of quality flags.
    """
    filters = form_dict.get('report_parameters', {}).get('filters', {})
    if filters:
        quality_flag_filters = filter(
            lambda x: 'quality_flags' in x,
            filters,
        )
        quality_flags = [flag for filt in quality_flag_filters
                         for flag in filt['quality_flags']]
    else:
        quality_flags = []
    return quality_flags


def template_variables():
    return {
        'dashboard_version': sfa_dash.__version__,
        'variable_options': VARIABLE_OPTIONS,
        'default_variable': DEFAULT_VARIABLE,
        'timezone_options': TIMEZONE_OPTIONS,
        'metric_categories': ALLOWED_CATEGORIES,
        'default_categories': DEFAULT_CATEGORIES,
        'deterministic_metrics': ALLOWED_DETERMINISTIC_METRICS,
        'default_deterministic_metrics': DEFAULT_METRICS,
        'event_metrics': ALLOWED_EVENT_METRICS,
        'probabilistic_metrics': ALLOWED_PROBABILISTIC_METRICS,
        'all_metrics': ALL_METRICS,
        'quality_flags': ALLOWED_QUALITY_FLAGS,
        'is_allowed': is_allowed,
        'current_path': request.path,
        'MAX_DATA_RANGE_DAYS': current_app.config['MAX_DATA_RANGE_DAYS'].days,
        'MAX_PLOT_DATAPOINTS': current_app.config['MAX_PLOT_DATAPOINTS'],
        'parse_quality_flags': parse_quality_flags,
        'variable_names': COMMON_NAMES,
        'variable_unit_map': ALLOWED_VARIABLES,
    }
