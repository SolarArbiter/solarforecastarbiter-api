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
                                            validate_index_period,
                                            validate_event_data)
from sfa_api.utils.validators import ALLOWED_TIMEZONES
from sfa_api.schema import (ObservationValuesSchema,
                            ObservationSchema,
                            ObservationPostSchema,
                            ObservationLinksSchema,
                            ObservationTimeRangeSchema,
                            ObservationGapSchema,
                            ObservationUnflaggedSchema,
                            ObservationUpdateSchema)


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
        interval_length, previous_time, _, is_event = (
            storage.read_metadata_for_observation_values(
                observation_id, observation_df.index[0])
        )
        validate_index_period(observation_df.index,
                              interval_length, previous_time)
        if is_event:
            validate_event_data(observation_df)
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


class OutagePing(MethodView):
    def get(self, observation_id, *args):
        """Endpoint that accepts an external connection to keep track of
        outages. Compares current timestamp to the last successful connection
        and stored outage series between the two if longer than one minute.
        """
        # Get the timestamp of the current connection.
        current_connection_time = pd.Timestamp.utcnow()

        storage = get_storage()
        
        last_connection_time = storage.read_latest_successful_connection()
        
        outage_threshold = pd.Timedelta('1T')

        if current_connection_time - last_connection_time > outage_threshold:
            storagelast_connection_time, current_connection_time)
        values = storage.read_latest_observation_value(observation_id)
        data = ObservationValuesSchema().dump(
            {"observation_id": observation_id, "values": values})
        return jsonify(data)


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
