from sfa_dash.api_interface import get_request


def get_metadata(user_id):
    req = get_request(f'/users/{user_id}')
    return req


def list_metadata():
    req = get_request('/users/')
    return req
