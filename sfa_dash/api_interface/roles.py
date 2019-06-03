from sfa_dash.api_interface import get_request


def get_metadata(role_id):
    req = get_request(f'/roles/{role_id}')
    return req


def list_metadata():
    req = get_request('/roles/')
    return req
