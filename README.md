[![Build Status](https://dev.azure.com/solararbiter/solarforecastarbiter/_apis/build/status/SolarArbiter.solarforecastarbiter-dashboard?branchName=master)](https://dev.azure.com/solararbiter/solarforecastarbiter/_build/latest?definitionId=3&branchName=master)

## Contents
- [Introduction](#solar-forecast-arbiter-dashboard)
- [Installation](#installation)
- [Acknowledgements](#acknowledgements)

# Solar Forecast Arbiter Dashboard

The [Solar Forecast Arbiter dashboard](https://dashboard.solarforecastarbiter.org)
if the [Flask](http://flask.pocoo.org/) based web front-end to the
[Solar Forecast Arbiter Framework](https://solarforecastarbiter.org/documentation/framework/).

## Installation

Installing the dashboard in development mode can be achieved using pip with the
following command:

`pip install -r requirements.txt && pip install -e .`

### Prerequisites
The Solar Forecast Arbiter dashboard relies on the
[Solar Forecast Arbiter API](https://github.com/SolarArbiter/solarforecastarbiter-api).
Starting an instance of the API locally at port 5000 is necessary to use the
dashboard's local development instance.


### Running

**Required Environment Variables**

- `AUTH0_CLIENT_SECRET` and `AUTH0_CLIENT_ID`: These environment variables
  tell the dashboard which [AUTH0](https://auth0.com/) application to use for
  authentication.

**Running the dashboard**
- Start the dashboard with the following command:
  `FLASK_APP='sfa_dash:create_app("sfa_dash.config.LocalConfig"' flask run -p 8080`

- Open [http://localhost:8080/](http://localhost:8080/) in a browser to view the dashboard.

## Acknowledgements

The Solar Forecat Arbiter Dashboard utilizes the following open source projects.

- [Flask](https://flask.palletsprojects.com/en/1.1.x/)
- [Flask SeaSurf](https://flask-seasurf.readthedocs.io/en/latest/)
- [Flask Dance](https://flask-dance.readthedocs.io/en/latest/)
- [Flask SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/en/2.x/)
- [Bokeh](http://docs.bokeh.org/en/1.3.2/index.html)
- [Gunicorn](https://gunicorn.org/)
- [Gevent](http://www.gevent.org/)
- [PyMySQL](https://pymysql.readthedocs.io/en/latest/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Requests](https://requests.readthedocs.io/en/master/)
- [Python-JOSE](https://python-jose.readthedocs.io/en/latest/)
- [Blinker](https://pythonhosted.org/blinker/)
- [Cryptography](https://cryptography.io/en/latest/)
- [PyTables](https://www.pytables.org/usersguide/tutorials.html)
- [Pandas](https://pandas.pydata.org/)

Authenication services for the Solar Forecast Arbiter by provided by [Auth0](https://auth0.com/)

Centralized error reporting for the Solar Forecast Arbiter framework is provided by
[Sentry](https://sentry.io).
