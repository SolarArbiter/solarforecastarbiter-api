"""This file contains method stubs to act as the interface for
storage interactions in the Solar Forecast Arbiter. The 'sfa_api.demo'
module is a static implementation intended for developing against when
it is not feasible to utilize a mysql instance or other persistent
storage.
"""
from contextlib import contextmanager
from copy import deepcopy
import datetime as dt
from functools import partial
import math
import random
import re
import uuid


from cryptography.fernet import Fernet
from flask import current_app
import numpy as np
import pandas as pd
import pymysql
from pymysql import converters
import pytz
from sqlalchemy.engine import create_engine
from sqlalchemy.pool import QueuePool


from sfa_api import schema, json
from sfa_api.utils import auth0_info
from sfa_api.utils.auth import current_user
from sfa_api.utils.errors import (StorageAuthError, DeleteRestrictionError,
                                  BadAPIRequest)


# min and max timestamps storable in mysql
MINTIMESTAMP = pd.Timestamp('19700101T000001Z')
MAXTIMESTAMP = pd.Timestamp('20380119T031407Z')
# microseconds dropped on purpose, must quote
# this is faster than using strftime
TIMEFORMAT = "'{0.year:04}-{0.month:02}-{0.day:02} {0.hour:02}:{0.minute:02}:{0.second:02}'"  # NOQA
NANSTR = '"__MYSQLNAN"'
INFSTR = '"__MYSQLINF"'
NINFSTR = '"__MYSQLNINF"'
# look back and match [{:, or the start, then any number of
# whitespace, then string like NaN, then ]}, or end of string
_RESTR = ('(?<![^[{:,])(?P<sp>\\s*)', '(?=[\\],}]|\\Z)')
RENAN = re.compile(_RESTR[0] + 'NaN' + _RESTR[1])
REINF = re.compile(_RESTR[0] + 'Infinity' + _RESTR[1])
RENINF = re.compile(_RESTR[0] + '-Infinity' + _RESTR[1])


POWER_VARIABLES = ['ac_power', 'dc_power', 'poa_global', 'availability']


def generate_uuid():
    """Generate a version 1 UUID and ensure clock_seq is random"""
    return str(uuid.uuid1(clock_seq=random.SystemRandom().getrandbits(14)))


def _replace(s):
    out = s
    if 'NaN' in out:
        out = RENAN.sub('\\g<1>' + NANSTR, out)
    if '-Infinity' in out:
        out = RENINF.sub('\\g<1>' + NINFSTR, out)
    if 'Infinity' in out:
        out = REINF.sub('\\g<1>' + INFSTR, out)
    return out


def dump_json_replace_nan(obj):
    """Dump the object to json and replace any NaN, +-Infinity
    values with special strings for storing in mysql"""
    outstr = json.dumps(obj, allow_nan=True)
    return _replace(outstr)


def load_json_replace_nan(inp):
    """Replace the special nan/inf strings with the json parser
    string for that value"""
    if NANSTR in inp:
        inp = inp.replace(NANSTR, 'NaN')
    if INFSTR in inp:
        inp = inp.replace(INFSTR, 'Infinity')
    if NINFSTR in inp:
        inp = inp.replace(NINFSTR, '-Infinity')
    return json.loads(inp)


def escape_float_with_nan(value, mapping=None):
    if math.isnan(value):
        return 'NULL'
    else:
        return ('%.15g' % value)


def escape_timestamp(value, mapping=None):
    if value.tzinfo is not None:
        return TIMEFORMAT.format(value.tz_convert('UTC'))
    else:
        return TIMEFORMAT.format(value)


def escape_datetime(value, mapping=None):
    if value.tzinfo is not None:
        return TIMEFORMAT.format(value.astimezone(dt.timezone.utc))
    else:
        return TIMEFORMAT.format(value)


def convert_datetime_utc(obj):
    unlocalized = converters.convert_datetime(obj)
    return pytz.utc.localize(unlocalized)


def _make_sql_connection_partial():
    config = current_app.config
    conv = converters.conversions.copy()
    # either convert decimals to floats, or add decimals to schema
    conv[converters.FIELD_TYPE.DECIMAL] = float
    conv[converters.FIELD_TYPE.NEWDECIMAL] = float
    conv[converters.FIELD_TYPE.TIMESTAMP] = convert_datetime_utc
    conv[converters.FIELD_TYPE.DATETIME] = convert_datetime_utc
    conv[converters.FIELD_TYPE.JSON] = load_json_replace_nan
    conv[pd.Timestamp] = escape_timestamp
    conv[dt.datetime] = escape_datetime
    conv[float] = escape_float_with_nan
    connect_kwargs = {
        'host': config['MYSQL_HOST'],
        'port': int(config['MYSQL_PORT']),
        'user': config['MYSQL_USER'],
        'password': config['MYSQL_PASSWORD'],
        'database': config['MYSQL_DATABASE'],
        'binary_prefix': True,
        'conv': conv,
        'use_unicode': True,
        'charset': 'utf8mb4',
        'init_command': "SET time_zone = '+00:00'",
        'ssl': {'ssl': True}
    }
    getconn = partial(pymysql.connect, **connect_kwargs)
    return getconn


def mysql_connection():
    if not hasattr(current_app, 'mysql_connection'):
        getconn = _make_sql_connection_partial()
        # use create engine to make pool in order to properly set dialect
        mysqlpool = create_engine('mysql+pymysql://',
                                  creator=getconn,
                                  poolclass=QueuePool,
                                  pool_recycle=3600,
                                  pool_pre_ping=True).pool
        current_app.mysql_connection = mysqlpool
    return current_app.mysql_connection.connect()


@contextmanager
def get_cursor(cursor_type, commit=True):
    if cursor_type == 'standard':
        cursorclass = pymysql.cursors.Cursor
    elif cursor_type == 'dict':
        cursorclass = pymysql.cursors.DictCursor
    else:
        raise AttributeError('cursor_type must be standard or dict')
    connection = mysql_connection()
    cursor = connection.cursor(cursor=cursorclass)
    try:
        yield cursor
    except Exception:
        connection.rollback()
        raise
    else:
        if commit:
            connection.commit()
    finally:
        connection.close()


def try_query(query_cmd):
    try:
        query_cmd()
    except (pymysql.err.OperationalError, pymysql.err.IntegrityError,
            pymysql.err.InternalError) as e:
        ecode = e.args[0]
        if ecode == 1142 or ecode == 1143 or ecode == 1411 or ecode == 1216:
            raise StorageAuthError(e.args[1])
        elif ecode == 1451 or ecode == 1217:
            raise DeleteRestrictionError
        elif ecode == 3140:
            raise BadAPIRequest({'error': e.args[1]})
        else:
            raise


def _call_procedure(
        procedure_name, *args, cursor_type='dict', with_current_user=True):
    """
    Can't user callproc since it doesn't properly use converters.
    Will not handle OUT or INOUT parameters without first setting
    local variables and retrieving from those variables
    """
    with get_cursor(cursor_type) as cursor:
        if with_current_user:
            new_args = (current_user, *args)
        else:
            new_args = args
        query = f'CALL {procedure_name}({",".join(["%s"] * len(new_args))})'
        query_cmd = partial(cursor.execute, query, new_args)
        try_query(query_cmd)
        return cursor.fetchall()


