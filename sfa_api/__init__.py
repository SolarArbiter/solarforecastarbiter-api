from flask import Flask
from sfa_api.api import api


from ._version import get_versions
__version__ = get_versions()['version']
del get_versions


def create_app(config_name='ProductionConfig'):
    app = Flask(__name__)
    app.config.from_object(f'sfa_api.config.{config_name}')
    api.init_app(app)

    from sfa_api.observations import blp
    api.register_blueprint(blp)
    return app
