"""
Verify JSON Web Tokens from the configured Auth0 application.
We use a custom solution here instead of a library like
flask-jwt-extended because we only need to verify valid tokens
and not issue any. We use python-jose instead of pyjwt because
it is better documented and is not missing any JWT features.
"""
from functools import wraps


from flask import (request, Response, current_app, render_template,
                   _request_ctx_stack)
from jose import jwt
from werkzeug.local import LocalProxy


current_user = LocalProxy(lambda: _request_ctx_stack.top.user)
current_jwt = LocalProxy(lambda: _request_ctx_stack.top.jwt)


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
                jwt.ExpiredSignatureError,
                jwt.JWTClaimsError,
                AttributeError,
                AssertionError) as e:
            return False
        else:
            # add the token and sub to the request context stack
            # so they can be accessed elsewhere in the code for
            # proper authorization
            _request_ctx_stack.top.jwt = token
            _request_ctx_stack.top.user = token['sub']
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
