from collections import OrderedDict


from flask import url_for, render_template, request, flash
from flask.views import MethodView
import pandas as pd

from sfa_dash.errors import DataRequestException
from sfa_dash.blueprints.util import timeseries_adapter


class BaseView(MethodView):
    subnav_format = {}

    def insert_plot(self, uuid, start, end):
        """Generate a plot and bokeh script for the data between
        start and end. Note that the core library requires a 'site'
        key with the full site metadata to create a plot.

        This inserts the rendered plot html and bokeh script into
        the temp_args keys plot and bokeh_script respectively.
        """
        try:
            values = self.api_handle.get_values(
                uuid, params={'start': start, 'end': end})
        except DataRequestException as e:
            if e.status_code == 422:
                self.temp_args.update({'warnings': e.errors})
            else:
                self.temp_args.update({'warnings': {
                    'Value Access': [
                        f'{self.human_label} values inaccessible.']},
                })
        else:
            script_plot = timeseries_adapter(
                self.plot_type, self.metadata, values)
            if script_plot is None:
                self.temp_args.update({
                    'messages': {
                        'Data': [
                            (f"No data available for this {self.human_label} "
                             "during this period.")]},
                })
            else:
                self.temp_args.update({
                    'plot': script_plot[1],
                    'includes_bokeh': True,
                    'bokeh_script': script_plot[0]
                })

    def set_timerange(self):
        """Retrieve the available timerange for an object and set the
        'min_timestamp' and 'max_timestamp' keys in metdata. If the range
        cannot be found the keys will not be set.
        """
        try:
            timerange = self.api_handle.valid_times(self.metadata[self.id_key])
        except DataRequestException:
            return
        else:
            self.metadata['timerange_start'] = timerange['min_timestamp']
            self.metadata['timerange_end'] = timerange['max_timestamp']

    def parse_start_end_from_querystring(self):
        """Attempts to find the start and end query parameters. If not found,
        returns defaults spanning the last three days. Used for setting
        reasonable defaults for requesting data for plots.

        Returns
        -------
        start,end
            Tuple of ISO 8601 datetime strings representing the start, end.
        """
        # set default arg to an invalid timestamp, to trigger ValueError
        start_arg = request.args.get('start', 'x')
        end_arg = request.args.get('end', 'x')
        try:
            end = pd.Timestamp(end_arg)
        except ValueError:
            meta_end = self.metadata.get('timerange_end')
            if meta_end is None:
                end = pd.Timestamp.utcnow()
            else:
                end = pd.Timestamp(meta_end)
        try:
            start = pd.Timestamp(start_arg)
        except ValueError:
            start = end - pd.Timedelta('3days')
        return start, end

    def format_download_params(self, form_data):
        """Parses start and end time and the format from the posted form.
        Returns headers and query parameters for requesting the data.

        Parameters
        ----------
        form_data: dict
            Dictionary of posted form values.

        Returns
        -------
        headers: dict
            The accept headers set to 'text/csv' or 'application/json'
            based on the selected format.
        params: dict
            Query parameters start and end, both formatted in iso8601 and
            localized to the provided timezone.
        """
        start_dt = pd.Timestamp(form_data['start'], tz='utc')
        end_dt = pd.Timestamp(form_data['end'], tz='utc')
        params = {
            'start': start_dt.isoformat(),
            'end': end_dt.isoformat(),
        }
        headers = {'Accept': form_data['format']}
        return headers, params

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

    def flash_api_errors(self, errors):
        """Formats a dictionary of api errors and flashes them to the user on
        the next request.

        Parameters
        ----------
        errors: dict
            Dict of errors returned by the API.
        """
        to_flash = [f'({key}) {", ".join(msg)}' for key, msg in errors.items()]
        for error in to_flash:
            flash(error, 'error')

    def template_args(self):
        return {}

    def get(self, **kwargs):
        if hasattr(self, 'subnav') and self.subnav is not None:
            subnav = self.subnav
        else:
            subnav = {}
        return render_template(self.template, subnav=subnav,
                               **self.template_args(), **kwargs)
