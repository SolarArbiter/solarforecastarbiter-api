from collections import defaultdict
from io import StringIO


from flask import request
import numpy as np
import pandas as pd


from sfa_api.utils.errors import BadAPIRequest


def validate_observation_values(observation_df, quality_flag_range=[0, 1]):
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

    if 'quality_flag' not in observation_df.columns:
        errors['quality_flag'].append('Missing "quality_flag" field.')
    else:
        # make sure quality flag is an integer
        if not np.isclose(
                observation_df['quality_flag'].mod(1), 0, 1e-12).all():
            errors['quality_flag'].append(
                'Item in "quality_flag" field is not an integer.')

        if not observation_df['quality_flag'].between(
                *quality_flag_range).all():
            errors['quality_flag'].append(
                'Item in "quality_flag" field out of range.')
    if errors:
        raise BadAPIRequest(errors)
    return observation_df


def validate_parsable_values():
    """Can be called from a POST view/endpoint to examine posted
    data for mimetype and attempt to parse to a DataFrame.

    Raises
    ------
    BadAPIRequest
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
