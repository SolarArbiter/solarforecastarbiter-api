from flask import Blueprint, request, jsonify, make_response, url_for, abort
from flask.views import MethodView
from marshmallow import ValidationError
from solarforecastarbiter.io.utils import HiddenToken
from solarforecastarbiter.validation import tasks


from sfa_api import spec
from sfa_api.utils.auth import current_access_token
from sfa_api.utils.storage import get_storage
from sfa_api.utils.queuing import get_queue
from sfa_api.utils.errors import BadAPIRequest, NotFoundException
from sfa_api.utils.request_handling import (validate_parsable_values,
                                            validate_start_end,
                                            validate_observation_values,
                                            validate_index_period)
from sfa_api.schema import (ObservationValuesSchema,
                            ObservationSchema,
                            ObservationPostSchema,
                            ObservationLinksSchema)


class AllObservationsView(MethodView):
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
        storage = get_storage()
        observations = storage.list_observations()
        return jsonify(ObservationSchema(many=True).dump(observations))

    def post(self, *args):
        """
        ---
        summary: Create observation.
        tags:
          - Observations
        description: >-
          Create a new Observation by posting metadata. Note that POST
          requests to this endpoint without a trailing slash will result
          in a redirect response.
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
        data = request.get_json()
        try:
            observation = ObservationPostSchema().load(data)
        except ValidationError as err:
            raise BadAPIRequest(err.messages)
        storage = get_storage()
        observation_id = storage.store_observation(observation)
        if observation_id is None:
            raise NotFoundException(error='Site does not exist')
        response = make_response(observation_id, 201)
        response.headers['Location'] = url_for('observations.single',
                                               observation_id=observation_id)
        return response


class ObservationView(MethodView):
    def get(self, observation_id, **kwargs):
        """
        ---
        summary: Get Observation options.
        description: List options available for Observation.
        tags:
          - Observations
        responses:
          200:
            description: Observation options retrieved successfully.
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/ObservationLinks'
          400:
            $ref: '#/components/responses/400-BadRequest'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        storage = get_storage()
        observation = storage.read_observation(observation_id)
        if observation is None:
            abort(404)
        return jsonify(ObservationLinksSchema().dump(observation))

    def delete(self, observation_id, *args):
        """
        ---
        summary: Delete observation.
        description: Delete an Observation, including its values and metadata.
        tags:
          - Observations
        parameters:
        - $ref: '#/components/parameters/observation_id'
        responses:
          200:
            description: Observation deleted successfully.
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        storage = get_storage()
        storage.delete_observation(observation_id)
        return '', 204


class ObservationValuesView(MethodView):
    def get(self, observation_id, *args):
        """
        ---
        summary: Get Observation data.
        description: Get the timeseries values from the Observation entry.
        tags:
        - Observations
        parameters:
          - $ref: '#/components/parameters/observation_id'
          - $ref: '#/components/parameters/start_time'
          - $ref: '#/components/parameters/end_time'
          - $ref: '#/components/parameters/accepts'
        responses:
          200:
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/ObservationValues'
              text/csv:
                schema:
                  type: string
                example: |-
                  timestamp,value,quality_flag
                  2018-10-29T12:00:00Z,32.93,0
                  2018-10-29T13:00:00Z,25.17,0

          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        start, end = validate_start_end()
        storage = get_storage()
        values = storage.read_observation_values(observation_id, start, end)
        if values is None:
            abort(404)
        accepts = request.accept_mimetypes.best_match(['application/json',
                                                       'text/csv'])
        if accepts == 'application/json':
            values['timestamp'] = values.index
            dict_values = values.to_dict(orient='records')
            data = ObservationValuesSchema().dump(
                {"observation_id": observation_id, "values": dict_values})

            return jsonify(data)
        else:
            meta_url = url_for('observations.metadata',
                               observation_id=observation_id,
                               _external=True)
            csv_header = f'# observation_id: {observation_id}\n# metadata: {meta_url}\n'  # NOQA
            csv_values = values.to_csv(columns=['value', 'quality_flag'],
                                       index_label='timestamp',
                                       date_format='%Y%m%dT%H:%M:%S%z')
            csv_data = csv_header + csv_values
            response = make_response(csv_data, 200)
            response.mimetype = 'text/csv'
            return response

    def post(self, observation_id, *args):
        """
        ---
        summary: Add Observation data.
        description: Add new timeseries values to the Observation entry.
        tags:
        - Observations
        parameters:
        - $ref: '#/components/parameters/observation_id'
        requestBody:
          required: True
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ObservationValuesPost'
            text/csv:
              schema:
                type: string
                description: |
                  Text file with fields separated by ',' and
                  lines separated by '\\n'. The first line must
                  be a header with the following fields:
                  timestamp, value, quality_flag. Timestamp must be
                  an ISO 8601 datetime, value may be an integer or float,
                  quality_flag may be 0 or 1 (indicating the value is not
                  to be trusted).
              example: |-
                timestamp,value,quality_flag
                2018-10-29T12:00:00Z,32.93,0
                2018-10-29T13:00:00Z,25.17,0
        responses:
          201:
            $ref: '#/components/responses/201-Created'
          400:
            $ref: '#/components/responses/400-BadRequest'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        run_validation = 'donotvalidate' not in request.args
        if run_validation:
            # users should only upload 0 or 1 for quality_flag
            qf_range = [0, 1]
        else:
            # but the validation task will post the quality flag
            # up a 2 byte unsigned int
            qf_range = [0, 2**16 - 1]

        observation_df = validate_observation_values(
            validate_parsable_values(), qf_range)
        observation_df = observation_df.set_index('timestamp')
        storage = get_storage()
        observation = storage.read_observation(observation_id)
        validate_index_period(observation_df.index,
                              observation['interval_length'])
        stored = storage.store_observation_values(
            observation_id, observation_df)
        if stored is None:
            abort(404)
        if run_validation:
            q = get_queue()
            q.enqueue(
                tasks.immediate_observation_validation,
                HiddenToken(current_access_token),
                observation_id,
                observation_df.index[0].isoformat(),
                observation_df.index[-1].isoformat(),
                base_url=request.url_root.rstrip('/'))
        return stored, 201


class ObservationMetadataView(MethodView):
    def get(self, observation_id, *args):
        """
        ---
        summary: Get Observation metadata.
        tags:
        - Observations
        parameters:
        - $ref: '#/components/parameters/observation_id'
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
        storage = get_storage()
        observation = storage.read_observation(observation_id)
        if observation is None:
            abort(404)
        return jsonify(ObservationSchema().dump(observation))


# Add path parameters used by these endpoints to the spec.
spec.components.parameter(
    'observation_id', 'path',
    {
        'schema': {
            'type': 'string',
            'format': 'uuid',
        },
        'description': "Resource's unique identifier.",
        'required': 'true'
    })

obs_blp = Blueprint(
    'observations', 'observations', url_prefix='/observations',
)

obs_blp.add_url_rule('/', view_func=AllObservationsView.as_view('all'))
obs_blp.add_url_rule(
    '/<observation_id>', view_func=ObservationView.as_view('single'))
obs_blp.add_url_rule(
    '/<observation_id>/values',
    view_func=ObservationValuesView.as_view('values'))
obs_blp.add_url_rule(
    '/<observation_id>/metadata',
    view_func=ObservationMetadataView.as_view('metadata'))
