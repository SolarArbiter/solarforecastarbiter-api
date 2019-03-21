"""This module provides a non-persistent storage backend to
develop against. It implements the functions found in
py:mod:`sfa_api.util.storage_interface`. On import, it
initializes the databases with existing site, observation, and
forecast data.
"""
import uuid


import pandas as pd

from sfa_api.demo.forecasts import static_forecasts
from sfa_api.demo.observations import static_observations
from sfa_api.demo.sites import static_sites
from sfa_api.demo.values import (static_observation_values,
                                 static_forecast_values)


# Initialize static data
sites = static_sites.copy()
forecasts = static_forecasts.copy()
observations = static_observations.copy()
observation_values = {}
forecast_values = {}

for obs_id, obs in observations.items():
    observation_values[obs_id] = static_observation_values()

for forecast_id, forecast in forecasts.items():
    forecast_values[forecast_id] = static_forecast_values()


def store_observation_values(obs_id, observation_df):
    """Insert the observation data into the database.

    Parameters
    ----------
    obs_id: string
        UUID of the associated observation.
    observation_df: DataFrame
        Dataframe with DatetimeIndex, value, and quality_flag column.

    Returns
    -------
    string
        The UUID of the associated observation
    """
    if obs_id not in observations:
        return None
    else:
        current_data = observation_values[obs_id]
        index_complement = current_data.index.difference(observation_df.index)
        complement = current_data.loc[index_complement]
        observation_values[obs_id] = observation_df.combine_first(complement)
    return obs_id


def read_observation_values(obs_id, start=None, end=None):
    """Read observation values between start and end.

    Parameters
    ----------
    obs_id: string
        UUID of associated observation.
    start: datetime
        Beginning of the period for which to request data.
    end: datetime
        End of the peried for which to request data.

    """
    if obs_id not in observations:
        return None
    else:
        obs_data = observation_values[obs_id].loc[start:end]
        return obs_data


def store_observation(observation):
    """
    Parameters
    ----------
    observation: dictionary
        A dictionary of observation fields to insert.
    """
    observation['site_id'] = str(observation['site_id'])
    if read_site(observation['site_id']) is None:
        return None
    obs_id = str(uuid.uuid1())
    observation['obs_id'] = obs_id
    observations[obs_id] = observation
    observation_values[obs_id] = pd.DataFrame()
    return obs_id


def read_observation(obs_id):
    """
    Parameters
    ----------
    obs_id: String
        UUID of the observation to retrieve

    Returns
    -------
    Observation or None
    """
    if obs_id not in observations:
        return None
    else:
        observation = observations[obs_id].copy()
        observation['site'] = read_site(str(observation['site_id']))
        return observation


def delete_observation(obs_id):
    """
    Parameters
    ----------
    obs_id: String
        UUID of observation to delete

    Returns
    -------
    """
    try:
        obs = observations.pop('obs_id')
    except KeyError:
        return None
    return obs


def list_observations(site_id=None):
    """Lists all observations a user has access to.
    """
    obs_list = []
    if site_id is not None:
        site = read_site(site_id)
        if site is None:
            return None
        filtered_obs = {obs_id: obs for obs_id, obs in observations.items()
                        if str(obs['site_id']) == site_id}
    else:
        filtered_obs = observations
    for obs_id, obs in filtered_obs.items():
        with_site = obs.copy()
        with_site['site'] = read_site(str(with_site['site_id']))
        obs_list.append(with_site)
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
    forecast = forecasts[forecast_id].copy()
    forecast['site'] = read_site(forecast['site_id'])
    return forecast


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
        forecast = forecasts.pop('forecast_id')
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
        filtered_forecasts = {fx_id: fx for fx_id, fx in forecasts.items()
                              if fx['site_id'] == site_id}
    else:
        filtered_forecasts = forecasts
    for forecast_id, forecast in filtered_forecasts.items():
        with_site = forecast.copy()
        with_site['site'] = read_site(with_site['site_id'])
        forecasts_list.append(with_site)
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
    sites[site_id] = site
    return site_id


def delete_site(site_id):
    """Deletes a Site.
    """
    try:
        site = sites[site_id]
    except KeyError:
        return None
    forecasts = list_forecasts(site_id)
    for forecast in forecasts:
        delete_forecast(forecast['forecast_id'])
    observations = list_observations(site_id)
    for observation in observations:
        delete_observation(observation['obs_id'])
    sites.pop(site_id)
    return site


def list_sites():
    """List all sites.

    Returns
    -------
    list
        List of Site dictionaries.
    """
    return [site for site_id, site in sites.items()]
