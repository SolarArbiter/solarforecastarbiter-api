from flask import Blueprint
from flask.views import MethodView
import marshmallow as ma


from sfa_api import spec


blp = Blueprint(
    'observations', 'observations', url_prefix='/observations',
)


@spec.define_schema('Site')
class SiteSchema(ma.Schema):
    class Meta:
        strict = True
        ordered = True
    name = ma.fields.String()
    latitude = ma.fields.Float()
    longitude = ma.fields.Float()
    owner = ma.fields.String()


@spec.define_schema('Observation')
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


class Observations(MethodView):
    def get(self, *args):
        """Observation view
        ---
        summary: List observations
        description: List all observations that the user has access to
        tags:
          - observations
        responses:
          200:
            description: A list of observations
            content:
              application/json:
                schema:
                  type: array
                  items:
                    $ref: '#/components/schemas/Observation'
        """
        return 'good'

    def post(self, *args):
        """
        ---
        summary: post to obs
        tags:
          - observations
        """
        pass


blp.add_url_rule('/', view_func=Observations.as_view('observations'))
