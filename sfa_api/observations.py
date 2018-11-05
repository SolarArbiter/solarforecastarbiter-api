from flask import Blueprint, jsonify
from flask.views import MethodView
import marshmallow as ma


from sfa_api import spec


# Add path parameters used by these endpoints to the spec.
spec.add_parameter('uuid', 'path',
                   type='string',
                   description="Resource's unique identifier.",
                   required='true')

blp = Blueprint(
    'observations', 'observations', url_prefix='/observations',
)


# TODO: Replace the demo content in these classes.
class Site(object):
    name = 'Ashland OR'
    resolution = '1 min'
    latitude = 42.19
    longitude = -122.70
    elevation = 595
    station_id = 94040
    abbreviation = 'AS'
    timezone = 'Etc/GMT+8'
    attribution = ''
    source = 'UO SMRL'


class Observation(object):
    uuid = '123e4567-e89b-12d3-a456-426655440000'
    site = Site()


@spec.define_schema('Site')
class SiteSchema(ma.Schema):
    class Meta:
        strict = True
        ordered = True
    name = ma.fields.String()
    latitude = ma.fields.Float()
    longitude = ma.fields.Float()
    elevation = ma.fields.Float()
    station_id = ma.fields.String()
    abbreviation = ma.fields.String()
    timezone = ma.fields.String()
    attribution = ma.fields.String()
    owner = ma.fields.String()


@spec.define_schema('Observation')
class ObservationSchema(ma.Schema):
    class Meta:
        strict = True
        ordered = True
    uuid = ma.fields.UUID(description='UUID response')
    site = ma.fields.Nested(SiteSchema)


class ObservationsView(MethodView):
    schema = ObservationSchema(many=True)
    def get(self, *args):
        """Observation view
        ---
        summary: List observations.
        description: List all observations that the user has access to.
        tags:
          - Observations
        responses:
          200:
            description: A list of observations
            content:
              application/json:
                schema:
                  type: array
                  items:
                    $ref: '#/components/schemas/Observation'
          401:
            $ref: '#/components/responses/401-Unauthorized'
        """
        # TODO: replace demo response, also do not allow top-level json array
        observations = []
        for i in range(5):
            observations.append(Observation())
        return jsonify(self.schema.dump(observations))


    def post(self, *args):
        """
        ---
        summary: Create observation.
        tags:
          - Observations
        description: Create a new Observation.
        responses:
          201:
            $ref: '#/components/responses/201-Created'
          400:
            $ref: '#/components/responses/400-BadRequest'
          401:
            $ref: '#/components/responses/401-Unauthorized'
        """
        # TODO: replace demo response
        return f'Created.'

class ObservationView(MethodView):
    schema = ObservationSchema()
    def get(self, uuid, **kwargs):
        """Loop up an observation by uuid
        ---
        summary: Get observation.
        description: Get an observation by uuid.
        tags:
          - Observations
        parameters:
          - $ref: '#/components/parameters/uuid'

        responses:
          200:
            description: Observation retrieved successfully.
            content:
              aplication/json:
                schema:
                  $ref: '#/components/schemas/Observation'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        # TODO: replace demo response
        observation = Observation()
        return jsonify(self.schema.dump(observation))

    def patch(self, *args): 
        """
        ---
        summary: Update observation.
        description: Update an observation.
        tags:
          - Observations
        parameters:
          - $ref: '#/components/parameters/uuid'
        responses:
          200:
            description: Observation updated successfully.
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        # TODO: replace demo response
        return f'{uuid} updated.'

    def delete(self, *args):
        """
        ---
        summary: Delete observation.
        description: Delete an observation by uuid.
        tags:
          - Observations
        parameters:
        - $ref: '#/components/parameters/uuid'
        responses:
          200:
            description: Observation deleted Successfully.
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        # TODO: replace demo response
        return f'{uuid} deleted.'


blp.add_url_rule('/', view_func=ObservationsView.as_view('observations'))
blp.add_url_rule('/<uuid>', view_func=ObservationView.as_view('observation'))

