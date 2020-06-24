from functools import partial

from flask import Blueprint, request, jsonify, make_response, url_for
from flask.views import MethodView
from marshmallow import ValidationError


from sfa_api import spec
from sfa_api.schema import (ForecastValuesSchema,
                            ForecastSchema,
                            ForecastPostSchema,
                            ForecastLinksSchema,
                            ForecastTimeRangeSchema,
                            CDFForecastGroupPostSchema,
                            CDFForecastGroupSchema,
                            CDFForecastSchema,
                            CDFForecastValuesSchema,
                            CDFForecastTimeRangeSchema,
                            ForecastGapSchema,
                            CDFForecastGapSchema,
                            CDFGroupForecastGapSchema)

from sfa_api.utils.errors import BadAPIRequest
from sfa_api.utils.storage import get_storage
from sfa_api.utils.request_handling import (validate_parsable_values,
                                            validate_start_end,
                                            validate_index_period,
                                            validate_forecast_values,
                                            restrict_forecast_upload_window)


class AllForecastsView(MethodView):
    def get(self, *args):
        """
        ---
        summary: List forecasts
        tags:
        - Forecasts
        responses:
          200:
            description:
            content:
              application/json:
                schema:
                  type: array
                  items:
                    $ref: '#/components/schemas/ForecastMetadata'
          401:
            $ref: '#/components/responses/401-Unauthorized'
        """
        storage = get_storage()
        forecasts = storage.list_forecasts()
        return jsonify(ForecastSchema(many=True).dump(forecasts))

    def post(self, *args):
        """
        ---
        summary: Create Forecast
        tags:
        - Forecasts
        description: >-
          Create a new Forecast by posting metadata. Note that POST
          requests to this endpoint without a trailing slash will
          result in a redirect response.
        requestBody:
          desctiption: JSON representation of a forecast.
          required: True
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ForecastDefinition'
        responses:
          201:
            description: Forecast created successfully
            content:
              application/json:
                schema:
                  type: string
                  format: uuid
                  description: The uuid of the created forecast.
            headers:
              Location:
                schema:
                  type: string
                  format: uri
                  description: Url of the created forecast.
          400:
            $ref: '#/components/responses/400-BadRequest'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        data = request.get_json()
        try:
            forecast = ForecastPostSchema().load(data)
        except ValidationError as err:
            raise BadAPIRequest(err.messages)
        else:
            storage = get_storage()
            forecast_id = storage.store_forecast(forecast)
            response = make_response(forecast_id, 201)
            response.headers['Location'] = url_for('forecasts.single',
                                                   forecast_id=forecast_id)
            return response


class ForecastView(MethodView):
    def get(self, forecast_id, *args):
        """
        ---
        summary: Get Forecast options
        description: List options available for Forecast.
        tags:
        - Forecasts
        parameters:
        - forecast_id
        responses:
          200:
            description: Forecast options retrieved sucessfully.
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/ForecastLinks'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        storage = get_storage()
        forecast = storage.read_forecast(forecast_id)
        return jsonify(ForecastLinksSchema().dump(forecast))

    def delete(self, forecast_id, *args):
        """
        ---
        summary: Delete forecast
        description: Delete a Forecast, including its values and metadata.
        tags:
        - Forecasts
        parameters:
        - forecast_id
        responses:
          200:
            description: Forecast deleted sucessfully.
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        storage = get_storage()
        storage.delete_forecast(forecast_id)
        return '', 204


class ForecastValuesView(MethodView):
    def get(self, forecast_id, *args):
        """
        ---
        summary: Get Forecast data
        description: Get the timeseries values from the Forecast entry.
        tags:
        - Forecasts
        parameters:
        - forecast_id
        - start_time
        - end_time
        - accepts
        responses:
          200:
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/ForecastValues'
              text/csv:
                schema:
                  type: string
                example: |-
                  timestamp,value
                  2018-10-29T12:00:00Z,32.93
                  2018-10-29T13:00:00Z,25.17
          400:
            $ref: '#/components/responses/400-TimerangeTooLarge'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        start, end = validate_start_end()
        storage = get_storage()
        values = storage.read_forecast_values(forecast_id, start, end)
        accepts = request.accept_mimetypes.best_match(['application/json',
                                                       'text/csv'])
        if accepts == 'application/json':
            data = ForecastValuesSchema().dump({"forecast_id": forecast_id,
                                                "values": values})
            return jsonify(data)
        else:
            meta_url = url_for('forecasts.metadata',
                               forecast_id=forecast_id,
                               _external=True)
            csv_header = (f'# forecast_id: {forecast_id}\n'
                          f'# metadata: {meta_url}\n')
            csv_values = values.to_csv(date_format='%Y%m%dT%H:%M:%S%z')
            csv_data = csv_header + csv_values
            response = make_response(csv_data, 200)
            response.mimetype = 'text/csv'
            return response

    def post(self, forecast_id, *args):
        """
        ---
        summary: Add Forecast data
        description: |
          Add new timeseries values to Forecast entry.
          Float values *will be rounded* to 8 decimal places before
          storage.
        tags:
        - Forecasts
        parameters:
        - forecast_id
        requestBody:
          required: True
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ForecastValuesPost'
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
                timestamp,value
                2018-10-29T12:00:00Z,32.93
                2018-10-29T13:00:00Z,25.17
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
        forecast_df = validate_parsable_values()
        validate_forecast_values(forecast_df)
        forecast_df = forecast_df.set_index('timestamp').sort_index()
        storage = get_storage()
        interval_length, previous_time, extra_params = (
            storage.read_metadata_for_forecast_values(
                forecast_id, forecast_df.index[0])
        )
        restrict_forecast_upload_window(
            extra_params, partial(storage.read_forecast, forecast_id),
            forecast_df.index[0]
        )
        validate_index_period(forecast_df.index, interval_length,
                              previous_time)
        stored = storage.store_forecast_values(forecast_id, forecast_df)
        return stored, 201


class ForecastLatestView(MethodView):
    def get(self, forecast_id, *args):
        """
        ---
        summary: Get latest Forecast data.
        description: |
          Get the most recent timeseries value from the Forecast
          entry.
        tags:
        - Forecasts
        parameters:
          - forecast_id
        responses:
          200:
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/ForecastValues'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        storage = get_storage()
        values = storage.read_latest_forecast_value(forecast_id)
        data = ForecastValuesSchema().dump(
            {"forecast_id": forecast_id, "values": values})
        return jsonify(data)


