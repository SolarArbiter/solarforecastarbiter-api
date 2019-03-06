from flask import Blueprint, jsonify, request, abort
from flask.views import MethodView
from marshmallow import ValidationError


from sfa_api import spec
from sfa_api.schema import (SiteSchema, SiteResponseSchema,
                            ForecastSchema, ObservationSchema)
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
            dref: '#/components/responses/401-Unauthorized'
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
        description: Create a new Site by posting metadata.
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
                  $ref: '#/components/schemas/SiteMetadata'
          400:
            $ref: '#/components/responses/400-BadRequest'
          401:
            $ref: '#/components/responses/401-Unauthorized'
        """
        data = request.get_json()
        try:
            site = SiteSchema().load(data)
        except ValidationError as err:
            return jsonify(err.messages), 400
        storage = get_storage()
        site_id = storage.store_site(site)
        return site_id


class SiteView(MethodView):
    def get(self, site_id, *args):
        """
        ---
        summary: Get site metadata
        tags:
        - Sites
        parameters:
        - $ref: '#/components/parameters/site_id'
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
        if site is None:
            abort(404)
        return jsonify(SiteResponseSchema().dump(site))

    def delete(self, site_id, *args):
        """
        ---
        summary: Delete site
        description: Delete an Site, including its values and metadata.
        tags:
          - Sites
        parameters:
        - $ref: '#/components/parameters/site_id'
        responses:
          200:
            description: Site deleted Successfully.
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        storage = get_storage()
        site = storage.delete_site(site_id)
        return jsonify(SiteResponseSchema().dump(site))


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
        - $ref: '#/components/parameters/site_id'
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
        - $ref: '#/components/parameters/site_id'
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
        forecasts = storage.list_forecasts(site_id)
        return jsonify(ForecastSchema(many=True).dump(forecasts))


spec.components.parameter(
    'site_id', 'path',
    {
        'schema': {
            'type': 'string',
            'format': 'uuid'
        },
        'description': "Site's unique identifier.",
        'required': 'true'
    })

site_blp = Blueprint(
    'sites', 'sites', url_prefix='/sites',
)
site_blp.add_url_rule('/', view_func=AllSitesView.as_view('all'))
site_blp.add_url_rule(
    '/<site_id>', view_func=SiteView.as_view('single'))
site_blp.add_url_rule('/<site_id>/observations',
                      view_func=SiteObservations.as_view('observations'))
site_blp.add_url_rule('/<site_id>/forecasts',
                      view_func=SiteForecasts.as_view('forecasts'))
