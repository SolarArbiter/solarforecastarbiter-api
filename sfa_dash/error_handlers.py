import logging


from flask import redirect, url_for


from oauthlib.oauth2.rfc6749.errors import OAuth2Error


def bad_oauth_token(error):
    # May be too broad to redirect all errors, see
    # https://github.com/oauthlib/oauthlib/blob/v3.0.1/oauthlib/oauth2/rfc6749/errors.py  # NOQA
    # for a list of errors that we may need to handle individually
    # for now, log the error
    logging.exception('OAuth2 error redirected to login')
    return redirect(url_for('auth0.login'))


def register_handlers(app):
    """Registers Errors handlers to catch exceptions raised that would otherwise
    propogate and crash the application.
    """
    # catch the more general OAuth2Error for any issue related to
    # authentication.
    app.register_error_handler(OAuth2Error, bad_oauth_token)
