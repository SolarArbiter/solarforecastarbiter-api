from sfa_dash.api_interface import get_request, post_request


def get_metadata(forecast_id):
    req = get_request(f'/forecasts/cdf/single/{forecast_id}')
    return req


def get_values(forecast_id, **kwargs):
    req = get_request(f'/forecasts/cdf/single/{forecast_id}/values', **kwargs)
    return req


def post_values(uuid, values, json=True):
    req = post_request(f'/forecasts/cdf/single/{uuid}/values', values, json)
    return req


def valid_times(forecast_id):
    req = get_request(f'/forecasts/cdf/single/{forecast_id}/values/timerange')
    return req
