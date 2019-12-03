from concurrent.futures import ThreadPoolExecutor
from functools import partial
import logging
import secrets
import string


from flask import current_app
from jose import jwt, jwk
import requests


from sfa_api.utils.queuing import make_redis_connection


logger = logging.getLogger(__name__)


def token_redis_connection():
    """Make a connection to Redis and the database specified by
    config['AUTH0_REDIS_DB']. The connection is stored on the
    application for reuse.
    """
    if not hasattr(current_app, 'auth0_redis_conn'):
        config = current_app.config.copy()
        config['REDIS_DB'] = config['AUTH0_REDIS_DB']
        # return everything as strings
        config['REDIS_DECODE_RESPONSES'] = True
        if config.get('USE_FAKE_REDIS', False):
            from fakeredis import FakeStrictRedis
            conn = FakeStrictRedis(decode_responses=True)
        else:
            conn = make_redis_connection(config)
        setattr(current_app, 'auth0_redis_conn', conn)
    return getattr(current_app, 'auth0_redis_conn')


def get_fresh_auth0_management_token():
    """Request an access token for the Auth0 Management API based on the
    AUTH0_CLIENT_ID and AUTH0_CLIENT_SECRET in the config.
    """
    if (
        current_app.config['AUTH0_CLIENT_ID'] == '' or
        current_app.config['AUTH0_CLIENT_SECRET'] == ''
    ):
        raise ValueError('Auth0 client ID or secret not specified')

    payload = {'client_id': current_app.config['AUTH0_CLIENT_ID'],
               'client_secret': current_app.config['AUTH0_CLIENT_SECRET'],
               'audience': current_app.config['AUTH0_BASE_URL'] + '/api/v2/',
               'grant_type': 'client_credentials'
               }
    req = requests.post(current_app.config['AUTH0_BASE_URL'] + '/oauth/token',
                        headers={'content-type': 'application/json'},
                        json=payload)
    req.raise_for_status()
    token = req.json()['access_token']
    return token


def check_if_token_is_valid(token):
    """
    Check if the JSON web token is valid.

    Parameters
    ----------
    token : str
        The JSON web token to check.

    Returns
    -------
    boolean or None
        Returns None if the token is None, otherwise returns whether
        the token is a valid, unexpired JWT issued by Auth0 for the
        Auth0 management API.
    """
    if token is None:
        return
    try:
        jwt.decode(
            token,
            key=current_app.config['JWT_KEY'],
            audience=current_app.config['AUTH0_BASE_URL'] + '/api/v2/',
            issuer=current_app.config['AUTH0_BASE_URL'] + '/')
    except (jwt.JWTError,
            jwk.JWKError,
            jwt.ExpiredSignatureError,
            jwt.JWTClaimsError,
            AttributeError,
            AssertionError,
            IndexError):
        return False
    else:
        return True


def auth0_token():
    """
    Get the auth0 management API access token from Redis,
    if present, and validate the token is good.
    Otherwise, get a new token and store it in Redis

    Returns
    -------
    token : str or None
        Returns None when could not retrieve a token to access the
        Auth0 Management API
    """
    redis_conn = token_redis_connection()
    token = redis_conn.get('auth0_token')
    token_valid = check_if_token_is_valid(token)
    if token is None or not token_valid:
        try:
            token = get_fresh_auth0_management_token()
        except (ValueError, requests.HTTPError) as e:
            logger.error('Failed to retrieve Auth0 token: %r', e)
            return
        redis_conn.set('auth0_token', token)
    return token


def _verify_auth0_id(auth0_id):
    if not auth0_id.startswith('auth0|'):
        raise ValueError('Invalid auth0 ID')


def _get_email_of_user(auth0_id, redis_conn, token,
                       config):
    # email is PII, but easy to clear db
    email = redis_conn.get(auth0_id)
    if email is None:
        headers = {'content-type': 'application/json',
                   'authorization': f'Bearer {token}'}
        req = requests.get(
            config['AUTH0_BASE_URL'] + '/api/v2/users/' + auth0_id,
            params={'fields': 'email',
                    'include_fields': 'true'},
            headers=headers)
        if req.status_code == 200:
            email = req.json()['email']
            # expire in 1 day
            redis_conn.set(auth0_id, email, ex=86400)
        else:
            logger.error('Failed to retrieve email from Auth0: %s %s',
                         req.status_code, req.text)
            email = 'Unable to retrieve'
    return email


def get_email_of_user(auth0_id):
    """
    Get the email of a user given their auth0 ID

    Parameters
    ----------
    auth0_id : str
        The auth0 ID of the user

    Returns
    -------
    str
        The email if found, otherwise 'Unable to retrieve'

    Raises
    ------
    ValueError
        If the auth0_id is not valid
    """
    _verify_auth0_id(auth0_id)
    return _get_email_of_user(
        auth0_id, token_redis_connection(), auth0_token(),
        current_app.config)


def list_user_emails(auth0_ids):
    """
    Get the emails of all users with the given ids

    Parameters
    ----------
    auth0_ids : list of str
        The auth0 IDs of the users

    Returns
    -------
    dict
        With auth0_id keys and email values

    Raises
    ------
    ValueError
        If any auth0 ID is not valid
    """

    list(map(_verify_auth0_id, auth0_ids))
    redis_conn = token_redis_connection()
    token = auth0_token()
    config = current_app.config
    func = partial(_get_email_of_user, redis_conn=redis_conn,
                   token=token, config=config)
    with ThreadPoolExecutor(max_workers=4) as exc:
        out = dict(zip(
            auth0_ids, exc.map(func, auth0_ids)))
    return out