class ForecastTimeRangeView(MethodView):
    def get(self, forecast_id, *args):
        """
        ---
        summary: Get the time range of an Forecast.
        description: |
          Get the minimum and maximum timestamps of Forecast
          values stored in the Arbiter.
        tags:
        - Forecasts
        parameters:
          - forecast_id
        responses:
          200:
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/ForecastTimeRange'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        storage = get_storage()
        timerange = storage.read_forecast_time_range(forecast_id)
        timerange['forecast_id'] = forecast_id
        data = ForecastTimeRangeSchema().dump(timerange)
        return jsonify(data)


class ForecastGapView(MethodView):
    def get(self, forecast_id, *args):
        """
        ---
        summary: Get the gaps in Forecast data.
        description: |
          Get the timestamps indicating where gaps in Forecast
          data between start and end.
        tags:
        - Forecasts
        parameters:
          - forecast_id
          - start_time
          - end_time
        responses:
          200:
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/ForecastValueGap'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        start, end = validate_start_end()
        storage = get_storage()
        out = {'gaps': storage.find_forecast_gaps(forecast_id, start, end),
               'forecast_id': forecast_id}
        data = ForecastGapSchema().dump(out)
        return jsonify(data)


class ForecastMetadataView(MethodView):
    def get(self, forecast_id, *args):
        """
        ---
        summary: Get Forecast metadata
        tags:
        - Forecasts
        parameters:
        - forecast_id
        responses:
          200:
            description: Successfully retrieved Forecasts.
            content:
              application/json:
                schema:
                  type: array
                  items:
                    $ref: '#/components/schemas/ForecastMetadata'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        storage = get_storage()
        forecast = storage.read_forecast(forecast_id)
        return jsonify(ForecastSchema().dump(forecast))


class AllCDFForecastGroupsView(MethodView):
    def get(self, *args):
        """
        ---
        summary: List Probabilistic Forecasts groups.
        description: List all probabilistic forecasts a user has access to.
        tags:
          - Probabilistic Forecasts
        responses:
          200:
            description: A list of probabilistic forecasts
            content:
              application/json:
                schema:
                  type: array
                  items:
                    $ref: '#/components/schemas/CDFForecastGroupMetadata'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        storage = get_storage()
        cdf_forecast_groups = storage.list_cdf_forecast_groups()
        return jsonify(
            CDFForecastGroupSchema(many=True).dump(cdf_forecast_groups)
        )

    def post(self, *args):
        """
        ---
        summary: Create Probabilistic Forecast group.
        tags:
          - Probabilistic Forecasts
        description: >-
          Create a new Probabilistic Forecast by posting metadata.
          Note that POST requests to this endpoint without a trailing
          slash will result in a redirect response.
        requestBody:
          desctiption: JSON representation of a probabilistic forecast.
          required: True
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CDFForecastGroupDefinition'
        responses:
          201:
            description: Probabilistic forecast created successfully
            content:
              application/json:
                schema:
                  type: string
                  format: uuid
                  description: The uuid of the created probabilistic forecast.
            headers:
              Location:
                schema:
                  type: string
                  format: uri
                  description: Url of the created probabilistic forecast.
          400:
            $ref: '#/components/responses/400-BadRequest'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        data = request.get_json()
        try:
            cdf_forecast_group = CDFForecastGroupPostSchema().load(data)
        except ValidationError as err:
            raise BadAPIRequest(err.messages)
        else:
            storage = get_storage()
            forecast_id = storage.store_cdf_forecast_group(cdf_forecast_group)
            response = make_response(forecast_id, 201)
            response.headers['Location'] = url_for(
                'forecasts.single_cdf_group',
                forecast_id=forecast_id)
            return response


class CDFForecastGroupMetadataView(MethodView):
    def get(self, forecast_id, *args):
        """
        ---
        summary: Get Probabilistic Forecast group Metadata.
        tags:
          - Probabilistic Forecasts
        parameters:
        - forecast_id
        responses:
          200:
            description: Successfully retrieved Forecasts.
            content:
              application/json:
                schema:
                  type: array
                  items:
                    $ref: '#/components/schemas/CDFForecastGroupMetadata'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        storage = get_storage()
        cdf_forecast_group = storage.read_cdf_forecast_group(forecast_id)
        return jsonify(CDFForecastGroupSchema().dump(cdf_forecast_group))

    def delete(self, forecast_id, *args):
        """
        ---
        summary: Delete Probabilistic Forecast group.
        description: >-
          Delete a Probabilistic Forecast group, including its constant
          values and metadata.
        tags:
        - Probabilistic Forecasts
        parameters:
        - forecast_id
        responses:
          200:
            description: Forecast deleted sucessfully.
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        storage = get_storage()
        storage.delete_cdf_forecast_group(forecast_id)
        return '', 204


class CDFForecastMetadata(MethodView):
    def get(self, forecast_id):
        """
        ---
        summary: Get Metadata for one Probabilistic Forecast constant value.
        tags:
          - Probabilistic Forecasts
        parameters:
        - forecast_id
        responses:
          200:
            description: Successfully retrieved Forecast CDF metadata.
            content:
              application/json:
                schema:
                  type: array
                  items:
                    $ref: '#/components/schemas/CDFForecastMetadata'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        storage = get_storage()
        cdf_forecast = storage.read_cdf_forecast(forecast_id)
        return jsonify(CDFForecastSchema().dump(cdf_forecast))


