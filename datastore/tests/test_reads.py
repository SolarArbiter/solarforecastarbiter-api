import datetime as dt
import json
import random


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
    cdf = valueset[7][0]
    report = valueset[8][0]
    for thing in (user, site, fx, obs, cdf):
        thing['strid'] = str(bin_to_uuid(thing['id']))
    cursor.execute(
        "DELETE FROM permissions WHERE action = 'read'")
    return user, site, fx, obs, org, role, cdf, report


@pytest.fixture()
def allow_read_sites(cursor, new_permission, insertuser):
    user, site, fx, obs, org, role, cdf, report = insertuser
    perm = new_permission('read', 'sites', True, org=org)
    cursor.execute(
        'INSERT INTO role_permission_mapping (role_id, permission_id) VALUES '
        '(%s, %s)', (role['id'], perm['id']))


@pytest.fixture()
def allow_read_observations(cursor, new_permission, insertuser):
    user, site, fx, obs, org, role, cdf, report = insertuser
    perm = new_permission('read', 'observations', True, org=org)
    cursor.execute(
        'INSERT INTO role_permission_mapping (role_id, permission_id) VALUES '
        '(%s, %s)', (role['id'], perm['id']))


@pytest.fixture()
def allow_read_observation_values(cursor, new_permission, insertuser):
    user, site, fx, obs, org, role, cdf, report = insertuser
    perm = new_permission('read_values', 'observations', True, org=org)
    cursor.execute(
        'INSERT INTO role_permission_mapping (role_id, permission_id) VALUES '
        '(%s, %s)', (role['id'], perm['id']))


@pytest.fixture()
def allow_read_forecasts(cursor, new_permission, insertuser):
    user, site, fx, obs, org, role, cdf, report = insertuser
    perm = new_permission('read', 'forecasts', True, org=org)
    cursor.execute(
        'INSERT INTO role_permission_mapping (role_id, permission_id) VALUES '
        '(%s, %s)', (role['id'], perm['id']))


@pytest.fixture()
def allow_read_forecast_values(cursor, new_permission, insertuser):
    user, site, fx, obs, org, role, cdf, report = insertuser
    perm = new_permission('read_values', 'forecasts', True, org=org)
    cursor.execute(
        'INSERT INTO role_permission_mapping (role_id, permission_id) VALUES '
        '(%s, %s)', (role['id'], perm['id']))


@pytest.fixture()
def allow_read_cdf_forecasts(cursor, new_permission, insertuser):
    user, site, fx, obs, org, role, cdf, report = insertuser
    perm = new_permission('read', 'cdf_forecasts', True, org=org)
    cursor.execute(
        'INSERT INTO role_permission_mapping (role_id, permission_id) VALUES '
        '(%s, %s)', (role['id'], perm['id']))


@pytest.fixture()
def allow_read_cdf_forecast_values(cursor, new_permission, insertuser):
    user, site, fx, obs, org, role, cdf, report = insertuser
    perm = new_permission('read_values', 'cdf_forecasts', True, org=org)
    cursor.execute(
        'INSERT INTO role_permission_mapping (role_id, permission_id) VALUES '
        '(%s, %s)', (role['id'], perm['id']))


@pytest.fixture()
def allow_read_reports(cursor, new_report, new_permission, insertuser):
    user, site, fx, obs, org, role, cdf, report = insertuser
    perm = new_permission('read', 'reports', True, org=org)
    cursor.execute(
        'INSERT INTO role_permission_mapping (role_id, permission_id) VALUES '
        '(%s, %s)', (role['id'], perm['id']))


def test_read_site(dictcursor, insertuser, allow_read_sites):
    auth0id = insertuser[0]['auth0_id']
    site = insertuser[1]
    dictcursor.callproc('read_site', (auth0id, site['strid']))
    res = dictcursor.fetchall()[0]
    site['site_id'] = site['strid']
    del site['strid']
    del site['id']
    site['provider'] = insertuser[4]['name']
    del site['organization_id']
    del res['created_at']
    del res['modified_at']
    assert res == site


