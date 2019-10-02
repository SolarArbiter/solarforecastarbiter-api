from marshmallow import validate, validates_schema
from marshmallow.exceptions import ValidationError

from sfa_api import spec, ma
from sfa_api.utils.validators import (
    TimeFormat, UserstringValidator, TimezoneValidator)
from solarforecastarbiter.datamodel import ALLOWED_VARIABLES


# solarforecastarbiter.datamodel defines allowed variable as a dict of
# variable: units we just want the variable names here
VARIABLES = ALLOWED_VARIABLES.keys()

ALLOWED_METRICS = ['mae', 'mbe', 'rmse']
INTERVAL_LABELS = ['beginning', 'ending', 'instant']

INTERVAL_VALUE_TYPES = ['interval_mean', 'interval_max', 'interval_min',
                        'interval_median', 'instantaneous']

EXTRA_PARAMETERS_FIELD = ma.String(
    title='Extra Parameters',
    description='Additional user specified parameters.',
    missing='')

VARIABLE_FIELD = ma.String(
    title='Variable',
    description="The variable being forecast",
    required=True,
    validate=validate.OneOf(VARIABLES))
ORGANIZATION_ID = ma.UUID(
    title="Organization ID",
    description="UUID of the Organization the Object belongs to."
)
CREATED_AT = ma.DateTime(
    title="Creation time",
    description="ISO 8601 Datetime when object was created",
    format='iso')

MODIFIED_AT = ma.DateTime(
    title="Last Modification Time",
    description="ISO 8601 Datetime when object was last modified",
    format='iso')


# Sites
@spec.define_schema('ModelingParameters')
class ModelingParameters(ma.Schema):
    class Meta:
        ordered = True
    ac_capacity = ma.Float(
        title="AC Capacity",
        description="Nameplate AC power rating.",
        missing=None)
    dc_capacity = ma.Float(
        title="DC Capacity",
        description="Nameplate DC power rating.",
        missing=None)
    temperature_coefficient = ma.Float(
        title="Temperature Coefficient",
        description=("The temperature coefficient of DC power in units of "
                     "1/C. Typically -0.002 to -0.005 per degree C."),
        missing=None)
    tracking_type = ma.String(
        title="Tracking Type",
        description=("Type of tracking system, i.e. fixed, single axis, two "
                     "axis."),
        validate=validate.OneOf(['fixed', 'single_axis']),
        missing=None)
    # fixed tilt systems
    surface_tilt = ma.Float(
        title="Surface Tilt",
        description="Tilt from horizontal of a fixed tilt system, degrees.",
        missing=None)
    surface_azimuth = ma.Float(
        title="Surface Azimuth",
        description="Azimuth angle of a fixed tilt system, degrees.",
        missing=None)
    # single axis tracker
    axis_tilt = ma.Float(
        title="Axis tilt",
        description="Tilt from horizontal of the tracker axis, degrees.",
        missing=None)
    axis_azimuth = ma.Float(
        title="Axis azimuth",
        description="Azimuth angle of the tracker axis, degrees.",
        missing=None)
    ground_coverage_ratio = ma.Float(
        title="Ground coverage ratio",
        description=("Ratio of total width of modules on a tracker to the "
                     "distance between tracker axes. For example, for "
                     "trackers each with two modules of 1m width each, and "
                     "a spacing between tracker axes of 7m, the ground "
                     "coverage ratio is 0.286(=2/7)."),
        missing=None)
    backtrack = ma.Boolean(
        title="Backtrack",
        description=("True/False indicator of if a tracking system uses "
                     "backtracking."),
        missing=None)
    max_rotation_angle = ma.Float(
        title="Maximum Rotation Angle",
        description=("Maximum rotation from horizontal of a single axis "
                     "tracker, degrees."),
        missing=None)
    dc_loss_factor = ma.Float(
        title="DC loss factor",
        description=("Loss factor in %, applied to DC current."),
        validate=validate.Range(0, 100),
        missing=None)
    ac_loss_factor = ma.Float(
        title="AC loss factor",
        description=("Loss factor in %, applied to inverter power "
                     "output."),
        validate=validate.Range(0, 100),
        missing=None)

    @validates_schema
    def validate_modeling_parameters(self, data):
        common_fields = {
            'ac_capacity', 'dc_capacity', 'temperature_coefficient',
            'dc_loss_factor', 'ac_loss_factor'}
        fixed_fields = {'surface_tilt', 'surface_azimuth'}
        singleaxis_fields = {
            'axis_tilt', 'axis_azimuth', 'ground_coverage_ratio',
            'backtrack', 'max_rotation_angle'}
        # if tracking type is None (weather station),
        # ensure all fields are None
        if data['tracking_type'] is None:
            errors = {
                key: ['Field must be null/none when tracking_type is none']
                for key in common_fields | fixed_fields | singleaxis_fields
                if data[key] is not None}
            if errors:
                raise ValidationError(errors)
        elif data['tracking_type'] == 'fixed':
            errors = {
                key: ["Field should be none with tracking_type='fixed'"]
                for key in singleaxis_fields if data[key] is not None}
            errors.update({key: ["Value required when tracking_type='fixed'"]
                           for key in common_fields | fixed_fields
                           if data[key] is None})
            if errors:
                raise ValidationError(errors)
        elif data['tracking_type'] == 'single_axis':
            errors = {
                key: ["Field should be none with tracking_type='single_axis'"]
                for key in fixed_fields if data[key] is not None}
            errors.update({
                key: ["Value required when tracking_type='single_axis'"]
                for key in common_fields | singleaxis_fields
                if data[key] is None})
            if errors:
                raise ValidationError(errors)


