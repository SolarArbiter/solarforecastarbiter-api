import datetime as dt
import os
import requests


class BaseConfig(object):
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', os.urandom(32))
    AUTH0_OAUTH_CLIENT_ID = os.getenv('AUTH0_CLIENT_ID', '')
    AUTH0_OAUTH_CLIENT_SECRET = os.getenv('AUTH0_CLIENT_SECRET', '')
    AUTH0_OAUTH_BASE_URL = 'https://solarforecastarbiter.auth0.com'
    AUTH0_OAUTH_JWT_KEY = requests.get(
        AUTH0_OAUTH_BASE_URL + '/.well-known/jwks.json').json()
    # require login every day
    PERMANENT_SESSION_LIFETIME = dt.timedelta(days=1)
    SESSION_REFRESH_EACH_REQUEST = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI',
                                        'sqlite:////tmp/test.db')


class LocalConfig(BaseConfig):
    SFA_API_URL = 'http://localhost:5000'
    TEMPLATES_AUTO_RELOAD = True


class TestConfig(BaseConfig):
    SFA_API_URL = 'http://localhost:5000'
    SQLALCHEMY_DATABASE_URI = ''


class DevConfig(BaseConfig):
    SFA_API_URL = 'https://dev-api.solarforecastarbiter.org'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True


class ProdConfig(BaseConfig):
    SFA_API_URL = 'https://api.solarforecastarbiter.org'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
