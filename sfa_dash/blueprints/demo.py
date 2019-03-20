from flask import Blueprint, render_template, abort
from sfa_dash.api_interface import demo_data
from sfa_dash.blueprints.base import BaseView

demo_blp = Blueprint('demo', 'demo', url_prefix='/demo')

class DemoViews(BaseView):
    def get(self, form_type):
        temp_args = {}
        if form_type=="obs_upload":
            metadata = {'name': 'GHI Instrument 1',
                        'variable': 'GHI',
                        'obs_id': '123e4567-e89b-12d3-a456-426655440000',
                        'site_id': '123e4567-e89b-12d3-a456-426655440001',
                        'value_type': 'Interval Mean',
                        'interval_label': 'beginning',
                        'site_link': '<a href="/sites/Ashland%20OR">Ashland OR</a>'}
            temp_args['metadata'] = render_template('data/metadata/observation_metadata.html',
                                                    **metadata)
            return render_template('forms/demo_obs_data_form.html', **temp_args)
        if form_type == "fx_upload":
            metadata = demo_data.forecast
            metadata['site_link'] = '<a href="/sites/Power%20Plant%201">Power Plant 1</a>'
            temp_args['metadata'] = render_template('data/metadata/forecast_metadata.html',
                                                    **metadata)
            return render_template('forms/demo_fx_data_form.html', **temp_args)
                                    
        abort(404) 


demo_blp.add_url_rule('/<form_type>/', view_func=DemoViews.as_view('site_form'))
