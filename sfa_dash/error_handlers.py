import logging


from flask import redirect, url_for, render_template


from oauthlib.oauth2.rfc6749.errors import OAuth2Error
from sfa_dash.errors import UnverifiedUserException


def bad_oauth_token(error):
    # May be too broad to redirect all errors, see
    # https://github.com/oauthlib/oauthlib/blob/v3.0.1/oauthlib/oauth2/rfc6749/errors.py  # NOQA
    # for a list of errors that we may need to handle individually
    # for now, log the error
    logging.exception('OAuth2 error redirected to login')
    return redirect(url_for('auth0.login'))


def unverified_user(error):
    """Displays the front page with an error that the user must verify their
    email before accessing data.
    """
    messages = {
        "Email Unverified": [
            "Please complete the sign up process by verifying your "
            "email account. You should receive a verification email "
            "from Solar Forecast Arbiter. The verification email is "
            "usually sent immediately, so remember to check your "
            "spam and junk mail folders if you don't see the message "
            "in your inbox."]}
    return render_template('index.html', messages=messages), 401


def register_handlers(app):
    """Registers Errors handlers to catch exceptions raised that would otherwise
    propogate and crash the application.
    """
    # catch the more general OAuth2Error for any issue related to
    # authentication.
    app.register_error_handler(OAuth2Error, bad_oauth_token)
    app.register_error_handler(UnverifiedUserException, unverified_user)