class CDFForecastValues(MethodView):
    def get(self, forecast_id):
        """
        ---
        summary: Get Probabilistic Forecast data for one constant value.
        tags:
          - Probabilistic Forecasts
        responses:
          200:
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/CDFForecastValues'
              text/csv:
                schema:
                  type: string
                example: |-
                  timestamp,value
                  2018-10-29T12:00:00Z,32.93
                  2018-10-29T13:00:00Z,25.17
          400:
            $ref: '#/components/responses/400-TimerangeTooLarge'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        start, end = validate_start_end()
        storage = get_storage()
        values = storage.read_cdf_forecast_values(forecast_id, start, end)
        accepts = request.accept_mimetypes.best_match(['application/json',
                                                       'text/csv'])
        if accepts == 'application/json':
            data = CDFForecastValuesSchema().dump({"forecast_id": forecast_id,
                                                   "values": values})
            return jsonify(data)
        else:
            meta_url = url_for('forecasts.single_cdf_metadata',
                               forecast_id=forecast_id,
                               _external=True)
            csv_header = (f'# forecast_id: {forecast_id}\n'
                          f'# metadata: {meta_url}\n')
            csv_values = values.to_csv(date_format='%Y%m%dT%H:%M:%S%z')
            csv_data = csv_header + csv_values
            response = make_response(csv_data, 200)
            response.mimetype = 'text/csv'
            return response

    def post(self, forecast_id):
        """
        ---
        summary: Add Probabilistic Forecast data for one constant value.
        description: |
          Add timeseries values to a Probabilistic Forecast constant value.
          Float values *will be rounded* to 8 decimal places before
          storage.
        tags:
        - Probabilistic Forecasts
        parameters:
        - forecast_id
        requestBody:
          required: True
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ForecastValuesPost'
            text/csv:
              schema:
                type: string
                description: |
                  Text file with fields separated by ',' and
                  lines separated by '\\n'. The first line must
                  be a header with the following fields: timestamp,
                  value. Timestamp must be an ISO 8601 datetime and
                  value may be an integer or floatquality_flag.
              example: |-
                timestamp,value
                2018-10-29T12:00:00Z,32.93
                2018-10-29T13:00:00Z,25.17
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
        forecast_df = validate_parsable_values()
        validate_forecast_values(forecast_df)
        forecast_df = forecast_df.set_index('timestamp').sort_index()
        storage = get_storage()
        interval_length, previous_time, extra_params = (
            storage.read_metadata_for_cdf_forecast_values(
                forecast_id, forecast_df.index[0])
        )
        restrict_forecast_upload_window(
            extra_params, partial(storage.read_cdf_forecast, forecast_id),
            forecast_df.index[0]
        )
        validate_index_period(forecast_df.index, interval_length,
                              previous_time)
        stored = storage.store_cdf_forecast_values(forecast_id, forecast_df)
        return stored, 201


