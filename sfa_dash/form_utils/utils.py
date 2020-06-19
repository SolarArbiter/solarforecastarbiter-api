def parse_timedelta_from_form(data_dict, key_root):
    """Parse values from a timedelta form element, and return the value in
    minutes

    Parameters
    ----------
    data_dict: dict
        Dictionary of posted form data

    key_root: string
        The shared part of the name attribute of the inputs to parse.
        e.g. 'lead_time' will parse and concatenate 'lead_time_number'
        and 'lead_time_units'

    Returns
    -------
    int
        The number of minutes in the Timedelta.

    Raises
    ------
    ValueError
        If the units field is not one of 'minutes', 'hours' or 'days', or if
        the number field is not a valid integer.
    """
    value = int(data_dict[f'{key_root}_number'])
    units = data_dict[f'{key_root}_units']
    if units == 'minutes':
        return value
    elif units == 'hours':
        return value * 60
    elif units == 'days':
        return value * 1440
    else:
        raise ValueError(f'Invalid units in {key_root} field.')


def parse_timedelta_from_api(data_dict, key_root):
    """Returns a dict with the appropriate key for filling a two-part timedelta
    field where the fields are named <key_root>_number and <key_root>_units.

    Parameters
    ----------
    data_dict: dict
        API json response containing a key matching the key_root argument.
    key_root: str
        The prefix used to identify the timedelta `<input>` elements. This
        should match the metadata dictionaries key for accessing the value.

    Returns
    -------
    dict
        dict with keys <key_root>_number and <key_root>_units set to the
        appropriate values.

    Raises
    ------
    TypeError
        If the interval length key is set to a non-numeric value or does not
        exist.
    """
    interval_minutes = data_dict.get(key_root)
    # set minutes as default interval_units, as these are returned by the API
    interval_units = 'minutes'
    if interval_minutes % 1440 == 0:
        interval_units = 'days'
        interval_value = interval_minutes / 1440
    elif interval_minutes % 60 == 0:
        interval_units = 'hours'
        interval_value = interval_minutes / 60
    else:
        interval_value = interval_minutes
    return {
        f'{key_root}_number': interval_value,
        f'{key_root}_units': interval_units,
    }


def parse_hhmm_field_from_form(data_dict, key_root):
    """ Extracts and parses the hours and minutes inputs to create a
    parseable time of day string in HH:MM format. These times are
    displayed as two select fields designated with a name (key_root)
    and _hours or _minutes suffix.

    Parameters
    ----------
    data_dict: dict
        Dictionary of posted form data

    key_root: string
        The shared part of the name attribute of the inputs to parse.
        e.g. 'issue_time' will parse and concatenate 'issue_time_hours'
        and 'issue_time_minutes'

    Returns
    -------
    string
        The time value in HH:MM format.
    """
    hours = int(data_dict[f'{key_root}_hours'])
    minutes = int(data_dict[f'{key_root}_minutes'])
    return f'{hours:02d}:{minutes:02d}'


def parse_hhmm_field_from_api(data_dict, key_root):
    """ Extracts and parses the hours and minutes from a HH:MM format into
    the keys for filling a time of day form field. These times are
    displayed as two select fields designated with names <key_root>_hours and
    <key_root>_minutes

    Parameters
    ----------
    data_dict: dict
        API json parsed into a python dict. Should contain the a key matching
        key_root argument.

    key_root: string
        The attribute of the data dict to parse. This should match the prefix
        of the input fields found in the form.

    Returns
    -------
    dict
        A dictionary where the keys are <key_root>_hours and <key_root>_minutes
        for prefilling form data.
    """
    tod_string = data_dict.get(key_root)
    parts = tod_string.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    return {
        f'{key_root}_hours': hours,
        f'{key_root}_minutes': minutes,
    }


def flatten_dict(to_flatten):
    """Flattens nested dictionaries, removing keys of the nested elements.
    Useful for flattening API responses for prefilling forms on the
    dashboard.
    """
    flattened = {}
    for key, value in to_flatten.items():
        if isinstance(value, dict):
            flattened.update(flatten_dict(value))
        else:
            flattened[key] = value
    return flattened


def get_location_id(from_dict):
    """Searched from_dict for a site_id or aggregate_id and sets the value of
    in to_dict.
    """
    location_dict = {}
    if 'site_id' in from_dict:
        location_dict['site_id'] = from_dict.get('site_id')
    if 'aggregate_id' in from_dict:
        location_dict['aggregate_id'] = from_dict.get('aggregate_id')
    return location_dict


def filter_form_fields(prefix, form_data):
    """Creates a list of values from a dictionary where
    keys start with prefix. Mainly used for gathering lists
    from form data.
        e.g. If a role form's permissions fields are prefixed
             with "role-permission-<index>" passing in a prefix
             if 'role-permission-' will return all of the inputs
             values as a list.

    Parameters
    ----------
    prefix: str
        The key prefix to search for.
    form_data: Dict
        The dictionary of form data to search for.

    Returns
    -------
    list
        List of all values where the corresponding key began with prefix.
    """
    values = [form_data[key]
              for key in form_data.keys()
              if key.startswith(prefix)]
    return [None if v == 'null' else v for v in values]
