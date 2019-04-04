"""This module provides a non-persistent storage backend to
develop against. It implements the functions found in
py:mod:`sfa_api.util.storage_interface`. On import, it
initializes the databases with existing site, observation, and
forecast data.
"""
import datetime as dt
import uuid


import pandas as pd


from sfa_api.demo.forecasts import static_forecasts
from sfa_api.demo.cdf_forecasts import (static_cdf_forecast_groups,
                                        static_cdf_forecasts)
from sfa_api.demo.observations import static_observations
from sfa_api.demo.sites import static_sites
from sfa_api.demo.values import (static_observation_values,
                                 static_forecast_values)
from sfa_api.utils.errors import DeleteRestrictionError


# Initialize static data
sites = static_sites.copy()
forecasts = static_forecasts.copy()
observations = static_observations.copy()
cdf_forecast_groups = static_cdf_forecast_groups.copy()
cdf_forecasts = static_cdf_forecasts.copy()
observation_values = {}
forecast_values = {}
cdf_forecast_values = {}

for observation_id, obs in observations.items():
    observation_values[observation_id] = static_observation_values()

for forecast_id, forecast in forecasts.items():
    forecast_values[forecast_id] = static_forecast_values()

for forecast_id, forecast in cdf_forecasts.items():
    cdf_forecast_values[forecast_id] = static_forecast_values()


def store_observation_values(observation_id, observation_df):
    """Insert the observation data into the database.

    Parameters
    ----------
    observation_id: string
        UUID of the associated observation.
    observation_df: DataFrame
        Dataframe with DatetimeIndex, value, and quality_flag column.

    Returns
    -------
    string
        The UUID of the associated observation
    """
    if observation_id not in observations:
        return None
    else:
        current_data = observation_values[observation_id]
        index_complement = current_data.index.difference(observation_df.index)
        complement = current_data.loc[index_complement]
        combined = observation_df.combine_first(complement)
        observation_values[observation_id] = combined.astype(
            observation_df.dtypes)
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

    """
    if observation_id not in observations:
        return None
    else:
        obs_data = observation_values[observation_id].loc[start:end]
        return obs_data


def store_observation(observation):
    """
    Parameters
    ----------
    observation: dictionary
        A dictionary of observation fields to insert.
    """
    observation['site_id'] = str(observation['site_id'])
    now = dt.datetime.utcnow()
    observation['created_at'] = now
    observation['modified_at'] = now
    if read_site(observation['site_id']) is None:
        return None
    observation_id = str(uuid.uuid1())
    observation['observation_id'] = observation_id
    observations[observation_id] = observation
    observation_values[observation_id] = pd.DataFrame()
    return observation_id


def read_observation(observation_id):
    """
    Parameters
    ----------
    observation_id: String
        UUID of the observation to retrieve

    Returns
    -------
    Observation or None
    """
    if observation_id not in observations:
        return None
    else:
        return observations[observation_id]


def delete_observation(observation_id):
    """
    Parameters
    ----------
    observation_id: String
        UUID of observation to delete

    Returns
    -------
    """
    try:
        obs = observations.pop(observation_id)
    except KeyError:
        return None
    return obs


def list_observations(site_id=None):
    """Lists all observations a user has access to.
    """
    if site_id is not None:
        site = read_site(site_id)
        if site is None:
            return None
        obs_list = [obs for obs in observations.values()
                    if str(obs['site_id']) == site_id]
    else:
        obs_list = list(observations.values())
    return obs_list


# Forecasts
def store_forecast_values(forecast_id, forecast_df):
    """Insert the forecast data into the database.

    Parameters
    ----------
    forecast_id: string
        UUID of the associated forecast.
    forecast_df: DataFrame
        Dataframe with DatetimeIndex and value column.

    Returns
    -------
    string
        The UUID of the associated forecast
    """
    if forecast_id not in forecasts:
        return None
    else:
        current_data = forecast_values[forecast_id]
        index_complement = current_data.index.difference(forecast_df.index)
        complement = current_data.loc[index_complement]
        forecast_values[forecast_id] = forecast_df.combine_first(complement)
    return forecast_id


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

    """
    if forecast_id not in forecasts:
        return None
    else:
        forecast_data = forecast_values[forecast_id].loc[start:end]
        return forecast_data


def store_forecast(forecast):
    """
    Parameters
    ----------
    forecast: dictionary
        A dictionary of forecast fields to insert.
    """
    forecast['site_id'] = str(forecast['site_id'])
    now = dt.datetime.utcnow()
    forecast['created_at'] = now
    forecast['modified_at'] = now
    if read_site(forecast['site_id']) is None:
        return None
    forecast_id = str(uuid.uuid1())
    forecast['forecast_id'] = forecast_id
    forecasts[forecast_id] = forecast
    forecast_values[forecast_id] = pd.DataFrame()
    return forecast_id


def read_forecast(forecast_id):
    """
    Parameters
    ----------
    forecast_id: String
        UUID of the forecast to retrieve

    Returns
    -------

    """
    if forecast_id not in forecasts:
        return None
    return forecasts[forecast_id]


def delete_forecast(forecast_id):
    """
    Parameters
    ----------
    forecast_id: String
        UUID of Forecast to delete

    Returns
    -------
    """
    try:
        forecast = forecasts.pop(forecast_id)
    except KeyError:
        return None
    return forecast