class CDFForecastLatestView(MethodView):
    def get(self, forecast_id, *args):
        """
        ---
        summary: Get latest Probabilistic Forecast value.
        description: |
          Get the most recent timeseries value for one constant value
          from the Probabilistic Forecast entry.
        tags:
          - Probabilistic Forecasts
        parameters:
          - forecast_id
        responses:
          200:
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/CDFForecastValues'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        storage = get_storage()
        values = storage.read_latest_cdf_forecast_value(forecast_id)
        data = CDFForecastValuesSchema().dump(
            {"forecast_id": forecast_id, "values": values})
        return jsonify(data)


class CDFForecastTimeRangeView(MethodView):
    def get(self, forecast_id, *args):
        """
        ---
        summary: Get the time range of an Probabilistic Forecast.
        description: |
          Get the minimum and maximum timestamps for one constant value
          of a Probabilistic Forecast values stored in the Arbiter.
        tags:
        - Probabilistic Forecasts
        parameters:
          - forecast_id
        responses:
          200:
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/CDFForecastTimeRange'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        storage = get_storage()
        timerange = storage.read_cdf_forecast_time_range(forecast_id)
        timerange['forecast_id'] = forecast_id
        data = CDFForecastTimeRangeSchema().dump(timerange)
        return jsonify(data)


