from sfa_dash.api_interface import get_request, post_request, delete_request


def get_metadata(role_id):
    req = get_request(f'/roles/{role_id}')
    return req


def list_metadata():
    req = get_request('/roles/')
    return req


def post_metadata(role_dict):
    req = post_request('/roles/', role_dict)
    return req


def delete(role_id):
    req = delete_request(f'/roles/{role_id}')
    return req


def add_permission(role_id, permission_id):
    req = post_request(f'/roles/{role_id}/permissions/{permission_id}',
                       payload=None)
    return req


def remove_permission(role_id, permission_id):
    req = delete_request(f'/roles/{role_id}/permissions/{permission_id}')
    return req
