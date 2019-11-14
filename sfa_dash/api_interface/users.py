from sfa_dash.api_interface import get_request, post_request, delete_request


def get_metadata(user_id):
    req = get_request(f'/users/{user_id}')
    return req


def list_metadata():
    req = get_request('/users/')
    return req


def current():
    req = get_request('/users/current')
    return req


def add_role(user_id, role_id):
    req = post_request(f'/users/{user_id}/roles/{role_id}', payload=None)
    return req


def remove_role(user_id, role_id):
    req = delete_request(f'/users/{user_id}/roles/{role_id}')
    return req


def get_metadata_by_email(email):
    req = get_request(f'/users-by-email/{email}')
    return req


def add_role_by_email(email, role_id):
    req = post_request(f'/users-by-email/{email}/roles/{role_id}',
                       payload=None)
    return req


def remove_role_by_email(email, role_id):
    req = delete_request(f'/users-by-email/{email}/roles/{role_id}')
    return req


def get_email(user_id):
    req = get_request(f'/users/{user_id}/email')
    return req
