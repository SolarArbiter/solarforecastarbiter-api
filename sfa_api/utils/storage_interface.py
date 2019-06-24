"""This file contains method stubs to act as the interface for
storage interactions in the Solar Forecast Arbiter. The 'sfa_api.demo'
module is a static implementation intended for developing against when
it is not feasible to utilize a mysql instance or other persistent
storage.
"""
from contextlib import contextmanager
import datetime as dt
from functools import partial
import math
import random
import uuid


from flask import current_app
import pandas as pd
import pymysql
from pymysql import converters
from sqlalchemy.engine import create_engine
from sqlalchemy.pool import QueuePool


from sfa_api import schema, json
from sfa_api.utils.auth import current_user
from sfa_api.utils.errors import StorageAuthError, DeleteRestrictionError


# min and max timestamps storable in mysql
MINTIMESTAMP = pd.Timestamp('19700101T000001Z')
MAXTIMESTAMP = pd.Timestamp('20380119T031407Z')
# microseconds dropped on purpose, must quote
# this is faster than using strftime
TIMEFORMAT = "'{0.year:04}-{0.month:02}-{0.day:02} {0.hour:02}:{0.minute:02}:{0.second:02}'"  # NOQA


def generate_uuid():
    """Generate a version 1 UUID and ensure clock_seq is random"""
    return str(uuid.uuid1(clock_seq=random.SystemRandom().getrandbits(14)))


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


def _make_sql_connection_partial():
    config = current_app.config
    conv = converters.conversions.copy()
    # either convert decimals to floats, or add decimals to schema
    conv[converters.FIELD_TYPE.DECIMAL] = float
    conv[converters.FIELD_TYPE.NEWDECIMAL] = float
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
        if ecode == 1142 or ecode == 1143 or ecode == 1411:
            raise StorageAuthError(e.args[1])
        elif ecode == 1451:
            raise DeleteRestrictionError
        else:
            raise


def _call_procedure(procedure_name, *args, cursor_type='dict'):
    """
    Can't user callproc since it doesn't properly use converters.
    Will not handle OUT or INOUT parameters without first setting
    local variables and retrieving from those variables
    """
    with get_cursor(cursor_type) as cursor:
        query = f'CALL {procedure_name}({",".join(["%s"] * (len(args) + 1))})'
        query_cmd = partial(cursor.execute, query, (current_user, *args))
        try_query(query_cmd)
        return cursor.fetchall()


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
    with get_cursor('standard') as cursor:
        query = 'CALL store_observation_values(%s, %s, %s, %s, %s)'
        query_cmd = partial(
            cursor.executemany, query,
            ((current_user, observation_id, row.Index, row.value,
              row.quality_flag)
             for row in observation_df.itertuples()))
        try_query(query_cmd)
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
        End of the peried for which to request data.

    Returns
    -------
    list
        A list of dictionaries representing data points.
        Data points contain a timestamp, value andquality_flag.
        Returns None if the Observation does not exist.
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
    ).drop(columns='observation_id').set_index('timestamp').tz_localize('UTC')
    return df


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
        _call_procedure('read_observation', observation_id)[0])
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
    with get_cursor('standard') as cursor:
        query = 'CALL store_forecast_values(%s, %s, %s, %s)'
        query_cmd = partial(
            cursor.executemany, query,
            ((current_user, forecast_id, row.Index, row.value)
             for row in forecast_df.itertuples()))
        try_query(query_cmd)
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
    ).drop(columns='forecast_id').set_index('timestamp').tz_localize('UTC')
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
        End of the peried for which to request data.

    Returns
    -------
    pandas.DataFrame
        With a value column and datetime index
    """
    return _read_fx_values('read_forecast_values', forecast_id,
                           start, end)


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
    # the procedure expects arguments in a certain order
    _call_procedure(
        'store_forecast', forecast_id, str(forecast['site_id']),
        forecast['name'], forecast['variable'], forecast['issue_time_of_day'],
        forecast['lead_time_to_start'], forecast['interval_label'],
        forecast['interval_length'], forecast['run_length'],
        forecast['interval_value_type'], forecast['extra_parameters'])
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
        _call_procedure('read_forecast', forecast_id)[0])
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


def list_forecasts(site_id=None):
    """Lists all Forecasts a user has access to.

    Parameters
    ----------
    site_id: string
        UUID of Site, when supplied returns only Forecasts
        made for this Site.

    Returns
    -------
    list
        List of dictionaries of Forecast metadata.
    """
    if site_id is not None:
        read_site(site_id)
    forecasts = [_set_forecast_parameters(fx)
                 for fx in _call_procedure('list_forecasts')
                 if site_id is None or fx['site_id'] == site_id]
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
        _call_procedure('read_site', site_id)[0])
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
    with get_cursor('standard') as cursor:
        query = 'CALL store_cdf_forecast_values(%s, %s, %s, %s)'
        query_cmd = partial(
            cursor.executemany, query,
            ((current_user, forecast_id, row.Index, row.value)
             for row in forecast_df.itertuples()))
        try_query(query_cmd)
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
        End of the peried for which to request data.

    Returns
    -------
    pandas.DataFrame
        With a value column and datetime index
    """
    return _read_fx_values('read_cdf_forecast_values', forecast_id,
                           start, end)


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
        _call_procedure('read_cdf_forecasts_single', forecast_id)[0])
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
    # the procedure expects arguments in a certain order
    _call_procedure('store_cdf_forecasts_group',
                    forecast_id,
                    str(cdf_forecast_group['site_id']),
                    cdf_forecast_group['name'],
                    cdf_forecast_group['variable'],
                    cdf_forecast_group['issue_time_of_day'],
                    cdf_forecast_group['lead_time_to_start'],
                    cdf_forecast_group['interval_label'],
                    cdf_forecast_group['interval_length'],
                    cdf_forecast_group['run_length'],
                    cdf_forecast_group['interval_value_type'],
                    cdf_forecast_group['extra_parameters'],
                    cdf_forecast_group['axis'])
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
            constant_vals = json.loads(forecast_dict['constant_values'])
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
        _call_procedure('read_cdf_forecasts_group', forecast_id)[0])
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


