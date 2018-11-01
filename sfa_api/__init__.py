from flask import Flask


from ._version import get_versions
__version__ = get_versions()['version']
del get_versions


app = Flask(__name__)


from sfa_api.api import api
from sfa_api.observations import blp
api.register_blueprint(blp)
