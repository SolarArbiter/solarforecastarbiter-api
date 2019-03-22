from flask import Blueprint, request, jsonify, make_response, url_for, abort
from flask.views import MethodView
from io import StringIO
from marshmallow import ValidationError
import pandas as pd


from sfa_api import spec
from sfa_api.schema import (ForecastValuesSchema,
                            ForecastSchema,
                            ForecastPostSchema,
                            ForecastLinksSchema)

from sfa_api.utils.storage import get_storage


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
          desctiption: JSON representation of an observation.
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
                  $ref: '#/components/schemas/ForecastMetadata'
          400:
            $ref: '#/components/responses/400-BadRequest'
          401:
            $ref: '#/components/responses/401-Unauthorized'
        """
        data = request.get_json()
        try:
            forecast = ForecastPostSchema().load(data)
        except ValidationError as err:
            return jsonify({"errors": err.messages}), 400
        else:
            storage = get_storage()
            forecast_id = storage.store_forecast(forecast)
            if forecast_id is None:
                return jsonify({'errors': 'Site does not exist'}), 400
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
        - $ref: '#/components/parameters/forecast_id'
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
        if forecast is None:
            abort(404)
        return jsonify(ForecastLinksSchema().dump(forecast))

    def delete(self, forecast_id, *args):
        """
        ---
        summary: Delete forecast
        description: Delete a Forecast, including its values and metadata.
        tags:
        - Forecasts
        parameters:
        - $ref: '#/components/parameters/forecast_id'
        responses:
          200:
            description: Forecast deleted sucessfully.
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        storage = get_storage()
        deletion_result = storage.delete_forecast(forecast_id)
        return deletion_result


class ForecastValuesView(MethodView):
    def get(self, forecast_id, *args):
        """
        ---
        summary: Get Forecast data
        description: Get the timeseries values from the Forecast entry.
        tags:
        - Forecasts
        parameters:
        - $ref: '#/components/parameters/forecast_id'
        - $ref: '#/components/parameters/start_time'
        - $ref: '#/components/parameters/end_time'
        - $ref: '#/components/parameters/accepts'
        responses:
          200:
            content:
              applciation/json:
                schema:
                  type: array
                  items:
                    $ref: '#/components/schemas/ForecastValue'
              text/csv:
                schema:
                  type: string
                example: |-
                  timestamp,value
                  2018-10-29T12:00:00Z,32.93
                  2018-10-29T13:00:00Z,25.17
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        errors = {}
        start = request.args.get('start', None)
        end = request.args.get('end', None)
        if start is not None:
            try:
                start = pd.Timestamp(start)
            except ValueError:
                errors.update({'start': ['Invalid start date format']})
        if end is not None:
            try:
                end = pd.Timestamp(end)
            except ValueError:
                errors.update({'end': ['Invalid end date format']})
        if errors:
            return jsonify({'errors': errors}), 400
        storage = get_storage()
        values = storage.read_forecast_values(forecast_id, start, end)
        if values is None:
            abort(404)
        accepts = request.accept_mimetypes.best_match(['application/json',
                                                       'text/csv'])
        if accepts == 'application/json':
            values['timestamp'] = values.index
            dict_values = values.to_dict(orient='records')
            data = ForecastValuesSchema().dump({"forecast_id": forecast_id,
                                                "values": dict_values})
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
        description: Add new timeseries values to Forecast entry.
        tags:
        - Forecasts
        parameters:
        - $ref: '#/components/parameters/forecast_id'
        requestBody:
          required: True
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ForecastValues'
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
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        if request.content_type == 'application/json':
            raw_data = request.get_json()
            try:
                raw_values = raw_data['values']
            except (TypeError, KeyError):
                error = 'Supplied JSON does not contain "values" field.'
                return jsonify({'errors': {'error': [error]}}), 400
            try:
                forecast_df = pd.DataFrame(raw_values)
            except ValueError:
                return jsonify({'errors': {'error': ['Malformed JSON']}}), 400
        elif request.content_type == 'text/csv':
            raw_data = StringIO(request.get_data(as_text=True))
            try:
                forecast_df = pd.read_csv(raw_data,
                                          na_values=[-999, -9999],
                                          keep_default_na=True,
                                          comment='#')
            except pd.errors.EmptyDataError:
                return jsonify({'errors': {'error': ['Malformed CSV']}}), 400
            finally:
                raw_data.close()
        else:
            error = 'Invalid Content-type.'
            return jsonify({'errors': {'error': [error]}}), 400
        errors = {}
        try:
            forecast_df['value'] = pd.to_numeric(forecast_df['value'],
                                                 downcast='float')
        except ValueError:
            error = ('Invalid item in "value" field. Ensure that all values '
                     'are integers, floats, empty, NaN, or NULL.')
            errors.update({'value': [error]})
        except KeyError:
            errors.update({'value': ['Missing "value" field.']})
        try:
            forecast_df['timestamp'] = pd.to_datetime(
                forecast_df['timestamp'],
                utc=True)
        except ValueError:
            error = ('Invalid item in "timestamp" field. Ensure that '
                     'timestamps are ISO8601 compliant')
            errors.update({'timestamp': []})
        except KeyError:
            errors.update({'timestamp': ['Missing "timestamp" field.']})

        if errors:
            return jsonify({'errors': errors}), 400
        forecast_df = forecast_df.set_index('timestamp')
        storage = get_storage()
        stored = storage.store_forecast_values(forecast_id, forecast_df)
        if stored is None:
            abort(404)
        return stored, 201


class ForecastMetadataView(MethodView):
    def get(self, forecast_id, *args):
        """
        ---
        summary: Get Forecast metadata
        tags:
        - Forecasts
        parameters:
        - $ref: '#/components/parameters/forecast_id'
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
        if forecast is None:
            abort(404)
        return jsonify(ForecastSchema().dump(forecast))


spec.components.parameter(
    'forecast_id', 'path',
    {
        'schema': {
            'type': 'string',
            'format': 'uuid'
        },
        'description': "Forecast's unique identifier.",
        'required': 'true'
    })

forecast_blp = Blueprint(
    'forecasts', 'forecasts', url_prefix="/forecasts",
)
forecast_blp.add_url_rule('/', view_func=AllForecastsView.as_view('all'))
forecast_blp.add_url_rule('/<forecast_id>',
                          view_func=ForecastView.as_view('single'))
forecast_blp.add_url_rule('/<forecast_id>/values',
                          view_func=ForecastValuesView.as_view('values'))
forecast_blp.add_url_rule('/<forecast_id>/metadata',
                          view_func=ForecastMetadataView.as_view('metadata'))
