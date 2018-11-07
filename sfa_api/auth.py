from functools import wraps


from flask import request, Response, current_app, render_template
from jose import jwt


def requires_auth(f):
    @wraps(f)
    def verify_token(*args, **kwargs):
        auth = request.headers.get('Authorization', '').split(' ')
        try:
            assert auth[0] == 'Bearer'
            jwt.decode(auth[1],
                       key=current_app.config['JWT_KEY'],
                       audience=current_app.config['AUTH0_AUDIENCE'],
                       issuer=current_app.config['AUTH0_BASE_URL'] + '/')
        except (jwt.JWTError,
                jwt.ExpiredSignatureError,
                jwt.JWTClaimsError,
                AttributeError,
                AssertionError) as e:
            return Response(
                render_template('auth_error.html'),
                401,
                {'WWW-Authenticate': f"Bearer realm='{current_app.config['AUTH0_BASE_URL']}'"})  # NOQA
        return f(*args, **kwargs)
    return verify_token
