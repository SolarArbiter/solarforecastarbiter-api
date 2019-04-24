from sfa_dash.blueprints.util import DataTables
from sfa_dash.blueprints.dash import SiteDashView
from sfa_dash.api_interface import sites
from flask import render_template, url_for, request, abort


class SitesListingView(SiteDashView):
    """Render a page with a table listing Sites.
    """
    template = 'org/obs.html'

    def breadcrumb_html(self, site=None, **kwargs):
        breadcrumb_format = '/<a href="{url}">{text}</a>'
        breadcrumb = breadcrumb_format.format(
            url=url_for('data_dashboard.sites'),
            text='Sites')
        return breadcrumb

    def get_template_args(self, create=None, **kwargs):
        """Create a dictionary containing the required arguments for the template
        """
        template_args = {}
        template_args['data_table'] = DataTables.get_site_table(create=create,
                                                                **kwargs)
        template_args['current_path'] = request.path
        if create is not None:
            template_args['page_title'] = f"Select a Site"
        else:
            template_args['breadcrumb'] = self.breadcrumb_html(**kwargs)
        return template_args

    def get(self, **kwargs):
        # Update kwargs with the create query parameter
        kwargs.update({'create': request.args.get('create')})
        return render_template(self.template,
                               **self.get_template_args(**kwargs))


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
        metadata_request = sites.get_metadata(uuid)
        if metadata_request.status_code != 200:
            abort(404)
        self.metadata = metadata_request.json()
        return render_template(self.template, **self.template_args(**kwargs))
