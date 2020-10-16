from flask import (Blueprint, request, jsonify, make_response, url_for,
                   current_app)
from flask.views import MethodView
from marshmallow import ValidationError
from solarforecastarbiter.io.utils import HiddenToken
from solarforecastarbiter.validation import tasks


from sfa_api import spec
from sfa_api.utils.auth import current_access_token
from sfa_api.utils.storage import get_storage
from sfa_api.utils.queuing import get_queue
from sfa_api.utils.errors import BadAPIRequest
from sfa_api.utils.request_handling import (validate_parsable_values,
                                            validate_start_end,
                                            validate_observation_values,
                                            validate_index_period)
from sfa_api.utils.validators import ALLOWED_TIMEZONES
from sfa_api.schema import (ObservationValuesSchema,
                            ObservationSchema,
                            ObservationPostSchema,
                            ObservationLinksSchema,
                            ObservationTimeRangeSchema,
                            ObservationGapSchema,
                            ObservationUnflaggedSchema,
                            ObservationUpdateSchema)


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
          description: JSON representation of an observation.
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
                  type: string
                  format: uuid
                  description: The uuid of the created observation.
            headers:
              Location:
                schema:
                  type: string
                  format: uri
                  description: Url of the created observation.
          400:
            $ref: '#/components/responses/400-BadRequest'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        data = request.get_json()
        try:
            observation = ObservationPostSchema().load(data)
        except ValidationError as err:
            raise BadAPIRequest(err.messages)
        storage = get_storage()
        observation_id = storage.store_observation(observation)
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
        return jsonify(ObservationLinksSchema().dump(observation))

    def delete(self, observation_id, *args):
        """
        ---
        summary: Delete observation.
        description: Delete an Observation, including its values and metadata.
        tags:
          - Observations
        parameters:
        - observation_id
        responses:
          204:
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
          - observation_id
          - start_time
          - end_time
          - accepts
        responses:
          200:
            description: Observation values retrieved successfully.
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
          400:
            $ref: '#/components/responses/400-TimerangeTooLarge'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        start, end = validate_start_end()
        storage = get_storage()
        values = storage.read_observation_values(observation_id, start, end)
        accepts = request.accept_mimetypes.best_match(['application/json',
                                                       'text/csv'])
        if accepts == 'application/json':
            data = ObservationValuesSchema().dump(
                {"observation_id": observation_id, "values": values})
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
        description: |
          Add new timeseries values to the Observation entry.
          Float values *will be rounded* to 8 decimal places before
          storage.
        tags:
        - Observations
        parameters:
        - observation_id
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
                  to be trusted). '#' is parsed as a comment character.
                  Values that will be interpreted as NaN include the
                  empty string, -999.0, -9999.0, 'nan', 'NaN', 'NA',
                  'N/A', 'n/a', 'null'.
              example: |-
                # comment line
                timestamp,value,quality_flag
                2018-10-29T12:00:00Z,32.93,0
                2018-10-29T13:00:00Z,25.17,0
                2018-10-29T14:00:00Z,,1  # this value is NaN
        responses:
          201:
            $ref: '#/components/responses/201-Created'
          400:
            $ref: '#/components/responses/400-BadRequest'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
          413:
            $ref: '#/components/responses/413-PayloadTooLarge'
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
        interval_length, previous_time, _ = (
            storage.read_metadata_for_observation_values(
                observation_id, observation_df.index[0])
        )
        validate_index_period(observation_df.index,
                              interval_length, previous_time)
        stored = storage.store_observation_values(
            observation_id, observation_df)
        if run_validation:
            q = get_queue()
            q.enqueue(
                tasks.fetch_and_validate_observation,
                HiddenToken(current_access_token),
                observation_id,
                observation_df.index[0].isoformat(),
                observation_df.index[-1].isoformat(),
                base_url=(current_app.config['JOB_BASE_URL']
                          or request.url_root.rstrip('/')),
                result_ttl=0,
                job_timeout=current_app.config['VALIDATION_JOB_TIMEOUT']
            )
        return stored, 201


class ObservationLatestView(MethodView):
    def get(self, observation_id, *args):
        """
        ---
        summary: Get latest Observation data.
        description: |
          Get the most recent timeseries value from the Observation
          entry.
        tags:
        - Observations
        parameters:
          - observation_id
        responses:
          200:
            description: Observation latest value retrieved successfully.
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/ObservationValues'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        storage = get_storage()
        values = storage.read_latest_observation_value(observation_id)
        data = ObservationValuesSchema().dump(
            {"observation_id": observation_id, "values": values})
        return jsonify(data)


class ObservationTimeRangeView(MethodView):
    def get(self, observation_id, *args):
        """
        ---
        summary: Get the time range of an Observation.
        description: |
          Get the minimum and maximum timestamps of Observation
          values stored in the Arbiter.
        tags:
        - Observations
        parameters:
          - observation_id
        responses:
          200:
            description: Observation time range retrieved successfully.
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/ObservationTimeRange'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        storage = get_storage()
        timerange = storage.read_observation_time_range(observation_id)
        timerange['observation_id'] = observation_id
        data = ObservationTimeRangeSchema().dump(timerange)
        return jsonify(data)


class ObservationGapView(MethodView):
    def get(self, observation_id, *args):
        """
        ---
        summary: Get the gaps in Observation data.
        description: |
          Get the timestamps indicating where gaps in Observation
          data between start and end.
        tags:
        - Observations
        parameters:
          - observation_id
          - start_time
          - end_time
        responses:
          200:
            description: Observation value gap retrieved successfully.
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/ObservationValueGap'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        start, end = validate_start_end()
        storage = get_storage()
        out = {
            'gaps': storage.find_observation_gaps(observation_id, start, end),
            'observation_id': observation_id
        }
        data = ObservationGapSchema().dump(out)
        return jsonify(data)