def list_cdf_forecast_groups(site_id=None):
    """Lists all CDF Forecast Groups a user has access to.

    Parameters
    ----------
    site_id: string
        UUID of Site, when supplied returns only CDF Forcast Groups
        made for this Site.

    Returns
    -------
    list
        List of dictionaries of CDF Forecast Group metadata.
    """
    if site_id is not None:
        read_site(site_id)
    forecasts = [_set_cdf_group_forecast_parameters(fx)
                 for fx in _call_procedure('list_cdf_forecasts_groups')
                 if site_id is None or fx['site_id'] == site_id]
    return forecasts


def list_users():
    """List all users that calling user has access to.

    Returns
    -------
        List of dictionaries of user information.
    """
    users = _call_procedure('list_users')
    for user in users:
        user['roles'] = json.loads(user['roles'])
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
    user = _call_procedure('read_user', user_id)[0]
    user['roles'] = json.loads(user['roles'])
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
        - If the user or role does not exist
        - If the calling user does not have
          permissions to read role and user.
        - If the calling user does not have
          permission to update the user.
    """
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
        - If the calling user does not have
          permissions to read role and user.
        - If the calling user does not have
          permission to update the user.
    """
    _call_procedure('add_role_to_user',
                    user_id, role_id)


def list_roles():
    """List all roles a user has access to.

    Returns
    -------
    list
        List of dictionaries of Role information.
    """
    roles = _call_procedure('list_roles')
    for role in roles:
        role['permissions'] = json.loads(role['permissions'])
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
    role = _call_procedure('create_role', role_id, name, description)
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
    role = _call_procedure('read_role', role_id)[0]
    role['permissions'] = json.loads(role['permissions'])
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
        - If the iser does not have permission to read the role and
          permission.
    """
    _call_procedure('add_permission_to_role', role_id, permission_id)


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
    permission = _call_procedure('read_permission', permission_id)[0]
    permission['objects'] = json.loads(permission['objects'])
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
    for permission in permissions:
        permission['objects'] = json.loads(permission['objects'])
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
    _call_procedure('add_object_to_permission',
                    permission_id, uuid)


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
    report['report_parameters'] = json.loads(report['report_parameters'])
    dt_start = pd.Timestamp(report['report_parameters']['start'])
    dt_end = pd.Timestamp(report['report_parameters']['end'])
    report['report_parameters']['start'] = dt_start
    report['report_parameters']['end'] = dt_end
    return report


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
    iso_start = report['report_parameters']['start'].isoformat()
    iso_end = report['report_parameters']['end'].isoformat()
    report['report_parameters']['start'] = iso_start
    report['report_parameters']['end'] = iso_end
    _call_procedure(
        'store_report',
        report_id,
        report['name'],
        json.dumps(report['report_parameters']),
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
        _call_procedure('read_report', report_id)[0])
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


def store_report_metrics(report_id, metrics, raw_report):
    """
    Parameters
    ----------
    report_id: str
        UUID of the report associated with the data.
    metrics: dict
        A dict containing the metrics and metadata
    raw_report: bytes
        byte representation of the rereport template.

    Raises
    ------
    StorageAuthError
        If the user does not have permission to update the report
    """
    json_metrics = json.dumps(metrics)
    _call_procedure('store_report_metrics', report_id,
                    json_metrics, raw_report)


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