def _call_procedure_for_single(procedure_name, *args, cursor_type='dict',
                               with_current_user=True):
    """Wrapper handling try/except logic when a single value is expected
    """
    try:
        result = _call_procedure(procedure_name, *args,
                                 cursor_type=cursor_type,
                                 with_current_user=with_current_user)[0]
    except IndexError:
        raise StorageAuthError()
    return result


def _set_modeling_parameters(site_dict):
    out = {}
    modeling_parameters = {}
    for key in schema.ModelingParameters().fields.keys():
        modeling_parameters[key] = site_dict[key]
    for key in schema.SiteResponseSchema().fields.keys():
        if key == 'modeling_parameters':
            out[key] = modeling_parameters
        else:
            out[key] = site_dict[key]
    return out


def _set_observation_parameters(observation_dict):
    out = {}
    for key in schema.ObservationSchema().fields.keys():
        if key in ('_links',):
            continue
        out[key] = observation_dict[key]
    return out


def _set_forecast_parameters(forecast_dict):
    out = {}
    for key in schema.ForecastSchema().fields.keys():
        if key in ('_links', ):
            continue
        out[key] = forecast_dict[key]
    return out


def _process_df_into_json(df, rounding=8):
    """Processes a Dataframe with DatetimeIndex and 'value' column
    (with optional 'quality_flag' column) into a json string of the
    form [{"ts": ..., "v": ...}, ...] for sending to MySQL.

    This numpy string processing to JSON is much faster than
    using the json module and converting the dataframe to a list
    of dicts. Also can't use the builtin pandas json exporter
    because we need to leave out the value key completely when
    the value is NaN (limitation of MySQL JSON_TABLE for json null).
    """
    timestr = np.char.add(
        '{"ts":"', df.index.values.astype('M8[s]').astype(str))
    timeend = '"'
    values = df['value'].values
    nans = np.isnan(values)
    valstr = np.char.add(
        timeend + ',"v":', np.round(values, rounding).astype('str'))
    valstr[nans] = timeend
    if 'quality_flag' in df.columns:
        qf = np.char.add(
            ',"qf":',
            df['quality_flag'].values.astype(int).astype(str))
        valstr = np.char.add(valstr, qf)
    objarr = np.char.add(timestr, valstr)
    if len(objarr) == 0:
        return '[]'
    else:
        return '[' + '},'.join(objarr) + '}]'


def store_observation_values(observation_id, observation_df):
    """Store observation data.

    Parameters
    ----------
    observation_id: string
        UUID of the associated observation.
    observation_df: DataFrame
        Dataframe with DatetimeIndex, value, and quality_flag column.

    Returns
    -------
    string
        The UUID of the associated Observation.

    Raises
    ------
    StorageAuthError
        If the user does not have permission to store values on the Observation
        or if the Observation does not exists
    """
    obs_json = _process_df_into_json(observation_df)
    _call_procedure('store_observation_values', observation_id, obs_json)
    return observation_id


def read_observation_values(observation_id, start=None, end=None):
    """Read observation values between start and end.

    Parameters
    ----------
    observation_id: string
        UUID of associated observation.
    start: datetime
        Beginning of the period for which to request data.
    end: datetime
        End of the period for which to request data.

    Returns
    -------
    pandas.DataFrame
        With 'value' and 'quality_flag' columns and a DatetimeIndex
        named 'timestamp'.
    """
    if start is None:
        start = MINTIMESTAMP
    if end is None:
        end = MAXTIMESTAMP

    obs_vals = _call_procedure('read_observation_values', observation_id,
                               start, end, cursor_type='standard')
    df = pd.DataFrame.from_records(
        list(obs_vals), columns=['observation_id', 'timestamp',
                                 'value', 'quality_flag']
    ).drop(columns='observation_id').set_index('timestamp')
    return df


def read_latest_observation_value(observation_id):
    """Read the most recent observation value.

    Parameters
    ----------
    observation_id: string
        UUID of associated observation.

    Returns
    -------
    pandas.DataFrame
        With a value column and datetime index and only one row
    """
    obs_vals = _call_procedure('read_latest_observation_value', observation_id,
                               cursor_type='standard')
    df = pd.DataFrame.from_records(
        list(obs_vals), columns=[
            'observation_id', 'timestamp', 'value', 'quality_flag']
    ).drop(columns='observation_id').set_index('timestamp')
    return df


def read_observation_time_range(observation_id):
    """Get the time range of values for a observation.

    Parameters
    ----------
    observation_id: string
        UUID of associated observation.

    Returns
    -------
    dict
        With `min_timestamp` and `max_timestamp` keys that are either
        dt.datetime objects or None
    """
    return _call_procedure_for_single(
        'read_observation_time_range', observation_id)


def store_observation(observation):
    """Store Observation metadata. Should generate and store a uuid
    as the 'observation_id' field.

    Parameters
    ----------
    observation: dictionary
        A dictionary of observation fields to insert.

    Returns
    -------
    string
        The UUID of the newly created Observation.
    """
    observation_id = generate_uuid()
    if observation['variable'] in POWER_VARIABLES:
        if not _site_has_modeling_params(str(observation['site_id'])):
            raise BadAPIRequest(
                site="Site must have modeling parameters to create "
                     f"{', '.join(POWER_VARIABLES)} observation.")

    # the procedure expects arguments in a certain order
    _call_procedure(
        'store_observation', observation_id,
        observation['variable'], str(observation['site_id']),
        observation['name'], observation['interval_label'],
        observation['interval_length'], observation['interval_value_type'],
        observation['uncertainty'], observation['extra_parameters'])

    return observation_id


def read_observation(observation_id):
    """Read Observation metadata.

    Parameters
    ----------
    observation_id: String
        UUID of the observation to retrieve.

    Returns
    -------
    dict
        The Observation's metadata or None if the Observation
        does not exist.
    """
    observation = _set_observation_parameters(
        _call_procedure_for_single('read_observation', observation_id))
    return observation


def delete_observation(observation_id):
    """Remove an Observation from storage.

    Parameters
    ----------
    observation_id: String
        UUID of observation to delete

    Raises
    ------
    StorageAuthError
        If the user does not have permission to delete the observation
    """
    _call_procedure('delete_observation', observation_id)


def list_observations(site_id=None):
    """Lists all observations a user has access to.

    Parameters
    ----------
    site_id: string
        UUID of Site, when supplied returns only Observations
        made for this Site.

    Returns
    -------
    list
        List of dictionaries of Observation metadata.

    Raises
    ------
    StorageAuthError
        If the user does not have access to observations with site_id or
        no observations exists for that id
    """
    if site_id is not None:
        read_site(site_id)
    observations = [_set_observation_parameters(obs)
                    for obs in _call_procedure('list_observations')
                    if site_id is None or obs['site_id'] == site_id]
    return observations


