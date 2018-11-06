from flask import Blueprint
from flask.views import MethodView


from sfa_api import spec, ma
from sfa_api.demo import Site


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
    station_id = ma.String(
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
        sites = [Site() for i in range(3)]
        return SiteResponseSchema(many=True).jsonify(sites)

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
        return SiteResponseSchema().jsonify(Site())


class SiteView(MethodView):
    def get(self, site_id, *args):
        """
        ---
        summary: Get site information
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
        # TODO: replace demo data
        demo_obs = Site()
        return SiteResponseSchema().jsonify(demo_obs)

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
        # TODO: replace demo response
        return f'{site_id} deleted.'

    def put(self, site_id, *args):
        """
        ---
        summary: Update site
        description: Update a site's metadata.
        tags:
          - Sites
        parameters:
          - $ref: '#/components/parameters/site_id'
        requestBody:
          description: JSON representation of an site's metadata.
          required: True
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SiteDefinition'
        responses:
          200:
            description: Site updated successfully.
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        return


class SiteObservations(MethodView):
    def get(self, site_id, *args):
        """
        ---
        summary: Get site observations
        description: >
          Get all observations associated with site that user has access to
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
        return


class SiteForecasts(MethodView):
    def get(self, site_id, *args):
        """
        ---
        summary: Get site forecasts
        description: >
          Get all forecasts associated with site that user has access to
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
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
             $ref: '#/components/responses/404-NotFound'
        """
        return


spec.add_parameter('site_id', 'path',
                   type='string',
                   description="Site's unique identifier.",
                   required='true')


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
