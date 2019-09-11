class BaseAPIException(Exception):
    """Base exception to be thrown from within API code to trigger
    an immediate HTTP response.

    Parameters
    ----------
    status_code: int
        The HTTP status code to return with the errors.

    errors: dict
        A dictionary where keys are names for an error and values are
        a description.
        e.g {'Longitude': 'Must be between -180 and 180.'}

    Notes
    -----
    Errors can be provided as a dictionary as described above, as
    keyword arguments or both. Any non-list descriptors will be
    wrapped in a list such that the dictionary:

        {'error0': 'error message',
         'fieldname': (error1, error2)}

     will become:

        {'error0': ['error message'],
         'fieldname': [(error1, error2)]}
    """
    def __init__(self, status_code, errors=None, **kwargs):
        Exception.__init__(self)
        if errors is None:
            errors = {}
        errors.update(kwargs)
        for key, error in errors.items():
            if not isinstance(error, list):
                errors[key] = [error]
        self.errors = errors
        self.status_code = status_code


class BadAPIRequest(BaseAPIException):
    def __init__(self, errors=None, **kwargs):
        super().__init__(400, errors, **kwargs)


class NotFoundException(BaseAPIException):
    def __init__(self, **kwargs):
        super().__init__(404, **kwargs)


class StorageAuthError(Exception):
    pass


class DeleteRestrictionError(Exception):
    pass
