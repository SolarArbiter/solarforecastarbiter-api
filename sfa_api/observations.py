from flask import Flask
from flask.views import MethodView
from flask_rest_api import Api, Blueprint
import marshmallow as ma


app = Flask(__name__)
app.config['API_SPEC_OPTIONS'] = {'basepath': '/v0'}
app.config['API_VERSION'] = '0.1'
app.config['OPENAPI_VERSION'] = '3.0'
app.config['OPENAPI_URL_PREFIX'] = '/'
app.config['OPENAPI_REDOC_PATH'] = '/docs'
app.config['OPENAPI_REDOC_VERSION'] = 'next'
api = Api(app)


@api.definition('Site')
class SiteSchema(ma.Schema):
    class Meta:
        strict = True
        ordered = True
    name = ma.fields.String()
    latitude = ma.fields.Float()
    longitude = ma.fields.Float()


@api.definition('Observation')
class ObservationSchema(ma.Schema):
    class Meta:
        strict = True
        ordered = True
    uuid = ma.fields.UUID(description='UUID response')
    site = ma.fields.Nested(SiteSchema)


class ObservationQueryArgsSchema(ma.Schema):
    """
    Query args
    """
    class Meta:
        strict = True
        ordered = True
    uuid = ma.fields.UUID(description='query UUID')


blp = Blueprint(
    'observations', 'observations', url_prefix='/observations',
    description='Operations on observations'
)


@blp.route('/')
class Observations(MethodView):
    @blp.arguments(ObservationQueryArgsSchema, location='query')
    @blp.response(ObservationSchema)
    @blp.response(code=401, description='fail')
    def get(self, args):
        """List all observations

        Return observations
        ---
        blah
        """
        return {'uid': 'asdfasdf', 'value': 999}


api.register_blueprint(blp)


if __name__ == '__main__':
    app.run(port=18888)