@spec.define_schema('SiteDefinition')
class SiteSchema(ma.Schema):
    class Meta:
        strict = True
        ordered = True
    name = ma.String(
        title='Name',
        description="Name of the Site",
        required=True,
        validate=UserstringValidator())
    latitude = ma.Float(
        title='Latitude',
        description="Latitude in degrees North",
        validate=validate.Range(-90, 90),
        required=True)
    longitude = ma.Float(
        title='Longitude',
        description="Longitude in degrees East of the Prime Meridian",
        validate=validate.Range(-180, 180),
        required=True)
    elevation = ma.Float(
        title='Elevation',
        description="Elevation in meters",
        required=True)
    timezone = ma.String(
        title="Timezone",
        description="IANA Timezone",
        required=True,
        validate=TimezoneValidator())
    modeling_parameters = ma.Nested(ModelingParameters,
                                    missing=ModelingParameters().load({}))
    extra_parameters = EXTRA_PARAMETERS_FIELD


@spec.define_schema('SiteMetadata')
class SiteResponseSchema(SiteSchema):
    site_id = ma.UUID(required=True)
    provider = ma.String()
    created_at = CREATED_AT
    modified_at = MODIFIED_AT


# Observations
@spec.define_schema('ObservationValue')
class ObservationValueSchema(ma.Schema):
    class Meta:
        strict = True
        ordered = True
    timestamp = ma.DateTime(
        title="Timestamp",
        description="ISO 8601 Datetime",
        format='iso')
    value = ma.Float(
        title='Value',
        description="Value of the measurement",
        allow_nan=True)
    quality_flag = ma.Integer(
        title='Quality flag',
        description="A flag indicating data quality.",
        missing=False)


@spec.define_schema('ObservationValuesPost')
class ObservationValuesPostSchema(ma.Schema):
    values = ma.Nested(ObservationValueSchema, many=True)


@spec.define_schema('ObservationValues')
class ObservationValuesSchema(ObservationValuesPostSchema):
    observation_id = ma.UUID(
        title='Obs ID',
        description="UUID of the Observation associated with this data.")
    _links = ma.Hyperlinks(
        {
            'metadata': ma.AbsoluteURLFor('observations.metadata',
                                          observation_id='<observation_id>'),
        },
        description="Contains a link to the values endpoint."
    )


@spec.define_schema('ObservationDefinition')
class ObservationPostSchema(ma.Schema):
    class Meta:
        strict = True
        ordered = True
    variable = VARIABLE_FIELD
    site_id = ma.UUID(
        title='Site ID',
        description="UUID the associated site",
        required=True)
    name = ma.String(
        title='Name',
        description='Human friendly name for the observation',
        required=True,
        validate=UserstringValidator())
    interval_label = ma.String(
        title='Interval Label',
        description=('For data that represents intervals, indicates if a time '
                     'labels the beginning or ending of the interval. '
                     'instant for instantaneous data'),
        validate=validate.OneOf(INTERVAL_LABELS),
        required=True)
    interval_length = ma.Integer(
        title='Interval length',
        description=('The length of time that each data point represents  in'
                     'minutes, e.g. 5 for 5 minutes.'),
        required=True)
    interval_value_type = ma.String(
        title='Value Type',
        validate=validate.OneOf(INTERVAL_VALUE_TYPES),
        required=True)
    uncertainty = ma.Float(
        title='Uncertainty',
        description='A measure of the uncertainty of the observation values.',
        required=True)
    extra_parameters = EXTRA_PARAMETERS_FIELD


