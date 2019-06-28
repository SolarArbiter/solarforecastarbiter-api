# Centralized definitions for injecting reusable variables
# into templates. Variables should be added to the dict returned by
# the template_variables function.

import pytz

import sfa_dash
from sfa_dash import filters

TIMEZONES = pytz.country_timezones('US') + list(
    filter(lambda x: 'GMT' in x, pytz.all_timezones))


VARIABLE_OPTIONS = {key: f'{value} ({filters.api_varname_to_units(key)})'
                    for key, value in filters.variable_mapping.items()}

TIMEZONE_OPTIONS = {tz: tz.replace('_', ' ') for tz in TIMEZONES}


def template_variables():
    return {
        'dashboard_version': sfa_dash.__version__,
        'variable_options': VARIABLE_OPTIONS,
        'timezone_options': TIMEZONE_OPTIONS,
    }
