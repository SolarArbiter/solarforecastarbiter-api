from flask import url_for
from flask.views import MethodView


class BaseView(MethodView):
    subnav_format = {}

    def generate_site_link(self, metadata):
        """Generate html for a link to a site page from an observation,
        forecast or site metadata dictionary.
        """
        # Existence of the 'site' key indicates an observation or forecast
        # so we must extract site data from the nested dict
        site_dict = metadata.get('site')
        if site_dict is None:
            site_name = metadata.get('name')
        else:
            site_name = site_dict['name']
        site_id = metadata['site_id']
        site_href = url_for('data_dashboard.site_view',
                            uuid=site_id)
        link_html = f'<a href="{site_href}">{site_name}</a>'
        return link_html

    def format_subnav(self, **kwargs):
        """
        """
        formatted_subnav = {}
        for url, linktext in self.subnav_format.items():
            formatted_subnav[url.format(**kwargs)] = linktext
        return formatted_subnav

    def breadcrumb_html(self, breadcrumb_dict):
        """Build the breadcrumb navigation from keyword arguments.
        """
        breadcrumb = ''
        for link_text, href in breadcrumb_dict:
            breadcrumb += f'/<a href="{href}">{link_text}</a>'
        return breadcrumb

    def get(self, **kwargs):
        template = self.env.get_template(self.template)
        if hasattr(self, 'subnav') and self.subnav is not None:
            subnav = self.subnav
        else:
            subnav = {}
        rendered = template.render(breadcrumb=self.breadcrumb_html(),
                                   current_path=self.request.uri,
                                   subnav=subnav)
        self.write(rendered)