def test_read_site_denied(cursor, insertuser):
    auth0id = insertuser[0]['auth0_id']
    site = insertuser[1]
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_site', (auth0id, site['strid']))
    assert e.value.args[0] == 1142


def test_read_observation(dictcursor, insertuser, allow_read_observations):
    auth0id = insertuser[0]['auth0_id']
    observation = insertuser[3]
    dictcursor.callproc('read_observation', (auth0id, observation['strid']))
    res = dictcursor.fetchall()[0]
    observation['observation_id'] = observation['strid']
    del observation['strid']
    del observation['id']
    observation['site_id'] = str(bin_to_uuid(observation['site_id']))
    observation['provider'] = insertuser[4]['name']
    del observation['organization_id']
    del res['created_at']
    del res['modified_at']
    assert res == observation


def test_read_observation_denied(cursor, insertuser):
    auth0id = insertuser[0]['auth0_id']
    obs = insertuser[3]
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_observation', (auth0id, obs['strid']))
    assert e.value.args[0] == 1142


def test_read_forecast(dictcursor, insertuser, allow_read_forecasts):
    auth0id = insertuser[0]['auth0_id']
    forecast = insertuser[2]
    dictcursor.callproc('read_forecast', (auth0id, forecast['strid']))
    res = dictcursor.fetchall()[0]
    forecast['forecast_id'] = forecast['strid']
    del forecast['id']
    del forecast['strid']
    forecast['site_id'] = str(bin_to_uuid(forecast['site_id']))
    forecast['provider'] = insertuser[4]['name']
    del forecast['organization_id']
    del res['created_at']
    del res['modified_at']
    assert res == forecast


def test_read_forecast_denied(cursor, insertuser):
    auth0id = insertuser[0]['auth0_id']
    forecast = insertuser[3]
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_forecast', (auth0id, forecast['strid']))
    assert e.value.args[0] == 1142


@pytest.fixture()
def obs_values(cursor, insertuser):
    auth0id = insertuser[0]['auth0_id']
    obsid = insertuser[3]['strid']
    start = dt.datetime(2019, 1, 30, 12, 28, 20)
    vals = tuple([
        (obsid, start + dt.timedelta(minutes=i),
         float(random.randint(0, 100)), 0) for i in range(10)])
    cursor.executemany(
        'INSERT INTO observations_values (id, timestamp, value, quality_flag) '
        'VALUES (UUID_TO_BIN(%s, 1), %s, %s, %s)', vals)
    start = dt.datetime(2019, 1, 30, 12, 20)
    end = dt.datetime(2019, 1, 30, 12, 40)
    return auth0id, obsid, vals, start, end


def test_read_observation_values(cursor, obs_values,
                                 allow_read_observation_values):
    auth0id, obsid, vals, start, end = obs_values
    cursor.callproc('read_observation_values', (auth0id, obsid, start, end))
    res = cursor.fetchall()
    assert res == vals


@pytest.mark.parametrize('start,end,theslice', [
    (dt.datetime(2019, 1, 30, 12, 20), dt.datetime(2019, 2, 10, 12, 20),
     slice(10)),
    (dt.datetime(2019, 1, 30, 12, 30), dt.datetime(2019, 1, 30, 12, 40),
     slice(2, 10)),
    (dt.datetime(2019, 1, 30, 12, 30), dt.datetime(2019, 1, 30, 12, 30),
     slice(0)),
    (dt.datetime(2019, 1, 30, 12, 30), dt.datetime(2019, 1, 29, 12, 30),
     slice(0)),
    (dt.datetime(2019, 1, 30, 12, 30), dt.datetime(2019, 1, 30, 12, 35),
     slice(2, 7)),
])
def test_read_observation_values_time_limits(
        cursor, obs_values, allow_read_observation_values, start, end,
        theslice):
    auth0id, obsid, vals, _, _ = obs_values
    cursor.callproc('read_observation_values', (auth0id, obsid, start, end))
    res = cursor.fetchall()
    assert res == vals[theslice]


def test_read_observation_values_denied(cursor, obs_values):
    auth0id, obsid, vals, start, end = obs_values
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_observation_values',
                        (auth0id, obsid, start, end))
    assert e.value.args[0] == 1142


