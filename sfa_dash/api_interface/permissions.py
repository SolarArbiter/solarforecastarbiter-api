from sfa_dash.api_interface import get_request


def get_metadata(permission_id):
    req = get_request(f'/permissions/{permission_id}')
    return req


def list_metadata():
    req = get_request('/permissions/')
    return req
