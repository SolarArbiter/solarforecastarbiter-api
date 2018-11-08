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
    'securitySchemes': {
        'auth0': {
            'type': 'oauth2',
            'description': """Authorization request must include
client_id='c16EJo48lbTCQEhqSztGGlmxxxmZ4zX' and
audience='https://api.solarforecastarbiter.org'""",
            'flows': {
                'password': {
                    'tokenUrl': 'https://solarforecastarbiter.auth0.com/oauth/token',  # NOQA
                    'scopes': {},
                    'client_id': 'c16EJo48lbTCQEhqSztGGlmxxxmZ4zX',
                    'audience': 'https://api.solarforecastarbiter.org'
                },
                'authorizationCode': {
                    'authorizationUrl': 'https://solarforecastarbiter.auth0.com/authorize',  # NOQA
                    'tokenUrl': 'https://solarforecastarbiter.auth0.com/oauth/token',  # NOQA
                    'scopes': {},
                    'client_id': 'c16EJo48lbTCQEhqSztGGlmxxxmZ4zX',
                    'audience': 'https://api.solarforecastarbiter.org'
                }
            }
        }
    }
}

api_description = """The backend RESTful API for Solar Forecast Arbiter.

# Introduction

This webpage documents the public Solar Forecast Arbiter API. This
RESTful API is primarily meant to be accessed by the Solar Forecast
Arbiter dashboard. Forecast providers will likely make use of the
[forecast post](#tag/Forecasts/paths/~1forecasts~1{forecast_id}~1values/post)
endpoint to upload forecasts programmatically. The API relies primarily on
JSON data structures in requests and responses, with the notable exception
of the forecast and observation get/post data endpoints which also support
CSV files.

# Authentication

We utilize OAuth 2.0 and OpenID Connect via [Auth0](https://auth0.com)
with JSON Web Tokens (JWT) for authentication. A valid JWT issued by
Auth0 must be included as a Bearer token in the Authorization header
for all requests to the API. A JWT will expire after a set period and
a valid one will be required to access the API.


A request to Auth0 for a valid JWT may be made in the following way
(with non-testing username and password when appropriate):

```
curl --request POST \\
     --url 'https://solarforecastarbiter.auth0.com/oauth/token' \\
     --header 'content-type: application/json' \\
     --data '{"grant_type": "password", "username": "testing@solarforecastarbiter.org", "password": "Thepassword123!", "audience": "https://api.solarforecastarbiter.org", "client_id": "c16EJo48lbTCQEhqSztGGlmxxxmZ4zX7"}'
```

A valid response will resemble:

```json
{"access_token":"BASE64_ENCODED_JWT","expires_in":10800,"token_type":"Bearer"}
```

Requests to the API need to send the access token in the Authorization header:

```
curl --header "Authorization: Bearer BASE64_ENCODED_JWT" \\
     --url "https://api.solarforecastarbiter.org/endpoint"
```

Extracting and using the access token might look like:

```
export ACCESS_TOKEN=\\
$(curl -s --request POST \\
     --url 'https://solarforecastarbiter.auth0.com/oauth/token' \\
     --header 'content-type: application/json' \\
     --data '{"grant_type": "password", "username": "testing@solarforecastarbiter.org", "password": "Thepassword123!", "audience": "https://api.solarforecastarbiter.org", "client_id": "c16EJo48lbTCQEhqSztGGlmxxxmZ4zX7"}' \\
| jq '.["access_token"]' | sed 's/"//g')

curl --header "Authorization: Bearer $ACCESS_TOKEN" \\
     --url "https://api.solarforecastarbiter.org/observations"
```

For more about how to obtain a JWT using the Resource Owner Password flow, see
https://developer.okta.com/blog/2018/06/29/what-is-the-oauth2-password-grant
and
https://auth0.com/docs/api/authentication#resource-owner-password.
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
        'x-logo': {
            'url': '/static/logo.png',
            'backgroundColor': '#528',
            'altText': 'SFA logo'
        }
    },
    plugins=[
        ma_plugin,
        FlaskPlugin()
    ],
    components=spec_components,
    tags=[
        {'name': 'Sites',
         'description': 'Access and upload observation site metadata and values.'},  # NOQA
        {'name': 'Observations',
         'description': 'Access and upload observation metadata and values.'},
        {'name': 'Forecasts',
         'description': 'Access and upload forecast metadata and values.'},
        {'name': 'Reports',
         'description': 'Access reports.'},
        {'name': 'Trials',
         'description': 'Access information about forecast trials.'}
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