def test_read_observation_values_denied_can_read_meta(
        cursor, obs_values, allow_read_observations):
    auth0id, obsid, vals, start, end = obs_values
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_observation_values',
                        (auth0id, obsid, start, end))
    assert e.value.args[0] == 1142


@pytest.fixture()
def fx_values(cursor, insertuser):
    auth0id = insertuser[0]['auth0_id']
    fxid = insertuser[2]['strid']
    start = dt.datetime(2019, 1, 30, 12, 28, 20)
    vals = tuple([
        (fxid, start + dt.timedelta(minutes=i),
         float(random.randint(0, 100))) for i in range(10)])
    cursor.executemany(
        'INSERT INTO forecasts_values (id, timestamp, value) '
        'VALUES (UUID_TO_BIN(%s, 1), %s, %s)', vals)
    start = dt.datetime(2019, 1, 30, 12, 20)
    end = dt.datetime(2019, 1, 30, 12, 40)
    return auth0id, fxid, vals, start, end


def test_read_forecast_values(cursor, fx_values,
                              allow_read_forecast_values):
    auth0id, fxid, vals, start, end = fx_values
    cursor.callproc('read_forecast_values', (auth0id, fxid, start, end))
    res = cursor.fetchall()
    assert res == vals


@pytest.mark.parametrize('start,end,theslice', [
    (dt.datetime(2019, 1, 30, 12, 20), dt.datetime(2019, 2, 10, 12, 20),
     slice(10)),
    (dt.datetime(2019, 1, 30, 12, 30), dt.datetime(2019, 1, 30, 12, 40),
     slice(2, 10)),
    (dt.datetime(2019, 1, 30, 12, 30), dt.datetime(2019, 1, 30, 12, 30),
     slice(0)),
    (dt.datetime(2019, 1, 30, 12, 30), dt.datetime(2019, 1, 29, 12, 30),
     slice(0)),
    (dt.datetime(2019, 1, 30, 12, 30), dt.datetime(2019, 1, 30, 12, 35),
     slice(2, 7)),
])
def test_read_forecast_values_time_limits(
        cursor, fx_values, allow_read_forecast_values, start, end,
        theslice):
    auth0id, fxid, vals, _, _ = fx_values
    cursor.callproc('read_forecast_values', (auth0id, fxid, start, end))
    res = cursor.fetchall()
    assert res == vals[theslice]


def test_read_forecast_values_denied(cursor, fx_values):
    auth0id, fxid, vals, start, end = fx_values
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_forecast_values',
                        (auth0id, fxid, start, end))
    assert e.value.args[0] == 1142


def test_read_forecast_values_denied_can_read_meta(
        cursor, fx_values, allow_read_forecasts):
    auth0id, fxid, vals, start, end = fx_values
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_forecast_values', (auth0id, fxid, start, end))
    assert e.value.args[0] == 1142


def test_read_cdf_forecast(dictcursor, insertuser, allow_read_cdf_forecasts):
    auth0id = insertuser[0]['auth0_id']
    forecast = insertuser[6]
    dictcursor.callproc('read_cdf_forecasts_group',
                        (auth0id, forecast['strid']))
    res = dictcursor.fetchall()[0]
    forecast['forecast_id'] = forecast['strid']
    del forecast['id']
    del forecast['strid']
    forecast['site_id'] = str(bin_to_uuid(forecast['site_id']))
    forecast['provider'] = insertuser[4]['name']
    forecast['constant_values'] = str(forecast['constant_values']).replace(
        '\'', '"')
    del forecast['organization_id']
    del res['created_at']
    del res['modified_at']
    assert res == forecast


def test_read_cdf_forecast_no_values(dictcursor, insertuser,
                                     allow_read_cdf_forecasts):
    auth0id = insertuser[0]['auth0_id']
    forecast = insertuser[6]
    dictcursor.execute('DELETE FROM cdf_forecasts_singles')
    dictcursor.callproc('read_cdf_forecasts_group',
                        (auth0id, forecast['strid']))
    res = dictcursor.fetchall()[0]
    forecast['forecast_id'] = forecast['strid']
    del forecast['id']
    del forecast['strid']
    forecast['site_id'] = str(bin_to_uuid(forecast['site_id']))
    forecast['provider'] = insertuser[4]['name']
    forecast['constant_values'] = '{}'
    del forecast['organization_id']
    del res['created_at']
    del res['modified_at']
    assert res == forecast