# Forecasts
def store_forecast_values(forecast_id, forecast_df):
    """Store Forecast data

    Parameters
    ----------
    forecast_id: string
        UUID of the associated forecast.
    forecast_df: DataFrame
        Dataframe with DatetimeIndex and value column.

    Returns
    -------
    string
        The UUID of the associated forecast.

    Raises
    ------
    StorageAuthError
        If the user does not have permission to write values for the Forecast
    """
    fx_json = _process_df_into_json(forecast_df)
    _call_procedure('store_forecast_values', forecast_id, fx_json)
    return forecast_id


def _read_fx_values(procedure_name, forecast_id, start, end):
    if start is None:
        start = MINTIMESTAMP
    if end is None:
        end = MAXTIMESTAMP

    fx_vals = _call_procedure(procedure_name, forecast_id,
                              start, end, cursor_type='standard')
    df = pd.DataFrame.from_records(
        list(fx_vals), columns=['forecast_id', 'timestamp', 'value']
    ).drop(columns='forecast_id').set_index('timestamp')
    return df


def read_forecast_values(forecast_id, start=None, end=None):
    """Read forecast values between start and end.

    Parameters
    ----------
    forecast_id: string
        UUID of associated forecast.
    start: datetime
        Beginning of the period for which to request data.
    end: datetime
        End of the period for which to request data.

    Returns
    -------
    pandas.DataFrame
        With a value column and datetime index
    """
    return _read_fx_values('read_forecast_values', forecast_id,
                           start, end)


def read_latest_forecast_value(forecast_id):
    """Read the most recent forecast value.

    Parameters
    ----------
    forecast_id: string
        UUID of associated forecast.

    Returns
    -------
    pandas.DataFrame
        With a value column and datetime index and only one row
    """
    fx_vals = _call_procedure('read_latest_forecast_value', forecast_id,
                              cursor_type='standard')
    df = pd.DataFrame.from_records(
        list(fx_vals), columns=['forecast_id', 'timestamp', 'value']
    ).drop(columns='forecast_id').set_index('timestamp')
    return df


def read_forecast_time_range(forecast_id):
    """Get the time range of values for a forecast.

    Parameters
    ----------
    forecast_id: string
        UUID of associated forecast.

    Returns
    -------
    dict
        With `min_timestamp` and `max_timestamp` keys that are either
        dt.datetime objects or None
    """
    return _call_procedure_for_single(
        'read_forecast_time_range', forecast_id)


def store_forecast(forecast):
    """Store Forecast metadata. Should generate and store a uuid
    as the 'forecast_id' field.

    Parameters
    ----------
    forecast: dictionary
        A dictionary of forecast fields to insert.

    Returns
    -------
    string
        The UUID of the newly created Forecast.

    Raises
    ------
    StorageAuthError
        If the user can create Forecasts or the user can't read the site
    """
    forecast_id = generate_uuid()
    if forecast.get('site_id') is not None:
        site_or_agg_id = str(forecast['site_id'])
        ref_site = True

        if forecast['variable'] in POWER_VARIABLES:
            if not _site_has_modeling_params(site_or_agg_id):
                raise BadAPIRequest(
                    site="Site must have modeling parameters to create "
                         f"{', '.join(POWER_VARIABLES)} forecasts.")
    else:
        site_or_agg_id = str(forecast['aggregate_id'])
        ref_site = False

    # the procedure expects arguments in a certain order
    _call_procedure(
        'store_forecast', forecast_id, site_or_agg_id,
        forecast['name'], forecast['variable'], forecast['issue_time_of_day'],
        forecast['lead_time_to_start'], forecast['interval_label'],
        forecast['interval_length'], forecast['run_length'],
        forecast['interval_value_type'], forecast['extra_parameters'],
        ref_site)
    return forecast_id


def read_forecast(forecast_id):
    """Read Forecast metadata.

    Parameters
    ----------
    forecast_id: String
        UUID of the forecast to retrieve.

    Returns
    -------
    dict
        The Forecast's metadata or None if the Forecast
        does not exist.
    """
    forecast = _set_forecast_parameters(
        _call_procedure_for_single('read_forecast', forecast_id))
    return forecast


def delete_forecast(forecast_id):
    """Remove a Forecast from storage.

    Parameters
    ----------
    forecast_id: String
        UUID of the Forecast to delete.

    Raises
    ------
    StorageAuthError
        If the user cannot delete the Forecast
    """
    _call_procedure('delete_forecast', forecast_id)


def list_forecasts(site_id=None, aggregate_id=None):
    """Lists all Forecasts a user has access to.

    Parameters
    ----------
    site_id: string
        UUID of Site, when supplied returns only Forecasts
        made for this Site.
    aggregate_id: string
        UUID of the aggregate, when supplied returns only
        forecasts made for this aggregate.

    Returns
    -------
    list
        List of dictionaries of Forecast metadata.
    """
    if site_id is not None:
        read_site(site_id)
    if aggregate_id is not None:
        read_aggregate(aggregate_id)
    forecasts = [_set_forecast_parameters(fx)
                 for fx in _call_procedure('list_forecasts')
                 if (
                     (site_id is None and aggregate_id is None) or
                     (site_id and fx['site_id'] == site_id) or
                     (aggregate_id and fx['aggregate_id'] == aggregate_id)
    )]
    return forecasts


def read_site(site_id):
    """Read Site metadata.

    Parameters
    ----------
    site_id: String
        UUID of the site to retrieve.

    Returns
    -------
    dict
        The Site's metadata

    Raises
    ------
    StorageAuthError
        If the user does not have access to the site_id or it doesn't exist
    """
    site = _set_modeling_parameters(
        _call_procedure_for_single('read_site', site_id))
    return site


def store_site(site):
    """Store Site metadata. Should generate and store a uuid
    as the 'site_id' field.

    Parameters
    ----------
    site: dict
        Dictionary of site data.

    Returns
    -------
    string
        UUID of the newly created site.
    Raises
    ------
    StorageAuthError
        If the user does not have create permissions
    """
    site_id = generate_uuid()
    # the procedure expects arguments in a certain order
    _call_procedure(
        'store_site', site_id, site['name'], site['latitude'],
        site['longitude'], site['elevation'], site['timezone'],
        site['extra_parameters'],
        *[site['modeling_parameters'][key] for key in [
            'ac_capacity', 'dc_capacity', 'temperature_coefficient',
            'tracking_type', 'surface_tilt', 'surface_azimuth',
            'axis_tilt', 'axis_azimuth', 'ground_coverage_ratio',
            'backtrack', 'max_rotation_angle', 'dc_loss_factor',
            'ac_loss_factor']])
    return site_id


def delete_site(site_id):
    """Remove a Site from storage.

    Parameters
    ----------
    site_id: String
        UUID of the Forecast to delete.

    Raises
    ------
    StorageAuthError
        If the user does not have permission to delete the site
    DeleteRestrictionError
        If the site cannote be delete because other objects depend on it
    """
    _call_procedure('delete_site', site_id)


