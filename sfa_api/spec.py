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


# Reusable, endpoint-agnostic components.
spec_components = {
    'responses': {
        '201-Created': {
            'description': 'Resource created successfully.',
        },
        '204-NoContent': {
            'description': 'Operation completed successfully.',
        },
        '400-BadRequest': {
            'description': 'Could not process request due to invalid syntax.',
        },
        '401-Unauthorized': {
            'description': 'User must authenticate to access resource.',
        },
        '403-Forbidden': {
            'description': 'User does not have authorization to access resource',
        },
        '404-NotFound':{
            'description': 'The resource could not be found.',
        },
    },
}


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
    ],
    components=spec_components,
)


