from sfa_dash.api_interface import get_request, post_request


def get_metadata(forecast_id):
    r = get_request(f'/forecasts/cdf/{forecast_id}')
    return r


def get_values(forecast_id, **kwargs):
    r = get_request(f'/forecasts/cdf/{forecast_id}/values', **kwargs)
    return r


def list_metadata(site_id=None):
    if site_id is not None:
        r = get_request(f'/sites/{site_id}/forecasts/cdf')
    else:
        r = get_request('/forecasts/cdf/')
    return r


def post_metadata(forecast_dict):
    r = post_request('/forecasts/cdf/', forecast_dict)
    return r


def post_values(uuid, values, json=True):
    r = post_request(f'/forecasts/cdf/single/{uuid}/values', values, json)
    return r
