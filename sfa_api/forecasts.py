from flask import Blueprint
from flask.views import MethodView


from sfa_api import spec, ma
from sfa_api.sites import SiteSchema
from sfa_api.demo import Forecast, TimeseriesValue


@spec.define_schema('ForecastValue')
class ForecastValueSchema(ma.Schema):
    class Meta:
        strict = True
        ordered = True
    timestamp = ma.DateTime(description="ISO 8601 Datetime")
    value = ma.Float(description="Value of the measurement")
    questionable = ma.Boolean(description="Whether the value is questionable",
                              default=False, missing=False)


@spec.define_schema('ForecastDefinition')
class ForecastPostSchema(ma.Schema):
    class Meta:
        strict = True
        ordered = True
    type = ma.String(
        description="Type of variable forecasted",
        required=True)
    site_id = ma.UUID(description="UUID of associated site",
                      required=True)
    name = ma.String(description="Human friendly name for forecast",
                     required=True)


@spec.define_schema('ForecastMetadata')
class ForecastSchema(ForecastPostSchema):
    site = ma.Nested(SiteSchema)
    uuid = ma.UUID()


@spec.define_schema('ForecastLinks')
class ForecastLinkSchema(ma.Schema):
    class Meta:
        string = True
        ordered = True
    uuid = ma.UUID()
    _links = ma.Hyperlinks({
        'metadata': ma.AbsoluteURLFor('forecasts.metadata',
                                      forecast_id='<uuid>'),
        'values': ma.AbsoluteURLFor('forecasts.values',
                                    forecast_id='<uuid>')
    })


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
        forecasts = [ Forecast() for i in range(3)]
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
        return ForecastResponseSchema().jsonify(forecast)

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
        return ForecastLinkSchema().jsonify(Forecast())


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
        forecast_values = [ TimeseriesValue() for i in range(3) ]
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
                   type='string',
                   description="Forecast's unique identifier.",
                   required='true')

forecast_blp = Blueprint(
    'forecasts', 'forecasts', url_prefix="/forecasts",
)
forecast_blp.add_url_rule('/', view_func=AllForecastsView.as_view('all'))
forecast_blp.add_url_rule('/<forecast_id>', view_func=ForecastView.as_view('single'))
forecast_blp.add_url_rule('/<forecast_id>/values', view_func=ForecastValuesView.as_view('values'))
forecast_blp.add_url_rule('/<forecast_id>/metadata',view_func=ForecastMetadataView.as_view('metadata'))
