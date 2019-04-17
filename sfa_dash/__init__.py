from flask import Flask, redirect, url_for, render_template, session, request
from flask_seasurf import SeaSurf


from sfa_dash.blueprints.auth0 import (make_auth0_blueprint,
                                       oauth_request_session)
from sfa_dash.database import db, session_storage
from sfa_dash.filters import register_jinja_filters
from sfa_dash.template_globals import template_variables
from sfa_dash import error_handlers


def create_app(config=None):
    app = Flask(__name__)
    config = config or 'sfa_dash.config.DevConfig'
    app.config.from_object(config)
    app.secret_key = app.config['SECRET_KEY']
    SeaSurf(app)
    register_jinja_filters(app)
    error_handlers.register_handlers(app)

    if app.config['SQLALCHEMY_DATABASE_URI']:
        db.init_app(app)
        db.create_all(app=app)

    make_auth0_blueprint(
        app,
        base_url=app.config['AUTH0_OAUTH_BASE_URL'],
        storage=session_storage)

    def protect_endpoint():
        try:
            authorized = oauth_request_session.authorized
        except ValueError:
            # no token set for user/no user set
            authorized = False

        # authorized == True means we have a token, not necessarily that it
        # hasn't expired, but refreshing is handled
        # by request_oauthlib and oauthlib
        # and the api validates expiration
        if not authorized:
            session['redirect_path'] = request.path
            return redirect(url_for('auth0.login'))

    @app.route('/')
    def index():
        # move index to app so all blueprints are secured
        # should probably test if authorized and show one
        # page, show a different page w/ login link otherwise
        return render_template('index.html')

    @app.context_processor
    def inject_globals():
        # Injects variables into all rendered templates
        global_template_args = {}
        global_template_args['user'] = session.get('userinfo')
        global_template_args.update(template_variables())
        return global_template_args

    from sfa_dash.blueprints.main import data_dash_blp
    from sfa_dash.blueprints.form import forms_blp

    for blp in (data_dash_blp, forms_blp):
        blp.before_request(protect_endpoint)
        app.register_blueprint(blp)
    return app


if __name__ == '__main__':
    app = create_app()
    app.run()
