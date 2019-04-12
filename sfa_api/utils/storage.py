from flask import current_app


import sfa_api.demo as demo
import sfa_api.utils.storage_interface as storage


def get_storage():
    """Return a handle to the storage interface object.
    See sfa_api.utils.storage_interface.

    A non-persistent, in-memory storage backend can be used
    for development by setting the 'STATIC_DATA' config variable.
    """
    if not hasattr(current_app, 'storage'):
        if current_app.config['SFA_API_STATIC_DATA']:
            current_app.storage = demo
        else:
            current_app.storage = storage
    return current_app.storage
