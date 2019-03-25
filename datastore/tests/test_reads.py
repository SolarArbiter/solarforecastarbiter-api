import pytest
import pymysql


from conftest import bin_to_uuid


@pytest.fixture()
def insertuser(cursor, new_permission, valueset, new_user):
    org = valueset[0][0]
    user = valueset[1][0]
    role = valueset[2][0]
    site = valueset[3][0]
    fx = valueset[5][0]
    obs = valueset[6][0]
    for thing in (user, site, fx, obs):
        thing['strid'] = str(bin_to_uuid(thing['id']))
    cursor.execute(
        "DELETE FROM permissions WHERE action = 'read'")
    return user, site, fx, obs, org, role


@pytest.fixture()
def allow_read_sites(cursor, new_permission, insertuser):
    user, site, fx, obs, org, role = insertuser
    perm = new_permission('read', 'sites', True, org=org)
    cursor.execute(
        'INSERT INTO role_permission_mapping (role_id, permission_id) VALUES '
        '(%s, %s)', (role['id'], perm['id']))


@pytest.fixture()
def allow_read_observations(cursor, new_permission, insertuser):
    user, site, fx, obs, org, role = insertuser
    perm = new_permission('read', 'observations', True, org=org)
    cursor.execute(
        'INSERT INTO role_permission_mapping (role_id, permission_id) VALUES '
        '(%s, %s)', (role['id'], perm['id']))


@pytest.fixture()
def allow_read_forecasts(cursor, new_permission, insertuser):
    user, site, fx, obs, org, role = insertuser
    perm = new_permission('read', 'forecasts', True, org=org)
    cursor.execute(
        'INSERT INTO role_permission_mapping (role_id, permission_id) VALUES '
        '(%s, %s)', (role['id'], perm['id']))


def test_read_site(dictcursor, insertuser, allow_read_sites):
    auth0id = insertuser[0]['auth0_id']
    site = insertuser[1]
    dictcursor.callproc('read_site', (auth0id, site['strid']))
    res = dictcursor.fetchall()[0]
    site['id'] = site['strid']
    del site['strid']
    site['organization_id'] = str(bin_to_uuid(site['organization_id']))
    del res['created_at']
    del res['modified_at']
    assert res == site


def test_read_site_denied(cursor, insertuser):
    auth0id = insertuser[0]['auth0_id']
    site = insertuser[1]
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_site', (auth0id, site['strid']))
        assert e.errcode == 1142


def test_read_observation(dictcursor, insertuser, allow_read_observations):
    auth0id = insertuser[0]['auth0_id']
    observation = insertuser[3]
    dictcursor.callproc('read_observation', (auth0id, observation['strid']))
    res = dictcursor.fetchall()[0]
    observation['id'] = observation['strid']
    del observation['strid']
    observation['site_id'] = str(bin_to_uuid(observation['site_id']))
    observation['organization_id'] = str(bin_to_uuid(
        observation['organization_id']))
    del res['created_at']
    del res['modified_at']
    assert res == observation


def test_read_observation_denied(cursor, insertuser):
    auth0id = insertuser[0]['auth0_id']
    obs = insertuser[3]
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_observation', (auth0id, obs['strid']))
        assert e.errcode == 1142


def test_read_forecast(dictcursor, insertuser, allow_read_forecasts):
    auth0id = insertuser[0]['auth0_id']
    forecast = insertuser[2]
    dictcursor.callproc('read_forecast', (auth0id, forecast['strid']))
    res = dictcursor.fetchall()[0]
    forecast['id'] = forecast['strid']
    del forecast['strid']
    forecast['site_id'] = str(bin_to_uuid(forecast['site_id']))
    forecast['organization_id'] = str(bin_to_uuid(
        forecast['organization_id']))
    del res['created_at']
    del res['modified_at']
    assert res == forecast


def test_read_forecast_denied(cursor, insertuser):
    auth0id = insertuser[0]['auth0_id']
    forecast = insertuser[3]
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_forecast', (auth0id, forecast['strid']))
        assert e.errcode == 1142
