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
    except (pd.errors.EmptyDataError, pd.errors.ParserError):
        raise BadAPIRequest({'error': 'Malformed CSV'})
    return value_df


def parse_json(json_str):
    """Parse a string of json values into a DataFrame

    Parameters
    ----------
    json_str: str

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
        json_dict = json.loads(json_str)
    except json.decoder.JSONDecodeError:
        raise BadAPIRequest(error='Malformed JSON.')
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


def parse_values(decoded_data, mimetype):
    """Attempts to parse a string of data into a DataFrame based on MIME type.

    Parameters
    ----------
    decoded_data: str
        A string of data to parse.
    mimetype: str
        The MIME type of the data.

    Returns
    -------
    pandas.DataFrame

    Raises
    ------
    BadAPIRequest
        - If the MIME type is not one of 'text/csv', 'application/json',
          or 'application/vnd.ms-excel'
        - If parsing fails, see parse_json or parse_csv for conditions.
    """
    if mimetype == 'text/csv' or mimetype == 'application/vnd.ms-excel':
        values = parse_csv(decoded_data)
    elif mimetype == 'application/json':
        values = parse_json(decoded_data)
    else:
        error = "Unsupported Content-Type or MIME type."
        raise BadAPIRequest(error=error)
    return values


def decode_file_in_request_body():
    """Decode the data from a utf-8 encoded file into a string and
    return the contents and the file's mimetype.

    Returns
    -------
    decoded_data: str
        The posted utf-8 data as a string.
    posted_file.mimetype: str
        MIME type of the file in the request body.

    Raises
    ------
    BadAPIRequest
        - There is more than one file in the request.
        - If the request does not contain a file.
        - The file does not contain valid utf-8.
    """
    posted_files = list(request.files.keys())
    if len(posted_files) > 1:
        error = "Multiple files found. Please upload one file at a time."
        raise BadAPIRequest(error=error)

    try:
        posted_filename = posted_files[0]
        posted_file = request.files[posted_filename]
    except IndexError:
        error = "Missing file in request body."
        raise BadAPIRequest(error=error)

    posted_data = posted_file.read()

    try:
        decoded_data = posted_data.decode('utf-8')
    except UnicodeDecodeError:
        error = 'File could not be decoded as UTF-8.'
        raise BadAPIRequest(error=error)

    return decoded_data, posted_file.mimetype


def validate_parsable_values():
    """Can be called from a POST view/endpoint to examine posted
    data for mimetype and attempt to parse to a DataFrame.

    Raises
    ------
    BadAPIRequest
        If the data cannot be parsed.
    """
    if request.mimetype == 'multipart/form-data':
        decoded_data, mimetype = decode_file_in_request_body()
    else:
        decoded_data = request.get_data(as_text=True)
        mimetype = request.mimetype
    value_df = parse_values(decoded_data, mimetype)
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
