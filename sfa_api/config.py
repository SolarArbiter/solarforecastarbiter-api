from sfa_api import __version__


class Config(object):
    API_VERSION = __version__
    OPENAPI_VERSION = '3.0.2'
    OPENAPI_URL_PREFIX = '/'
    OPENAPI_REDOC_PATH = '/docs'
    OPENAPI_REDOC_VERSION = 'next'


class ProductionConfig(Config):
    DEBUG = False


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
