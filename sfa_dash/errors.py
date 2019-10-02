class BaseDashboardException(Exception):
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


class UnverifiedUserException(BaseDashboardException):
    def __init__(self):
        pass


class DataRequestException(BaseDashboardException):
    def __init__(self, status_code, errors=None, **kwargs):
        super().__init__(status_code, errors=errors, **kwargs)