def test_read_cdf_forecast_denied(cursor, insertuser):
    auth0id = insertuser[0]['auth0_id']
    forecast = insertuser[6]
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_cdf_forecasts_group',
                        (auth0id, forecast['strid']))
    assert e.value.args[0] == 1142


def test_read_cdf_forecast_single(dictcursor, insertuser,
                                  allow_read_cdf_forecasts):
    auth0id = insertuser[0]['auth0_id']
    forecast = insertuser[6]
    strid = list(forecast['constant_values'].keys())[0]
    dictcursor.callproc('read_cdf_forecasts_single',
                        (auth0id, strid))
    res = dictcursor.fetchall()[0]
    forecast['forecast_id'] = strid
    forecast['parent'] = forecast['strid']
    del forecast['id']
    del forecast['strid']
    forecast['site_id'] = str(bin_to_uuid(forecast['site_id']))
    forecast['provider'] = insertuser[4]['name']
    forecast['constant_value'] = forecast['constant_values'][strid]
    del forecast['constant_values']
    del forecast['organization_id']
    del res['created_at']
    assert res == forecast


def test_read_cdf_forecast_single_denied(cursor, insertuser):
    auth0id = insertuser[0]['auth0_id']
    forecast = insertuser[6]
    strid = list(forecast['constant_values'].keys())[0]
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_cdf_forecasts_single',
                        (auth0id, strid))
    assert e.value.args[0] == 1142


@pytest.fixture(params=[0, 1, 2])
def cdf_fx_values(cursor, insertuser, request):
    auth0id = insertuser[0]['auth0_id']
    forecast = insertuser[6]
    strid = list(forecast['constant_values'].keys())[request.param]
    start = dt.datetime(2019, 1, 30, 12, 28, 20)
    vals = tuple([
        (strid, start + dt.timedelta(minutes=i),
         float(random.randint(0, 100))) for i in range(10)])
    cursor.executemany(
        'INSERT INTO cdf_forecasts_values (id, timestamp, value) '
        'VALUES (UUID_TO_BIN(%s, 1), %s, %s)', vals)
    start = dt.datetime(2019, 1, 30, 12, 20)
    end = dt.datetime(2019, 1, 30, 12, 40)
    return auth0id, strid, vals, start, end


def test_read_cdf_forecast_values(cursor, cdf_fx_values,
                                  allow_read_cdf_forecast_values):
    auth0id, fxid, vals, start, end = cdf_fx_values
    cursor.callproc('read_cdf_forecast_values', (auth0id, fxid, start, end))
    res = cursor.fetchall()
    assert res == vals


@pytest.mark.parametrize('start,end,theslice', [
    (dt.datetime(2019, 1, 30, 12, 20), dt.datetime(2019, 2, 10, 12, 20),
     slice(10)),
    (dt.datetime(2019, 1, 30, 12, 30), dt.datetime(2019, 1, 30, 12, 40),
     slice(2, 10)),
    (dt.datetime(2019, 1, 30, 12, 30), dt.datetime(2019, 1, 30, 12, 30),
     slice(0)),
    (dt.datetime(2019, 1, 30, 12, 30), dt.datetime(2019, 1, 29, 12, 30),
     slice(0)),
    (dt.datetime(2019, 1, 30, 12, 30), dt.datetime(2019, 1, 30, 12, 35),
     slice(2, 7)),
])
def test_read_cdf_forecast_values_time_limits(
        cursor, cdf_fx_values, allow_read_cdf_forecast_values, start, end,
        theslice):
    auth0id, fxid, vals, _, _ = cdf_fx_values
    cursor.callproc('read_cdf_forecast_values', (auth0id, fxid, start, end))
    res = cursor.fetchall()
    assert res == vals[theslice]


