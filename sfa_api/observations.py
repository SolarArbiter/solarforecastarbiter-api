from flask import Blueprint
from flask.views import MethodView


from sfa_api import spec, ma
from sfa_api.sites import SiteSchema
from sfa_api.demo import Observation


@spec.define_schema('ObservationValue')
class ObservationValueSchema(ma.Schema):
    class Meta:
        strict = True
        ordered = True
    timestamp = ma.DateTime(description="ISO 8601 Datetime")
    value = ma.Float(description="Value of the measurement")
    questionable = ma.Boolean(description="Whether the value is questionable",
                              default=False, missing=False)


@spec.define_schema('ObservationDefinition')
class ObservationPostSchema(ma.Schema):
    class Meta:
        strict = True
        ordered = True
    variable = ma.String(
        description="Name of variable recorded by this observation",
        required=True)
    site_id = ma.UUID(description="UUID the assocaiated site",
                      required=True)


@spec.define_schema('ObservationMetadata')
class ObservationSchema(ObservationPostSchema):
    site = ma.Nested(SiteSchema)
    uuid = ma.UUID()


@spec.define_schema('ObservationLinks')
class ObservationLinksSchema(ma.Schema):
    class Meta:
        strict = True
        ordered = True
    uuid = ma.UUID()
    _links = ma.Hyperlinks({
        'metadata': ma.AbsoluteURLFor('observations.metadata',
                                      uuid='<uuid>'),
        'values': ma.AbsoluteURLFor('observations.values',
                                    uuid='<uuid>')
    })


class AllObservationsView(MethodView):
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
                    $ref: '#/components/schemas/ObservationMetadata'
          401:
            $ref: '#/components/responses/401-Unauthorized'
        """
        # TODO: replace demo response, also do not allow top-level json array
        observations = []
        for i in range(5):
            observations.append(Observation())
        return self.schema.jsonify(observations)

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
                  $ref: '#/components/schemas/ObservationDefinition'
        responses:
          201:
            description: Observation created successfully
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/ObservationMetadata'
          400:
            $ref: '#/components/responses/400-BadRequest'
          401:
            $ref: '#/components/responses/401-Unauthorized'
        """
        # TODO: replace demo response
        return f'Created an observation resource.'


class ObservationView(MethodView):
    schema = ObservationLinksSchema()

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
                  $ref: '#/components/schemas/ObservationLinks'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        return self.schema.jsonify({'uuid': uuid})

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
        TODO: Limits???
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
          required: True
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/ObservationValue'
            text/csv:
              schema:
                type: string
                description: |
                  Text file with fields separated by ',' and
                  lines separated by '\\n'. The first line must
                  be a header with the following fields:
                  timestamp, value, questionable. Timestamp must be
                  an ISO 8601 datetime, value may be an integer or float,
                  questionable may be 0 or 1 (indicating the value is not
                  to be trusted).
              example: |-
                timestamp,value,questionable
                2018-10-29T12:04:23Z,32.93,0
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
                  $ref: '#/components/schemas/ObservationMetadata'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
             $ref: '#/components/responses/404-NotFound'
        """
        # TODO: replace demo data
        demo_obs = Observation()
        return self.schema.jsonify(demo_obs)

    def put(self, uuid, *args):
        """
        TODO: MAY NOT MAKE SENSE TO KEEP if schema is so simple
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
                $ref: '#/components/schemas/ObservationDefinition'
        responses:
          200:
            description: Observation updated successfully.
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        return


# Add path parameters used by these endpoints to the spec.
spec.add_parameter('uuid', 'path',
                   type='string',
                   description="Resource's unique identifier.",
                   required='true')

obs_blp = Blueprint(
    'observations', 'observations', url_prefix='/observations',
)

obs_blp.add_url_rule('/', view_func=AllObservationsView.as_view('all'))
obs_blp.add_url_rule(
    '/<uuid>', view_func=ObservationView.as_view('single'))
obs_blp.add_url_rule(
    '/<uuid>/values',
    view_func=ObservationValuesView.as_view('values'))
obs_blp.add_url_rule(
    '/<uuid>/metadata',
    view_func=ObservationMetadataView.as_view('metadata'))