class ObservationUnflaggedView(MethodView):
    def get(self, observation_id, *args):
        """
        ---
        summary: Get dates where flag not present.
        description: |
          Get the dates where and Observation data is NOT
          flagged with the given flag.
        tags:
        - Observations
        parameters:
          - observation_id
          - start_time
          - end_time
          - flag
          - timezone
        responses:
          200:
            description: Unflagged observation values retrieved successfully.
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/ObservationUnflagged'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        errors = {}
        try:
            start, end = validate_start_end()
        except BadAPIRequest as err:
            errors = err.errors
        tz = request.args.get('timezone', 'UTC')
        flag = request.args.get('flag', None)
        if tz not in ALLOWED_TIMEZONES:
            errors['timezone'] = f'Unknown timezone {tz}'
        if flag is None:
            errors['flag'] = 'Must provide the flag parameter'
        else:
            try:
                int(flag)
            except ValueError:
                errors['flag'] = 'Flag must be an integer'
            else:
                if int(flag) > (2**16 - 1) or int(flag) < 0:
                    errors['flag'] = ('Flag must be a 2 byte unsigned '
                                      'integer between 0 and 65535')
        if errors:
            raise BadAPIRequest(errors)
        storage = get_storage()
        out = {
            'dates': storage.find_unflagged_observation_dates(
                observation_id, start, end, flag, tz),
            'observation_id': observation_id
        }
        data = ObservationUnflaggedSchema().dump(out)
        return jsonify(data)


class ObservationMetadataView(MethodView):
    def get(self, observation_id, *args):
        """
        ---
        summary: Get Observation metadata.
        tags:
        - Observations
        parameters:
        - observation_id
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
        return jsonify(ObservationSchema().dump(observation))

    def post(self, observation_id, *args):
        """
        ---
        summary: Update Observation metadata.
        tags:
        - Observations
        parameters:
        - observation_id
        requestBody:
          description: JSON object of observation metadata to update.
          required: True
          content:
            application/json:
                schema:
                  $ref: '#/components/schemas/ObservationUpdate'
        responses:
          200:
            description: Observation updated successfully
            content:
              application/json:
                schema:
                  type: string
                  format: uuid
                  description: The uuid of the updated observation.
            headers:
              Location:
                schema:
                  type: string
                  format: uri
                  description: Url of the updated observation.
          400:
            $ref: '#/components/responses/400-BadRequest'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        data = request.get_json()
        try:
            changes = ObservationUpdateSchema().load(data)
        except ValidationError as err:
            raise BadAPIRequest(err.messages)
        storage = get_storage()
        storage.update_observation(observation_id, **changes)
        response = make_response(observation_id, 200)
        response.headers['Location'] = url_for('observations.single',
                                               observation_id=observation_id)
        return response


# Add path parameters used by these endpoints to the spec.
spec.components.parameter(
    'observation_id', 'path',
    {
        'schema': {
            'type': 'string',
            'format': 'uuid',
        },
        'description': "Resource's unique identifier.",
        'required': 'true',
        'name': 'observation_id'
    }
)
spec.components.parameter(
    'flag', 'query',
    {
        'schema': {
            'type': 'integer',
        },
        'description': "Observation quality flag or compound quality flag",
        'required': 'true',
        'name': 'flag'
    }
)
spec.components.parameter(
    'timezone', 'query',
    {
        'schema': {
            'type': 'string',
        },
        'description': "IANA Timezone",
        'required': 'false',
        'name': 'timezone'
    }
)

obs_blp = Blueprint(
    'observations', 'observations', url_prefix='/observations',
)

obs_blp.add_url_rule('/', view_func=AllObservationsView.as_view('all'))
obs_blp.add_url_rule(
    '/<uuid_str:observation_id>', view_func=ObservationView.as_view('single'))
obs_blp.add_url_rule(
    '/<uuid_str:observation_id>/values',
    view_func=ObservationValuesView.as_view('values'))
obs_blp.add_url_rule(
    '/<uuid_str:observation_id>/values/latest',
    view_func=ObservationLatestView.as_view('latest_value'))
obs_blp.add_url_rule(
    '/<uuid_str:observation_id>/values/timerange',
    view_func=ObservationTimeRangeView.as_view('time_range'))
obs_blp.add_url_rule(
    '/<uuid_str:observation_id>/values/unflagged',
    view_func=ObservationUnflaggedView.as_view('unflagged'))
obs_blp.add_url_rule(
    '/<uuid_str:observation_id>/values/gaps',
    view_func=ObservationGapView.as_view('gaps'))
obs_blp.add_url_rule(
    '/<uuid_str:observation_id>/metadata',
    view_func=ObservationMetadataView.as_view('metadata'))
