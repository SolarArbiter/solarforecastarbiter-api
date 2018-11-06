import apispec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec.ext.flask import FlaskPlugin
from flask_marshmallow.fields import URLFor, AbsoluteURLFor, Hyperlinks


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
            'description': 'User does not have authorization to access resource',  # NOQA
        },
        '404-NotFound': {
            'description': 'The resource could not be found.',
        },
    },
}

api_description = """The backend RESTful API for Solar Forecast Arbiter.

# Introduction
...

# Authentication

OAuth2
"""
ma_plugin = MarshmallowPlugin()
spec = APISpec(
    title='Solar Forecast Arbiter API',
    version=__version__,
    openapi_version='3.0.2',
    info={
        'description': api_description,
        'contact': {
            'name': 'Solar Forecast Arbiter Team',
            'email': 'info@solarforecastarbiter.org',
            'url': 'https://github.com/solararbiter/solarforecastarbiter-api'
        },
        'license': {'name': 'MIT',
                    'url': 'https://opensource.org/licenses/MIT'},
    },
    plugins=[
        ma_plugin,
        FlaskPlugin()
    ],
    components=spec_components,
    tags=[
        {'name': 'Observations',
         'description': 'Access and upload observation metadata and values.'},
        {'name': 'Sites',
         'description': 'Access and upload observation site metadata and values.'}  # NOQA
    ],
    servers=[
        {'url': '//dev-api.solarforecastarbiter.org/',
         'description': 'Development server'},
        {'url': '//testing-api.solarforecastarbiter.org/',
         'description': 'Testing server'},
        {'url': '//api.solarforecastarbiter.org/',
         'description': 'Prodution server'}
    ]
)

ma_plugin.map_to_openapi_type('string', 'url')(URLFor)
ma_plugin.map_to_openapi_type('string', 'url')(AbsoluteURLFor)
ma_plugin.map_to_openapi_type('object', None)(Hyperlinks)
