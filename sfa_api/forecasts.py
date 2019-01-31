from flask import Blueprint
from flask.views import MethodView


from sfa_api import spec
from sfa_api.schema import (ForecastValueSchema,
                            ForecastSchema,
                            ForecastLinksSchema)
from sfa_api.demo import Forecast, TimeseriesValue


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
        forecasts = [Forecast() for i in range(3)]
        return ForecastSchema(many=True).jsonify(forecasts)

    def post(self, *args):
        """
        ---
        summary: Create forecast
        tags:
        - Forecasts
        description: Create a new Forecast by posting metadata
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
        forecast = Forecast()
        return ForecastSchema().jsonify(forecast)


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
        return ForecastLinksSchema().jsonify(Forecast())

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
        return f'Delete forecast {forecast_id}'


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
        responses:
          200:
            content:
              applciation/json:
                schema:
                  type: array
                  items:
                    $ref: '#/components/schemas/ForecastValue'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        forecast_values = [TimeseriesValue() for i in range(3)]
        return ForecastValueSchema(many=True).jsonify(forecast_values)

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
                type: array
                items:
                  $ref: '#/components/schemas/ForecastValue'
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
        return


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
        return ForecastSchema().jsonify(Forecast())

    def put(self, forecast_id, *args):
        """
        ---
        summary: Update forecast metadata
        tags:
        - Forecasts
        parameters:
        - $ref: '#/components/parameters/forecast_id'
        requestBody:
          description: JSON representation of a forecast's metadata.
          required: True
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ForecastDefinition'
        responses:
          200:
           description: Forecast updated successfully.
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        return


spec.add_parameter('forecast_id', 'path',
                   schema={
                       'type': 'string',
                       'format': 'uuid'
                   },
                   description="Forecast's unique identifier.",
                   required='true')

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
