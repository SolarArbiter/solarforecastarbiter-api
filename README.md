[![Build Status](https://dev.azure.com/solararbiter/solarforecastarbiter/_apis/build/status/SolarArbiter.solarforecastarbiter-api?branchName=master)](https://dev.azure.com/solararbiter/solarforecastarbiter/_build/latest?definitionId=2&branchName=master)
[![codecov](https://codecov.io/gh/SolarArbiter/solarforecastarbiter-api/branch/master/graph/badge.svg)](https://codecov.io/gh/SolarArbiter/solarforecastarbiter-api)

# Solar Forecast Arbiter API

This repository contains the code and development of the Solar Forecast Arbiter
API available at api.solarforecastarbiter.org. At the moment, classes are
skeletons to aid in API design.


The API is built with Python and depends on the following libraries:
- Flask
- webargs
- marshmallow
- flask-talisman
- flask-seasurf
- apispec
- flask-rest-api


To run the API in development mode, first ``pip install -e`` the package. Then, run:

``` sh
FLASK_APP=sfa_api FLASK_ENV=development SFA_API_STATIC_DATA=true flask run -p <port>
```
