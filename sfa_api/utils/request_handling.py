from flask import request
from io import StringIO
import pandas as pd

from sfa_api.utils.errors import BadAPIRequest


def validate_parsable_values():
    """Can be called from a POST view/endpoint to examine posted
    data for mimetype and attempt to parse to a DataFrame.

    Raises
    ------
    BasAPIRequest
        If the data cannot be parsed.
    """
    if request.content_type == 'application/json':
        raw_data = request.get_json()
        try:
            raw_values = raw_data['values']
        except (TypeError, KeyError):
            error = 'Supplied JSON does not contain "values" field.'
            raise BadAPIRequest(error=error)
        try:
            value_df = pd.DataFrame(raw_values)
        except ValueError:
            raise BadAPIRequest({'error': 'Malformed JSON'})
    elif request.content_type == 'text/csv':
        raw_data = StringIO(request.get_data(as_text=True))
        try:
            value_df = pd.read_csv(raw_data,
                                   na_values=[-999.0, -9999.0],
                                   keep_default_na=True,
                                   comment='#')
        except pd.errors.EmptyDataError:
            raise BadAPIRequest({'error': 'Malformed CSV'})
        finally:
            raw_data.close()
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
