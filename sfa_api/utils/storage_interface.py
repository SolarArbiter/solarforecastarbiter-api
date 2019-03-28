"""This file contains method stubs to act as the interface for
storage interactions in the Solar Forecast Arbiter. The 'sfa_api.demo'
module is a static implementation intended for developing against when
it is not feasible to utilize a mysql instance or other persistent
storage.
"""
from contextlib import contextmanager


from flask import g, current_app
import pymysql
from pymysql import converters


from sfa_api.auth import current_user
from sfa_api import schema
from sfa_api.utils.errors import StorageAuthError


def mysql_connection():
    if 'mysql_connection' not in g:
        config = current_app.config
        conv = converters.conversions.copy()
        conv[converters.FIELD_TYPE.TIME] = converters.convert_time
        # either convert decimals to floats, or add decimals to schema
        conv[converters.FIELD_TYPE.DECIMAL] = float
        conv[converters.FIELD_TYPE.NEWDECIMAL] = float
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
            'init_command': "SET time_zone = '+00:00'"
        }
        connection = pymysql.connect(**connect_kwargs)
        g.mysql_connection = connection
    return g.mysql_connection


@contextmanager
def get_cursor(cursor_type='standard'):
    if cursor_type == 'standard':
        cursorclass = pymysql.cursors.Cursor
    elif cursor_type == 'dict':
        cursorclass = pymysql.cursors.DictCursor
    else:
        raise AttributeError('cursor_type must be standard or dict')
    connection = mysql_connection()
    cursor = connection.cursor(cursor=cursorclass)
    yield cursor
    connection.commit()
    cursor.close()


def _call_procedure(procedure_name, *args):
    with get_cursor('dict') as cursor:
        try:
            cursor.callproc(procedure_name, (current_user, *args))
        except pymysql.err.OperationalError as e:
            if e.args[0] == 1142:
                raise StorageAuthError(e.args[1])
            else:
                raise
        else:
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
        The UUID of the associated Observation or None if the it does
        not exist.
    """
    # PROC: store_observation_values
    raise NotImplementedError


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
    # PROC: read_observation_values
    raise NotImplementedError


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
    # PROC: store_observation
    raise NotImplementedError


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

    Returns
    -------
    dict
        The Observation's metadata if successful or None
        if the Observation does not exist.
    """
    # PROC: delete_observation
    raise NotImplementedError


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
        The UUID of the associated forecast. Returns
        None if the Forecast does not exist.
    """
    # PROC: store_forecast_values
    raise NotImplementedError


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
    list
        A list of dictionaries representing data points.
        Data points contain a timestamp and value. Returns
        None if the Observation does not exist.
    """
    # PROC: read_forecast_values
    raise NotImplementedError


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

    """
    # PROC: store_forecast
    raise NotImplementedError


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

    Returns
    -------
    dict
        The Forecast's metadata if successful or None
        if the Forecast does not exist.
    """
    # PROC: delete_forecast
    raise NotImplementedError


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
    """
    # PROC: store_site
    raise NotImplementedError


def delete_site(site_id):
    """Remove a Site from storage.

    Parameters
    ----------
    site_id: String
        UUID of the Forecast to delete.

    Returns
    -------
    dict
        The Site's metadata if successful or None
        if the Site does not exist.
    """
    # PROC: delete_site
    raise NotImplementedError


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
