from flask import Blueprint, jsonify, request, make_response, url_for
from flask.views import MethodView
from marshmallow import ValidationError


from sfa_api import spec
from sfa_api.schema import (SiteSchema, SiteResponseSchema,
                            SiteUpdateSchema,
                            ForecastSchema, ObservationSchema,
                            CDFForecastGroupSchema)
from sfa_api.utils.errors import BadAPIRequest
from sfa_api.utils.storage import get_storage


class AllSitesView(MethodView):
    def get(self, *args):
        """
        ---
        summary: List sites
        description: List all sites that the user has access to.
        tags:
        - Sites
        responses:
          200:
            description: A list of sites
            content:
              application/json:
                schema:
                  type: array
                  items:
                    $ref: '#/components/schemas/SiteMetadata'
          401:
            $ref: '#/components/responses/401-Unauthorized'
        """
        storage = get_storage()
        sites = storage.list_sites()
        return jsonify(SiteResponseSchema(many=True).dump(sites))

    def post(self, *args):
        """
        ---
        summary: Create site
        tags:
          - Sites
        description: >-
          Create a new Site by posting metadata. Note that POST
          requests to this endpoint without a trailing slash will
          result in a redirect response.
        requestBody:
          description: JSON respresentation of an site.
          required: True
          content:
            application/json:
                schema:
                  $ref: '#/components/schemas/SiteDefinition'
        responses:
          201:
            description: Site created successfully
            content:
              application/json:
                schema:
                  type: string
                  format: uuid
                  description: The uuid of the created site.
            headers:
              Location:
                schema:
                  type: string
                  format: uri
                  description: Url of the created site.
          400:
            $ref: '#/components/responses/400-BadRequest'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        data = request.get_json()
        try:
            site = SiteSchema().load(data)
        except ValidationError as err:
            return jsonify({'errors': err.messages}), 400
        storage = get_storage()
        site_id = storage.store_site(site)
        response = make_response(site_id, 201)
        response.headers['Location'] = url_for('sites.single',
                                               site_id=site_id)
        return response


class AllSitesInZoneView(MethodView):
    def get(self, zone, *args):
        """
        ---
        summary: List sites in a climate zone
        description: List all sites that the user has access to within
                     the climate zone.
        tags:
        - Sites
        - Climate Zones
        parameters:
        - zone
        responses:
          200:
            description: A list of sites
            content:
              application/json:
                schema:
                  type: array
                  items:
                    $ref: '#/components/schemas/SiteMetadata'
          401:
            $ref: '#/components/responses/401-Unauthorized'
        """
        storage = get_storage()
        sites = storage.list_sites_in_zone(zone.replace('+', ' '))
        return jsonify(SiteResponseSchema(many=True).dump(sites))


class SiteView(MethodView):
    def get(self, site_id, *args):
        """
        ---
        summary: Get site metadata
        tags:
        - Sites
        parameters:
        - site_id
        responses:
          200:
            description: Successfully retrieved site metadata.
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/SiteMetadata'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
             $ref: '#/components/responses/404-NotFound'
        """
        storage = get_storage()
        site = storage.read_site(site_id)
        return jsonify(SiteResponseSchema().dump(site))

    def post(self, site_id, *args):
        """
        ---
        summary: Update Site metadata.
        tags:
        - Sites
        parameters:
        - site_id
        requestBody:
          description: >-
            JSON object of site metadata to update.
            If modeling parameters are to be updated,
            all parameters for a given tracking_type are
            required even if most values are the same to
            ensure proper validation. An empty object
            for modeling_parameters will have the effect of
            clearing all modeling parameters.
          required: True
          content:
            application/json:
                schema:
                  $ref: '#/components/schemas/SiteUpdate'
        responses:
          200:
            description: Site updated successfully
            content:
              application/json:
                schema:
                  type: string
                  format: uuid
                  description: The uuid of the updated site.
            headers:
              Location:
                schema:
                  type: string
                  format: uri
                  description: Url of the updated site.
          400:
            $ref: '#/components/responses/400-BadRequest'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        data = request.get_json()
        try:
            changes = SiteUpdateSchema().load(data)
        except ValidationError as err:
            raise BadAPIRequest(err.messages)
        storage = get_storage()
        changes.update(changes.pop('modeling_parameters', {}))
        storage.update_site(site_id, **changes)
        response = make_response(site_id, 200)
        response.headers['Location'] = url_for('sites.single',
                                               site_id=site_id)
        return response

    def delete(self, site_id, *args):
        """
        ---
        summary: Delete site
        description: Delete an Site, including its values and metadata.
        tags:
          - Sites
        parameters:
        - site_id
        responses:
          204:
            description: Site deleted Successfully.
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        storage = get_storage()
        storage.delete_site(site_id)
        return '', 204


class SiteObservations(MethodView):
    def get(self, site_id, *args):
        """
        ---
        summary: Get site observations
        description: >
          Get metadata for all observations associated with site
          that user has access to.
        tags:
        - Sites
        parameters:
        - site_id
        responses:
          200:
            description: Successfully retrieved site observations.
            content:
              application/json:
                schema:
                  type: array
                  items:
                    $ref: '#/components/schemas/ObservationMetadata'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
             $ref: '#/components/responses/404-NotFound'
        """
        storage = get_storage()
        observations = storage.list_observations(site_id)
        return jsonify(ObservationSchema(many=True).dump(observations))


class SiteForecasts(MethodView):
    def get(self, site_id, *args):
        """
        ---
        summary: Get site forecasts
        description: >
          Get metadata for all forecasts associated with site that
          user has access to.
        tags:
        - Sites
        parameters:
        - site_id
        responses:
          200:
            description: Successfully retrieved site forecasts
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
        forecasts = storage.list_forecasts(site_id=site_id)
        return jsonify(ForecastSchema(many=True).dump(forecasts))


class SiteCDFForecastGroups(MethodView):
    def get(self, site_id, *args):
        """
        ---
        summary: Get site probabilistic forecast groups
        description: >
          Get metadata for all CDF forecasts associated with site that
          user has access to.
        tags:
        - Sites
        parameters:
        - site_id
        responses:
          200:
            description: Successfully retrieved site cdf forecasts
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
        forecasts = storage.list_cdf_forecast_groups(site_id)
        return jsonify(CDFForecastGroupSchema(many=True).dump(forecasts))


spec.components.parameter(
    'site_id', 'path',
    {
        'schema': {
            'type': 'string',
            'format': 'uuid'
        },
        'description': "Site's unique identifier.",
        'required': 'true',
        'name': 'site_id'
    })

site_blp = Blueprint(
    'sites', 'sites', url_prefix='/sites',
)
site_blp.add_url_rule('/', view_func=AllSitesView.as_view('all'))
site_blp.add_url_rule('/in/<zone_str:zone>',
                      view_func=AllSitesInZoneView.as_view('allinzone'))
site_blp.add_url_rule(
    '/<uuid_str:site_id>', view_func=SiteView.as_view('single'))
site_blp.add_url_rule('/<uuid_str:site_id>/observations',
                      view_func=SiteObservations.as_view('observations'))
site_blp.add_url_rule('/<uuid_str:site_id>/forecasts/single',
                      view_func=SiteForecasts.as_view('forecasts'))
site_blp.add_url_rule('/<uuid_str:site_id>/forecasts/cdf',
                      view_func=SiteCDFForecastGroups.as_view('cdf_forecasts'))