def list_sites():
    """List all sites.

    Returns
    -------
    list
        List of Site metadata as dictionaries.
    """
    sites = [_set_modeling_parameters(site)
             for site in _call_procedure('list_sites')]
    return sites


def list_sites_in_zone(zone):
    """List all sites within the given zone

    Parameters
    ----------
    zone : str
        The climate zone to get sites from

    Returns
    -------
    list
        List of Site metadata as dictionaries.
    """
    sites = [_set_modeling_parameters(site)
             for site in _call_procedure('list_sites_in_zone', zone)]
    return sites


# CDF Forecasts
def store_cdf_forecast_values(forecast_id, forecast_df):
    """Store CDF Forecast data

    Parameters
    ----------
    forecast_id: string
        UUID of the associated forecast.
    forecast_df: DataFrame
        Dataframe with DatetimeIndex and value column.

    Returns
    -------
    string
        The UUID of the associated forecast. Returns
        None if the CDFForecast does not exist.
    """
    fx_json = _process_df_into_json(forecast_df)
    _call_procedure('store_cdf_forecast_values', forecast_id, fx_json)
    return forecast_id


def read_cdf_forecast_values(forecast_id, start=None, end=None):
    """Read CDF forecast values between start and end.

    Parameters
    ----------
    forecast_id: string
        UUID of associated forecast.
    start: datetime
        Beginning of the period for which to request data.
    end: datetime
        End of the period for which to request data.

    Returns
    -------
    pandas.DataFrame
        With a value column and datetime index
    """
    return _read_fx_values('read_cdf_forecast_values', forecast_id,
                           start, end)


def read_latest_cdf_forecast_value(forecast_id):
    """Read the most recent CDF forecast value.

    Parameters
    ----------
    forecast_id: string
        UUID of associated forecast.

    Returns
    -------
    pandas.DataFrame
        With a value column and datetime index and only one row
    """
    fx_vals = _call_procedure('read_latest_cdf_forecast_value', forecast_id,
                              cursor_type='standard')
    df = pd.DataFrame.from_records(
        list(fx_vals), columns=['forecast_id', 'timestamp', 'value']
    ).drop(columns='forecast_id').set_index('timestamp')
    return df


def read_cdf_forecast_time_range(forecast_id):
    """Get the time range of values for a CDF forecast.

    Parameters
    ----------
    forecast_id: string
        UUID of associated forecast.

    Returns
    -------
    dict
        With `min_timestamp` and `max_timestamp` keys that are either
        dt.datetime objects or None
    """
    return _call_procedure_for_single(
        'read_cdf_forecast_time_range', forecast_id)


def store_cdf_forecast(cdf_forecast):
    """Store CDF Forecast Single metadata. Should generate and store a uuid
    as the 'forecast_id' field.

    Parameters
    ----------
    cdf_forecast: dictionary
        A dictionary of forecast fields to insert.

    Returns
    -------
    string
        The UUID of the newly created CDF Forecast.

    """
    forecast_id = generate_uuid()
    _call_procedure(
        'store_cdf_forecasts_single', forecast_id, cdf_forecast['parent'],
        cdf_forecast['constant_value'])
    return forecast_id


def _set_cdf_forecast_parameters(forecast_dict):
    out = {}
    for key in schema.CDFForecastSchema().fields.keys():
        if key in ('_links', ):
            continue
        elif key == 'modified_at':
            out[key] = forecast_dict['created_at']
        else:
            out[key] = forecast_dict[key]
    return out


def read_cdf_forecast(forecast_id):
    """Read CDF Forecast metadata.

    Parameters
    ----------
    forecast_id: String
        UUID of the forecast to retrieve.

    Returns
    -------
    dict
        The CDF Forecast's metadata or None if the Forecast
        does not exist.
    """
    forecast = _set_cdf_forecast_parameters(
        _call_procedure_for_single('read_cdf_forecasts_single', forecast_id))
    return forecast


def delete_cdf_forecast(forecast_id):
    """Remove a CDF Forecast from storage.

    Parameters
    ----------
    forecast_id: String
        UUID of the Forecast to delete.

    Returns
    -------
    dict
        The CDF Forecast's metadata if successful or None
        if the CDF Forecast does not exist.
    """
    _call_procedure('delete_cdf_forecasts_single', forecast_id)


def list_cdf_forecasts(parent_forecast_id=None):
    """Lists all Forecasts a user has access to.

    Parameters
    ----------
    parent_forecast_id: string
        UUID of the parent CDF Forecast Group.

    Returns
    -------
    list
        List of dictionaries of CDF Forecast metadata.
    """
    if parent_forecast_id is not None:
        read_cdf_forecast_group(parent_forecast_id)
    forecasts = [_set_cdf_forecast_parameters(fx)
                 for fx in _call_procedure('list_cdf_forecasts_singles')
                 if parent_forecast_id is None or
                 fx['parent'] == parent_forecast_id]
    return forecasts


# CDF Probability Groups
def store_cdf_forecast_group(cdf_forecast_group):
    """Store CDF Forecast Group metadata. Should generate
    and store a uuid as the 'forecast_id' field.

    Parameters
    ----------
    cdf_forecast_group: dictionary
        A dictionary of CDF Forecast Group fields to insert.

    Returns
    -------
    string
        The UUID of the newly created CDF Forecast.

    """
    forecast_id = generate_uuid()
    if cdf_forecast_group.get('site_id') is not None:
        site_or_agg_id = str(cdf_forecast_group['site_id'])
        ref_site = True

        if cdf_forecast_group['variable'] in POWER_VARIABLES:
            if not _site_has_modeling_params(site_or_agg_id):
                raise BadAPIRequest(
                    site="Site must have modeling parameters to create "
                         f"{', '.join(POWER_VARIABLES)} forecasts.")
    else:
        site_or_agg_id = str(cdf_forecast_group['aggregate_id'])
        ref_site = False

    # the procedure expects arguments in a certain order
    _call_procedure('store_cdf_forecasts_group',
                    forecast_id,
                    site_or_agg_id,
                    cdf_forecast_group['name'],
                    cdf_forecast_group['variable'],
                    cdf_forecast_group['issue_time_of_day'],
                    cdf_forecast_group['lead_time_to_start'],
                    cdf_forecast_group['interval_label'],
                    cdf_forecast_group['interval_length'],
                    cdf_forecast_group['run_length'],
                    cdf_forecast_group['interval_value_type'],
                    cdf_forecast_group['extra_parameters'],
                    cdf_forecast_group['axis'],
                    ref_site)
    for cv in cdf_forecast_group['constant_values']:
        cdfsingle = {'parent': forecast_id,
                     'constant_value': cv}
        store_cdf_forecast(cdfsingle)
    return forecast_id


def _set_cdf_group_forecast_parameters(forecast_dict):
    out = {}
    for key in schema.CDFForecastGroupSchema().fields.keys():
        if key in ('_links', ):
            continue
        elif key == 'constant_values':
            out[key] = []
            constant_vals = forecast_dict['constant_values']
            for single_id, val in constant_vals.items():
                out[key].append({'forecast_id': single_id,
                                 'constant_value': val})
        else:
            out[key] = forecast_dict[key]
    return out


