from sfa_dash.api_interface import get_request, post_request


def get_metadata(forecast_id):
    r = get_request(f'/forecasts/cdf/single/{forecast_id}')
    return r


def get_values(forecast_id, **kwargs):
    r = get_request(f'/forecasts/cdf/single/{forecast_id}/values', **kwargs)
    return r


def post_values(uuid, values, json=True):
    r = post_request(f'/forecasts/cdf/single/{uuid}/values', values, json)
    return r
