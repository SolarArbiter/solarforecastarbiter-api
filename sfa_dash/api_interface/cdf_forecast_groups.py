from sfa_dash.api_interface import get_request, post_request, delete_request


def get_metadata(forecast_id):
    req = get_request(f'/forecasts/cdf/{forecast_id}')
    return req


def get_values(forecast_id, **kwargs):
    req = get_request(f'/forecasts/cdf/{forecast_id}/values', **kwargs)
    return req


def list_metadata(site_id=None, aggregate_id=None):
    if site_id is not None:
        req = get_request(f'/sites/{site_id}/forecasts/cdf')
    elif aggregate_id is not None:
        req = get_request(f'/aggregates/{aggregate_id}/forecasts/cdf')
    else:
        req = get_request('/forecasts/cdf/')
    return req


def post_metadata(forecast_dict):
    req = post_request('/forecasts/cdf/', forecast_dict)
    return req


def delete(forecast_id):
    req = delete_request(f'/forecasts/cdf/{forecast_id}')
    return req
