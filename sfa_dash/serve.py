import os
import logging


from sfa_dash import create_app


logging.basicConfig(format='%(asctime)s %(levelname)8s %(name)25s %(message)s',
                    level=logging.INFO)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
app = create_app('sfa_dash.config.LocalConfig')
app.run(port=8080)
