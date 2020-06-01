import os


import pandas as pd
import requests


from sfa_api import __version__


class Config(object):
    API_VERSION = __version__
    REDOC_VERSION = os.getenv('REDOC_VERSION', 'next')
    AUTH0_BASE_URL = 'https://solarforecastarbiter.auth0.com'
    AUTH0_AUDIENCE = 'https://api.solarforecastarbiter.org'
    AUTH0_CLIENT_ID = os.getenv('AUTH0_CLIENT_ID', '')
    AUTH0_CLIENT_SECRET = os.getenv('AUTH0_CLIENT_SECRET', '')
    AUTH0_REDIS_DB = os.getenv('AUTH0_REDIS_DB', 1)
    JWT_KEY = requests.get(
        AUTH0_BASE_URL + '/.well-known/jwks.json').json()
    MYSQL_HOST = os.getenv('MYSQL_HOST', '127.0.0.1')
    MYSQL_PORT = os.getenv('MYSQL_PORT', '3306')
    MYSQL_USER = os.getenv('MYSQL_USER', None)
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', None)
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', None)
    SFA_API_STATIC_DATA = os.getenv('SFA_API_STATIC_DATA', False)
    # limit requests to 16MB
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
    JOB_BASE_URL = os.getenv('JOB_BASE_URL', None)
    REPORT_JOB_TIMEOUT = int(os.getenv('REPORT_JOB_TIMEOUT', 600))
    VALIDATION_JOB_TIMEOUT = int(os.getenv('VALIDATION_JOB_TIMEOUT', 150))
    MAX_POST_DATAPOINTS = int(os.getenv('MAX_POST_DATAPOINTS',
                                        200000))
    MAX_DATA_RANGE_DAYS = pd.Timedelta(os.getenv('MAX_DATA_RANGE_DAYS', '366')
                                       + ' days')


class ProductionConfig(Config):
    DEBUG = False


class DevelopmentConfig(Config):
    DEBUG = True
    MYSQL_USER = 'apiuser'
    MYSQL_PASSWORD = 'thisisaterribleandpublicpassword'
    MYSQL_DATABASE = 'arbiter_data'
    USE_FAKE_REDIS = True


class TestingConfig(Config):
    TESTING = True
    MYSQL_USER = 'apiuser'
    MYSQL_PASSWORD = 'thisisaterribleandpublicpassword'
    MYSQL_DATABASE = 'arbiter_data'
    USE_FAKE_REDIS = True
    AUTH0_CLIENT_ID = 'clientid'
    AUTH0_CLIENT_SECRET = 'secret'


class AdminTestConfig(TestingConfig):
    MYSQL_USER = 'frameworkadmin'
    MYSQL_PASSWORD = 'thisisaterribleandpublicpassword'
    MYSQL_DATABASE = 'arbiter_data'
