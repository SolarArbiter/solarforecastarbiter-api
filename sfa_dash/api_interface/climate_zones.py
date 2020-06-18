from sfa_dash.api_interface import get_request


def get_zones():
    req = get_request('/climatezones')
    return req


def get_zone_by_lat_lon(latitude, longitude):
    req = get_request(
        '/climatezones/search',
        params={'latitude': latitude,
                'longitude': longitude}
    )
    return req


def get_zone_geojson(zone):
    req = get_request(f'/climatezones/{zone}')
    return req


def get_sites_in_zone(zone):
    req = get_request(f'/sites/in/{zone}')
    return req
