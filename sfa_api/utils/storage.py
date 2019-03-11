import os


from flask import g


import sfa_api.demo as demo
import sfa_api.utils.storage_interface as storage


def get_storage():
    """Return a handle to the storage interface object.
    See sfa_api.utils.storage_interface.

    A non-persistent, in-memory storage backend can be used
    for development by setting the 'STATIC_DATA' config variable.
    """
    if 'storage' not in g:
        if os.getenv('SFA_API_STATIC_DATA'):
            g.storage = demo
        else:
            g.storage = storage
    return g.storage
