from flask import current_app


def get_storage():
    """Return a handle to the storage interface object.
    See sfa_api.utils.storage_interface.

    A non-persistent, in-memory storage backend can be used
    for development by setting the 'STATIC_DATA' config variable.
    """
    if not hasattr(current_app, 'storage'):
        import sfa_api.utils.storage_interface as storage
        current_app.storage = storage
    return current_app.storage
