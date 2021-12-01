from ._version import get_versions
__version__ = get_versions()['version']
del get_versions


import os  # NOQA


from flask import Flask, Response, json, jsonify, render_template, url_for  # NOQA
from flask_marshmallow import Marshmallow  # NOQA
from flask_talisman import Talisman  # NOQA
import sentry_sdk  # NOQA
from sentry_sdk.integrations.flask import FlaskIntegration  # NOQA


from sfa_api.spec import spec  # NOQA
from sfa_api.error_handlers import register_error_handlers  # NOQA
from sfa_api.utils.auth import requires_auth  # NOQA
from sfa_api.utils.url_converters import (  # NOQA
    UUIDStringConverter, ZoneStringConverter)


ma = Marshmallow()
talisman = Talisman()


@requires_auth
def protect_endpoint():
    """Require authorization to access the endpoint. To be used as as
    before_request function"""
    pass


def create_app(config_name='ProductionConfig'):
    sentry_sdk.init(send_default_pii=False,
                    integrations=[FlaskIntegration()])
    app = Flask(__name__)
    app.config.from_object(f'sfa_api.config.{config_name}')
    if 'REDIS_SETTINGS' in os.environ:
        app.config.from_envvar('REDIS_SETTINGS')
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
                          'child-src': "blob:",
                          'base-uri': "'none'"
                      },
                      content_security_policy_nonce_in=['script-src'])
    app.url_map.converters['uuid_str'] = UUIDStringConverter
    app.url_map.converters['zone_str'] = ZoneStringConverter

    from sfa_api.observations import obs_blp
    from sfa_api.forecasts import forecast_blp
    from sfa_api.sites import site_blp
    from sfa_api.users import user_blp, user_email_blp
    from sfa_api.roles import role_blp
    from sfa_api.permissions import permission_blp
    from sfa_api.reports import reports_blp
    from sfa_api.aggregates import agg_blp
    from sfa_api.zones import zone_blp
    from sfa_api.outages import outage_blp

    for blp in (obs_blp, forecast_blp, site_blp, user_blp, user_email_blp,
                role_blp, permission_blp, reports_blp, agg_blp, zone_blp,
                outage_blp):
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


def create_app_with_metrics(config_name='ProductionConfig'):  # pragma: no cover  # NOQA
    from prometheus_flask_exporter.multiprocess import (
        GunicornPrometheusMetrics)
    app = create_app(config_name)
    GunicornPrometheusMetrics(app=app, group_by='url_rule')
    return app


def __getattr__(name):  # pragma: no cover
    """
    Enable lazy evaluation of app creation while supporting running the app
    with gunicorn like 'gunicorn sfa_api:app'
    """
    if name == 'app':
        return create_app()
    elif name == 'app_with_metrics':
        return create_app_with_metrics()
    else:
        raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
