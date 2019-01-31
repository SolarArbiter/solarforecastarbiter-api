from datetime import datetime


class Site(object):
    """Object for serializing site metadata.
    """

    site_id = '123e4567-e89b-12d3-a456-426655440001'
    name = 'Ashland OR'
    latitude = 42.19
    longitude = -122.70
    elevation = 595
    timezone = 'Etc/GMT+8'
    network = 'UO SMRL'
    well_known_text = None
    modeling_parameters = {
        "ac_power": "",
        "axis_azimuth": 45.0,
        "axis_tilt": 45.0,
        "backtrack": True,
        "dc_power": "",
        "temperature_coefficient": "",
        "ground_coverage_ratio": 0.5,
        "surface_azimuth": 45.0,
        "surface_tilt": 45.0,
        "tracking_type": "fixed"
    }
    extra_parameters = "{'provider_api_id': 94040,'abbreviation': 'AS'}"


class Observation(object):
    """Container for serializing observation metadata.
    """
    obs_id = '123e4567-e89b-12d3-a456-426655440000'
    variable = 'ghi'
    site_id = '123e4567-e89b-12d3-a456-426655440001'
    name = 'Ashland OR, ghi'
    site = Site()


class TimeseriesValue(object):
    """Object for serializing timeseries data.
    """
    timestamp = datetime.strptime('2018-11-05T18:19:33+0000',
                                  '%Y-%m-%dT%H:%M:%S%z')
    value = 35
    questionable = False


class Forecast(object):
    """Object for serializing forecast metadata.
    """
    forecast_id = "f79e4f84-e2c3-11e8-9f32-f2801f1b9fd1"
    variable = 'ghi'
    site_id = '123e4567-e89b-12d3-a456-426655440001'
    name = 'Ashland OR, ghi'
    site = Site()
