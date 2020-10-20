[![Build Status](https://dev.azure.com/solararbiter/solarforecastarbiter/_apis/build/status/SolarArbiter.solarforecastarbiter-api?branchName=master)](https://dev.azure.com/solararbiter/solarforecastarbiter/_build/latest?definitionId=2&branchName=master)
[![codecov](https://codecov.io/gh/SolarArbiter/solarforecastarbiter-api/branch/master/graph/badge.svg)](https://codecov.io/gh/SolarArbiter/solarforecastarbiter-api)

# Solar Forecast Arbiter API

This repository contains the code and development of the Solar Forecast Arbiter
API available at api.solarforecastarbiter.org. The API is built with Python and
Flask. See ``requirements.txt`` for a full list of dependencies. Error reporting
is graciously hosted by [Sentry](https://sentry.io).


To run the API in development mode, first ``pip install -e`` the package,
install requirements from ``requirements.txt`` and run:

``` sh
sfa-api devserver
```

A token for the testing user can be used to access this API following the
Authentication Docs on the
[local development server](http://localhost:5000/#section/Authentication) or
the [live dev API](https://dev-api.solarforecastarbiter.org/#section/Authentication).

A connection to a MySQL/Percona database on port 3306 with the migrations from
``datastore`` is required. One way to set up the database is to use
docker or podman to run a Percona container:

``` sh
podman run -d -p 3306:3306 -e MYSQL_ROOT_PASSWORD=testpassword -e MYSQL_DATABASE=arbiter_data -v $(pwd)/datastore/conf:/etc/my.cnf.d:z  percona:8.0-centos
```

Migrations to create the proper objects in the database can then be run with:

``` sh
podman run --rm -it --net host -v $(pwd)/datastore/migrations:/migrations:Z migrate/migrate -path=/migrations/ -database 'mysql://root:testpassword@tcp(127.0.0.1:3306)/arbiter_data' goto 59
```