def _get_auth0_id_of_user(email, redis_conn, token,
                          config):
    # email is PII, but easy to clear db
    user_id = redis_conn.get(email)
    if user_id is None:
        headers = {'content-type': 'application/json',
                   'authorization': f'Bearer {token}'}
        req = requests.get(
            config['AUTH0_BASE_URL'] + '/api/v2/users-by-email',
            params={'fields': 'user_id',
                    'email': email,
                    'include_fields': 'true'},
            headers=headers)
        if req.status_code == 200:
            userjson = req.json()
            if len(userjson) != 1:
                # not found in auth0 at all
                # or somehow more than 1?
                user_id = 'Unable to retrieve'
            else:
                user_id = userjson[0]['user_id']
                # expire in 1 day
                redis_conn.set(email, user_id, ex=86400)
        else:
            logger.error('Failed to retrieve user_id from Auth0: %s %s',
                         req.status_code, req.text)
            user_id = 'Unable to retrieve'
    return user_id


def get_auth0_id_of_user(email):
    """
    Get the auth0 id of a user given their email.
    To be used internally to match emails with database
    user ids.

    Parameters
    ----------
    email : str
        The email to check the auth0 api for

    Returns
    -------
    str
        The auth0 id if found, otherwise 'Unable to retrieve'
    """
    return _get_auth0_id_of_user(email,
                                 token_redis_connection(),
                                 auth0_token(),
                                 current_app.config)


def random_password():
    """
    Generate a random password of letters, digits, punctuation, and whitespace
    with a random length between 32 and 48 characters.
    """
    pass_len = secrets.choice(range(32, 49))
    return ''.join(secrets.choice(string.printable)
                   for _ in range(pass_len))


def create_user(email, password, verified=False):
    """
    Create a new Auth0 user.

    Parameters
    ----------
    email : str
        The email address of the new user.
    password : str
        The password for the user.
    verified : boolean, default False
        Whether or not to set 'email_verified' with Auth0

    Returns
    -------
    user_id : str
        The Auth0 user id of the newly created user

    Raises
    ------
    HTTPError
        If the request to the Auth0 API fails
    """
    token = auth0_token()
    config = current_app.config
    body = {'email': email,
            'password': password,
            'email_verified': verified,
            'connection': 'Username-Password-Authentication'}
    headers = {'content-type': 'application/json',
               'authorization': f'Bearer {token}'}
    req = requests.post(
        config['AUTH0_BASE_URL'] + '/api/v2/users',
        json=body,
        headers=headers)
    req.raise_for_status()
    user_id = req.json()['user_id']
    return user_id


def get_refresh_token(email, password):
    """
    Requests a refresh token from Auth0

    Parameters
    ----------
    email : str
        The email address of the new user.
    password : str
        The password for the user.

    Returns
    -------
    refresh_token : str
        The refresh token

    Raises
    ------
    HTTPError
        If the request to the Auth0 API fails
    """
    body = {'grant_type': 'password',
            'username': email,
            'password': password,
            'client_id': current_app.config['AUTH0_CLIENT_ID'],
            'client_secret': current_app.config['AUTH0_CLIENT_SECRET'],
            'audience': current_app.config['AUTH0_AUDIENCE'],
            'scope': 'offline_access'
            }
    req = requests.post(
        current_app.config['AUTH0_BASE_URL'] + '/oauth/token',
        json=body
    )
    req.raise_for_status()
    return req.json()['refresh_token']


def exchange_refresh_token(refresh_token):
    """
    Requests an access token from Auth0 from a refresh token

    Parameters
    ----------
    refresh_token : str
        The refresh token to use.

    Returns
    -------
    access_token : str
        The access token to be used to authenticate with the SFA API

    Raises
    ------
    HTTPError
        If the request to the Auth0 API fails
    """
    body = {'grant_type': 'refresh_token',
            'client_id': current_app.config['AUTH0_CLIENT_ID'],
            'client_secret': current_app.config['AUTH0_CLIENT_SECRET'],
            'audience': current_app.config['AUTH0_AUDIENCE'],
            'refresh_token': refresh_token
            }
    req = requests.post(
        current_app.config['AUTH0_BASE_URL'] + '/oauth/token',
        json=body)
    req.raise_for_status()
    return req.json()['access_token']


def get_password_reset_link(email):
    """
    Get a link to set a new password for the user

    Parameters
    ----------
    email : str
        The email address of the user.

    Returns
    -------
    link : str
        The HTTP link to Auth0 to set a new password

    Raises
    ------
    HTTPError
        If the request to the Auth0 API fails
    """
    token = auth0_token()
    config = current_app.config
    auth0_id = get_auth0_id_of_user(email)
    body = {'user_id': auth0_id,
            'ttl_sec': 86400 * 7,  # link will live for 7 days
            'mark_email_as_verified': False,
            'includeEmailInRedirect': False
            }
    headers = {'content-type': 'application/json',
               'authorization': f'Bearer {token}'}
    req = requests.post(
        config['AUTH0_BASE_URL'] + '/api/v2/tickets/password-change',
        json=body,
        headers=headers)
    req.raise_for_status()
    link = req.json()['ticket']
    return link