@spec.define_schema('ObservationMetadata')
class ObservationSchema(ObservationPostSchema):
    class Meta:
        strict = True
        ordered = True
    _links = ma.Hyperlinks(
        {
            'site': ma.AbsoluteURLFor('sites.single',
                                      site_id='<site_id>')
        },
        description="Contains a link to the associated site."
    )
    observation_id = ma.UUID()
    provider = ma.String()
    created_at = CREATED_AT
    modified_at = MODIFIED_AT


@spec.define_schema('ObservationLinks')
class ObservationLinksSchema(ma.Schema):
    class Meta:
        strict = True
        ordered = True
    observation_id = ma.UUID()
    _links = ma.Hyperlinks(
        {
            'metadata': ma.AbsoluteURLFor('observations.metadata',
                                          observation_id='<observation_id>'),
            'values': ma.AbsoluteURLFor('observations.values',
                                        observation_id='<observation_id>')
        },
        description="Contains links to the values and metadata endpoints."
    )


# Forecasts
@spec.define_schema('ForecastValue')
class ForecastValueSchema(ma.Schema):
    class Meta:
        strict = True
        ordered = True
    timestamp = ma.DateTime(
        title="Timestamp",
        description="ISO 8601 Datetime",
        format='iso')
    value = ma.Float(
        title="Value",
        description="Value of the forecast variable.",
        allow_nan=True)


@spec.define_schema('ForecastValuesPost')
class ForecastValuesPostSchema(ma.Schema):
    values = ma.Nested(ForecastValueSchema, many=True)


@spec.define_schema('CDFForecastValues')
class CDFForecastValuesSchema(ForecastValuesPostSchema):
    forecast_id = ma.UUID(
        title="Forecast ID",
        description="UUID of the forecast associated with this data.")
    _links = ma.Hyperlinks(
        {
            'metadata': ma.AbsoluteURLFor('forecasts.single_cdf_metadata',
                                          forecast_id='<forecast_id>'),
        },
        description="Contains a link to the metadata endpoint."
    )


@spec.define_schema('ForecastValues')
class ForecastValuesSchema(ForecastValuesPostSchema):
    forecast_id = ma.UUID(
        title="Forecast ID",
        description="UUID of the forecast associated with this data.")
    _links = ma.Hyperlinks(
        {
            'metadata': ma.AbsoluteURLFor('forecasts.metadata',
                                          forecast_id='<forecast_id>'),
        },
        description="Contains a link to the metadata endpoint."
    )


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
        required=True,
        validate=UserstringValidator())
    variable = VARIABLE_FIELD
    issue_time_of_day = ma.String(
        title='Issue Time of Day',
        required=True,
        validate=TimeFormat('%H:%M'),
        description=('The time of day that a forecast run is issued specified '
                     'in the timezone of the site in HH:MM format, e.g. 00:30.'
                     'For forecast runs issued multiple times within one day '
                     '(e.g. hourly), this specifies the first issue time of '
                     'day. Additional issue times are uniquely determined by '
                     'the first issue time and the run length & issue '
                     'frequency attribute.'))
    lead_time_to_start = ma.Integer(
        title='Lead time to start',
        description=("The difference between the issue time and the start of "
                     "the first forecast interval in minutes, e.g. 60 for one"
                     "hour."),
        required=True)
    interval_label = ma.String(
        title='Interval Label',
        description=('For data that represents intervals, indicates if a time '
                     'labels the beginning or ending of the interval.'),
        validate=validate.OneOf(INTERVAL_LABELS),
        required=True)
    interval_length = ma.Integer(
        title='Interval length',
        description=('The length of time that each data point represents in'
                     'minutes, e.g. 5 for 5 minutes.'),
        required=True
    )
    run_length = ma.Integer(
        title='Run Length / Issue Frequency',
        description=('The total length of a single issued forecast run in '
                     'minutes, e.g. 60 for 1 hour. To enforce a continuous,'
                     'non-overlapping sequence, this is equal to the forecast'
                     'run issue frequency.'),
        required=True
    )
    interval_value_type = ma.String(
        title='Value Type',
        validate=validate.OneOf(INTERVAL_VALUE_TYPES)
    )
    extra_parameters = EXTRA_PARAMETERS_FIELD


