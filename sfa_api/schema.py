from sfa_api import spec, ma


# Sites
@spec.define_schema('SiteDefinition')
class SiteSchema(ma.Schema):
    class Meta:
        strict = True
        ordered = True
    name = ma.String(description="Name of the Site",
                     required=True)
    latitude = ma.Float(description="Latitude in degrees North",
                        required=True)
    longitude = ma.Float(
        description="Longitude in degrees East of the Prime Meridian",
        required=True)
    elevation = ma.Float(description="Elevation in meters",
                         required=True)
    provider_api_id = ma.String(
        description="Unique ID used by data provider")
    abbreviation = ma.String(
        description="Abbreviated station name used by data provider")
    timezone = ma.String(description="Timezone",
                         required=True)
    attribution = ma.String(
        description="Attribution to be included in derived works")
    provider = ma.String(description="Data provider")


@spec.define_schema('SiteMetadata')
class SiteResponseSchema(SiteSchema):
    site_id = ma.UUID(required=True)


# Observations
@spec.define_schema('ObservationValue')
class ObservationValueSchema(ma.Schema):
    class Meta:
        strict = True
        ordered = True
    timestamp = ma.DateTime(description="ISO 8601 Datetime")
    value = ma.Float(description="Value of the measurement")
    questionable = ma.Boolean(description="Whether the value is questionable",
                              default=False, missing=False)


@spec.define_schema('ObservationDefinition')
class ObservationPostSchema(ma.Schema):
    class Meta:
        strict = True
        ordered = True
    type = ma.String(
        description="Type of variable recorded by this observation",
        required=True)
    site_id = ma.UUID(description="UUID the assocaiated site",
                      required=True)
    name = ma.String(description='Human friendly name for the observation',
                     required=True)


@spec.define_schema('ObservationMetadata')
class ObservationSchema(ObservationPostSchema):
    site = ma.Nested(SiteSchema)
    obs_id = ma.UUID()


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
                                    obs_id='<obd_id>')
    })

# Forecasts
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
    site_id = ma.UUID(description="UUID of the associated site",
                      required=True)
    name = ma.String(description="Human friendly name for forecast",
                     required=True)
    type = ma.String(
        description="Type of variable forecasted",
        required=True)
    lead_time = ma.String(description="Lead time to start of forecast",
                          required=True)
    duration = ma.String(description="Interval duration",
                         required=True)
    intervals =  ma.Integer(description="Intervals per submission",
                            required=True)
    issue_frequency = ma.String(description="Forecast issue frequency",
                                required=True)
    value_type = ma.String(
        description="Value type (e.g. mean, max, 95th percentile, instantaneous)",  # NOQA
        required=True)


@spec.define_schema('ForecastMetadata')
class ForecastSchema(ForecastPostSchema):
    site = ma.Nested(SiteSchema)
    forecast_id = ma.UUID()


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