def list_forecasts(site_id=None):
    """Lists all forecasts a user has access to.
    """
    forecasts_list = []
    if site_id is not None:
        site = read_site(site_id)
        if site is None:
            return None
        forecasts_list = [fx for fx in forecasts.values()
                          if fx['site_id'] == site_id]
    else:
        forecasts_list = list(forecasts.values())
    return forecasts_list


def read_site(site_id):
    """Retrieve a Site object.

    Parameters
    ----------
    site_id: string
        UUID of the site to retrieve

    Returns
    -------
    dict
        Dictionary of the Site data.
    """
    if site_id not in sites:
        return None
    return sites[site_id]


def store_site(site):
    """Create a new site from a site dictionary.

    Parameters
    ----------
    site: dict
        Dictionary of site data.

    Returns
    -------
    string
        UUID of the newly created site.
    """
    site_id = str(uuid.uuid1())
    site['site_id'] = site_id
    site['provider'] = 'test post'
    now = dt.datetime.utcnow()
    site['created_at'] = now
    site['modified_at'] = now
    sites[site_id] = site
    return site_id


def delete_site(site_id):
    """Deletes a Site.
    """
    try:
        site = sites[site_id]
    except KeyError:
        return None
    if len(list_forecasts(site_id)) > 0:
        raise DeleteRestrictionError
    if len(list_observations(site_id)) > 0:
        raise DeleteRestrictionError
    sites.pop(site_id)
    return site


def list_sites():
    """List all sites.

    Returns
    -------
    list
        List of Site dictionaries.
    """
    return list(sites.values())


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
    if forecast_id not in cdf_forecasts:
        return None
    else:
        current_data = cdf_forecast_values[forecast_id]
        index_complement = current_data.index.difference(forecast_df.index)
        complement = current_data.loc[index_complement]
        cdf_forecast_values[forecast_id] = forecast_df.combine_first(
            complement)
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
    list
        A list of dictionaries representing data points.
        Data points contain a timestamp and value. Returns
        None if the CDF Forecast does not exist.
    """
    if forecast_id not in cdf_forecasts:
        return None
    else:
        forecast_data = cdf_forecast_values[forecast_id].loc[start:end]
        return forecast_data


def store_cdf_forecast(cdf_forecast):
    """Store Forecast metadata. Should generate and store a uuid
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
    cdf_forecast['parent'] = str(cdf_forecast['parent'])
    forecast_id = str(uuid.uuid1())
    cdf_forecast['forecast_id'] = forecast_id
    cdf_forecasts[forecast_id] = cdf_forecast
    cdf_forecast_values[forecast_id] = pd.DataFrame()
    return forecast_id


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
    if forecast_id not in cdf_forecasts:
        return None
    forecast = cdf_forecasts[forecast_id]
    with_parent = cdf_forecast_groups[forecast['parent']].copy()
    with_parent.update(forecast)
    return with_parent


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
    try:
        cdf_forecast = cdf_forecasts.pop(forecast_id)
    except KeyError:
        return None
    return cdf_forecast


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
    forecasts_list = []
    if parent_forecast_id is not None:
        parent = read_cdf_forecast_group(parent_forecast_id)
        if parent is None:
            return None
        filtered_forecasts = {fx_id: fx for fx_id, fx in cdf_forecasts.items()
                              if fx['parent'] == parent_forecast_id}
    else:
        filtered_forecasts = cdf_forecasts
    for forecast_id, forecast in filtered_forecasts.items():
        with_metadata = read_cdf_forecast_group(forecast['parent'])
        with_metadata = with_metadata.copy()
        with_metadata.update(forecast)
        forecasts_list.append(with_metadata)
    return forecasts_list


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
    cdf_forecast_group['site_id'] = str(cdf_forecast_group['site_id'])
    if read_site(cdf_forecast_group['site_id']) is None:
        return None
    forecast_id = str(uuid.uuid1())
    cdf_forecast_group['forecast_id'] = forecast_id
    axis = cdf_forecast_group['axis']
    instantiated_constants = []
    for constant in cdf_forecast_group['constant_values']:
        cdf_forecast = {
            "axis": axis,
            "parent": forecast_id,
            "constant_value": constant
        }
        new_id = store_cdf_forecast(cdf_forecast)
        cdf_forecast['forecast_id'] = new_id
        instantiated_constants.append(cdf_forecast)
    cdf_forecast_group['constant_values'] = instantiated_constants
    cdf_forecast_groups[forecast_id] = cdf_forecast_group
    return forecast_id


def read_cdf_forecast_group(forecast_id):
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
    if forecast_id not in cdf_forecast_groups:
        return None
    else:
        forecast_group = cdf_forecast_groups[forecast_id]
        return forecast_group


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
    if forecast_id not in cdf_forecast_groups:
        return None
    else:
        child_cdf_forecasts = list_cdf_forecasts(forecast_id)
        for forecast in child_cdf_forecasts:
            delete_cdf_forecast(forecast['forecast_id'])
        return cdf_forecast_groups.pop(forecast_id)


def list_cdf_forecast_groups(site_id=None):
    """Lists all CDF Forecast Groups a user has access to.

    Returns
    -------
    list
        List of dictionaries of CDF Forecast Group metadata.
    """
    forecast_groups = [read_cdf_forecast_group(forecast_id)
                       for forecast_id, forecast_group
                       in cdf_forecast_groups.items()]
    if site_id is not None:
        forecast_groups = [forecast_group
                           for forecast_group in forecast_groups
                           if forecast_group['site_id'] == site_id]
    return forecast_groups
