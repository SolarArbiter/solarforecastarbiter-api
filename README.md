[![Build Status](https://dev.azure.com/solararbiter/solarforecastarbiter/_apis/build/status/SolarArbiter.solarforecastarbiter_dashboard?branchName=master)](https://dev.azure.com/solararbiter/solarforecastarbiter/_build/latest?definitionId=3&branchName=master)

# Solar Forecast Arbiter Dashboard
The front end [Flask](http://flask.pocoo.org/) application for the Solar Forecast Arbiter.

### Usage/ Installation

Currently the dashboard is hardcoded to utilize a local development api instance. These instructions will guide you through running it locally.

**You will need to set the environment variables `AUTH0_CLIENT_SECRET` and `AUTH0_CLIENT_ID` for authentication to operate correctly.**

- Install the [Solar Forecast Arbiter API](https://github.com/SolarArbiter/solarforecastarbiter-api) and run it with the `SFA_API_STATIC_DATA=true` option and `port` set to 5000.

- Install dashboard with `pip install -e .`

- Run the script with `python sfa_dash/serve.py`

- Open [http://localhost:8080/](http://localhost:8080/) in a browser to view the dashboard.


### Template Layout

base.html

 - Basic html structure, includes navbar, footer and head. Will conditionally include sidebar if `sidebar` variable is defined.

navbar.html

 - Includes header for logo/site name and main navigation.

head.html

 - The <head> html element.

sidebar.html

 - Left sidebar html to be included when the sidebar variable is defined either in a template or passed into the render() function.

footer.html

 - Site footer.

dash/

 - Dash includes secondary nav content and anything else that may be section-wide.

data/

 - Templates extending the `dash/data.html` dashboard.

org/

 - Templates extending the `dash/org.html` dashboard.

sections/

 - Templates to be included in others. I.E. a notifications section.
