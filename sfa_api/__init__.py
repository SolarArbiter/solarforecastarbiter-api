from flask import Flask

app = Flask(__name__)

from sfa_api.api import api
from sfa_api.observations import blp
api.register_blueprint(blp)