def test_read_cdf_forecast_values_denied(cursor, cdf_fx_values,
                                         allow_read_forecast_values):
    auth0id, fxid, vals, start, end = cdf_fx_values
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_cdf_forecast_values',
                        (auth0id, fxid, start, end))
    assert e.value.args[0] == 1142


def test_read_cdf_forecast_values_denied_can_read_meta(
        cursor, cdf_fx_values, allow_read_cdf_forecasts):
    auth0id, fxid, vals, start, end = cdf_fx_values
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_cdf_forecast_values', (auth0id, fxid, start, end))
    assert e.value.args[0] == 1142


@pytest.fixture()
def allow_read_users(cursor, new_permission, insertuser):
    user, site, fx, obs, org, role, cdf, report = insertuser
    perm = new_permission('read', 'users', True, org=org)
    cursor.execute(
        'INSERT INTO role_permission_mapping (role_id, permission_id) VALUES '
        '(%s, %s)', (role['id'], perm['id']))


def test_read_user(dictcursor, new_user, allow_read_users,
                   valueset, insertuser):
    org = insertuser[4]
    old_user = insertuser[0]
    roles = valueset[2]
    user = new_user(org=org)
    dictcursor.executemany(
        'INSERT INTO user_role_mapping (user_id, role_id) VALUES (%s, %s)',
        [(user['id'], r['id']) for r in roles])
    dictcursor.callproc('read_user', (old_user['auth0_id'],
                                      str(bin_to_uuid(user['id']))))
    res = dictcursor.fetchall()[0]
    res_roles = set(json.loads(res['roles']).keys())
    for tstr in json.loads(res['roles']).values():
        dt.datetime.strptime(tstr, '%Y-%m-%d %H:%M:%S.%f')
    assert res_roles == set([str(bin_to_uuid(r['id'])) for r in roles])
    assert res['auth0_id'] == user['auth0_id']
    assert res['user_id'] == str(bin_to_uuid(user['id']))


def test_read_user_no_roles(dictcursor, new_user, allow_read_users,
                            valueset, insertuser):
    org = insertuser[4]
    old_user = insertuser[0]
    user = new_user(org=org)
    dictcursor.callproc('read_user', (old_user['auth0_id'],
                                      str(bin_to_uuid(user['id']))))
    res = dictcursor.fetchall()[0]
    assert res['roles'] == '{}'
    assert res['auth0_id'] == user['auth0_id']
    assert res['user_id'] == str(bin_to_uuid(user['id']))


def test_read_user_denied(dictcursor, new_user,
                          valueset, insertuser):
    org = insertuser[4]
    old_user = insertuser[0]
    user = new_user(org=org)
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc('read_user', (old_user['auth0_id'],
                                          str(bin_to_uuid(user['id']))))
    assert e.value.args[0] == 1142


@pytest.fixture()
def allow_read_roles(cursor, new_permission, insertuser):
    user, site, fx, obs, org, role, cdf, report = insertuser
    perm = new_permission('read', 'roles', True, org=org)
    cursor.execute(
        'INSERT INTO role_permission_mapping (role_id, permission_id) VALUES '
        '(%s, %s)', (role['id'], perm['id']))


def test_read_role(dictcursor, new_role, allow_read_roles,
                   new_permission, insertuser):
    org = insertuser[4]
    user = insertuser[0]
    perms = [new_permission('read', 'observations', False, org=org)
             for _ in range(3)]
    role = new_role(org=org)
    dictcursor.executemany(
        'INSERT INTO role_permission_mapping (role_id, permission_id) VALUES '
        '(%s, %s)', [(role['id'], p['id']) for p in perms])
    dictcursor.callproc('read_role', (user['auth0_id'],
                                      str(bin_to_uuid(role['id']))))
    res = dictcursor.fetchall()[0]
    res_perms = set(json.loads(res['permissions']).keys())
    for tstr in json.loads(res['permissions']).values():
        dt.datetime.strptime(tstr, '%Y-%m-%d %H:%M:%S.%f')
    assert res_perms == set([str(bin_to_uuid(r['id'])) for r in perms])
    assert res['role_id'] == str(bin_to_uuid(role['id']))
    assert res['name'] == role['name']
    assert res['description'] == role['description']


