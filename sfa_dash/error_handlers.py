from flask import redirect, url_for


from oauthlib.oauth2.rfc6749.errors import InvalidClientIdError


def no_refresh_token(error):
    return redirect(url_for('auth0.login'))


def register_handlers(app):
    """Registers Errors handlers to catch exceptions raised that would otherwise
    propogate and crash the application.
    """
    app.register_error_handler(InvalidClientIdError, no_refresh_token)
