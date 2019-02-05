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
`client_id='c16EJo48lbTCQEhqSztGGlmxxxmZ4zX'` and
`audience='https://api.solarforecastarbiter.org'`""",
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
Arbiter dashboard. The API relies primarily on JSON data structures in
requests and responses, with the notable exception of the forecast and
observation GET/POST data endpoints which also support CSV files.

Most users will interact with the API indirectly through actions on
the [dashboard](https://dashboard.solarforecastarbiter.org). Those
users who require direct access to the API may include observational
data providers, forecast data providers, and reference data users.

## Interaction for Observational Data Providers

Observational data providers will likely use the API to
programmatically upload data to the Solar Forecast Arbiter
framework. A typical upload may have the following steps:

1. A provider retrieves an access token or loads a token that is still
   valid; see [Authentication](/#section/Authentication) below.

2. A provider loads the known ID for the site and variable of
   interest, or finds the correct ID by querying the
   [observations](/#tag/Observations/paths/~1observations~1/get)
   endpoint

3. The provider prepares the data to POST in either JSON or CSV format
   (see options of
   [POST](#tag/Observations/paths/~1observations~1{obs_id}~1values/post)
   for application/json and text/csv Request Body Schema)

4. The provider sends the POST request to the [add observation
   endpoint](#tag/Observations/paths/~1observations~1{obs_id}~1values/post)
   with the ID from step 2 in the URL and the token from step 1 as the
   Authorization Bearer header

5. The provider checks the response of the POST request to ensure there were
   no errors with the upload.

This process will need to be repeated for each variable and each
site. For example, a user uploading both AC Power and GHI data for a
power plant must make two different POST requests.

## Interaction for Forecast Providers

Forecast providers will likely use the API to programmatically upload
forecasts to the Solar Forecast Arbiter framework. A typical upload
may have the following steps:

1. A provider retrieves an access token or loads a token that is still
   valid; see [Authentication](/#section/Authentication) below.

2. A provider loads the known ID for the site and variable of
   interest, or finds the correct ID by querying the
   [forecasts](/#tag/Forecasts/paths/~1forecasts~1/get)
   endpoint

3. The provider prepares the data to POST in either JSON or CSV format
   (see options of
   [POST](#tag/Forecasts/paths/~1forecasts~1{forecast_id}~1values/post)
   for application/json and text/csv Request Body Schema)

4. The provider sends the POST request to the [add forecast
   endpoint](#tag/Forecasts/paths/~1forecasts~1{forecast_id}~1values/post)
   with the ID from step 2 in the URL and the token from step 1 as the
   Authorization Bearer header

5. The provider checks the response of the POST request to ensure there were
   no errors with the upload.

This process will need to be repeated for each forecast. For example,
a user uploading both a five minute lead time forecast and a one hour
lead time forecast must make two POST requests.


## Interaction for Reference Data Consumer

Users wishing to pull reference data for forecast development or other
purposes may wish to programmatically pull the data. A typical workflow
may be:

1. A user retrieves an access token or loads a token that is still
   valid; see [Authentication](/#section/Authentication) below.

2. A user loads the known ID for the site and variable of
   interest, or finds the correct ID by querying the
   [observations](/#tag/Observations/paths/~1observations~1/get)
   endpoint

3. The user requests the data from the [get observation data
   endpoint](/#tag/Observations/paths/~1observations~1{obs_id}~1values/get)
   in either JSON or CSV format

This process will need to be repeated for each observation site and
variable the user wants. For example, a request for the Desert Rock
SURFRAD DNI and GHI will require two requests, one for each variable.

# Authentication

We utilize OAuth 2.0 and OpenID Connect via [Auth0](https://auth0.com)
with JSON Web Tokens (JWT) for authentication. Auth0 has numereous
[security credentials and undergoes routine
audits](https://auth0.com/security). Since Auth0 stores and manages
user credentials, a compromise in the framework will not compromise
user credentials. Furthermore, by utilizing JWT access tokens that
have a short expiration time (typically a few hours), an accidentally
leaked access token can only be used to access the API for a limited
amount of time unlike API keys which often have no expiration.


A valid JWT issued by Auth0 must be included as a Bearer token in the
Authorization header for all requests to the API. A JWT will expire
after a set period and a valid one will be required to access the
API. Access control is strictly enforced so that only data owners and
authorized users have access to any data.


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
[What is the OAuth2 password grant](https://developer.okta.com/blog/2018/06/29/what-is-the-oauth2-password-grant)
and [Auth0 Resource Owner Password](https://auth0.com/docs/api/authentication#resource-owner-password).
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
         'description': 'Access reports. '
                        'API to be determined in March/April 2019.'},
        {'name': 'Trials',
         'description': 'Access information about forecast trials. '
                        'API to be determined in March/April 2019.'}
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