def read_cdf_forecast_group(forecast_id):
    """Read CDF Group Forecast metadata.

    Parameters
    ----------
    forecast_id: String
        UUID of the forecast to retrieve.

    Returns
    -------
    dict
        The CDF Forecast's metadata or None if the Forecast
        does not exist.
    """
    forecast = _set_cdf_group_forecast_parameters(
        _call_procedure_for_single('read_cdf_forecasts_group', forecast_id))
    return forecast


def delete_cdf_forecast_group(forecast_id):
    """Remove a CDF Forecast Grpup from storage.

    Parameters
    ----------
    forecast_id: String
        UUID of the CDF Forecast Group to delete.

    Returns
    -------
    dict
        The CDF Forecast Groups's metadata if successful or
        None if the CDF Forecast does not exist.
    """
    _call_procedure('delete_cdf_forecasts_group', forecast_id)


def list_cdf_forecast_groups(site_id=None, aggregate_id=None):
    """Lists all CDF Forecast Groups a user has access to.

    Parameters
    ----------
    site_id: string
        UUID of Site, when supplied returns only CDF Forcast Groups
        made for this Site.
    aggregate_id:
        UUID of aggregate, when supplied returns only CDF Forecast
        Groups made for this aggregate.

    Returns
    -------
    list
        List of dictionaries of CDF Forecast Group metadata.
    """
    if site_id is not None:
        read_site(site_id)
    if aggregate_id is not None:
        read_aggregate(aggregate_id)
    forecasts = [_set_cdf_group_forecast_parameters(fx)
                 for fx in _call_procedure('list_cdf_forecasts_groups')
                 if (
                     (site_id is None and aggregate_id is None) or
                     (site_id and fx['site_id'] == site_id) or
                     (aggregate_id and fx['aggregate_id'] == aggregate_id)
    )]
    return forecasts


def list_users():
    """List all users that calling user has access to.

    Returns
    -------
        List of dictionaries of user information.
    """
    users = _call_procedure('list_users')
    return users


def read_user(user_id):
    """Read user information.

    Parameters
    ----------
    user_id : str
        The UUID of the user to read.

    Returns
    -------
    user : dict
        Dictionary of user information.
    """
    user = _call_procedure_for_single('read_user', user_id)
    return user


def remove_role_from_user(user_id, role_id):
    """
    Parameters
    ----------
    user_id : str
        UUID of the user to remove role from.
    role_id : str
        UUID of role to remove from user

    Raises
    ------
    StorageAuthError
        - If the role does not exist
        - If the calling user does not have the revoke permission on the role
        - If the calling user and role have different organizations
    """
    # does not fail when user does not exist
    # if a user has revoke role perm and this did fail on user dne,
    # the user could use this to determine if a user_id exists
    _call_procedure('remove_role_from_user',
                    role_id, user_id)


def add_role_to_user(user_id, role_id):
    """
    Parameters
    ----------
    user_id : str
        UUID of the user to remove role from.
    role_id : str
        UUID of role to remove from user

    Raises
    ------
    StorageAuthError
        - If the user or role does not exist
        - If the calling user org and the role org do not match
        - If the user has not accepted the TOU
        - If the user is not in an organization other than Unaffiliated
        - If the calling user does not have the grant permission on the role
        - If the role contains RBAC permissions and the user is in
          a different organization
    BadAPIRequest
        - If the user has already been granted
          the role.
    """
    try:
        _call_procedure('add_role_to_user',
                        user_id, role_id)
    except pymysql.err.IntegrityError as e:
        ecode = e.args[0]
        if ecode == 1062:
            raise BadAPIRequest(
                user="User already granted role.")


def list_roles():
    """List all roles a user has access to.

    Returns
    -------
    list
        List of dictionaries of Role information.
    """
    roles = _call_procedure('list_roles')
    return roles


def store_role(role):
    """Create a new role.

    Parameters
    ----------
    role : dict
        A Dictionary containing the role's name and description.

    Returns
    -------
    string
        The UUID of the new Role.

    Raises
    ------
    StorageAuthError
        If the user does not have permission to create roles.
    """
    role_id = generate_uuid()
    name = role['name']
    description = role['description']
    try:
        role = _call_procedure('create_role', role_id, name, description)
    except pymysql.err.IntegrityError as e:
        ecode = e.args[0]
        if ecode == 1062:
            raise BadAPIRequest(
                role=f"Role '{name}' already exists.")
    return role_id


def read_role(role_id):
    """Read role information.

    Parameters
    ----------
    role_id : str
        The UUID of the role to read.

    Returns
    -------
    dict
        Dictionary of role information.
    Raises
    ------
    StorageAuthError
        If the user does not have permission to read the role or
        the role does not exist.
    """
    role = _call_procedure_for_single('read_role', role_id)
    return role


def delete_role(role_id):
    """
    Parameters
    ----------
    role_id : str
        The UUID of the role to delete.

    Raises
    ------
    StorageAuthError
        If the user does not have permission to delete the role or
        the role does not exist.

    """
    _call_procedure('delete_role', role_id)


def add_permission_to_role(role_id, permission_id):
    """
    Parameters
    ----------
    role_id : str
        The UUID of the Role to add a permission to.
    permission_id : str
        The UUID of the permission to add.

    Raises
    ------
    StorageAuthError
        - If the user does not have permission to update the role.
        - If the role or permission does not exist.
        - If the user does not have permission to read the role and
          permission.
    BadAPIRequest
        - If the role already contains the permission.
    """
    try:
        _call_procedure('add_permission_to_role', role_id, permission_id)
    except pymysql.err.IntegrityError as e:
        ecode = e.args[0]
        if ecode == 1062:
            raise BadAPIRequest(
                role="Role already contains permission.")


def remove_permission_from_role(role_id, permission_id):
    """
    Parameters
    ----------
    role_id : str
        The UUID of the Role to remove a permission from.
    permission_id : str
        The UUID of the permission to remove.

    Raises
    ------
    StorageAuthError
        - If the user does not have permission to update the role.
        - If the role or permission does not exist.
        - If the iser does not have permission to read the role and
          permission.
    """
    _call_procedure('remove_permission_from_role', permission_id, role_id)


def read_permission(permission_id):
    """
    Parameters
    ----------
    permission_id : str
        The UUID of the Permission to read.

    Returns
    -------
    dict
        Dict of permission information.

    Raises
    ------
    StorageAuthError
        If the user does not have permission to read the permission
        or the permission does not exist.

    """
    permission = _call_procedure_for_single('read_permission', permission_id)
    return permission


def delete_permission(permission_id):
    """
    Parameters
    ----------
    permission_id : str
        The UUID of the Permission to delete.

    Raises
    ------
    StorageAuthError
        If the user does not have permission to delete the permission,
        or the permission does not exist.
    """
    _call_procedure('delete_permission', permission_id)


