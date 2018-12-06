"""Static demo content to develop against.
"""
from datetime import datetime


class ModelingParams(object):
    """Power plant modeling parameters
    """
    ac_power = ''
    dc_power = ''
    gamma_pdc = ''
    tracking_type = ''
    surface_tilt = 45.0
    surface_azimuth = 45.0
    axis_tilt = 45.0
    axis_azimuth = 45.0
    ground_coverage_ratio = 0.5
    backtrack = True
    maximum_rotation_angle = 45.0


class Site(object):
    """Object for serializing site metadata.
    """
    site_id = '123e4567-e89b-12d3-a456-426655440001'
    name = 'Ashland OR'
    resolution = '1 min'
    latitude = 42.19
    longitude = -122.70
    elevation = 595
    provider = 'Reference'
    timezone = 'Etc/GMT+8'
    attribution = ''
    modeling_parameters = ModelingParams()
    extra_parameters = {
        'network': 'UO SRML',
        'network_api_id': '94040',
        'net_work_api_abbreviation': 'AS',
    }


class Observation(object):
    """Container for serializing observation metadata.
    """
    provider = 'UO SRML'
    obs_id = '123e4567-e89b-12d3-a456-426655440000'
    variable = 'ghi'
    site_id = '123e4567-e89b-12d3-a456-426655440001'
    name = 'Ashland OR, ghi'
    site = Site()
    extra_parameters = {
        'instrument': 'Ascension Technology Rotating Shadowband Pyranometer',
    }


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
    provider = 'University of Arizona'
    forecast_id = "f79e4f84-e2c3-11e8-9f32-f2801f1b9fd1"
    variable = 'ghi'
    site_id = '123e4567-e89b-12d3-a456-426655440001'
    name = 'Ashland OR, ghi'
    site = Site()
