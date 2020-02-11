import uuid


from flask import abort
from werkzeug.routing import BaseConverter


class UUIDStringConverter(BaseConverter):
    def to_python(self, value):
        try:
            return str(uuid.UUID(value, version=1))
        except ValueError:
            abort(404)

    def to_url(self, value):
        return value