def list_permissions():
    """List all permissions readable by the user.

    Returns
    -------
    list of dicts
        A list of dicts of Permissions information

    Raises
    ------
    StorageAuthError
        If the User does not have permission to list permissions.
    """
    permissions = _call_procedure('list_permissions')
    return permissions


def store_permission(permission):
    """Create a new permission.

    Parameters
    ----------
    permission : dict
        Dictionary of permission data.

    Returns
    -------
    str
        UUID of the newly created permission.

    Raises
    ------
    StorageAuthError
        If the user does not have permission to create new
        permissions.
    """
    uuid = generate_uuid()
    _call_procedure(
        'create_permission',
        uuid,
        permission['description'],
        permission['action'],
        permission['object_type'],
        permission['applies_to_all']
    )
    return uuid


def add_object_to_permission(permission_id, uuid):
    """
    Parameters
    ----------
    permission_id: str
        The UUID of the permission to add the object to.
    uuid: str
        UUID of the object to add.

    Raises
    ------
    StorageAuthError
        - If the object or permission does not exist.
        - If user does not have permissions to read
          both permission and object.
        - If the user does not have permission to update
          the permission.
    """
    try:
        _call_procedure('add_object_to_permission',
                        permission_id, uuid)
    except pymysql.err.IntegrityError as e:
        ecode = e.args[0]
        if ecode == 1062:
            raise BadAPIRequest(
                permission="Permission already acts upon object.")


def remove_object_from_permission(permission_id, uuid):
    """
    Parameters
    ----------
    permission_id: str
        The UUID of the permission to remove the object from.
    uuid: str
        UUID of the object to remove.

    Raises
    ------
    StorageAuthError
        - If the object or permission does not exist.
        - If user does not have permissions to read
          both permission and object.
        - If the user does not have permission to update
          the permission.
    """
    _call_procedure('remove_object_from_permission',
                    uuid, permission_id)


def _decode_report_parameters(report):
    out = deepcopy(report)
    dt_start = pd.Timestamp(report['report_parameters']['start'])
    dt_end = pd.Timestamp(report['report_parameters']['end'])
    out['report_parameters']['start'] = dt_start.to_pydatetime()
    out['report_parameters']['end'] = dt_end.to_pydatetime()
    if (
            report.get('raw_report', None) is not None and
            'generated_at' in report['raw_report']
    ):
        out['raw_report']['generated_at'] = pd.Timestamp(
            report['raw_report']['generated_at']).to_pydatetime()
    return out


def list_reports():
    """
    Returns
    -------
    list of dicts
        List of dictionaries of report metadata.
    """
    reports = _call_procedure('list_reports')
    return [_decode_report_parameters(r) for r in reports]


def store_report(report):
    """Store a report's metadata

    Parameters
    ----------
    report: dict
        Dictionary of report metadata

    Returns
    -------
    str
        UUID of newly created report.

    Raises
    ------
    StorageAuthError
        - If the user does not have permission to create a report
        - If any of the objects in object_pairs does not exist,
          or the user lacks permissions to read the data.
    """
    report_id = generate_uuid()
    _call_procedure(
        'store_report',
        report_id,
        report['report_parameters']['name'],
        dump_json_replace_nan(report['report_parameters'])
    )
    return report_id


def read_report(report_id):
    """
    Parameters
    ----------
    report_id
        UUID of the report to read.

    Returns
    -------
    dict
        A dictionary of Report metadata.

    Raises
    ------
    StorageAuthError
        If the report does not exist, or the the user does not have
        permission to read the report.
    """
    report = _decode_report_parameters(
        _call_procedure_for_single('read_report', report_id))
    report_values = read_report_values(report_id)
    report['values'] = report_values
    return report


def delete_report(report_id):
    """
    Parameters
    ----------
    report_id
        UUID of the report to read.

    Raises
    ------
    StorageAuthError
        If the report does not exist, or the user does not have permission
        to delete the report.
    """
    _call_procedure('delete_report', report_id)


def store_report_values(report_id, object_id, values):
    """
    Parameters
    ----------
    report_id: str
        UUID of the report associated with the data.
    object_id: str
        UUID of the original object
    values: str
        Temporary string values field

    Returns
    -------
    uuid: str
        UUID of the inserted processed data.

    Raises
    ------
    StorageAuthError
        - If the user does not have permission to store values for the
          report.
        - If the user does not have permission to read the original object
        - If the user does not have access to the report.
    """
    uuid = generate_uuid()
    # encode values? Should values be a dataframe?
    # temporary dump to json and encode so we can pack this in a blob
    values_bytes = values.encode()
    _call_procedure('store_report_values', uuid, str(report_id),
                    str(object_id), values_bytes)
    return uuid


def read_report_values(report_id):
    """Returns all of the processed values in the report that the user has
    access too.

    Parameters
    ----------
    report_id: str
        UUID of the report associated with the data.

    Returns
    -------
    list
        List of processed data dicts containing a unique id, report_id,
        original object_id and values in some serialized form.

    Raises
    ------
    StorageAuthError
        If the user does not have access to the report.
    """
    values = _call_procedure('read_report_values', report_id)
    # decode values?
    # temporary decode from bytes
    for row in values:
        row['processed_values'] = row['processed_values'].decode()
    return values


def store_raw_report(report_id, raw_report):
    """
    Parameters
    ----------
    report_id: str
        UUID of the report associated with the data.
    raw_report: dict
        dict representation of the raw report.

    Raises
    ------
    StorageAuthError
        If the user does not have permission to update the report
    """
    json_raw_report = dump_json_replace_nan(raw_report)
    _call_procedure('store_raw_report', report_id,
                    json_raw_report)


def store_report_status(report_id, status):
    """
    Parameters
    ----------
    report_id: str
        UUID of the report associated with the data.

    status: str
        The new status of the report

    Raises
    ------
    StorageAuthError
        If the user does not haveupdate permission on the report
    """
    _call_procedure('store_report_status', report_id, status)


def get_current_user_info():
    user_info = _call_procedure_for_single('get_current_user_info')
    return user_info


def create_new_user():
    _call_procedure('create_user_if_not_exists')


def user_exists():
    with get_cursor('dict') as cursor:
        query = f'SELECT does_user_exist(%s)'
        query_cmd = partial(cursor.execute, query, (current_user))
        try_query(query_cmd)
        exists = cursor.fetchone()
    return exists.get(f"does_user_exist('{current_user}')") == 1


def _set_previous_time(out):
    # easier mocking
    previous_time = out['previous_time']
    if previous_time is not None:
        previous_time = pd.Timestamp(previous_time)
    return previous_time


def _set_extra_params(out):
    # for mocking
    return out['extra_parameters']


def _read_metadata_for_write(obj_id, type_, start):
    out = _call_procedure_for_single(
        'read_metadata_for_value_write', obj_id, type_, start)
    interval_length = out['interval_length']
    previous_time = _set_previous_time(out)
    extra_parameters = _set_extra_params(out)
    return interval_length, previous_time, extra_parameters


