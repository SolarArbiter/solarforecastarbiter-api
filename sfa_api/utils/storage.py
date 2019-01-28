def store_observation_values(obs_id, observation_df):
    """Insert the observation data into the database.

    Parameters
    ----------
    obs_id: string
        UUID of the associated observation.
    observation_df: DataFrame
        Dataframe with DatetimeIndex, value, and questionable column.
    """
    # Method stub for storing observation time-series in the database.
    return 'OK'


def read_observation_values(obs_id, start, end):
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
    raise NotImplementedError


def store_observation():
    """
    """
    raise NotImplementedError


def read_observation():
    """
    """
    raise NotImplementedError
