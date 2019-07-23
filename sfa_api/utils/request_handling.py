from collections import defaultdict
from io import StringIO
import json


from flask import request
import numpy as np
import pandas as pd


from sfa_api.utils.errors import BadAPIRequest


def validate_observation_values(observation_df, quality_flag_range=(0, 1)):
    """
    Validate the columns of an observation value DataFrame.

    Parameters
    ----------
    observation_df : pandas.DataFrame
        DataFrame to validate columns and values
    quality_flag_range : tuple, default (0, 1)
        Range of allowable quality_flag

    Returns
    -------
    pandas.DataFrame
       With types adjusted as appropriate

    Raises
    ------
    BadAPIRequest
        For any errors in the columns or values
    """
    errors = defaultdict(list)
    try:
        observation_df['value'] = pd.to_numeric(observation_df['value'],
                                                downcast='float')
    except ValueError:
        errors['value'].append(
            'Invalid item in "value" field. Ensure that all '
            'values are integers, floats, empty, NaN, or NULL.')
    except KeyError:
        errors['value'].append('Missing "value" field.')

    try:
        observation_df['timestamp'] = pd.to_datetime(
            observation_df['timestamp'],
            utc=True)
    except ValueError:
        errors['timestamp'].append(
            'Invalid item in "timestamp" field. Ensure '
            'that timestamps are ISO8601 compliant')
    except KeyError:
        errors['timestamp'].append('Missing "timestamp" field.')

    try:
        observation_df['quality_flag'].astype(int)
    except KeyError:
        errors['quality_flag'].append('Missing "quality_flag" field.')
    except (ValueError, TypeError):
        errors['quality_flag'].append(
            'Item in "quality_flag" field is not an integer.')
    else:
        if not np.isclose(
                observation_df['quality_flag'].mod(1), 0, 1e-12).all():
            errors['quality_flag'].append(
                'Item in "quality_flag" field is not an integer.')

        if not observation_df['quality_flag'].between(
                *quality_flag_range).all():
            errors['quality_flag'].append(
                'Item in "quality_flag" field out of range '
                f'{quality_flag_range}.')
    if errors:
        raise BadAPIRequest(errors)
    return observation_df


def parse_csv(csv_string):
    """Parse a csv into a dataframe and raise appropriate errors

    Parameters
    ----------
    csv_string: str
        String representation of csv to read into a dataframe

    Returns
    -------
    pandas.DataFrame

    Raises
    ------
    BadAPIRequestError
        If the string cannot be parsed.
    """
    raw_data = StringIO(csv_string)
    try:
        value_df = pd.read_csv(raw_data,
                               na_values=[-999.0, -9999.0],
                               keep_default_na=True,
                               comment='#')
    except pd.errors.EmptyDataError:
        raise BadAPIRequest({'error': 'Malformed CSV'})
    return value_df


def parse_json(json_dict):
    """Parse a dictionary representing POSTed JSON into a DataFrame

    Parameters
    ----------
    json_dict: dict

    Returns
    -------
    pandas.DataFrame

    Raises
    ------
    BadAPIRequestError
        If the 'values' key is missing, or if the contents of the
        values key cannot be parsed into a DataFrame.
    """
    try:
        raw_values = json_dict['values']
    except (TypeError, KeyError):
        error = 'Supplied JSON does not contain "values" field.'
        raise BadAPIRequest(error=error)
    try:
        value_df = pd.DataFrame(raw_values)
    except ValueError:
        raise BadAPIRequest({'error': 'Malformed JSON'})
    return value_df


def validate_parsable_values():
    """Can be called from a POST view/endpoint to examine posted
    data for mimetype and attempt to parse to a DataFrame.

    Raises
    ------
    BadAPIRequest
        If the data cannot be parsed.
    """
    if request.mimetype == 'multipart/form-data':
        # handle single file uploads
        try:
            posted_filename = list(request.files.keys())[0]
            posted_file = request.files[posted_filename]
        except IndexError:
            error = "Missing file in request body."
            raise BadAPIRequest(error=error)
        if (
                posted_file.mimetype == 'text/csv' or
                posted_file.mimetype == 'application/vnd.ms-excel' or
                posted_file.mimetype == 'application/json'
        ):
            posted_data = posted_file.read()
            try:
                decoded_data = posted_data.decode('utf-8')
            except UnicodeDecodeError:
                error = 'File could not be decoded as UTF-8.'
                raise BadAPIRequest(error=error)
        else:
            error = "Uploaded file has invalid mimetype."
            raise BadAPIRequest(error=error)
        if posted_file.mimetype == 'application/json':
            try:
                json_dict = json.loads(decoded_data)
            except json.decoder.JSONDecodeError:
                raise BadAPIRequest(error='Malformed JSON.')
            value_df = parse_json(json_dict)
        else:
            value_df = parse_csv(decoded_data)
    elif request.mimetype == 'application/json':
        # handle json in request body
        raw_data = request.get_json()
        value_df = parse_json(raw_data)
    elif request.mimetype == 'text/csv':
        # handle a csv in request body
        csv_string = request.get_data(as_text=True)
        value_df = parse_csv(csv_string)
    else:
        error = 'Invalid Content-type.'
        raise BadAPIRequest({'error': error})
    return value_df


def validate_start_end():
    """Parses start and end query parameters into pandas
    Timestamps.

    Returns
    -------
    start: Pandas Timestamp
    end: Pandas TimeStamp

    Raises
    ------
    BadAPIRequest
        If start and end values cannot be parsed.
    """
    errors = {}
    start = request.args.get('start', None)
    end = request.args.get('end', None)
    if start is not None:
        try:
            start = pd.Timestamp(start)
        except ValueError:
            errors.update({'start': ['Invalid start date format']})
    if end is not None:
        try:
            end = pd.Timestamp(end)
        except ValueError:
            errors.update({'end': ['Invalid end date format']})
    if errors:
        raise BadAPIRequest(errors)
    return start, end
