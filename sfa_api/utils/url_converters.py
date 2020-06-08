import uuid


from flask import abort
from werkzeug.routing import BaseConverter


class UUIDStringConverter(BaseConverter):
    def to_python(self, value):
        try:
            return str(uuid.UUID(value))
        except ValueError:
            abort(404)

    def to_url(self, value):
        return value


class ZoneStringConverter(BaseConverter):
    def to_python(self, value):
        if len(value) > 255:
            abort(404)
        else:
            return value

    def to_url(self, value):
        return value