def read_metadata_for_forecast_values(forecast_id, start):
    """Reads necessary metadata to process forecast values
    before storing them.

    Parameters
    ----------
    forecast_id : string
        UUID of the associated forecast.
    start : datetime
        Reference datetime to find last value before

    Returns
    -------
    interval_length : int
        The interval length of the forecast
    previous_time : pandas.Timestamp or None
       The most recent timestamp before start or None if no times
    extra_parameters : str
       The extra parameters of the forecast

    Raises
    ------
    StorageAuthError
        If the user does not have permission to write values for the Forecast
    """
    return _read_metadata_for_write(forecast_id, 'forecasts', start)


def read_metadata_for_cdf_forecast_values(forecast_id, start):
    """Reads necessary metadata to process CDF forecast values
    before storing them.

    Parameters
    ----------
    forecast_id : string
        UUID of the associated CDF forecast single.
    start : datetime
        Reference datetime to find last value before

    Returns
    -------
    interval_length : int
        The interval length of the forecast
    previous_time : pandas.Timestamp or None
       The most recent timestamp before start or None if no times
    extra_parameters : str
       The extra parameters of the forecast

    Raises
    ------
    StorageAuthError
        If the user does not have permission to write values for the
        CDF Forecast
    """
    return _read_metadata_for_write(forecast_id, 'cdf_forecasts', start)


def read_metadata_for_observation_values(observation_id, start):
    """Reads necessary metadata to process observation values
    before storing them.

    Parameters
    ----------
    observation_id : string
        UUID of the associated observation.
    start : datetime
        Reference datetime to find last value before

    Returns
    -------
    interval_length : int
        The interval length of the observation
    previous_time : pandas.Timestamp or None
       The most recent timestamp before start or None if no times
    extra_parameters : str
       The extra parameters of the observation

    Raises
    ------
    StorageAuthError
        If the user does not have permission to write values for the
        Observation
    """
    return _read_metadata_for_write(observation_id, 'observations', start)


def store_aggregate(aggregate):
    """Store Aggregate metadata. Should generate and store a uuid
    as the 'aggregate_id' field.

    Parameters
    ----------
    aggregate: dictionary
        A dictionary of aggregate fields to insert.

    Returns
    -------
    string
        The UUID of the newly created Aggregate.
    """
    aggregate_id = generate_uuid()
    # the procedure expects arguments in a certain order
    _call_procedure(
        'store_aggregate', aggregate_id,
        aggregate['name'], aggregate['description'],
        aggregate['variable'], aggregate['timezone'],
        aggregate['interval_label'], aggregate['interval_length'],
        aggregate['aggregate_type'], aggregate['extra_parameters'])
    return aggregate_id


def _set_aggregate_parameters(aggregate_dict):
    out = {}
    for key in schema.AggregateSchema().fields.keys():
        if key == 'observations':
            out[key] = []
            for obs in aggregate_dict['observations']:
                for tkey in ('created_at', 'observation_deleted_at',
                             'effective_until', 'effective_from'):
                    if obs[tkey] is not None:
                        keydt = dt.datetime.fromisoformat(obs[tkey])
                        if keydt.tzinfo is None:
                            keydt = pytz.utc.localize(keydt)
                        obs[tkey] = keydt
                out[key].append(obs)
        else:
            out[key] = aggregate_dict[key]
    return out


def read_aggregate(aggregate_id):
    """Read Aggregate metadata.

    Parameters
    ----------
    aggregate_id: String
        UUID of the aggregate to retrieve.

    Returns
    -------
    dict
        The Aggregate's metadata or None if the Aggregate
        does not exist.
    """
    aggregate = _set_aggregate_parameters(
        _call_procedure_for_single('read_aggregate', aggregate_id))
    return aggregate


def delete_aggregate(aggregate_id):
    """Remove an Aggregate from storage.

    Parameters
    ----------
    aggregate_id: String
        UUID of aggregate to delete

    Raises
    ------
    StorageAuthError
        If the user does not have permission to delete the aggregate
    """
    _call_procedure('delete_aggregate', aggregate_id)


def list_aggregates():
    """Lists all aggregates a user has access to.

    Returns
    -------
    list
        List of dictionaries of Aggregate metadata.

    Raises
    ------
    StorageAuthError
        If the user does not have access to aggregates with site_id or
        no aggregates exists for that id
    """
    aggregates = [_set_aggregate_parameters(agg)
                  for agg in _call_procedure('list_aggregates')]
    return aggregates


def add_observation_to_aggregate(
        aggregate_id, observation_id,
        effective_from=dt.datetime(
            1970, 1, 1, 0, 0, 1, tzinfo=dt.timezone.utc)):
    """Add an Observation to an Aggregate

    Parameters
    ----------
    aggregate_id : string
        UUID of aggregate
    observation_id : string
        UUID of the observation
    effective_from : datetime
        The time that the observation should be included in the aggregate.
        Default to 1970-01-01 00:00:01 UTC (start of UNIX Epoch).

    Raises
    ------
    StorageAuthError
        - If the user does not have update permission on the aggregate
        - If the observation is already present in the aggregate
        - If the user cannot read the observation object
    """
    _call_procedure('add_observation_to_aggregate', aggregate_id,
                    observation_id, effective_from)


def remove_observation_from_aggregate(
        aggregate_id, observation_id,
        effective_until=dt.datetime.now(dt.timezone.utc)):
    """Remove an Observation from an Aggregate

    Parameters
    ----------
    aggregate_id : string
        UUID of aggregate
    observation_id : string
        UUID of the observation
    effective_until : datetime
        Time after which this observation is no longer considered in the
        aggregate. Default is now.


    Raises
    ------
    StorageAuthError
        If the user does not have update permission on the aggregate
    """
    _call_procedure('remove_observation_from_aggregate', aggregate_id,
                    observation_id, effective_until)


def read_aggregate_values(aggregate_id, start=None, end=None):
    """Read aggregate values between start and end.

    Parameters
    ----------
    aggregate_id: string
        UUID of associated aggregate.
    start : datetime
        Beginning of the period for which to request data.
    end : datetime
        End of the period for which to request data.

    Returns
    -------
    dict of pandas.DataFrame
        Keys are observation IDs and DataFrames have DatetimeIndex and
        value and quality_flag columns
    """
    start = start or pd.Timestamp('19700101T000001Z')
    end = end or pd.Timestamp('20380119T031407Z')
    agg_vals = _call_procedure('read_aggregate_values', aggregate_id,
                               start, end)
    groups = pd.DataFrame.from_records(
        list(agg_vals), columns=['observation_id', 'timestamp',
                                 'value', 'quality_flag']
    ).groupby('observation_id')
    out = {}
    for obs_id, df in groups:
        out[obs_id] = df.drop(columns='observation_id').drop_duplicates(
        ).set_index('timestamp').sort_index()
    return out


def read_user_id(auth0_id):
    """Gets the user id for a given auth0 id

    Parameters
    ----------
    auth0_id : string
        Auth0 id fo the user of interest

    Returns
    -------
    str
        User UUID

    Raises
    ------
    StorageAuthError
        If the calling user and user of interest have not both signed the TOU
    """
    return _call_procedure_for_single('read_user_id', auth0_id,
                                      cursor_type='standard')[0]


