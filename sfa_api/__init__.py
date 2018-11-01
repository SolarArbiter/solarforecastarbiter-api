from ._version import get_versions
__version__ = get_versions()['version']
del get_versions


from flask import Flask, Response, jsonify  # NOQA
from sfa_api.spec import spec   # NOQA


def create_app(config_name='ProductionConfig'):
    app = Flask(__name__)
    app.config.from_object(f'sfa_api.config.{config_name}')

    from sfa_api.observations import blp
    app.register_blueprint(blp)
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

    return app
