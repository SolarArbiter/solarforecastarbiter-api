from flask import Blueprint, request, make_response, url_for
from flask.views import MethodView
from marshmallow import ValidationError


from sfa_api import spec
from sfa_api.utils.errors import BadAPIRequest, NotFoundException
from sfa_api.utils import storage_interface
from sfa_api.schema import ReportPostSchema


class AllReportsView(MethodView):
    def get(self):
        """
        ---
        summary: List Reports.
        tags:
          - Reports
        responses:
          200:
            description: A List of reports
            content:
              application/json:
                schema:
                  type: array
                  items:
                    $ref: '#/components/schemas/ReportSchema'
          401:
            $ref: '#/components/responses/401-Unauthorized'
        """
        pass

    def post(self):
        """
        ---
        summary: Create a new report.
        tags:
          - Reports
        requestBody:
          description: Metadata of the report to create.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ReportMetadata'
        responses:
          201:
            description: Report created successfully.
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/ReportMetadata'
          400:
            $ref: '#/components/responses/400-BadRequest'
          401:
            $ref: '#/components/responses/401-Unauthorized'
        """
        data = request.get_json()
        try:
            report = ReportPostSchema().load(data)
        except ValidationError as err:
            raise BadAPIRequest(err.messages)
        report_id = storage_interface.store_report(report)
        if report_id is None:
            raise NotFoundException()
        response = make_response(report_id, 201)
        response.headers['Location'] = url_for('reports.single',
                                               report_id=report_id)
        return response


class ReportView(MethodView):
    def get(self, report_id):
        """
        ---
        summary: Get report metadata.
        tags:
          - Reports
        parameters:
        - $ref: '#/components/parameters/report_id'
        responses:
          200:
            description: Successfully retrieved report metadata.
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/ReportMetadata'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#components/responses/404-NotFound'
        """
        pass

    def delete(self, report_id):
        """
        ---
        summary: Delete a report.
        tags:
          - Reports
        parameters:
        - $ref: '#/components/parameters/report_id'

        responses:
          204:
            description: Deleted report successfully.
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#components/responses/404-NotFound'

        """
        pass


class ReportValuesView(MethodView):
    def get(self, report_id, object_id):
        """
        ---
        summary: Get the processed values used in a report
        tags:
        - Reports
        parameters:
        - $ref: '#/components/parameters/report_id'
        responses:
          200:
            description: Successfulyl retrieved
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/ReportValuesSchema'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        pass

    def post(self, report_id, object_id):
        """
        ---
        summary: Store processed values used in the report.
        tags:
        - Reports
        parameters:
        - $ref: '#/components/parameters/report_id'
        requestBody:
          description: >-
            JSON object mapping uuids to processed data used in report
            generation.
          required: True
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ReportValuesSchema'
        responses:
          204:
            description: Values stores successfully.
          400:
            $ref: '#/components/responses/400-BadRequest'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        # Should there be any other validation here? Do we need to
        # look up the original object and validate the processed data?
        pass


spec.components.parameter(
    'report_id', 'path',
    {
        'schema': {
            'type': 'string',
            'format': 'uuid'
        },
        'description': "The report's unique identifier",
        'required': 'true'
    })
reports_blp = Blueprint(
    'reports', 'reports', url_prefix='/reports',
)
reports_blp.add_url_rule(
    '/',
    view_func=AllReportsView.as_view('all')
)
reports_blp.add_url_rule(
    '/<report_id>',
    view_func=ReportView.as_view('metadata')
)
reports_blp.add_url_rule(
    '/<report_id>/values/<object_id>',
    view_func=ReportValuesView.as_view('values')
)
