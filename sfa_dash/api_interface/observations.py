from sfa_dash.api_interface import get_request, post_request, delete_request


def get_metadata(observation_id):
    req = get_request(f'/observations/{observation_id}/metadata')
    return req


def get_values(observation_id, **kwargs):
    req = get_request(f'/observations/{observation_id}/values', **kwargs)
    return req


def list_metadata(site_id=None):
    if site_id is not None:
        req = get_request(f'/sites/{site_id}/observations')
    else:
        req = get_request('/observations/')
    return req


def post_metadata(obs_dict):
    req = post_request('/observations/', obs_dict)
    return req


def post_values(uuid, values, json=True):
    req = post_request(f'/observations/{uuid}/values', values, json)
    return req


def delete(observation_id):
    req = delete_request(f'/observations/{observation_id}')
    return req
