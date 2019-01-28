from flask import Blueprint, request, jsonify
from flask.views import MethodView
from io import StringIO
import pandas as pd


from sfa_api import spec
from sfa_api.utils import storage
from sfa_api.schema import (ObservationSchema, ObservationLinksSchema,
                            ObservationValueSchema)

from sfa_api.demo import Observation, TimeseriesValue


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
        # TODO: replace demo response, also do not allow top-level json array
        observations = [Observation() for i in range(5)]
        return ObservationSchema().jsonify(observations)

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
        # TODO: Authorization/Authentication

        observation = request.get_json()
        ObservationSchema.load(observation)
        return '', 400
        return '', 201



class ObservationView(MethodView):
    def get(self, obs_id, **kwargs):
        """
        ---
        summary: Get Observation options.
        description: List options available for Observation.
        tags:
          - Observations
        parameters:
          - $ref: '#/components/parameters/obs_id'
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
        return ObservationLinksSchema().jsonify(Observation())

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
        # TODO: replace demo response
        return f'{obs_id} deleted.'


class ObservationValuesView(MethodView):
    def get(self, obs_id, *args):
        """
        TODO: Limits???
        ---
        summary: Get Observation data.
        description: Get the timeseries values from the Observation entry.
        tags:
        - Observations
        parameters:
          - $ref: '#/components/parameters/obs_id'
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
        values = [TimeseriesValue() for i in range(5)]
        return ObservationValueSchema(many=True).jsonify(values)

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
          400:
            $ref: '#/components/responses/400-BadRequest'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        # TODO: Authorize User for this observation

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
                return 'Malformed JSON', 400
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

        if 'questionable' not in observation_df.columns:
            errors.append('Missing "questionable" field.')
        elif not observation_df['questionable'].isin([0, 1]).all():
            errors.append('Invalid item in "questionable" field.')

        if errors:
            return jsonify({'errors': errors}), 400

        stored = storage.store_observation_values(obs_id, observation_df)
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
        return ObservationSchema().jsonify(Observation())

    def put(self, obs_id, *args):
        """
        TODO: MAY NOT MAKE SENSE TO KEEP if schema is so simple
        ---
        summary: Update observation metadata.
        description: Update an observation's metadata.
        tags:
          - Observations
        parameters:
          - $ref: '#/components/parameters/obs_id'
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
spec.add_parameter('obs_id', 'path',
                   schema={
                       'type': 'string',
                       'format': 'uuid'
                   },
                   description="Resource's unique identifier.",
                   required='true')

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
