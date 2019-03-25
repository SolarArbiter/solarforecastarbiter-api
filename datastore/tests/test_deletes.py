import pytest
import pymysql


from conftest import bin_to_uuid


@pytest.fixture()
def site_obj(cursor, valueset, new_site):
    org = valueset[0][0]
    user = valueset[1][0]
    auth0id = user['auth0_id']
    site = new_site(org=org)
    return auth0id, str(bin_to_uuid(site['id'])), site


@pytest.fixture()
def fx_obj(site_obj, new_forecast):
    auth0id, _, site = site_obj
    fx = new_forecast(site=site)
    return auth0id, str(bin_to_uuid(fx['id']))


@pytest.fixture()
def obs_obj(site_obj, new_observation):
    auth0id, _, site = site_obj
    obs = new_observation(site=site)
    return auth0id, str(bin_to_uuid(obs['id']))


@pytest.fixture()
def allow_delete(cursor, new_permission, valueset):
    def do(what):
        org = valueset[0][0]
        role = valueset[2][0]
        perm = new_permission('delete', what, True, org=org)
        cursor.execute(
            'INSERT INTO role_permission_mapping (role_id, permission_id)'
            ' VALUES (%s, %s)', (role['id'], perm['id']))
    return do


@pytest.fixture()
def allow_delete_site(allow_delete):
    allow_delete('sites')


@pytest.fixture()
def allow_delete_observation(allow_delete):
    allow_delete('observations')


@pytest.fixture()
def allow_delete_forecast(allow_delete):
    allow_delete('forecasts')


def test_delete_site(cursor, site_obj, allow_delete_site):
    auth0id, siteid, *_ = site_obj
    cursor.execute(
        'SELECT COUNT(id) FROM arbiter_data.sites WHERE id = UUID_TO_BIN(%s, 1)',  # NOQA
        siteid)
    assert cursor.fetchone()[0] > 0
    cursor.callproc('delete_site', (auth0id, siteid))
    cursor.execute(
        'SELECT COUNT(id) FROM arbiter_data.sites WHERE id = UUID_TO_BIN(%s, 1)',  # NOQA
        siteid)
    assert cursor.fetchone()[0] == 0


def test_delete_site_denied(cursor, site_obj):
    auth0id, siteid, *_ = site_obj
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('delete_site', (auth0id, siteid))
        assert e.errcode == 1142


def test_delete_forecast(cursor, fx_obj, allow_delete_forecast):
    auth0id, fxid = fx_obj
    cursor.execute(
        'SELECT COUNT(id) FROM arbiter_data.forecasts WHERE id = UUID_TO_BIN(%s, 1)',  # NOQA
        fxid)
    assert cursor.fetchone()[0] > 0
    cursor.callproc('delete_forecast', (auth0id, fxid))
    cursor.execute(
        'SELECT COUNT(id) FROM arbiter_data.forecasts WHERE id = UUID_TO_BIN(%s, 1)',  # NOQA
        fxid)
    assert cursor.fetchone()[0] == 0


def test_delete_forecast_denied(cursor, fx_obj):
    auth0id, fxid = fx_obj
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('delete_forecast', (auth0id, fxid))
        assert e.errcode == 1142


def test_delete_observation(cursor, obs_obj, allow_delete_observation):
    auth0id, obsid = obs_obj
    cursor.execute(
        'SELECT COUNT(id) FROM arbiter_data.observations WHERE id = UUID_TO_BIN(%s, 1)',  # NOQA
        obsid)
    assert cursor.fetchone()[0] > 0
    cursor.callproc('delete_observation', (auth0id, obsid))
    cursor.execute(
        'SELECT COUNT(id) FROM arbiter_data.observations WHERE id = UUID_TO_BIN(%s, 1)',  # NOQA
        obsid)
    assert cursor.fetchone()[0] == 0


def test_delete_observation_denied(cursor, obs_obj):
    auth0id, obsid = obs_obj
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('delete_observation', (auth0id, obsid))
        assert e.errcode == 1142
