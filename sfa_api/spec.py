import apispec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec.ext.flask import FlaskPlugin


from sfa_api import __version__


class APISpec(apispec.APISpec):
    _views = set()

    def define_schema(self, name):
        def decorator(schema, **kwargs):
            self.definition(name, schema=schema, **kwargs)
            return schema
        return decorator


spec = APISpec(
    title='Solar Forecast Arbiter API',
    version=__version__,
    openapi_version='3.0.2',
    info={
        'description': 'The backend API for Solar Forecast Arbiter'
    },
    plugins=[
        MarshmallowPlugin(),
        FlaskPlugin()
    ]
)