def read_auth0id(user_id):
    """Read the auth0 id of another user. Only allowed if both users are affiliated
        with organizations that have accepted the TOU.

    Parameters
    ----------
    user_id: string
        User id of the auth0id to read.

    Returns
    -------
    str
        The user's auth0 id.

    Raises
    ------
    StorageAuthError
        If either user's organization has not accepted the terms of use.
    """
    return _call_procedure_for_single('read_auth0id', user_id,
                                      cursor_type='standard')[0]


def create_job_user(username, passwd, org_id, encryption_key):
    """
    Create a job user in Auth0 and in the database. Only works
    with the framework admin user.

    Parameters
    ----------
    username : str
        Auth0 username/email
    passwd : str
        Password for the new user
    org_id : uuid
        Organization to create job user for
    encryption_key : bytes
        Encryption key to store refresh token in the database

    Returns
    -------
    user_id : str
        UUID of the newly created user
    auth0_id : str
        Auth0 ID of the newly create user
    """
    auth0_id = auth0_info.create_user(username, passwd, True)
    # create user in db
    user_id = _call_procedure('create_job_user', auth0_id, org_id,
                              with_current_user=False,
                              cursor_type='standard')[0][0]
    refresh_token = auth0_info.get_refresh_token(username, passwd)
    f = Fernet(encryption_key)
    sec_token = f.encrypt(refresh_token.encode())
    _call_procedure('store_token', auth0_id, sec_token,
                    with_current_user=False)
    return user_id, auth0_id


def get_user_actions_on_object(object_id):
    """Read the list of actions that the user can perform on object.

    Parameters
    ----------
    object_id: String
        UUID of the observation to retrieve.

    Returns
    -------
    list
        The list of actions.
    """
    permissions = _call_procedure('get_user_actions_on_object', object_id)
    if not permissions:
        raise StorageAuthError()
    actions = list(set([perm['action'] for perm in permissions]))
    return actions


def list_zones():
    """List all climate zones

    Returns
    -------
    list
        List of the climate zone metadata as dictionaries.
    """
    return _call_procedure('list_climate_zones', with_current_user=False)


def read_climate_zone(zone):
    """Read the GeoJSON for a zone

    Parameters
    ----------
    zone : str

    Returns
    -------
    dict
        The GeoJSON of the zone
    """
    return _call_procedure_for_single('read_climate_zone', zone,
                                      with_current_user=False)['geojson']


def find_climate_zones(latitude, longitude):
    """Find the climate zones the point is within

    Parameters
    ----------
    latitude : float
    longitude: float

    Returns
    -------
    list
        List of zones the point is in
    """
    return _call_procedure(
        'find_climate_zones', latitude, longitude,
        with_current_user=False)


def find_unflagged_observation_dates(
        observation_id, start, end, flag, timezone='UTC'):
    """List the dates between start and end (in timezone) where the observations
    values are not flagged with the given flag.

    Parameters
    ----------
    observation_id: string
        UUID of associated observation.
    start: datetime
        Beginning of the period for which to request data.
    end: datetime
        End of the period for which to request data.
    flag: int
        The integer quality flag to check if data has NOT been
        flagged with
    timezone: str
        Timezone to adjust unflagged timestamps before retrieving date

    Returns
    -------
    list of datetime.date
        List of dates that contain observations not flagged

    Raises
    ------
    StorageAuthError
        If the user does not have permission to read values on the Observation
        or if the Observation does not exists
    """
    return [d['date'] for d in _call_procedure(
        'find_unflagged_observation_dates',
        observation_id, start, end, flag, timezone)]


def find_observation_gaps(observation_id, start, end):
    """Find gaps in the observation values between start and end

    Parameters
    ----------
    observation_id: string
        UUID of associated observation.
    start: datetime
        Beginning of the period for which to request data.
    end: datetime
        End of the period for which to request data.

    Returns
    -------
    list of dicts
        With keys 'timestamp' and 'next_timestamp' which indicate
        the range where data is missing.

    Raises
    ------
    StorageAuthError
        If the user does not have permission to read values on the Observation
        or the user does not have permission to read the Observation metadata
        or if the Observation does not exists
    """
    return _call_procedure('find_observation_gaps', observation_id, start, end)


def find_forecast_gaps(forecast_id, start, end):
    """Find gaps in the forecast values between start and end

    Parameters
    ----------
    forecast_id: string
        UUID of associated forecast.
    start: datetime
        Beginning of the period for which to request data.
    end: datetime
        End of the period for which to request data.

    Returns
    -------
    list of dicts
        With keys 'timestamp' and 'next_timestamp' which indicate
        the range where data is missing.

    Raises
    ------
    StorageAuthError
        If the user does not have permission to read values on the Forecast
        or the user does not have permission to read the Forecast metadata
        or if the Forecast does not exists
    """
    return _call_procedure('find_forecast_gaps', forecast_id, start, end)


def find_cdf_forecast_gaps(cdf_forecast_id, start, end):
    """Find gaps in the single CDF forecast values between start and end

    Parameters
    ----------
    cdf_forecast_id: string
        UUID of associated cdf_forecast.
    start: datetime
        Beginning of the period for which to request data.
    end: datetime
        End of the period for which to request data.

    Returns
    -------
    list of dicts
        With keys 'timestamp' and 'next_timestamp' which indicate
        the range where data is missing.

    Raises
    ------
    StorageAuthError
        If the user does not have permission to read values on the CDF Forecast
        or the user does not have permission to read the CDF Forecast metadata
        or if the CDF Forecast does not exists
    """
    return _call_procedure('find_cdf_single_forecast_gaps', cdf_forecast_id,
                           start, end)


def find_cdf_forecast_group_gaps(cdf_group_id, start, end):
    """Find gaps in the CDF forecast group values between start and end

    Parameters
    ----------
    cdf_group_id: string
        UUID of associated CDF forecast group.
    start: datetime
        Beginning of the period for which to request data.
    end: datetime
        End of the period for which to request data.

    Returns
    -------
    list of dicts
        With keys 'timestamp' and 'next_timestamp' which indicate
        the range where data is missing.

    Raises
    ------
    StorageAuthError
        If the user does not have permission to read values on the CDF Forecast
        or the user does not have permission to read the CDF Forecast metadata
        or if the CDF Forecast does not exists
    """
    return _call_procedure('find_cdf_forecast_gaps', cdf_group_id,
                           start, end)


def _site_has_modeling_params(site_id):
    """Check if the site has modeling parameters.

    Parameters
    ----------
    site_id: str
        uuid of the site

    Returns
    -------
    boolean
        True if the site has modeling parameters, otherwise False.

    Raises
    ------
    StorageAuthError
        If the user does not have permission to read the site
    """
    has_modeling_params = _call_procedure_for_single(
        'site_has_modeling_parameters',
        site_id,
        cursor_type='standard')
    return has_modeling_params[0] == 1
