import logging
from requests.exceptions import HTTPError

import pandas as pd
from solarforecastarbiter.io.api import APISession
from solarforecastarbiter.validation.quality_mapping import (
    BITMASK_DESCRIPTION_DICT
)

USER_FLAGGED = BITMASK_DESCRIPTION_DICT[1]["USER FLAGGED"]


def copy_observation_data(token, copy_from, copy_to, base_url=None):
    """Helper job to copy observation data from one observation to
    another.

    Parameters
    ----------
    token: str
        API token to use.
    copy_from: str
        UUID of the observation to copy data from. Must have read_values
        permission on this observation.
    copy_to: str
        UUID of the observation to copy data to. Must have write_values
        permission on this observation.
    base_url: str
        URL of the api instance to connect to.

    Raises
    ------
    ValueError
        If reading values from either observation fails, or writing to
        copy_to fails.
    """
    logger = logging.getLogger(__name__)
    sess = APISession(token, base_url=base_url)
    # Get latest values for copy_to and adjust forward by 1 minute to
    # not overwrite values
    try:
        latest_copy_to = sess.get_observation_time_range(copy_to)[1]
    except HTTPError as e:
        raise ValueError(
            "Copy observation failed. Read values failure for copy_to "
            f"observation with error code: {e.response.status_code}"
        )
    latest_copy_to += pd.Timedelta('1T')

    # If no data in copy_to, start from latest copy_from value.
    try:
        if pd.isna(latest_copy_to):
            latest_copy_to = sess.get_observation_time_range(copy_from)[1]

        # Get values for copy_from from latest copy_to to now.
        values_to_copy = sess.get_observation_values(
            copy_from,
            latest_copy_to,
            pd.Timestamp.utcnow()
        )
    except HTTPError as e:
        raise ValueError(
            "Copy observation failed. Read values failure for copy_from "
            f"observation with error code: {e.response.status_code}"
        )

    if not values_to_copy.empty:
        # Need to reset quality_flag and retained user flagged data, so
        # take the & of current flags and USER_FLAGGED
        flags = values_to_copy['quality_flag'] & USER_FLAGGED
        values_to_copy['quality_flag'] = flags

        try:
            sess.post_observation_values(copy_to, values_to_copy)
        except HTTPError as e:
            raise ValueError(
                "Copy observation failed. Write values failure for copy_to "
                f"observation with error code: {e.response.status_code}"
            )
        else:
            logger.info(
                "Copied %s points from obs %s to %s.",
                len(values_to_copy), copy_from, copy_to
            )
    else:
        logger.info("No points to copy from %s to %s.", copy_from, copy_to)
