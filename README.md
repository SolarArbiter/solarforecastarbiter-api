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
FLASK_APP=sfa_api FLASK_ENV=development flask run -p <port>
```