@spec.define_schema('ForecastMetadata')
class ForecastSchema(ForecastPostSchema):
    _links = ma.Hyperlinks(
        {
            'site': ma.AbsoluteURLFor('sites.single',
                                      site_id='<site_id>'),
        },
        description="Contains a link to the associated site."
    )
    forecast_id = ma.UUID()
    provider = ma.String()
    created_at = CREATED_AT
    modified_at = MODIFIED_AT


@spec.define_schema('ForecastLinks')
class ForecastLinksSchema(ma.Schema):
    class Meta:
        string = True
        ordered = True
    forecast_id = ma.UUID()
    _links = ma.Hyperlinks(
        {
            'metadata': ma.AbsoluteURLFor('forecasts.metadata',
                                          forecast_id='<forecast_id>'),
            'values': ma.AbsoluteURLFor('forecasts.values',
                                        forecast_id='<forecast_id>')
        },
        description="Contains links to the values and metadata endpoints."
    )


# Probabilistic Forecasts
AXIS_FIELD = ma.String(
    title='Axis',
    description=('Axis - The axis on which the constant values of the CDF '
                 'is specified. The axis can be either x (constant '
                 'variable values) or y (constant percentiles). The axis '
                 'is fixed and the same for all forecasts in the '
                 'probabilistic forecast.'),
    required=True,
    validate=validate.OneOf(['x', 'y'])
)


@spec.define_schema('CDFForecastGroupDefinition')
class CDFForecastGroupPostSchema(ForecastPostSchema):
    axis = AXIS_FIELD
    constant_values = ma.List(
        ma.Float,
        title='Constant Values',
        description=('The variable values or percentiles for the set of '
                     'forecasts in the probabilistic forecast.'),
        required=True
    )


@spec.define_schema('CDFForecastMetadata')
class CDFForecastSchema(ForecastSchema):
    _links = ma.Hyperlinks(
        {
            'probability_forecast_group': ma.AbsoluteURLFor(
                'forecasts.single_cdf_group',
                forecast_id='<parent>'),
            'values': ma.AbsoluteURLFor(
                'forecasts.single_cdf_value',
                forecast_id='<forecast_id>')
        },
        description=("Contains a link to the associated Probabilistic "
                     "Forecast Group."),
    )
    forecast_id = ma.UUID()
    axis = AXIS_FIELD
    parent = ma.UUID()
    constant_value = ma.Float(
        title='Constant Value',
        description=('The variable value or percentile for the probabilistic'
                     'forecast'),
    )


@spec.define_schema('CDFForecastSingle')
class CDFForecastSingleSchema(ma.Schema):
    forecast_id = ma.UUID()
    constant_value = ma.Float()
    _links = ma.Hyperlinks(
        {
            'values': ma.AbsoluteURLFor('forecasts.single_cdf_value',
                                        forecast_id='<forecast_id>')
        },
        description="Contains a link to the values endpoint."
    )


@spec.define_schema('CDFForecastGroupMetadata')
class CDFForecastGroupSchema(CDFForecastGroupPostSchema):
    _links = ma.Hyperlinks(
        {
            'site': ma.AbsoluteURLFor('sites.single',
                                      site_id='<site_id>'),
        },
        description="Contains a link to the associated site."
    )
    forecast_id = ma.UUID()
    provider = ma.String()
    constant_values = ma.Nested(CDFForecastSingleSchema, many=True)
    created_at = CREATED_AT
    modified_at = MODIFIED_AT


@spec.define_schema('UserPostSchema')
class UserPostSchema(ma.Schema):
    auth0_id = ma.String(
        title="Auth0 ID",
        description="The User's unique Auth0 identifier.",
    )
    organization_id = ma.UUID(
        title="Organization ID",
        description="UUID of the Organization the User belongs to."
    )


@spec.define_schema('UserSchema')
class UserSchema(ma.Schema):
    user_id = ma.UUID(
        title="User ID",
        description="Unique UUID of the User.",
    )
    organization = ma.String(title='Organization')
    created_at = CREATED_AT
    modified_at = MODIFIED_AT
    roles = ma.Dict()


