from flask import Blueprint, jsonify, make_response
from flask.views import MethodView


from sfa_api import spec, json
from sfa_api.schema import ZoneListSchema
from sfa_api.utils.storage import get_storage
from sfa_api.utils.request_handling import validate_latitude_longitude


class AllZonesView(MethodView):
    def get(self, *args):
        """
        ---
        summary: List climate zones
        description: List all climate zones that the user has access to.
        tags:
        - Climate Zones
        responses:
          200:
            description: A list of climate zones.
            content:
              application/json:
                schema:
                  type: array
                  items:
                    $ref: '#/components/schemas/ZoneMetadata'
          401:
            $ref: '#/components/responses/401-Unauthorized'
        """
        storage = get_storage()
        zones = storage.list_zones()
        return jsonify(ZoneListSchema(many=True).dump(zones))


class ZoneView(MethodView):
    def get(self, zone, *args):
        """
        ---
        summary: Get zone GeoJSON
        description: Get the GeoJSON for a requested climate zone.
        tags:
        - Climate Zones
        parameters:
        - zone
        responses:
          200:
            description: The GeoJSON definition for the climate zone
            content:
              application/geo+json:
                schema:
                  type: object
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
             $ref: '#/components/responses/404-NotFound'
        """
        storage = get_storage()
        geojson = storage.read_climate_zone(zone.replace('+', ' '))
        response = make_response(json.dumps(geojson), 200)
        response.mimetype = 'application/geo+json'
        return response


class SearchZones(MethodView):
    def get(self, *args):
        """
        ---
        summary: Find zones
        description: Find all zones that the given point falls within
        tags:
        - Climate Zones
        parameters:
        - latitude
        - longitude
        responses:
          200:
            content:
              application/json:
                schema:
                  type: array
                  items:
                    $ref: '#/components/schemas/ZoneMetadata'
          400:
            $ref: '#/components/responses/400-BadRequest'
          401:
            $ref: '#/components/responses/401-Unauthorized'
        """
        lat, lon = validate_latitude_longitude()
        storage = get_storage()
        zones = storage.find_climate_zones(lat, lon)
        return jsonify(ZoneListSchema(many=True).dump(zones))


spec.components.parameter(
    'zone', 'path',
    {
        'schema': {
            'type': 'string',
        },
        'description': "Climate zone name. Spaces may be replaced with +.",
        'required': 'true',
        'name': 'zone'
    })
spec.components.parameter(
    'latitude', 'query',
    {
        'name': 'latitude',
        'required': True,
        'description': 'The latitude (in degrees North) of the location.',
        'schema': {
            'type': 'float',
        }
    })
spec.components.parameter(
    'longitude', 'query',
    {
        'name': 'longitude',
        'required': True,
        'description': 'The longitude (in degrees East of the Prime Meridian)'
                       ' of the location.',
        'schema': {
            'type': 'float',
        }
    })

zone_blp = Blueprint(
    'climatezones', 'climatezones', url_prefix='/climatezones',
)
zone_blp.add_url_rule('/', view_func=AllZonesView.as_view('all'))
zone_blp.add_url_rule('/<zone>', view_func=ZoneView.as_view('single'))
zone_blp.add_url_rule('/search', view_func=SearchZones.as_view('search'))
