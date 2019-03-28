import uuid


import pandas as pd
import pytest
import pymysql


from sfa_api import create_app
from sfa_api.demo.sites import static_sites as demo_sites
from sfa_api.demo.observations import static_observations as demo_observations
from sfa_api.demo.forecasts import static_forecasts as demo_forecasts
from sfa_api.demo.values import generate_randoms
from sfa_api.utils import storage_interface


TESTINDEX = generate_randoms()[0].to_series()


@pytest.fixture(scope='module')
def app():
    app = create_app('TestingConfig')
    with app.app_context():
        try:
            storage_interface.mysql_connection()
        except pymysql.err.OperationalError:
            pytest.skip('No connection to test database')
        else:
            yield app


@pytest.fixture()
def user(app):
    ctx = app.test_request_context()
    ctx.user = 'auth0|testtesttest'
    ctx.push()
    yield
    ctx.pop()


@pytest.fixture()
def invalid_user(app):
    ctx = app.test_request_context()
    ctx.user = 'bad'
    ctx.push()
    yield
    ctx.pop()


@pytest.fixture(params=[0, 1, 2, 3])
def startend(request):
    if request.param == 0:
        start = None
        end = None
    elif request.param == 1:
        start = pd.Timestamp('20190101T1205Z')
        end = None
    elif request.param == 2:
        start = None
        end = pd.Timestamp('20190101T1215Z')
    else:
        start = pd.Timestamp('20190101T1205Z')
        end = pd.Timestamp('20190101T1215Z')
    return start, end


def test_get_cursor_and_timezone(app):
    with storage_interface.get_cursor('standard') as cursor:
        cursor.execute('SELECT @@session.time_zone')
        res = cursor.fetchone()[0]
    assert res == '+00:00'


def test_list_observations(app, user):
    observations = storage_interface.list_observations()
    for obs in observations:
        assert obs == demo_observations[obs['observation_id']]


def test_list_observations_invalid_user(app, invalid_user):
    observations = storage_interface.list_observations()
    assert len(observations) == 0


def test_list_observations_invalid_site(app, user):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.list_observations(str(uuid.uuid1()))


@pytest.mark.parametrize('observation_id', demo_observations.keys())
def test_read_observation(app, user, observation_id):
    observation = storage_interface.read_observation(observation_id)
    assert observation == demo_observations[observation_id]


def test_read_observation_invalid_observation(app, user):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_observation(str(uuid.uuid1()))


def test_read_observation_invalid_user(app, invalid_user):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_observation(list(demo_observations.keys())[0])


@pytest.mark.parametrize('observation_id', demo_observations.keys())
def test_read_observation_values(app, user, observation_id, startend):
    start, end = startend
    observation_values = storage_interface.read_observation_values(
        observation_id, start, end)
    assert (observation_values.index == TESTINDEX.loc[start:end].index).all()
    assert (observation_values.columns == ['value', 'quality_flag']).all()


def test_read_observation_values_invalid_observation(app, user, startend):
    start, end = startend
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_observation_values(
            str(uuid.uuid1()), start, end)


def test_read_observation_values_invalid_user(app, invalid_user, startend):
    start, end = startend
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_observation_values(
            list(demo_observations.keys())[0], start, end)


def test_list_forecasts(app, user):
    forecasts = storage_interface.list_forecasts()
    for fx in forecasts:
        assert fx == demo_forecasts[fx['forecast_id']]


def test_list_forecasts_invalid_user(app, invalid_user):
    forecasts = storage_interface.list_forecasts()
    assert len(forecasts) == 0


def test_list_forecasts_invalid_site(app, user):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.list_forecasts(str(uuid.uuid1()))


@pytest.mark.parametrize('forecast_id', demo_forecasts.keys())
def test_read_forecast(app, user, forecast_id):
    forecast = storage_interface.read_forecast(forecast_id)
    assert forecast == demo_forecasts[forecast_id]


def test_read_forecast_invalid_forecast(app, user):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_forecast(str(uuid.uuid1()))


def test_read_forecast_invalid_user(app, invalid_user):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_forecast(list(demo_forecasts.keys())[0])


@pytest.mark.parametrize('forecast_id', demo_forecasts.keys())
def test_read_forecast_values(app, user, forecast_id, startend):
    start, end = startend
    forecast_values = storage_interface.read_forecast_values(
        forecast_id, start, end)
    assert (forecast_values.index == TESTINDEX.loc[start:end].index).all()
    assert (forecast_values.columns == ['value']).all()


def test_read_forecast_values_invalid_forecast(app, user, startend):
    start, end = startend
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_forecast_values(
            str(uuid.uuid1()), start, end)


def test_read_forecast_values_invalid_user(app, invalid_user, startend):
    start, end = startend
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_forecast_values(
            list(demo_forecasts.keys())[0], start, end)


@pytest.mark.parametrize('site_id', demo_sites.keys())
def test_read_site(app, user, site_id):
    site = storage_interface.read_site(site_id)
    assert site == demo_sites[site_id]


def test_read_site_invalid_site(app, user):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_site(str(uuid.uuid1()))


def test_read_site_invalid_user(app, invalid_user):
    with pytest.raises(storage_interface.StorageAuthError):
        storage_interface.read_site(list(demo_sites.keys())[0])


def test_list_sites(app, user):
    sites = storage_interface.list_sites()
    for site in sites:
        assert site == demo_sites[site['site_id']]


def test_list_sites_invalid_user(app, invalid_user):
    sites = storage_interface.list_sites()
    assert len(sites) == 0