@spec.define_schema('PermissionPostSchema')
class PermissionPostSchema(ma.Schema):
    description = ma.String(
        title='Desctription',
        required=True,
        description="Description of the purpose of a permission.",
    )
    action = ma.String(
        title='Action',
        description="The action that the permission allows.",
        required=True,
        validate=validate.OneOf(['create', 'read', 'update',
                                 'delete', 'read_values', 'write_values',
                                 'delete_values', 'grant', 'revoke']),
    )
    object_type = ma.String(
        title="Object Type",
        description="The type of object this permission will act on.",
        required=True,
        validate=validate.OneOf(['sites', 'aggregates', 'forecasts',
                                 'observations', 'users', 'roles',
                                 'permissions', 'cdf_forecasts']),
    )
    applies_to_all = ma.Boolean(
        title="Applies to all",
        default=False,
        description=("Whether or not the permission applied to all objects "
                     "of object_type."),
    )


@spec.define_schema('PermissionSchema')
class PermissionSchema(PermissionPostSchema):
    permission_id = ma.UUID(
        title="Permission ID",
        description="UUID of the Permission",
    )
    organization = ma.String(title="Organization")
    objects = ma.Dict()
    created_at = CREATED_AT
    modified_at = MODIFIED_AT


@spec.define_schema('RolePostSchema')
class RolePostSchema(ma.Schema):
    name = ma.String(
        title='Name',
        description="Name of the Role",
        required=True,
        validate=UserstringValidator()
    )
    # Perhaps this needs some validation?
    description = ma.String(
        title='Description',
        description="A description of the responsibility of the role.",
        required=True,
    )


@spec.define_schema('RoleSchema')
class RoleSchema(RolePostSchema):
    role_id = ma.UUID(
        title='Role ID',
        description="UUID of the role",
        required=True,
        validate=UserstringValidator()
    )
    organization = ma.String(title="Organization")
    permissions = ma.Dict()
    users = ma.Dict()
    created_at = CREATED_AT
    modified_at = MODIFIED_AT


@spec.define_schema('ReportParameters')
class ReportParameters(ma.Schema):
    start = ma.DateTime(
        title="Start",
        description=("The beginning of the analysis period as an ISO 8601"
                     "datetime."),
        format='iso'
    )
    end = ma.DateTime(
        title="End",
        description="The end of the analysis period as an ISO 8601 datetime.",
        format='iso'
    )
    # Tuple is a new addition to marshmallow fields in v3.0.0rc4, and hasn't
    # been added to apispec, so this will not render correctly right now
    # Issue: https://github.com/marshmallow-code/apispec/issues/399
    object_pairs = ma.List(ma.Tuple(
        (ma.UUID(title="Observation UUID"), ma.UUID(title="Forecast UUID")),
        many=True))
    filters = ma.List(
        ma.String(),
        title="Filters",
        description="List of Filters Applied to the data in the report"
    )
    metrics = ma.List(
        ma.String(
            validate=validate.OneOf(ALLOWED_METRICS)
        ),
        title='Metrics',
        description=('The metrics to include in the report.'),
        required=True
    )


@spec.define_schema('ReportValuesPostSchema')
class ReportValuesPostSchema(ma.Schema):
    object_id = ma.UUID(
        title="Object ID",
        description="UUID of the original object"
    )
    # maybe custom field for binary data?
    processed_values = ma.String()


@spec.define_schema('ReportValuesSchema')
class ReportValuesSchema(ReportValuesPostSchema):
    # Not sure how this dict should be structured. Nested
    # Forecast/ObservationValueSchema?
    # we definitely want the uuid:values mapping
    id = ma.UUID(
        title="Report Value ID",
        description="UUID for this set of processed values",
    )
    report_id = ma.UUID(
        title="Report ID",
        description="UUID of the associated report"
    )


# Currently, the marshmallow API Spec
@spec.define_schema('ReportMetadata')
class ReportPostSchema(ma.Schema):
    name = ma.String(
        title="Name",
        required=True,
        validate=UserstringValidator()
    )
    report_parameters = ma.Nested(ReportParameters,
                                  required=True)


