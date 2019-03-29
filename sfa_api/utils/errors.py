class BaseAPIException(Exception):
    """Will accept a dictionary of {error_name: description} or will
    build a dictionary from kwargs. Both types of arguments can be
    provided and will be joined. Wraps any non-list descriptions
    in a list to mimic  the format of marshmallow errors.

    Parameters
    ----------
    errors: Dict
        A dictionary of errors to reply with. Optionally, key word
        arguments can be provided instead of a dictionary.
    kwargs:
    """
    def __init__(self, status_code, errors={}, **kwargs):
        Exception.__init__(self)
        errors.update(kwargs)
        for key, error in errors.items():
            if not isinstance(error, list):
                errors[key] = [error]
        self.errors = errors
        self.status_code = status_code


class BadAPIRequest(BaseAPIException):
    def __init__(self, errors={}, **kwargs):
        super().__init__(400, errors, **kwargs)


class NotFoundException(BaseAPIException):
    def __init__(self, **kwargs):
        super().__init__(self, 404, **kwargs)

class StorageAuthError(Exception):
    pass


class DeleteRestrictionError(Exception):
    pass