class CDFForecastGapView(MethodView):
    def get(self, forecast_id, *args):
        """
        ---
        summary: Get the gaps in Probabilistic Forecast
        description: |
          Get the timestamps indicating where gaps in the data
          of one constant value from the probabilistic forecast
          between start and end.
        tags:
        - Probabilistic Forecasts
        parameters:
          - forecast_id
          - start_time
          - end_time
        responses:
          200:
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/CDFForecastValueGap'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        start, end = validate_start_end()
        storage = get_storage()
        out = {'gaps': storage.find_cdf_forecast_gaps(forecast_id, start, end),
               'forecast_id': forecast_id}
        data = CDFForecastGapSchema().dump(out)
        return jsonify(data)


class CDFGroupForecastGapView(MethodView):
    def get(self, forecast_id, *args):
        """
        ---
        summary: Get the gaps in Probabilistic Forecast Group
        description: |
          Get the timestamps indicating where gaps in the data
          for all constant values of a Probabilistic Forecast
          group between start and end.
        tags:
        - Probabilistic Forecasts
        parameters:
          - forecast_id
          - start_time
          - end_time
        responses:
          200:
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/CDFGroupForecastValueGap'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        start, end = validate_start_end()
        storage = get_storage()
        out = {'gaps': storage.find_cdf_forecast_group_gaps(
            forecast_id, start, end),
               'forecast_id': forecast_id}
        data = CDFGroupForecastGapSchema().dump(out)
        return jsonify(data)


spec.components.parameter(
    'forecast_id', 'path',
    {
        'schema': {
            'type': 'string',
            'format': 'uuid'
        },
        'description': "Forecast's unique identifier.",
        'name': 'forecast_id',
        'required': 'true'
    })

forecast_blp = Blueprint(
    'forecasts', 'forecasts', url_prefix="/forecasts",
)
forecast_blp.add_url_rule(
    '/single/',
    view_func=AllForecastsView.as_view('all'))
forecast_blp.add_url_rule(
    '/single/<uuid_str:forecast_id>',
    view_func=ForecastView.as_view('single'))
forecast_blp.add_url_rule(
    '/single/<uuid_str:forecast_id>/values',
    view_func=ForecastValuesView.as_view('values'))
forecast_blp.add_url_rule(
    '/single/<uuid_str:forecast_id>/values/latest',
    view_func=ForecastLatestView.as_view('latest_value'))
forecast_blp.add_url_rule(
    '/single/<uuid_str:forecast_id>/values/timerange',
    view_func=ForecastTimeRangeView.as_view('time_range'))
forecast_blp.add_url_rule(
    '/single/<uuid_str:forecast_id>/values/gaps',
    view_func=ForecastGapView.as_view('gaps'))
forecast_blp.add_url_rule(
    '/single/<uuid_str:forecast_id>/metadata',
    view_func=ForecastMetadataView.as_view('metadata'))

forecast_blp.add_url_rule(
    '/cdf/',
    view_func=AllCDFForecastGroupsView.as_view('all_cdf_groups'))
forecast_blp.add_url_rule(
    '/cdf/<uuid_str:forecast_id>',
    view_func=CDFForecastGroupMetadataView.as_view('single_cdf_group'))
forecast_blp.add_url_rule(
    '/cdf/<uuid_str:forecast_id>/values/gaps',
    view_func=CDFGroupForecastGapView.as_view('cdf_group_gaps'))
forecast_blp.add_url_rule(
    '/cdf/single/<uuid_str:forecast_id>',
    view_func=CDFForecastMetadata.as_view('single_cdf_metadata'))
forecast_blp.add_url_rule(
    '/cdf/single/<uuid_str:forecast_id>/values',
    view_func=CDFForecastValues.as_view('single_cdf_value'))
forecast_blp.add_url_rule(
    '/cdf/single/<uuid_str:forecast_id>/values/latest',
    view_func=CDFForecastLatestView.as_view('cdf_latest_value'))
forecast_blp.add_url_rule(
    '/cdf/single/<uuid_str:forecast_id>/values/timerange',
    view_func=CDFForecastTimeRangeView.as_view('cdf_time_range'))
forecast_blp.add_url_rule(
    '/cdf/single/<uuid_str:forecast_id>/values/gaps',
    view_func=CDFForecastGapView.as_view('cdf_gaps'))
