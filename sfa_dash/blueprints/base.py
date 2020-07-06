from copy import deepcopy


from flask import url_for, render_template, request, flash, current_app
from flask.views import MethodView
import pandas as pd

from sfa_dash.api_interface import sites, aggregates
from sfa_dash.blueprints.util import timeseries_adapter
from sfa_dash.errors import DataRequestException


class BaseView(MethodView):
    subnav_format = {}

    def insert_plot(self, uuid, start, end):
        """Generate a plot and bokeh script for the data between
        start and end. Note that the core library requires a 'site'
        key with the full site metadata to create a plot.

        This inserts the rendered plot html and bokeh script into
        the template_args keys plot and bokeh_script respectively.

        Parameters
        ----------
        uuid: str
            The UUID of the object to request data for.
        start: datetime
        end: datetime
        """
        # determine limit by number of datapoints in the maximum allowable
        # time range based on interval length.
        timerange_limit = current_app.config['MAX_DATA_RANGE_DAYS']
        interval_length = self.metadata['interval_length']
        max_pts = min(
            timerange_limit / pd.Timedelta(f'{interval_length} minutes'),
            current_app.config['MAX_PLOT_DATAPOINTS']
        )

        timerange_minutes = (end - start).total_seconds() / 60
        total_points = timerange_minutes / interval_length

        if total_points <= max_pts:
            try:
                values = self.api_handle.get_values(
                    uuid, params={'start': start.isoformat(),
                                  'end': end.isoformat()})
            except DataRequestException as e:
                if e.status_code == 422:
                    self.template_args.update({'warnings': e.errors})
                else:
                    self.template_args.update({'warnings': {
                        'Value Access': [
                            f'{self.human_label} values inaccessible.']},
                    })
            else:
                script_plot = timeseries_adapter(
                    self.plot_type, self.metadata, values)
                if script_plot is None:
                    self.template_args.update({
                        'messages': {
                            'Data': [
                                ("No data available for this "
                                 f"{self.human_label} during this period.")]},
                    })
                else:
                    self.template_args.update({
                        'plot': script_plot[1],
                        'includes_bokeh': True,
                        'bokeh_script': script_plot[0]
                    })
        else:
            allowable_days = pd.Timedelta(f"{max_pts*interval_length} minutes")
            self.template_args.update({
                'plot': '<div class="alert alert-warning">Too many datapoints '
                        'to display. The maximum number of datapoints to plot '
                        f'is {max_pts}. This amounts to {allowable_days.days} '
                        f'days and {allowable_days.components.hours} hours of '
                        f'data. The requested data contains {total_points}'
                        ' datapoints.</div>'
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
        start_arg = request.args.get('start')
        end_arg = request.args.get('end')
        utc_now = pd.Timestamp.utcnow()
        try:
            end = pd.Timestamp(end_arg)
        except ValueError:
            end = None
        if pd.isnull(end):
            meta_end = self.metadata.get('timerange_end')
            if meta_end is None:
                end = utc_now
            else:
                end = pd.Timestamp(meta_end)
        try:
            start = pd.Timestamp(start_arg)
        except ValueError:
            start = None
        if pd.isnull(start):
            if end > utc_now:
                start = utc_now - pd.Timedelta('1day')
            else:
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

    def breadcrumb_html(self, breadcrumb_list):
        """Build the breadcrumb navigation from an OrderedDict.

        Parameters
        ----------
        breadcrumb_list: list of 2-tuples
            List of (link_text, url) tuples. Urls can be relative
            or absolute. See BaseView.get_breadcrumb for an
            example of the expected format.

        Returns
        -------
        breadcrumb: str
            HTML breadcrumb to be printed in the template. Note that
            jinja requires the use of the 'safe' filter to avoid
            escaping tags.
        """
        breadcrumb = ''
        for (link_text, href) in breadcrumb_list:
            breadcrumb += f'/<a href="{href}">{link_text}</a>'
        return breadcrumb

    def get_breadcrumb(self):
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
        return []

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

    def safe_metadata(self):
        """Creates a copy of the metadata attribute without the
        `extra_parameters` keys.
        """
        def _pop_nonjson(meta_dict):
            new_dict = deepcopy(meta_dict)
            new_dict.pop('extra_parameters', None)
            new_dict.pop('location_link', None)
            for key, val in meta_dict.items():
                if isinstance(val, dict):
                    new_dict[key] = _pop_nonjson(val)
            return new_dict
        return _pop_nonjson(self.metadata)

    def set_site_or_aggregate_metadata(self):
        """Searches for a site_id or aggregate_id  in self.metadata
        and loads the expected metadata object from the api in either
        the 'site' or 'aggregate' key. If the object could not be retrieved,
        sets a warning and reraises the DataRequestError.
        """
        if self.metadata.get('site_id') is not None:
            try:
                self.metadata['site'] = sites.get_metadata(
                    self.metadata['site_id'])
            except DataRequestException:
                self.template_args.update({
                    'warnings': {
                        'Site Access': [
                            'Site inaccessible. Plots will not be displayed.']
                    },
                })
                raise
        elif self.metadata.get('aggregate_id'):
            try:
                self.metadata['aggregate'] = aggregates.get_metadata(
                    self.metadata['aggregate_id'])
            except DataRequestException:
                self.template_args.update({
                    'warnings': {
                        'Aggregate Access': [
                            'Aggregate inaccessible. Plots will not be '
                            'displayed.']
                    },
                })
                raise
        else:
            self.template_args.update({
                'warnings': {
                    'Warning': [
                        'Site or aggregate has been deleted.'],
                }
            })
            raise DataRequestException(404)

    def set_site_or_aggregate_link(self):
        """Creates a url to the forecast's site or aggregate. For injection
        into the metadata template.

        Returns
        -------
        link_html: str
            An anchor tag referencing the site/aggregates page on the
            dashboard or a string uuid if the metadata wasn't not available,
            indicating that the current user does not have access to the
            site or aggregate.
        """
        if self.metadata.get('site_id') is not None:
            if self.metadata.get('site') is not None:
                site_metadata = self.metadata.get('site')
                site_name = site_metadata['name']
                site_id = site_metadata['site_id']
                site_href = url_for('data_dashboard.site_view',
                                    uuid=site_id)
                link_html = f'<a href="{site_href}">{site_name}</a>'
            else:
                link_html = self.metadata['site_id']
        elif self.metadata.get('aggregate_id') is not None:
            if self.metadata.get('aggregate') is not None:
                aggregate_metadata = self.metadata.get('aggregate')
                aggregate_name = aggregate_metadata['name']
                aggregate_id = aggregate_metadata['aggregate_id']
                aggregate_href = url_for('data_dashboard.aggregate_view',
                                         uuid=aggregate_id)
                link_html = f'<a href="{aggregate_href}">{aggregate_name}</a>'
            else:
                link_html = self.metadata['aggregate_id']
        else:
            link_html = 'Object Deleted'
        self.metadata['location_link'] = link_html

    def set_template_args(self):
        self.template_args = {}

    def get(self, **kwargs):
        if hasattr(self, 'subnav') and self.subnav is not None:
            subnav = self.subnav
        else:
            subnav = {}
        self.set_template_args()
        return render_template(self.template, subnav=subnav,
                               **self.template_args, **kwargs)
