class BaseDashboardException(Exception):
    def __init__(self, status_code, errors={}, **kwargs):
        Exception.__init__(self)
        errors.update(kwargs)
        for key, error in errors.items():
            if not isinstance(error, list):
                errors['key'] = [error]
        self.errors = errors
        self.status_code = status_code


class UnverifiedUserException(BaseDashboardException):
    def __init__(self):
        pass
