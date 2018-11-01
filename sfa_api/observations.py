from flask.views import MethodView
from flask_rest_api import Blueprint
import marshmallow as ma


from sfa_api.api import api
blp = Blueprint(
    'observations', 'observations', url_prefix='/observations',
    description='Operations on observations'
)


@api.definition('Site')
class SiteSchema(ma.Schema):
    class Meta:
        strict = True
        ordered = True
    name = ma.fields.String()
    latitude = ma.fields.Float()
    longitude = ma.fields.Float()
    owner = ma.fields.String()


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



@blp.route('/')
class Observations(MethodView):
    @blp.arguments(ObservationQueryArgsSchema, location='query')
    @blp.response(ObservationSchema)
    def get(self, args):
        """List all observations

        Return observations
        ---
        blah
        """
        return {'uid': 'asdfasdf', 'value': 999}
