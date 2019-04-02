from ._version import get_versions
__version__ = get_versions()['version']
del get_versions


from flask import Flask, Response, jsonify, json, render_template, url_for  # NOQA
from flask_marshmallow import Marshmallow  # NOQA
from flask_talisman import Talisman  # NOQA


from sfa_api.spec import spec   # NOQA
from sfa_api.error_handlers import register_error_handlers  # NOQA
from sfa_api.utils.auth import requires_auth  # NOQA


ma = Marshmallow()
talisman = Talisman()


@requires_auth
def protect_endpoint():
    """Require authorization to access the endpoint. To be used as as
    before_request function"""
    pass


def create_app(config_name='ProductionConfig'):

    app = Flask(__name__)
    app.config.from_object(f'sfa_api.config.{config_name}')
    ma.init_app(app)
    register_error_handlers(app)
    redoc_script = f"https://cdn.jsdelivr.net/npm/redoc@{app.config['REDOC_VERSION']}/bundles/redoc.standalone.js"  # NOQA
    talisman.init_app(app,
                      content_security_policy={
                          'default-src': "'self'",
                          'style-src': "'unsafe-inline' 'self'",
                          'img-src': "'self' data:",
                          'object-src': "'none'",
                          'script-src': ["'unsafe-inline'",
                                         'blob:',
                                         redoc_script,
                                         "'strict-dynamic'"],
                          'base-uri': "'none'"
                      },
                      content_security_policy_nonce_in=['script-src'])

    from sfa_api.observations import obs_blp
    from sfa_api.forecasts import forecast_blp
    from sfa_api.sites import site_blp

    for blp in (obs_blp, forecast_blp, site_blp):
        blp.before_request(protect_endpoint)
        app.register_blueprint(blp)

    with app.test_request_context():
        for k, view in app.view_functions.items():
            if k == 'static':
                continue
            spec.path(view=view)

    @app.route('/openapi.yaml')
    def get_apispec_yaml():
        return Response(spec.to_yaml(), mimetype='application/yaml')

    @app.route('/openapi.json')
    def get_apispec_json():
        return jsonify(spec.to_dict())

    @app.route('/')
    def render_docs():
        return render_template('doc.html',
                               apispec_path=url_for('get_apispec_json'),
                               redoc_script=redoc_script)
    return app
