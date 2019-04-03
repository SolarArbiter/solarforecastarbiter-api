import os
from sfa_dash import create_app


os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
app = create_app('sfa_dash.config.LocalConfig')
app.run(port=8080)
