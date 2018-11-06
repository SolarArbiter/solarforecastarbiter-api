from ._version import get_versions
__version__ = get_versions()['version']
del get_versions


from flask import Flask, Response, jsonify, render_template, url_for  # NOQA
from flask_marshmallow import Marshmallow  # NOQA
from flask_talisman import Talisman  # NOQA


from sfa_api.spec import spec   # NOQA


ma = Marshmallow()
talisman = Talisman()


def create_app(config_name='ProductionConfig'):
    app = Flask(__name__)
    app.config.from_object(f'sfa_api.config.{config_name}')
    ma.init_app(app)
    talisman.init_app(app)

    from sfa_api.observations import obs_blp
    from sfa_api.sites import site_blp
    app.register_blueprint(obs_blp)
    app.register_blueprint(site_blp)
    with app.test_request_context():
        for k, view in app.view_functions.items():
            if k == 'static':
                continue
            spec.add_path(view=view)

    @app.route('/openapi.yaml')
    def get_apispec_yaml():
        return Response(spec.to_yaml(), mimetype='application/yaml')

    @app.route('/openapi.json')
    def get_apispec_json():
        return jsonify(spec.to_dict())

    redoc_script = f"https://cdn.jsdelivr.net/npm/redoc@{app.config['REDOC_VERSION']}/bundles/redoc.standalone.js"  # NOQA

    @app.route('/')
    @talisman(content_security_policy={
        'script-src': f"{redoc_script} 'self' blob:",
    })
    def render_docs():
        return render_template('doc.html',
                               apispec_path=url_for('get_apispec_json'),
                               redoc_script=redoc_script)
    return app
