from flask import Blueprint, request, jsonify
from flask.views import MethodView


from sfa_api.utils.errors import BadAPIRequest
from sfa_api.utils.storage import get_storage
from sfa_api.utils.request_handling import parse_to_timestamp
from sfa_api.schema import (OutageSchema)


class OutagesView(MethodView):
    def get(self, *args):
        """
        ---
        summary: Get Solar Forecast Arbiter outage data.
        tags:
        - Outages
        parameters:
          - start_time
          - end_time
        responses:
          200:
            description: Observation values retrieved successfully.
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/ObservationValues'
          400:
            $ref: '#/components/responses/400-TimerangeTooLarge'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        start = request.args.get('start', None)
        end = request.args.get('end', None)
        storage = get_storage()
        outages = storage.list_system_outages()
        if start is not None:
            try:
                start = parse_to_timestamp(start)
            except ValueError:
                raise BadAPIRequest({'start': ['Invalid start date format']})
            outages = list(filter(lambda x: x['end'] >= start, outages))
        if end is not None:
            try:
                end = parse_to_timestamp(end)
            except ValueError:
                raise BadAPIRequest({'end': ['Invalid end date format']})
            outages = list(filter(lambda x: x['start'] <= end, outages))
        return jsonify(OutageSchema(many=True).dump(outages))


outage_blp = Blueprint(
    'outages', 'outages', url_prefix='/outages',
)

outage_blp.add_url_rule('/', view_func=OutagesView.as_view('all'))
