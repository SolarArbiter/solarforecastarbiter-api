from flask import Blueprint, jsonify
from flask.views import MethodView
from marshmallow_jsonschema import JSONSchema

from sfa_api import spec, ma


# Sites
@spec.define_schema('ModelingParameters')
class ModelingParameters(ma.Schema):
    ac_power = ma.String(
        title="AC Power",
        description="Nameplate AC power rating.")
    dc_power = ma.String(
        title="DC Power",
        description="Nameplate DC power rating.")
    gamma_pdc = ma.String(
        title="Gamma PDC",
        description=("The temperature coefficient of DC power in units of "
                     "1/C. Typically -0.002 to -0.005 per degree C."))
    tracking_type = ma.String(
        title="Tracking Type",
        description=("Type of tracking system, i.e. fixed, single axis, two "
                     "axis."))
    # fixed tilt systems
    surface_tilt = ma.Float(
        title="Surface Tilt",
        description="Tilt from horizontal of a fixed tilt system, degrees.")
    surface_azimuth = ma.Float(
        title="Surface Azimuth",
        description="Azimuth angle of a fixed tilt system, degrees.")
    # single axis tracker
    axis_tilt = ma.Float(
        title="Axis tilt",
        description="Tilt from horizontal of the tracker axis, degrees.")
    axis_azimuth = ma.Float(
        title="Axis azimuth",
        description="Azimuth angle of the tracker axis, degrees.")
    ground_coverage_ratio = ma.Float(
        title="Ground coverage ratio",
        description="Ground coverage ratio of a tracking system.")
    backtrack = ma.Boolean(
        title="Backtrack",
        description=("True/False indicator of if a tracking system uses "
                     "backtracking."))
    max_rotation_angle = ma.Float(
        title="Maximum Rotation Angle",
        description=("Maximum rotation from horizontal of a single axis "
                     "tracker, degrees."))


@spec.define_schema('SiteDefinition')
class SiteSchema(ma.Schema):
    class Meta:
        strict = True
        ordered = True
    name = ma.String(
        title='Name',
        description="Name of the Site",
        required=True)
    latitude = ma.Float(
        title='Latitude',
        description="Latitude in degrees North",
        required=True)
    longitude = ma.Float(
        title='Longitude',
        description="Longitude in degrees East of the Prime Meridian",
        required=True)
    elevation = ma.Float(
        title='Elevation',
        description="Elevation in meters",
        required=True)
    timezone = ma.String(
        title="Timezone",
        description="IANA Timezone",
        required=True)
    modeling_parameters = ma.Nested(ModelingParameters)
    extra_parameters = ma.Dict(
        title='Extra Parameters',
        description='Additional user specified parameters.')


@spec.define_schema('SiteMetadata')
class SiteResponseSchema(SiteSchema):
    site_id = ma.UUID(required=True)
    provider = ma.String()


# Observations
@spec.define_schema('ObservationValue')
class ObservationValueSchema(ma.Schema):
    class Meta:
        strict = True
        ordered = True
    timestamp = ma.DateTime(
        title="Timestamp",
        description="ISO 8601 Datetime")
    value = ma.Float(description="Value of the measurement")
    questionable = ma.Boolean(description="Whether the value is questionable",
                              default=False, missing=False)


@spec.define_schema('ObservationDefinition')
class ObservationPostSchema(ma.Schema):
    class Meta:
        strict = True
        ordered = True
    variable = ma.String(
        title='Variable',
        description="The variable recorded by this observation",
        required=True)
    site_id = ma.UUID(
        title='Site ID',
        description="UUID the assocaiated site",
        required=True)
    name = ma.String(
        title='Name',
        description='Human friendly name for the observation',
        required=True)
    extra_parameters = ma.Dict(
        title='Extra Parameters',
        description='Additional user specified parameters.')


@spec.define_schema('ObservationMetadata')
class ObservationSchema(ObservationPostSchema):
    site = ma.Nested(SiteSchema)
    obs_id = ma.UUID()
    provider = ma.String()


@spec.define_schema('ObservationLinks')
class ObservationLinksSchema(ma.Schema):
    class Meta:
        strict = True
        ordered = True
    obs_id = ma.UUID()
    _links = ma.Hyperlinks({
        'metadata': ma.AbsoluteURLFor('observations.metadata',
                                      obs_id='<obs_id>'),
        'values': ma.AbsoluteURLFor('observations.values',
                                    obs_id='<obs_id>')
    })


# Forecasts
@spec.define_schema('ForecastValue')
class ForecastValueSchema(ma.Schema):
    class Meta:
        strict = True
        ordered = True
    timestamp = ma.DateTime(
        title="Timestamp",
        description="ISO 8601 Datetime")
    value = ma.Float(
        title="Value",
        description="Value of the forecast variable.")
    questionable = ma.Boolean(
        title="Questionable",
        description="Whether the value is questionable",
        default=False, missing=False)


@spec.define_schema('ForecastDefinition')
class ForecastPostSchema(ma.Schema):
    class Meta:
        strict = True
        ordered = True
    site_id = ma.UUID(
        name="Site ID",
        description="UUID of the associated site",
        required=True)
    name = ma.String(
        title='Name',
        description="Human friendly name for forecast",
        required=True)
    variable = ma.String(
        title='Variable',
        description="The variable being forecast",
        required=True)
    lead_time = ma.String(
        title='Lead Time',
        description="Lead time to start of forecast",
        required=True)
    duration = ma.String(
        title='Duration',
        description="Interval duration",
        required=True)
    intervals = ma.Integer(
        title='Intervals',
        description="Intervals per submission",
        required=True)
    issue_frequency = ma.String(
        title='Issue Frequency',
        description="Forecast issue frequency",
        required=True)
    value_type = ma.String(
        title='Value Type',
        description="Value type (e.g. mean, max, 95th percentile, instantaneous)",  # NOQA
        required=True)
    extra_parameters = ma.Dict(
        title='Extra Parameters',
        description='Additional user specified parameters.')


@spec.define_schema('ForecastMetadata')
class ForecastSchema(ForecastPostSchema):
    site = ma.Nested(SiteSchema)
    forecast_id = ma.UUID()
    provider = ma.String()


@spec.define_schema('ForecastLinks')
class ForecastLinksSchema(ma.Schema):
    class Meta:
        string = True
        ordered = True
    forecast_id = ma.UUID()
    _links = ma.Hyperlinks({
        'metadata': ma.AbsoluteURLFor('forecasts.metadata',
                                      forecast_id='<forecast_id>'),
        'values': ma.AbsoluteURLFor('forecasts.values',
                                    forecast_id='<forecast_id>')
    })


# API Endpoints
schema_blp = Blueprint('schema', 'schema', url_prefix='/schema')


class SchemaEndpoint(MethodView):
    def get(self, schema_type):
        """
        ---
        summary: Get schemas in JSON.
        description: >
          Return a JSON Schema representation of marshmallow schema for
          posting.
        tags:
          - Schemas
        parameters:
          - in: path
            name: schema_type
            schema:
              type: string
            required: true
            description: Type of schema to request.
        responses:
          200:
            description: A JSON object of the schema.
            content:
              application/json:
                schema:
                  type: object
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        schemas = {
            'site': SiteSchema(),
            'forecast': ForecastPostSchema(),
            'observation': ObservationPostSchema(),
        }
        schema = schemas.get(schema_type, None)
        if schema is None:
            return None, 404
        return jsonify(JSONSchema().dump(schema))


schema_blp.add_url_rule('/<schema_type>',
                        view_func=SchemaEndpoint.as_view('schemas'))
