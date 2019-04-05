from functools import partial


try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack
from flask import url_for, redirect, current_app, session
from flask.globals import LocalProxy, _lookup_app_object
from flask_dance.consumer import OAuth2ConsumerBlueprint
from six.moves.urllib.parse import urlencode


oauth_request_session = LocalProxy(partial(_lookup_app_object, 'auth0_oauth'))


def logout():
    session.clear()
    params = {'returnTo': url_for('index',
                                  _external=True),
              'client_id': current_app.config['AUTH0_OAUTH_CLIENT_ID']}
    return redirect(
        current_app.config['AUTH0_OAUTH_BASE_URL'] + '/v2/logout?'
        + urlencode(params))


def make_auth0_blueprint(
        base_url,
        scope=None,
        storage=None):
    scope = scope or ['openid', 'email', 'profile']
    # add 'offline_access' to the scope once secure storage is implemented
    # so the refresh token can be stored and used
    auth0_bp = OAuth2ConsumerBlueprint(
        'auth0', __name__,
        base_url=base_url,
        token_url=f'{base_url}/oauth/token',
        auto_refresh_url=f'{base_url}/oauth/token',
        authorization_url=f'{base_url}/authorize',
        authorization_url_params={
            'audience': 'https://api.solarforecastarbiter.org'},
        redirect_to='.callback_handling',
        scope=scope,
        storage=storage,
    )
    auth0_bp.from_config['client_id'] = 'AUTH0_OAUTH_CLIENT_ID'
    auth0_bp.from_config['client_secret'] = 'AUTH0_OAUTH_CLIENT_SECRET'

    @auth0_bp.before_app_request
    def set_applocal_session():
        ctx = stack.top
        ctx.auth0_oauth = auth0_bp.session

    @auth0_bp.route('/callback')
    def callback_handling():
        # can probably just decode the id_token
        # might also want to make a current_user proxy with the
        # sub or email
        userinfo = oauth_request_session.get(f'{base_url}/userinfo').json()
        session['userinfo'] = userinfo
        return redirect(url_for('index'))

    return auth0_bp
