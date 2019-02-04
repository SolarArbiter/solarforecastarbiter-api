from sfa_api import demo


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
        The UUID of the newly created resource
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
    return [demo.TimeseriesValue for i in range(5)]


def store_observation(observation):
    """
    Parameters
    ----------
    observation: dictionary
        A dictionary of observation fields to insert.
    """
    return 200


def read_observation(obs_id):
    """
    Parameters
    ----------
    obs_id: String
        UUID of the observation to retrieve

    Returns
    -------

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
