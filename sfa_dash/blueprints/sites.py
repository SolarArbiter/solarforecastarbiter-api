from sfa_dash.blueprints.util import DataTables, handle_response
from sfa_dash.blueprints.dash import SiteDashView
from sfa_dash.api_interface import sites
from sfa_dash.errors import DataRequestException
from flask import render_template, url_for, request


class SitesListingView(SiteDashView):
    """Render a page with a table listing Sites.
    """
    template = 'data/table.html'

    def breadcrumb_html(self, site=None, **kwargs):
        breadcrumb_format = '/<a href="{url}">{text}</a>'
        breadcrumb = breadcrumb_format.format(
            url=url_for('data_dashboard.sites'),
            text='Sites')
        return breadcrumb

    def get_template_args(self):
        """Create a dictionary containing the required arguments for the template
        """
        template_args = {}
        template_args['data_table'] = DataTables.get_site_table()
        template_args['current_path'] = request.path
        template_args['breadcrumb'] = self.breadcrumb_html()
        return template_args

    def get(self):
        try:
            temp_args = self.get_template_args()
        except DataRequestException as e:
            temp_args = {'errors': e.errors}
        return render_template(self.template, **temp_args)


class SingleSiteView(SiteDashView):
    """Render a page to display the metadata of a a single Site.
    """
    template = 'data/site.html'

    def breadcrumb_html(self, **kwargs):
        bc_format = '/<a href="{url}">{text}</a>'
        bc = ''
        bc += bc_format.format(
            url=url_for('data_dashboard.sites'),
            text="Sites")
        bc += bc_format.format(
            url=url_for('data_dashboard.site_view',
                        uuid=self.metadata['site_id']),
            text=self.metadata['name'])
        return bc

    def get(self, uuid, **kwargs):
        try:
            self.metadata = handle_response(
                sites.get_metadata(uuid))
        except DataRequestException as e:
            return render_template(self.template, errors=e.errors)
        return render_template(self.template, **self.template_args(**kwargs))
