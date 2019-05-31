from solarforecastarbiter.datamodel import ALLOWED_VARIABLES, COMMON_NAMES


variable_mapping = COMMON_NAMES


def api_to_dash_varname(api_varname):
    return COMMON_NAMES[api_varname]


def api_varname_to_units(api_varname):
    return ALLOWED_VARIABLES[api_varname]


def display_timedelta(minutes):
    """Converts timedelta in seconds to human friendly format.

    Parameters
    ----------
    minutes: int

    Returns
    -------
    string
        The timedelta in 'x days y hours z minutes' format.

    Raises
    ------
    ValueError
        If the timedelta is negative or evaluates to 0.
    """
    def plural(num):
        if num > 1:
            return 's'
        else:
            return ''
    if minutes <= 0:
        raise ValueError
    days = minutes // 1440
    hours = minutes // 60 % 24
    minutes = minutes % 60
    time_elements = []
    if days > 0:
        time_elements.append(f'{days} day{plural(days)}')
    if hours > 0:
        time_elements.append(f'{hours} hour{plural(hours)}')
    if minutes > 0:
        time_elements.append(f'{minutes} minute{plural(minutes)}')
    time_string = ' '.join(time_elements)
    return time_string


def register_jinja_filters(app):
    app.jinja_env.filters['convert_varname'] = api_to_dash_varname
    app.jinja_env.filters['var_to_units'] = api_varname_to_units
    app.jinja_env.filters['display_timedelta'] = display_timedelta
