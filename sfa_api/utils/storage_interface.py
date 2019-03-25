"""This file contains method stubs to act as the interface for
storage interactions in the Solar Forecast Arbiter. The 'sfa_api.demo'
module is a static implementation intended for developing against when
it is not feasible to utilize a mysql instance or other persistent
storage.
"""


def store_observation_values(obs_id, observation_df):
    """Store observation data.

    Parameters
    ----------
    obs_id: string
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

    Returns
    -------
    list
        A list of dictionaries representing data points.
        Data points contain a timestamp, value andquality_flag.
        Returns None if the Observation does not exist.
    """
    raise NotImplementedError


def store_observation(observation):
    """Store Observation metadata. Should generate and store a uuid
    as the 'obs_id' field.

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


def read_observation(obs_id):
    """Read Observation metadata.

    Parameters
    ----------
    obs_id: String
        UUID of the observation to retrieve.

    Returns
    -------
    dict
        The Observation's metadata or None if the Observation
        does not exist.
    """
    raise NotImplementedError


def delete_observation(obs_id):
    """Remove an Observation from storage.

    Parameters
    ----------
    obs_id: String
        UUID of observation to delete

    Returns
    -------
    dict
        The Observation's metadata if successful or None
        if the Observation does not exist.
    """
    raise NotImplementedError


def list_observations(site=None):
    """Lists all observations a user has access to.

    Parameters
    ----------
    site: string
        UUID of Site, when supplied returns only Observations
        made for this Site.

    Returns
    -------
    list
        List of dictionaries of Observation metadata.
    """
    # PROC: list_observations
    raise NotImplementedError


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
    raise NotImplementedError


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
    raise NotImplementedError


def list_forecasts(site=None):
    """Lists all Forecasts a user has access to.

    Parameters
    ----------
    site: string
        UUID of Site, when supplied returns only Forecasts
        made for this Site.

    Returns
    -------
    list
        List of dictionaries of Forecast metadata.
    """
    # PROC: list_forecasts
    raise NotImplementedError


def read_site(site_id):
    """Read Site metadata.

    Parameters
    ----------
    site_id: String
        UUID of the site to retrieve.

    Returns
    -------
    dict
        The Site's metadata or None if the Site does not exist.
    """
    raise NotImplementedError


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
    raise NotImplementedError


def list_sites():
    """List all sites.

    Returns
    -------
    list
        List of Site metadata as dictionaries.
    """
    # PROC: list_sites
    raise NotImplementedError
