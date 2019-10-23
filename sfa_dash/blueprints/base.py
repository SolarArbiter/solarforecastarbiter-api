from collections import OrderedDict


from flask import url_for, render_template
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
            site_name = metadata.get('site_id')
            link_html = site_name
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
        """Build the breadcrumb navigation from an OrderedDict.

        Parameters
        ----------
        breadcrumb_dict: OrderedDict
            A dictionary of link_text: url. Urls can be relative
            or absolute. See BaseView.get_breadcrumb_dict for an
            example of the expected format.

        Returns
        -------
        breadcrumb: str
            HTML breadcrumb to be printed in the template. Note that
            jinja requires the use of the 'safe' filter to avoid
            escaping tags.
        """
        breadcrumb = ''
        for link_text, href in breadcrumb_dict.items():
            breadcrumb += f'/<a href="{href}">{link_text}</a>'
        return breadcrumb

    def get_breadcrumb_dict(self):
        """Creates an ordered dictionary used for building the page's
        breadcrumb. Output can be passed to the BaseView.breadcrumb_html
        function.

        This is a base function that should be overridden by any view
        that wants to display a breadcrumb.

        Notes
        -----
        The breadcrumb dictionary should be built in the form:

            { "link text": "url", ...}

            Example:

            { "home": "/", "users": "/users" }

        Where the order of the keys is rendered from left to right.
        """
        return OrderedDict()

    def template_args(self):
        return {}

    def get(self, **kwargs):
        if hasattr(self, 'subnav') and self.subnav is not None:
            subnav = self.subnav
        else:
            subnav = {}
        return render_template(self.template, subnav=subnav,
                               **self.template_args(), **kwargs)