def test_read_role_no_perm(dictcursor, new_role, allow_read_roles,
                           insertuser):
    org = insertuser[4]
    user = insertuser[0]
    role = new_role(org=org)
    dictcursor.callproc('read_role', (user['auth0_id'],
                                      str(bin_to_uuid(role['id']))))
    res = dictcursor.fetchall()[0]
    assert res['permissions'] == '{}'
    assert res['role_id'] == str(bin_to_uuid(role['id']))
    assert res['name'] == role['name']
    assert res['description'] == role['description']


def test_read_role_denied(dictcursor, new_role,
                          insertuser):
    org = insertuser[4]
    user = insertuser[0]
    role = new_role(org=org)
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc('read_role', (user['auth0_id'],
                                          str(bin_to_uuid(role['id']))))
    assert e.value.args[0] == 1142


@pytest.fixture()
def allow_read_permissions(cursor, new_permission, insertuser):
    user, site, fx, obs, org, role, cdf, report = insertuser
    perm = new_permission('read', 'permissions', True, org=org)
    cursor.execute(
        'INSERT INTO role_permission_mapping (role_id, permission_id) VALUES '
        '(%s, %s)', (role['id'], perm['id']))


def test_read_permission(dictcursor, new_permission, allow_read_permissions,
                         valueset, insertuser):
    org = insertuser[4]
    user = insertuser[0]
    obs = valueset[6][:3]
    perm = new_permission('read', 'observations', False, org=org)
    dictcursor.executemany(
        'INSERT INTO permission_object_mapping (permission_id, object_id)'
        ' VALUES (%s, %s)', [(perm['id'], o['id']) for o in obs])
    dictcursor.callproc('read_permission', (user['auth0_id'],
                                            str(bin_to_uuid(perm['id']))))
    res = dictcursor.fetchall()[0]
    res_obs = set(json.loads(res['objects']).keys())
    for tstr in json.loads(res['objects']).values():
        dt.datetime.strptime(tstr, '%Y-%m-%d %H:%M:%S.%f')
    assert res_obs == set([str(bin_to_uuid(o['id'])) for o in obs])
    assert res['permission_id'] == str(bin_to_uuid(perm['id']))
    for key in ('description', 'action', 'object_type', 'applies_to_all'):
        assert res[key] == perm[key]


def test_read_permission_no_obj(dictcursor, new_permission,
                                allow_read_permissions,
                                valueset, insertuser):
    org = insertuser[4]
    user = insertuser[0]
    perm = new_permission('read', 'observations', False, org=org)
    dictcursor.callproc('read_permission', (user['auth0_id'],
                                            str(bin_to_uuid(perm['id']))))
    res = dictcursor.fetchall()[0]
    assert res['objects'] == '{}'
    assert res['permission_id'] == str(bin_to_uuid(perm['id']))
    for key in ('description', 'action', 'object_type', 'applies_to_all'):
        assert res[key] == perm[key]


def test_read_permission_denied(dictcursor, new_permission,
                                valueset, insertuser):
    org = insertuser[4]
    user = insertuser[0]
    perm = new_permission('read', 'observations', False, org=org)
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc('read_permission', (user['auth0_id'],
                                                str(bin_to_uuid(perm['id']))))
    assert e.value.args[0] == 1142

def test_read_report(dictcursor, valueset, new_report, allow_read_reports, insertuser):
    org = insertuser[4]
    user = insertuser[0]
    report = insertuser[7]
    dictcursor.callproc('read_report', (user['auth0_id'], str(bin_to_uuid(report['id']))))
    res = dictcursor.fetchall()[0]
    assert res['name'] == report['name']
    assert res['provider'] == org['name']
    assert json.loads(res['report_parameters']) == json.loads(report['report_parameters'])
    assert res['metrics'] == '{}'

def test_read_report_denied(dictcursor, new_report, valueset, insertuser):
    user = insertuser[0]
    report = new_report()
    with pytest.raises(pymysql.err.OperationalError) as e:
       dictcursor.callproc('read_report', (user['auth0_id'], str(bin_to_uuid(report['id']))))
    assert e.value.args[0] == 1142
