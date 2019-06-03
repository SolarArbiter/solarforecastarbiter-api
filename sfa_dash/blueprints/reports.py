"""TEMPORARY MOCKUP ENDPOINTS
"""
from sfa_dash.blueprints.base import BaseView


class ReportsView(BaseView):
    template = 'dash/reports.html'

    def template_args(self):
        return {
            "page_title": 'Reports',
        }


class ReportForm(BaseView):
    template = 'forms/report_form.html'

    def template_args(self):
        return {
            "form_title": "Create new Report",
        }


class ReportView(BaseView):
    template = 'data/report.html'

    def template_args(self):
        return {}

    def get(self, uuid):
        return super().get()