@spec.define_schema('ReportSchema')
class ReportSchema(ReportPostSchema):
    """For serializing a list or reports.
    """
    class Meta:
        string = True
        ordered = True
    report_id = ma.UUID()
    organization = ma.String(title="Organization")
    metrics = ma.Dict(
        title='Calculated Metrics',
        description='Metrics calculated over the '
                    'analysis period of the report.')
    raw_report = ma.String(
        title="Raw Report",
        description="A Markdown template with rendered metrics, and a block "
                    "for inserting timeseries plots")
    status = ma.String(validate=validate.OneOf(
        ['pending', 'complete', 'failed']))
    created_at = CREATED_AT
    modified_at = MODIFIED_AT


@spec.define_schema('SingleReportSchema')
class SingleReportSchema(ReportSchema):
    """For serializing a report with values
    """
    values = ma.List(ma.Nested(ReportValuesSchema()),
                     many=True)


@spec.define_schema('ReportMetricsSchema')
class ReportMetricsSchema(ma.Schema):
    """Parses metrics and raw_report out of a single object.
    """
    metrics = ma.Dict(
        title="Calculated Metrics",
        Description="calculated metrics of the field",
        required=True)
    raw_report = ma.String(
        title="Raw Report",
        description=("A Markdown template with rendered metrics, and a block "
                     "for inserting timeseries plots"),
        required=True
    )


@spec.define_schema('AggregateDefinition')
class AggregatePostSchema(ma.Schema):
    class Meta:
        strict = True
        ordered = True
    name = ma.String(
        title='Name',
        description="Human friendly name for aggregate",
        required=True,
        validate=UserstringValidator())
    variable = VARIABLE_FIELD
    interval_label = ma.String(
        title='Interval Label',
        description=('For data that represents intervals, indicates if a time '
                     'labels the beginning or ending of the interval.'),
        validate=validate.OneOf(INTERVAL_LABELS),
        required=True)
    interval_length = ma.Integer(
        title='Interval length',
        description=('The length of time that each data point represents in'
                     'minutes, e.g. 5 for 5 minutes.'),
        required=True
    )
    interval_value_type = ma.String(
        title='Value Type',
        validate=validate.OneOf(INTERVAL_VALUE_TYPES)
    )
    extra_parameters = EXTRA_PARAMETERS_FIELD
    timezone = ma.String(
        title="Timezone",
        description="IANA Timezone",
        required=True,
        validate=TimezoneValidator())
    description = ma.String(
        title='Desctription',
        required=True,
        description="Description of the aggregate"
    )


@spec.define_schema('AggregateObservation')
class AggregateObservationSchema(ma.Schema):
    observation_id = ma.UUID()
    created_at = CREATED_AT
    observation_deleted_at = ma.DateTime(
        title="Observation deletion time",
        description="ISO 8601 Datetime when the observation was deleted",
        format='iso')
    observation_removed_at = ma.DateTime(
        title="Observation removal time",
        description=("ISO 8601 Datetime when the observation was"
                     " removed from the aggregate"),
        format='iso')
    constant_value = ma.Float()
    _links = ma.Hyperlinks(
        {
            'observation': ma.AbsoluteURLFor(
                'observations.metadata',
                observation_id='<observation_id>'),
        },
        description="Contains a link to the observation endpoint."
    )


@spec.define_schema('AggregateMetadata')
class AggregateSchema(AggregatePostSchema):
    aggregate_id = ma.UUID()
    provider = ma.String()
    created_at = CREATED_AT
    modified_at = MODIFIED_AT
    observations = ma.List(ma.Nested(AggregateObservationSchema()),
                           many=True)


@spec.define_schema('AggregateLinks')
class AggregateLinksSchema(ma.Schema):
    class Meta:
        strict = True
        ordered = True
    aggregate_id = ma.UUID()
    _links = ma.Hyperlinks(
        {
            'metadata': ma.AbsoluteURLFor('aggregates.metadata',
                                          aggregate_id='<aggregate_id>'),
            'values': ma.AbsoluteURLFor('aggregates.values',
                                        aggregate_id='<aggregate_id>')
        },
        description="Contains links to the values and metadata endpoints."
    )


@spec.define_schema('AggregateValues')
class AggregateValuesSchema(ObservationValuesPostSchema):
    aggregate_id = ma.UUID(
        title='Obs ID',
        description="UUID of the Aggregate associated with this data.")
    _links = ma.Hyperlinks(
        {
            'metadata': ma.AbsoluteURLFor('aggregates.metadata',
                                          aggregate_id='<aggregate_id>'),
        },
        description="Contains a link to the values endpoint."
    )
