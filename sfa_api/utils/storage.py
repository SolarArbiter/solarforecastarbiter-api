from sfa_api.demo import demo


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
    # Method stub for storing observation time-series in the database.

    return demo.Observation.obs_id


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
    return [demo.ObservationTimeseriesValue for i in range(5)]


def store_observation(observation):
    """
    Parameters
    ----------
    observation: dictionary
        A dictionary of observation fields to insert.
    """
    return demo.Observation.obs_id


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
    return demo.Observation


def delete_observation(obs_id):
    """
    Parameters
    ----------
    obs_id: String
        UUID of observation to delete

    Returns
    -------
    """
    return 200


def list_observations():
    """Lists all observations a user has access to.
    """
    return [demo.Observation() for i in range(5)]


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
    # Method stub for storing forecast time-series in the database.

    return demo.Forecast.forecast_id


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
    return [demo.ForecastTimeseriesValue for i in range(5)]


def store_forecast(forecast):
    """
    Parameters
    ----------
    forecast: dictionary
        A dictionary of forecast fields to insert.
    """
    return demo.Forecast.forecast_id


def read_forecast(forecast_id):
    """
    Parameters
    ----------
    forecast_id: String
        UUID of the forecast to retrieve

    Returns
    -------

    """
    return demo.Forecast


def delete_forecast(forecast_id):
    """
    Parameters
    ----------
    forecast_id: String
        UUID of Forecast to delete

    Returns
    -------
    """
    return 200


def list_forecasts():
    """Lists all forecasts a user has access to.
    """
    return [demo.Forecast() for i in range(5)]
