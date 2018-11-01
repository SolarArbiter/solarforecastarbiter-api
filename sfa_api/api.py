from flask_rest_api import Api

from sfa_api import app

app.config['API_VERSION'] = '0.1'
app.config['OPENAPI_VERSION'] = '3.0'
app.config['OPENAPI_URL_PREFIX'] = '/'
app.config['OPENAPI_REDOC_PATH'] = '/docs'
app.config['OPENAPI_REDOC_VERSION'] = 'next'
api = Api(app)
