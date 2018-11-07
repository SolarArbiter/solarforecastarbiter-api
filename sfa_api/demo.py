from datetime import datetime
# TODO: Replace the static demo content in these classes.
class Site(object):
    """Object for serializing site metadata.
    """
    site_id = '123e4567-e89b-12d3-a456-426655440001'
    name = 'Ashland OR'
    resolution = '1 min'
    latitude = 42.19
    longitude = -122.70
    elevation = 595
    station_id = 94040
    abbreviation = 'AS'
    timezone = 'Etc/GMT+8'
    attribution = ''
    source = 'UO SMRL'


class Observation(object):
    """Container for serializing observation metadata.
    """
    uuid = '123e4567-e89b-12d3-a456-426655440000'
    variable = 'ghi'
    site_id = '123e4567-e89b-12d3-a456-426655440001'
    name = 'Ashland OR, ghi'
    site = Site()


class TimeseriesValue(object):
    """Object for serializing timeseries data.
    """
    timestamp = datetime.strptime('2018-11-05T18:19:33+0000','%Y-%m-%dT%H:%M:%S%z')
    value = 35
    questionable = False


class Forecast(object):
    """Object for serializing forecast metadata.
    """
    uuid = "f79e4f84-e2c3-11e8-9f32-f2801f1b9fd1"
    variable = 'ghi'
    site_id = '123e4567-e89b-12d3-a456-426655440001'
    name = 'Ashland OR, ghi'
    site = Site()
