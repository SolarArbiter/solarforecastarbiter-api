from flask import Blueprint, jsonify
from flask.views import MethodView
import marshmallow as ma


from sfa_api import spec


# TODO: Replace the static demo content in these classes.
class Site(object):
    """Object for serializing site metadata. 
    """
    uuid = '123e4567-e89b-12d3-a456-426655440001'
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
    """Container for serializing observation metadata.
    """
    uuid = '123e4567-e89b-12d3-a456-426655440000'
    variable = 'ghi'
    site_id = '123e4567-e89b-12d3-a456-426655440001'
    site = Site()


class ObservationValue(object):
    """Object for serializing observation's timeseries data.
    """
    timestamp = '2018-11-05T18:19:33+00:00'
    value = 35


@spec.define_schema('ObservationValue')
class ObservationValueSchema(ma.Schema):
    class Meta:
        strict = True
        ordered = True
    timestamp = ma.fields.DateTime()
    value = ma.fields.Float()


@spec.define_schema('SiteRequest')
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


@spec.define_schema('SiteResponse')
class SiteResponseSchema(SiteSchema):
    uuid = ma.fields.UUID()

@spec.define_schema('ObservationRequest')
class ObservationSchema(ma.Schema):
    class Meta:
        strict = True
        ordered = True
    variable = ma.fields.String()
    site_id = ma.fields.UUID()
    site = ma.fields.Nested(SiteSchema)

@spec.define_schema('ObservationResponse')
class ObservationResponseSchema(ObservationSchema):
    uuid = ma.fields.UUID()


class ObservationsView(MethodView):
    schema = ObservationSchema(many=True)

    def get(self, *args):
        """
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
                    $ref: '#/components/schemas/ObservationResponse'
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
        description: Create a new Observation by posting metadata.
        requestBody:
          description: JSON respresentation of an observation.
          required: True
          content:
            application/json:
                schema:
                  $ref: '#/components/schemas/ObservationRequest'
        responses:
          201:
            $ref: '#/components/responses/201-Created'
          400:
            $ref: '#/components/responses/400-BadRequest'
          401:
            $ref: '#/components/responses/401-Unauthorized'
        """
        # TODO: replace demo response
        return f'Created an observation resource.'


class ObservationView(MethodView):
    schema = ObservationSchema()

    def get(self, uuid, **kwargs):
        """
        ---
        summary: Get Observation options.
        description: List options available for Observation.
        tags:
          - Observations
        parameters:
          - $ref: '#/components/parameters/uuid'
        responses:
          200:
            description: Observation options retrieved successfully.
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/ObservationResponse'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        # TODO: replace demo response
        links = {
            'metadata': f'/observations/{uuid}/metadata',
            'values': f'/observations/{uuid}/values',
        }
        return jsonify(links)

    def delete(self, uuid, *args):
        """
        ---
        summary: Delete observation.
        description: Delete an Observation, including its values and metadata.
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


class ObservationValuesView(MethodView):
    schema = ObservationValueSchema()

    def get(self, uuid, *args):
        """
        ---
        summary: Get Observation data.
        description: Get the timeseries values from the Observation entry.
        tags:
        - Observations
        parameters:
          - $ref: '#/components/parameters/uuid'
        responses:
          200:
            content:
              application/json:
                schema:
                  type: array
                  items:
                    $ref: '#/components/schemas/ObservationValue'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        return f'Get values for {uuid}'

    def post(self, uuid, *args):
        """
        ---
        summary: Add Observation data.
        description: Add new timeseries values to the Observation entry.
        tags:
        - Observations
        parameters:
        - $ref: '#/components/parameters/uuid'
        requestBody:
          description: JSON respresentation of an observation.
          required: True
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/ObservationValue'
        responses:
          201:
            $ref: '#/components/responses/201-Created'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        return f'Added timeseries values to {uuid}'


class ObservationMetadataView(MethodView):
    schema = ObservationSchema()

    def get(self, uuid, *args):
        """
        ---
        summary: Get Observation metadata.
        tags:
        - Observations
        parameters:
        - $ref: '#/components/parameters/uuid'
        responses:
          200:
            description: Successfully retrieved observation metadata.
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/ObservationResponse'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
             $ref: '#/components/responses/404-NotFound'
        """
        # TODO: replace demo data
        demo_obs = Observation()
        return self.schema.dumps(demo_obs)

    def put(self, uuid, *args):
        """
        ---
        summary: Update observation metadata.
        description: Update an observation's metadata.
        tags:
          - Observations
        parameters:
          - $ref: '#/components/parameters/uuid'
        requestBody:
          description: JSON representation of an observation's metadata.
          required: True
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ObservationRequest'
        responses:
          200:
            description: Observation updated successfully.
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        return 'OK'

# Add path parameters used by these endpoints to the spec.
spec.add_parameter('uuid', 'path',
                   type='string',
                   description="Resource's unique identifier.",
                   required='true')

blp = Blueprint(
    'observations', 'observations', url_prefix='/observations',
)

blp.add_url_rule('/', view_func=ObservationsView.as_view('observations'))
blp.add_url_rule('/<uuid>', view_func=ObservationView.as_view('observation'))
blp.add_url_rule('/<uuid>/values',
                 view_func=ObservationValuesView.as_view('observation_values'))
blp.add_url_rule('/<uuid>/metadata',
                 view_func=ObservationMetadataView.as_view('observation_metadata'))
