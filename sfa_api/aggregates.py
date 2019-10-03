from flask import Blueprint, request, jsonify, make_response, url_for, abort
from flask.views import MethodView
from marshmallow import ValidationError

from sfa_api.utils.request_handling import validate_start_end
from sfa_api.utils.errors import BadAPIRequest
from sfa_api.utils.storage import get_storage
from sfa_api.schema import (AggregateSchema,
                            AggregatePostSchema,
                            AggregateValuesSchema,
                            AggregateLinksSchema)


class AllAggregatesView(MethodView):
    def get(self, *args):
        """
        ---
        summary: List aggregates.
        description: List all aggregates that the user has access to.
        tags:
          - Aggregates
        responses:
          200:
            description: A list of aggregates
            content:
              application/json:
                schema:
                  type: array
                  items:
                    $ref: '#/components/schemas/AggregateMetadata'
          401:
            $ref: '#/components/responses/401-Unauthorized'
        """
        storage = get_storage()
        aggregates = storage.list_aggregates()
        return jsonify(AggregateSchema(many=True).dump(aggregates))

    def post(self, *args):
        """
        ---
        summary: Create aggregate.
        tags:
          - Aggregates
        description: >-
          Create a new Aggregate by posting metadata. Note that POST
          requests to this endpoint without a trailing slash will result
          in a redirect response.
        requestBody:
          description: JSON respresentation of an aggregate.
          required: True
          content:
            application/json:
                schema:
                  $ref: '#/components/schemas/AggregateDefinition'
        responses:
          201:
            description: Aggregate created successfully
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/AggregateMetadata'
          400:
            $ref: '#/components/responses/400-BadRequest'
          401:
            $ref: '#/components/responses/401-Unauthorized'
        """
        data = request.get_json()
        try:
            aggregate = AggregatePostSchema().load(data)
        except ValidationError as err:
            raise BadAPIRequest(err.messages)
        storage = get_storage()
        aggregate_id = storage.store_aggregate(aggregate)
        response = make_response(aggregate_id, 201)
        # response.headers['Location'] = url_for('aggregates.single',
        #                                        aggregate_id=aggregate_id)
        return response


class AggregateView(MethodView):
    def get(self, aggregate_id, **kwargs):
        """
        ---
        summary: Get Aggregate options.
        description: List options available for Aggregate.
        tags:
          - Aggregates
        responses:
          200:
            description: Aggregate options retrieved successfully.
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/AggregateLinks'
          400:
            $ref: '#/components/responses/400-BadRequest'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        storage = get_storage()
        aggregate = storage.read_aggregate(aggregate_id)
        if aggregate is None:
            abort(404)
        return jsonify(AggregateLinksSchema().dump(aggregate))

    def delete(self, aggregate_id, *args):
        """
        ---
        summary: Delete aggregate.
        description: Delete an Aggregate, including its values and metadata.
        tags:
          - Aggregates
        parameters:
        - $ref: '#/components/parameters/aggregate_id'
        responses:
          200:
            description: Aggregate deleted successfully.
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        storage = get_storage()
        storage.delete_aggregate(aggregate_id)
        return '', 204


class AggregateValuesView(MethodView):
    def get(self, aggregate_id, *args):
        """
        ---
        summary: Get Aggregate data.
        description: Get the timeseries values from the Aggregate entry.
        tags:
        - Aggregates
        parameters:
          - $ref: '#/components/parameters/aggregate_id'
          - $ref: '#/components/parameters/start_time'
          - $ref: '#/components/parameters/end_time'
          - $ref: '#/components/parameters/accepts'
        responses:
          200:
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/AggregateValues'
              text/csv:
                schema:
                  type: string
                example: |-
                  timestamp,value,quality_flag
                  2018-10-29T12:00:00Z,32.93,0
                  2018-10-29T13:00:00Z,25.17,0

          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        start, end = validate_start_end()
        storage = get_storage()
        values = storage.read_aggregate_values(aggregate_id, start, end)
        if values is None:
            abort(404)
        accepts = request.accept_mimetypes.best_match(['application/json',
                                                       'text/csv'])
        if accepts == 'application/json':
            values['timestamp'] = values.index
            dict_values = values.to_dict(orient='records')
            data = AggregateValuesSchema().dump(
                {"aggregate_id": aggregate_id, "values": dict_values})

            return jsonify(data)
        else:
            meta_url = url_for('aggregates.metadata',
                               aggregate_id=aggregate_id,
                               _external=True)
            csv_header = f'# aggregate_id: {aggregate_id}\n# metadata: {meta_url}\n'  # NOQA
            csv_values = values.to_csv(columns=['value', 'quality_flag'],
                                       index_label='timestamp',
                                       date_format='%Y%m%dT%H:%M:%S%z')
            csv_data = csv_header + csv_values
            response = make_response(csv_data, 200)
            response.mimetype = 'text/csv'
            return response


class AggregateMetadataView(MethodView):
    def get(self, aggregate_id, *args):
        """
        ---
        summary: Get Aggregate metadata.
        tags:
        - Aggregates
        parameters:
        - $ref: '#/components/parameters/aggregate_id'
        responses:
          200:
            description: Successfully retrieved aggregate metadata.
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/AggregateMetadata'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
             $ref: '#/components/responses/404-NotFound'
        """
        storage = get_storage()
        aggregate = storage.read_aggregate(aggregate_id)
        if aggregate is None:
            abort(404)
        return jsonify(AggregateSchema().dump(aggregate))


agg_blp = Blueprint(
    'aggregates', 'aggregates', url_prefix='/aggregates'
)
agg_blp.add_url_rule('/', view_func=AllAggregatesView.as_view('all'))
agg_blp.add_url_rule(
    '/<aggregate_id>', view_func=AggregateView.as_view('single'))
agg_blp.add_url_rule(
    '/<aggregate_id>/values',
    view_func=AggregateValuesView.as_view('values'))
agg_blp.add_url_rule(
    '/<aggregate_id>/metadata',
    view_func=AggregateMetadataView.as_view('metadata'))
