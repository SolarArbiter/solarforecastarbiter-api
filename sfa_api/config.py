import requests
from sfa_api import __version__


class Config(object):
    API_VERSION = __version__
    REDOC_VERSION = 'next'
    AUTH0_BASE_URL = 'https://solarforecastarbiter.auth0.com'
    AUTH0_AUDIENCE = 'https://api.solarforecastarbiter.org'
    JWT_KEY = requests.get(
        AUTH0_BASE_URL + '/.well-known/jwks.json').json()


class ProductionConfig(Config):
    DEBUG = False


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
