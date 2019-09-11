from sfa_dash.api_interface import get_request, post_request, delete_request


def get_metadata(permission_id):
    req = get_request(f'/permissions/{permission_id}')
    return req


def list_metadata():
    req = get_request('/permissions/')
    return req


def post_metadata(permission_dict):
    req = post_request('/permissions/', permission_dict)
    return req


def delete(permission_id):
    req = delete_request(f'/permissions/{permission_id}')
    return req


def add_object(permission_id, object_id):
    req = post_request(f'/permissions/{permission_id}/objects/{object_id}',
                       payload=None)
    return req


def remove_object(permission_id, object_id):
    req = delete_request(f'/permissions/{permission_id}/objects/{object_id}')
    return req
