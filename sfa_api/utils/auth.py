"""
Verify JSON Web Tokens from the configured Auth0 application.
We use a custom solution here instead of a library like
flask-jwt-extended because we only need to verify valid tokens
and not issue any. We use python-jose instead of pyjwt because
it is better documented and is not missing any JWT features.
"""
from json.decoder import JSONDecodeError
from functools import wraps
import requests


from flask import (request, Response, current_app, render_template,
                   _request_ctx_stack)
from jose import jwt, jwk
from werkzeug.local import LocalProxy


current_user = LocalProxy(
    lambda: getattr(_request_ctx_stack.top, 'user', ''))
current_jwt_claims = LocalProxy(
    lambda: getattr(_request_ctx_stack.top, 'jwt_claims', None))
current_access_token = LocalProxy(
    lambda: getattr(_request_ctx_stack.top, 'access_token', ''))


def verify_access_token():
    auth = request.headers.get('Authorization', '').split(' ')
    try:
        assert auth[0] == 'Bearer'
        token = jwt.decode(
            auth[1],
            key=current_app.config['JWT_KEY'],
            audience=current_app.config['AUTH0_AUDIENCE'],
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
        # add the token and sub to the request context stack
        # so they can be accessed elsewhere in the code for
        # proper authorization
        _request_ctx_stack.top.jwt_claims = token
        _request_ctx_stack.top.access_token = auth[1]
        _request_ctx_stack.top.user = token['sub']
        return validate_user_existence()


def request_user_info():
    """Makes a user info request to check if the user exists
    and is verified.
    Returns
    -------
    unser_info: dict
        Dict of user information provided by auth0 or None on failure
    Raises
    ------
    json.decoder.JSONDecodeError
        If the user info request fails.
    """
    info_request = requests.get(
        current_app.config['AUTH0_BASE_URL'] + '/userinfo',
        headers={
            'Authorization': f'Bearer {current_access_token}',
        })
    user_info = info_request.json()
    return user_info


def validate_user_existence():
    """Ensures users exist in both auth0 and the database
    Returns
    -------
    True
        If the user already existed, or was created.
    False
        If the user does not have a verified auth0 account or If
        the /userinfo endpoint fails. See notes for details.
    Notes
    -----
    Since a JWT hold it's own expiration, it is possible for a user
    to be deleted in auth0 and still carry a valid token. In order
    to avoid adding that use back to our database, we return false
    if the request for user info fails.
    """
    from sfa_api.utils.storage import get_storage
    storage = get_storage()
    if not storage.user_exists():
        try:
            info = request_user_info()
        except JSONDecodeError:
            # The user has been removed from auth0 but the
            # token is still valid
            return False
        else:
            if not info.get('email_verified', False):
                # User has a valid token, but their email
                # is yet to be verified
                return False
            storage.create_new_user()
    return True


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if verify_access_token():
            return f(*args, **kwargs)
        else:
            return Response(
                render_template('auth_error.html'),
                401,
                {'WWW-Authenticate': 'Bearer'})
    return decorated
