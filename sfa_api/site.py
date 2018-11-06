from flask import Blueprint, jsonify
from flask.views import MethodView


from sfa_api import spec, ma


@spec.define_schema('SiteRequest')
class SiteSchema(ma.Schema):
    class Meta:
        strict = True
        ordered = True
    name = ma.String(description="Name of the Site")
    latitude = ma.Float(description="Latitude in degrees North")
    longitude = ma.Float(
        description="Longitude in degrees East of the Prime Meridian")
    elevation = ma.Float(description="Elevation in meters")
    station_id = ma.String(
        description="Unique ID used by data provider")
    abbreviation = ma.String(
        description="Abbreviated station name used by data provider")
    timezone = ma.String(description="Timezone")
    attribution = ma.String(
        description="Attribution to be included in derived works")
    owner = ma.String(description="Data provider")


@spec.define_schema('SiteResponse')
class SiteResponseSchema(SiteSchema):
    uuid = ma.UUID()
