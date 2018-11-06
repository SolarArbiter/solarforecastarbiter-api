# TODO: Replace the static demo content in these classes.
class Site(object):
    """Object for serializing site metadata.
    """
    uuid = '123e4567-e89b-12d3-a456-426655440001'
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
    site = Site()


class ObservationValue(object):
    """Object for serializing observation's timeseries data.
    """
    timestamp = '2018-11-05T18:19:33+00:00'
    value = 35
