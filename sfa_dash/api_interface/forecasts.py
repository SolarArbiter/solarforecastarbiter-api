from sfa_dash.api_interface import get_request, post_request


def get_metadata(forecast_id):
    r = get_request(f'/forecasts/single/{forecast_id}/metadata')
    return r


def get_values(forecast_id, **kwargs):
    r = get_request(f'/forecasts/single/{forecast_id}/values', **kwargs)
    return r


def list_metadata(site_id=None):
    if site_id is not None:
        r = get_request(f'/sites/{site_id}/forecasts/single')
    else:
        r = get_request('/forecasts/single/')
    return r


def post_metadata(forecast_dict):
    r = post_request('/forecasts/single/', forecast_dict)
    return r


def post_values(uuid, values, json=True):
    r = post_request(f'/forecasts/single/{uuid}/values', values, json)
    return r
