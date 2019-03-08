from flask import Blueprint, request, jsonify, make_response, url_for, abort
from flask.views import MethodView
from io import StringIO
from marshmallow import ValidationError
import pandas as pd


from sfa_api import spec
from sfa_api.utils.storage import get_storage

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
            return jsonify({'errors': err.messages}), 400
        storage = get_storage()
        obs_id = storage.store_observation(observation)
        if obs_id is None:
            return jsonify({'errors': 'Site does not exist'}), 400
        response = make_response(obs_id, 201)
        response.headers['Location'] = url_for('observations.single',
                                               obs_id=obs_id)
        return response


class ObservationView(MethodView):
    def get(self, obs_id, **kwargs):
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
        observation = storage.read_observation(obs_id)
        if observation is None:
            abort(404)
        return jsonify(ObservationLinksSchema().dump(observation))

    def delete(self, obs_id, *args):
        """
        ---
        summary: Delete observation.
        description: Delete an Observation, including its values and metadata.
        tags:
          - Observations
        parameters:
        - $ref: '#/components/parameters/obs_id'
        responses:
          200:
            description: Observation deleted successfully.
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        storage = get_storage()
        deletion_result = storage.delete_observation(obs_id)
        return deletion_result


class ObservationValuesView(MethodView):
    def get(self, obs_id, *args):
        """
        ---
        summary: Get Observation data.
        description: Get the timeseries values from the Observation entry.
        tags:
        - Observations
        parameters:
          - $ref: '#/components/parameters/obs_id'
          - $ref: '#/components/parameters/start_time'
          - $ref: '#/components/parameters/end_time'
          - $ref: '#/components/parameters/accepts'
        responses:
          200:
            content:
              application/json:
                schema:
                  type: array
                  items:
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
        errors = []
        start = request.args.get('start', None)
        end = request.args.get('end', None)
        if start is not None:
            try:
                start = pd.Timestamp(start)
            except ValueError:
                errors.append('Invalid start date format')
        if end is not None:
            try:
                end = pd.Timestamp(end)
            except ValueError:
                errors.append('Invalid end date format')
        if errors:
            return jsonify({'errors': errors}), 400
        storage = get_storage()
        values = storage.read_observation_values(obs_id, start, end)
        if values is None:
            abort(404)
        data = ObservationValuesSchema().dump({"obs_id": obs_id,
                                               "values":values})
        accepts = request.accept_mimetypes.best_match(['application/json',
                                                       'text/csv'])
        if accepts == 'application/json':
            return jsonify(data)
        else:
            csv_data = pd.DataFrame(data).to_csv(index=False)
            response = make_response(csv_data, 200)
            response.mimetype = 'text/csv'
            return response

    def post(self, obs_id, *args):
        """
        ---
        summary: Add Observation data.
        description: Add new timeseries values to the Observation entry.
        tags:
        - Observations
        parameters:
        - $ref: '#/components/parameters/obs_id'
        requestBody:
          required: True
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ObservationValues'
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
        # Check content-type and parse data conditionally
        if request.content_type == 'application/json':
            raw_data = request.get_json()
            try:
                raw_values = raw_data['values']
            except (TypeError, KeyError):
                return 'Supplied JSON does not contain "values" field.', 400
            try:
                observation_df = pd.DataFrame(raw_values)
            except ValueError:
                return 'Malformed JSON', 400
        elif request.content_type == 'text/csv':
            raw_data = StringIO(request.get_data(as_text=True))
            try:
                observation_df = pd.read_csv(raw_data, comment='#')
            except pd.errors.EmptyDataError:
                return 'Malformed CSV', 400
            raw_data.close()
        else:
            return 'Invalid Content-type.', 400

        # Verify data format and types are parseable.
        # create list of errors to return meaningful messages to the user.
        errors = []
        try:
            observation_df['value'] = pd.to_numeric(observation_df['value'],
                                                    downcast='float')
        except ValueError:
            errors.append('Invalid item in "value" field.')
        except KeyError:
            errors.append('Missing "value" field.')

        try:
            observation_df['timestamp'] = pd.to_datetime(
                observation_df['timestamp'],
                utc=True)
        except ValueError:
            errors.append('Invalid item in "timestamp" field.')
        except KeyError:
            errors.append('Missing "timestamp" field.')

        if 'quality_flag' not in observation_df.columns:
            errors.append('Missing "quality_flag" field.')
        elif not observation_df['quality_flag'].isin([0, 1]).all():
            errors.append('Invalid item in "quality_flag" field.')

        if errors:
            return jsonify({'errors': errors}), 400
        index = observation_df['timestamp'].copy()
        observation_df = observation_df.set_index(index)
        storage = get_storage()
        stored = storage.store_observation_values(obs_id, observation_df)
        if stored is None:
            abort(404)
        return stored, 201


class ObservationMetadataView(MethodView):
    def get(self, obs_id, *args):
        """
        ---
        summary: Get Observation metadata.
        tags:
        - Observations
        parameters:
        - $ref: '#/components/parameters/obs_id'
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
        observation = storage.read_observation(obs_id)
        if observation is None:
            abort(404)
        return jsonify(ObservationSchema().dump(observation))


# Add path parameters used by these endpoints to the spec.
spec.components.parameter(
    'obs_id', 'path',
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
    '/<obs_id>', view_func=ObservationView.as_view('single'))
obs_blp.add_url_rule(
    '/<obs_id>/values',
    view_func=ObservationValuesView.as_view('values'))
obs_blp.add_url_rule(
    '/<obs_id>/metadata',
    view_func=ObservationMetadataView.as_view('metadata'))
