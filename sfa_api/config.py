from sfa_api import __version__


class Config(object):
    API_VERSION = __version__
    REDOC_VERSION = 'next'


class ProductionConfig(Config):
    DEBUG = False


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
