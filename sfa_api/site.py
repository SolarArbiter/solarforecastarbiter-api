from flask import Blueprint, jsonify
from flask.views import MethodView
import marshmallow as ma


from sfa_api import spec


@spec.define_schema('SiteRequest')
class SiteSchema(ma.Schema):
    class Meta:
        strict = True
        ordered = True
    name = ma.fields.String(description="Name of the Site")
    latitude = ma.fields.Float(description="Latitude in degrees North")
    longitude = ma.fields.Float(
        description="Longitude in degrees East of the Prime Meridian")
    elevation = ma.fields.Float(description="Elevation in meters")
    station_id = ma.fields.String(
        description="Unique ID used by data provider")
    abbreviation = ma.fields.String(
        description="Abbreviated station name used by data provider")
    timezone = ma.fields.String(description="Timezone")
    attribution = ma.fields.String(
        description="Attribution to be included in derived works")
    owner = ma.fields.String(description="Data provider")


@spec.define_schema('SiteResponse')
class SiteResponseSchema(SiteSchema):
    uuid = ma.fields.UUID()
