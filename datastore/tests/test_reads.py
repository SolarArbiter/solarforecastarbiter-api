from collections import namedtuple
import datetime as dt
import itertools
import json
import random
import unittest


import pytest
import pymysql


from conftest import bin_to_uuid


@pytest.fixture()
def insertuser(cursor, new_permission, valueset, new_user):
    AllMeta = namedtuple('AllMeta', ['user', 'site', 'fx', 'obs', 'org',
                                     'role', 'cdf', 'report', 'agg',
                                     'auth0id', 'agg_fx', 'agg_cdf'])
    org = valueset[0][0]
    user = valueset[1][0]
    role = valueset[2][0]
    site = valueset[3][0]
    fx = valueset[5][0]
    agg_fx = valueset[5][-1]
    obs = valueset[6][0]
    cdf = valueset[7][0]
    agg_cdf = valueset[7][2]
    report = valueset[8][2]
    agg = valueset[9][0]
    for thing in (user, site, fx, obs, cdf, agg_fx, agg_cdf):
        thing['strid'] = str(bin_to_uuid(thing['id']))
    cursor.execute(
        "DELETE FROM permissions WHERE action = 'read'")
    return AllMeta(user, site, fx, obs, org, role, cdf, report, agg,
                   user['auth0_id'], agg_fx, agg_cdf)


@pytest.fixture()
def user_org_role(insertuser):
    return insertuser[0], insertuser[4], insertuser[5]


@pytest.fixture()
def add_perm(user_org_role, new_permission, cursor):
    user, org, role = user_org_role

    def fcn(action, what):
        perm = new_permission(action, what, True, org=org)
        cursor.execute(
            'INSERT INTO role_permission_mapping (role_id, permission_id) '
            'VALUES (%s, %s)', (role['id'], perm['id']))
    return fcn


@pytest.fixture()
def allow_read_sites(add_perm):
    add_perm('read', 'sites')


@pytest.fixture()
def allow_read_observations(add_perm):
    add_perm('read', 'observations')


@pytest.fixture()
def allow_read_observation_values(add_perm):
    add_perm('read_values', 'observations')


@pytest.fixture()
def allow_read_forecasts(add_perm):
    add_perm('read', 'forecasts')


@pytest.fixture()
def allow_read_forecast_values(add_perm):
    add_perm('read_values', 'forecasts')


@pytest.fixture()
def allow_read_cdf_forecasts(add_perm):
    add_perm('read', 'cdf_forecasts')


@pytest.fixture()
def allow_read_cdf_forecast_values(add_perm):
    add_perm('read_values', 'cdf_forecasts')


@pytest.fixture()
def allow_read_reports(add_perm):
    add_perm('read', 'reports')


@pytest.fixture()
def allow_read_report_values(add_perm):
    add_perm('read_values', 'reports')


@pytest.fixture()
def allow_read_aggregates(add_perm):
    add_perm('read', 'aggregates')


@pytest.fixture()
def allow_update_aggregates(add_perm):
    add_perm('update', 'aggregates')


@pytest.fixture()
def allow_read_aggregate_values(add_perm):
    add_perm('read_values', 'aggregates')


def test_read_site(dictcursor, insertuser, allow_read_sites):
    auth0id = insertuser[0]['auth0_id']
    site = insertuser[1]
    dictcursor.callproc('read_site', (auth0id, site['strid']))
    res = dictcursor.fetchall()[0]
    site['site_id'] = site['strid']
    del site['strid']
    del site['id']
    site['provider'] = insertuser[4]['name']
    site['climate_zones'] = '[]'
    del site['organization_id']
    del res['created_at']
    del res['modified_at']
    assert res == site


@pytest.mark.parametrize('lat,lon,zones', [
    (0, 0, 0),
    (25, -119, 1),
    (32, -110, 2)
])
def test_read_site_zones(dictcursor, insertuser, allow_read_sites,
                         lat, lon, zones, new_climzone):
    new_climzone()
    auth0id = insertuser[0]['auth0_id']
    site = insertuser[1]
    site['latitude'] = lat
    site['longitude'] = lon
    dictcursor.execute(
        'UPDATE sites SET latitude = %s, longitude = %s WHERE '
        'id = UUID_TO_BIN(%s, 1)',
        (lat, lon, site['strid'])
    )
    dictcursor.callproc('read_site', (auth0id, site['strid']))
    res = dictcursor.fetchall()[0]
    assert len(json.loads(res['climate_zones'])) == zones


def test_read_site_denied(cursor, insertuser):
    auth0id = insertuser[0]['auth0_id']
    site = insertuser[1]
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_site', (auth0id, site['strid']))
    assert e.value.args[0] == 1142


def test_read_climate_zone(dictcursor, new_climzone):
    geojson = new_climzone('other', [
        [-110.0, 30.0], [-110.0, 32.0], [-111.0, 32.0],
        [-111.0, 30.0], [-110.0, 30.0]])
    dictcursor.callproc('read_climate_zone', ('other',))
    res = json.loads(dictcursor.fetchone()['geojson'])
    assert res == geojson
    # check res geojson is valid
    dictcursor.execute('select st_isvalid(st_geomfromgeojson(%s)) as valid',
                       (json.dumps(res)))
    assert dictcursor.fetchone()['valid']


def test_read_climate_zone_invalid(dictcursor):
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc('read_climate_zone', ('other',))
    assert e.value.args[0] == 1142


def test_read_observation(dictcursor, insertuser, allow_read_observations):
    auth0id = insertuser[0]['auth0_id']
    observation = insertuser[3]
    dictcursor.callproc('read_observation', (auth0id, observation['strid']))
    res = dictcursor.fetchall()[0]
    observation['observation_id'] = observation['strid']
    del observation['strid']
    del observation['id']
    observation['site_id'] = bin_to_uuid(observation['site_id'])
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


@pytest.fixture(params=[0, 1])
def both_fx_types(insertuser, request):
    if request.param:
        fx = insertuser.fx
    else:
        fx = insertuser.agg_fx
    return insertuser[0]['auth0_id'], fx, insertuser[4]['name']


def test_read_forecast(dictcursor, allow_read_forecasts, both_fx_types):
    auth0id, forecast, provider = both_fx_types
    dictcursor.callproc('read_forecast', (auth0id, forecast['strid']))
    res = dictcursor.fetchall()[0]
    forecast['forecast_id'] = forecast['strid']
    del forecast['id']
    del forecast['strid']
    forecast['site_id'] = bin_to_uuid(forecast['site_id'])
    forecast['aggregate_id'] = bin_to_uuid(forecast['aggregate_id'])
    forecast['provider'] = provider
    del forecast['organization_id']
    del res['created_at']
    del res['modified_at']
    assert res == forecast


def test_read_forecast_denied(cursor, both_fx_types):
    auth0id, forecast, provider = both_fx_types
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_forecast', (auth0id, forecast['strid']))
    assert e.value.args[0] == 1142


@pytest.fixture()
def obs_values(cursor, insertuser):
    auth0id = insertuser[0]['auth0_id']

    def insert(obsid):
        start = dt.datetime(2020, 1, 30, 12, 28, 20)
        vals = tuple([
            (obsid, start + dt.timedelta(minutes=i),
             float(random.randint(0, 100)), 0) for i in range(10)])
        cursor.executemany(
            'INSERT INTO observations_values (id, timestamp, value, '
            'quality_flag) VALUES (UUID_TO_BIN(%s, 1), %s, %s, %s)',
            vals)
        start = dt.datetime(2020, 1, 30, 12, 20)
        end = dt.datetime(2020, 1, 30, 12, 40)
        return auth0id, obsid, vals, start, end
    return insert


def test_read_observation_values(cursor, obs_values, insertuser,
                                 allow_read_observation_values):
    auth0id, obsid, vals, start, end = obs_values(insertuser[3]['strid'])
    cursor.callproc('read_observation_values', (auth0id, obsid, start, end))
    res = cursor.fetchall()
    assert res == vals


@pytest.mark.parametrize('start,end,theslice', [
    (dt.datetime(2020, 1, 30, 12, 20), dt.datetime(2020, 2, 10, 12, 20),
     slice(10)),
    (dt.datetime(2020, 1, 30, 12, 30), dt.datetime(2020, 1, 30, 12, 40),
     slice(2, 10)),
    (dt.datetime(2020, 1, 30, 12, 30), dt.datetime(2020, 1, 30, 12, 30),
     slice(0)),
    (dt.datetime(2020, 1, 30, 12, 30), dt.datetime(2020, 1, 29, 12, 30),
     slice(0)),
    (dt.datetime(2020, 1, 30, 12, 30), dt.datetime(2020, 1, 30, 12, 35),
     slice(2, 7)),
])
def test_read_observation_values_time_limits(
        cursor, obs_values, allow_read_observation_values, start, end,
        theslice, insertuser):
    auth0id, obsid, vals, _, _ = obs_values(insertuser[3]['strid'])
    cursor.callproc('read_observation_values', (auth0id, obsid, start, end))
    res = cursor.fetchall()
    assert res == vals[theslice]


def test_read_observation_values_denied(cursor, obs_values, insertuser):
    auth0id, obsid, vals, start, end = obs_values(insertuser[3]['strid'])
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_observation_values',
                        (auth0id, obsid, start, end))
    assert e.value.args[0] == 1142


def test_read_observation_values_denied_can_read_meta(
        cursor, obs_values, allow_read_observations, insertuser):
    auth0id, obsid, vals, start, end = obs_values(insertuser[3]['strid'])
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_observation_values',
                        (auth0id, obsid, start, end))
    assert e.value.args[0] == 1142


@pytest.fixture()
def fx_values(cursor, insertuser):
    auth0id = insertuser[0]['auth0_id']
    fxid = insertuser[2]['strid']
    start = dt.datetime(2020, 1, 30, 12, 28, 20)
    vals = tuple([
        (fxid, start + dt.timedelta(minutes=i),
         float(random.randint(0, 100))) for i in range(10)])
    cursor.executemany(
        'INSERT INTO forecasts_values (id, timestamp, value) '
        'VALUES (UUID_TO_BIN(%s, 1), %s, %s)', vals)
    start = dt.datetime(2020, 1, 30, 12, 20)
    end = dt.datetime(2020, 1, 30, 12, 40)
    return auth0id, fxid, vals, start, end


def test_read_forecast_values(cursor, fx_values,
                              allow_read_forecast_values):
    auth0id, fxid, vals, start, end = fx_values
    cursor.callproc('read_forecast_values', (auth0id, fxid, start, end))
    res = cursor.fetchall()
    assert res == vals


@pytest.mark.parametrize('start,end,theslice', [
    (dt.datetime(2020, 1, 30, 12, 20), dt.datetime(2020, 2, 10, 12, 20),
     slice(10)),
    (dt.datetime(2020, 1, 30, 12, 30), dt.datetime(2020, 1, 30, 12, 40),
     slice(2, 10)),
    (dt.datetime(2020, 1, 30, 12, 30), dt.datetime(2020, 1, 30, 12, 30),
     slice(0)),
    (dt.datetime(2020, 1, 30, 12, 30), dt.datetime(2020, 1, 29, 12, 30),
     slice(0)),
    (dt.datetime(2020, 1, 30, 12, 30), dt.datetime(2020, 1, 30, 12, 35),
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


@pytest.fixture(params=[0, 1])
def both_cdf_fx_types(insertuser, request):
    if request.param:
        fx = insertuser.cdf
    else:
        fx = insertuser.agg_cdf
    return insertuser[0]['auth0_id'], fx, insertuser[4]['name']


def test_read_cdf_forecast(
        dictcursor, both_cdf_fx_types, allow_read_cdf_forecasts):
    auth0id, forecast, provider = both_cdf_fx_types
    dictcursor.callproc('read_cdf_forecasts_group',
                        (auth0id, forecast['strid']))
    res = dictcursor.fetchall()[0]
    forecast['forecast_id'] = forecast['strid']
    del forecast['id']
    del forecast['strid']
    forecast['site_id'] = bin_to_uuid(forecast['site_id'])
    forecast['aggregate_id'] = bin_to_uuid(forecast['aggregate_id'])
    forecast['provider'] = provider
    forecast['constant_values'] = str(forecast['constant_values']).replace(
        '\'', '"')
    del forecast['organization_id']
    del res['created_at']
    del res['modified_at']
    assert res == forecast


def test_read_cdf_forecast_no_values(dictcursor, both_cdf_fx_types,
                                     allow_read_cdf_forecasts):
    auth0id, forecast, provider = both_cdf_fx_types
    dictcursor.execute('DELETE FROM cdf_forecasts_singles')
    dictcursor.callproc('read_cdf_forecasts_group',
                        (auth0id, forecast['strid']))
    res = dictcursor.fetchall()[0]
    forecast['forecast_id'] = forecast['strid']
    del forecast['id']
    del forecast['strid']
    forecast['site_id'] = bin_to_uuid(forecast['site_id'])
    forecast['aggregate_id'] = bin_to_uuid(forecast['aggregate_id'])
    forecast['provider'] = provider
    forecast['constant_values'] = '{}'
    del forecast['organization_id']
    del res['created_at']
    del res['modified_at']
    assert res == forecast


def test_read_cdf_forecast_denied(cursor, both_cdf_fx_types):
    auth0id, forecast, provider = both_cdf_fx_types
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_cdf_forecasts_group',
                        (auth0id, forecast['strid']))
    assert e.value.args[0] == 1142


def test_read_cdf_forecast_single(dictcursor, both_cdf_fx_types,
                                  allow_read_cdf_forecasts):
    auth0id, forecast, provider = both_cdf_fx_types
    strid = list(forecast['constant_values'].keys())[0]
    dictcursor.callproc('read_cdf_forecasts_single',
                        (auth0id, strid))
    res = dictcursor.fetchall()[0]
    forecast['forecast_id'] = strid
    forecast['parent'] = forecast['strid']
    del forecast['id']
    del forecast['strid']
    forecast['site_id'] = bin_to_uuid(forecast['site_id'])
    forecast['aggregate_id'] = bin_to_uuid(forecast['aggregate_id'])
    forecast['provider'] = provider
    forecast['constant_value'] = forecast['constant_values'][strid]
    del forecast['constant_values']
    del forecast['organization_id']
    del res['created_at']
    assert res == forecast


def test_read_cdf_forecast_single_denied(cursor, both_cdf_fx_types):
    auth0id, forecast, provider = both_cdf_fx_types
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
    start = dt.datetime(2020, 1, 30, 12, 28, 20)
    vals = tuple([
        (strid, start + dt.timedelta(minutes=i),
         float(random.randint(0, 100))) for i in range(10)])
    cursor.executemany(
        'INSERT INTO cdf_forecasts_values (id, timestamp, value) '
        'VALUES (UUID_TO_BIN(%s, 1), %s, %s)', vals)
    start = dt.datetime(2020, 1, 30, 12, 20)
    end = dt.datetime(2020, 1, 30, 12, 40)
    return auth0id, strid, vals, start, end


def test_read_cdf_forecast_values(cursor, cdf_fx_values,
                                  allow_read_cdf_forecast_values):
    auth0id, fxid, vals, start, end = cdf_fx_values
    cursor.callproc('read_cdf_forecast_values', (auth0id, fxid, start, end))
    res = cursor.fetchall()
    assert res == vals


@pytest.mark.parametrize('start,end,theslice', [
    (dt.datetime(2020, 1, 30, 12, 20), dt.datetime(2020, 2, 10, 12, 20),
     slice(10)),
    (dt.datetime(2020, 1, 30, 12, 30), dt.datetime(2020, 1, 30, 12, 40),
     slice(2, 10)),
    (dt.datetime(2020, 1, 30, 12, 30), dt.datetime(2020, 1, 30, 12, 30),
     slice(0)),
    (dt.datetime(2020, 1, 30, 12, 30), dt.datetime(2020, 1, 29, 12, 30),
     slice(0)),
    (dt.datetime(2020, 1, 30, 12, 30), dt.datetime(2020, 1, 30, 12, 35),
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
        cursor.callproc('read_cdf_forecast_values',
                        (auth0id, fxid, start, end))
    assert e.value.args[0] == 1142


@pytest.fixture()
def allow_read_users(add_perm):
    add_perm('read', 'users')


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
def allow_read_roles(add_perm):
    add_perm('read', 'roles')


def test_read_role(dictcursor, new_role, new_user,
                   allow_read_roles, new_permission, insertuser):
    org = insertuser[4]
    user = insertuser[0]
    users_with_role = [new_user(org=org) for _ in range(3)]
    perms = [new_permission('read', 'observations', False, org=org)
             for _ in range(3)]
    role = new_role(org=org)
    dictcursor.executemany(
        'INSERT INTO role_permission_mapping (role_id, permission_id) VALUES '
        '(%s, %s)', [(role['id'], p['id']) for p in perms])
    for grantee in users_with_role:
        dictcursor.execute(
            'INSERT INTO arbiter_data.user_role_mapping(user_id, role_id) '
            ' VALUES (%s, %s)',
            (grantee['id'], role['id']))
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
    user_dict = json.loads(res['users'])
    assert len(users_with_role) == len(list(user_dict.keys()))
    for grantee in users_with_role:
        assert str(bin_to_uuid(grantee['id'])) in user_dict


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
def allow_read_permissions(add_perm):
    add_perm('read', 'permissions')


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


def test_read_permission_denied(
        dictcursor, new_permission, valueset, insertuser):
    org = insertuser[4]
    user = insertuser[0]
    perm = new_permission('read', 'observations', False, org=org)
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc('read_permission', (user['auth0_id'],
                                                str(bin_to_uuid(perm['id']))))
    assert e.value.args[0] == 1142


def test_read_report(
        dictcursor, valueset, new_report, allow_read_reports, insertuser):
    org = insertuser[4]
    user = insertuser[0]
    report = insertuser[7]
    dictcursor.callproc(
        'read_report', (user['auth0_id'], str(bin_to_uuid(report['id']))))
    res = dictcursor.fetchall()[0]
    assert res['name'] == report['name']
    assert res['provider'] == org['name']
    res_params = json.loads(res['report_parameters'])
    orig_params = json.loads(report['report_parameters'])
    assert res_params == orig_params
    assert res['raw_report'] is None


def test_read_report_denied(dictcursor, new_report, valueset, insertuser):
    user = insertuser[0]
    report = new_report()
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc(
            'read_report', (user['auth0_id'], str(bin_to_uuid(report['id']))))
    assert e.value.args[0] == 1142


def test_read_report_values(
        dictcursor, valueset, new_report, allow_read_reports,
        allow_read_observations, allow_read_observation_values,
        allow_read_forecasts, allow_read_forecast_values,
        allow_read_cdf_forecast_values, allow_read_cdf_forecasts,
        allow_read_report_values, insertuser):
    user = insertuser[0]
    report = insertuser[7]
    object_pairs = json.loads(report['report_parameters'])['object_pairs']
    dictcursor.callproc(
        'read_report_values',
        (user['auth0_id'], str(bin_to_uuid(report['id'])))
    )
    res = dictcursor.fetchall()
    res_objects = [r['object_id'] for r in res]
    for (obs, fx) in object_pairs:
        assert obs in res_objects
        assert fx in res_objects


def test_read_report_values_no_cdf_read(
        dictcursor, valueset, new_report, allow_read_reports,
        allow_read_observations, allow_read_observation_values,
        allow_read_forecasts, allow_read_forecast_values,
        allow_read_cdf_forecasts,
        allow_read_report_values, insertuser):
    user = insertuser[0]
    report = insertuser[7]
    object_pairs = json.loads(report['report_parameters'])['object_pairs']
    dictcursor.callproc(
        'read_report_values',
        (user['auth0_id'], str(bin_to_uuid(report['id'])))
    )
    res = dictcursor.fetchall()
    res_objects = [r['object_id'] for r in res]
    for (obs, fx) in object_pairs[:-4]:
        assert obs in res_objects
        assert fx in res_objects


def test_read_report_values_partial_access(
        dictcursor, valueset, new_report, allow_read_reports,
        allow_read_observation_values, allow_read_report_values,
        insertuser, new_permission):
    user = insertuser[0]
    report = insertuser[7]
    object_pairs = json.loads(report['report_parameters'])['object_pairs']
    obs_id = object_pairs[0][0]
    fx_ids = [obj[1] for obj in object_pairs]
    dictcursor.callproc(
        'read_report_values',
        (user['auth0_id'], str(bin_to_uuid(report['id'])))
    )
    res = dictcursor.fetchall()
    res_objects = [r['object_id'] for r in res]
    assert obs_id in res_objects
    for fx_id in fx_ids:
        assert fx_id not in res_objects


def test_read_report_values_no_data_access(
        dictcursor, valueset, new_report, allow_read_reports,
        insertuser, allow_read_report_values):
    user = insertuser[0]
    report = insertuser[7]
    dictcursor.callproc(
        'read_report_values',
        (user['auth0_id'], str(bin_to_uuid(report['id'])))
    )
    res = dictcursor.fetchall()
    assert len(res) == 0


def test_read_report_values_denied(
        dictcursor, valueset, new_report, allow_read_report_values,
        allow_read_observations, allow_read_observation_values,
        allow_read_forecasts, allow_read_forecast_values,
        insertuser):
    user = insertuser[0]
    report = new_report()
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc(
            'read_report_values',
            (user['auth0_id'], str(bin_to_uuid(report['id'])))
        )
    assert e.value.args[0] == 1142


def test_read_aggregate(
        dictcursor, allow_read_aggregates, insertuser):
    org = insertuser[4]
    user = insertuser[0]
    agg = insertuser[8]
    dictcursor.callproc(
        'read_aggregate', (user['auth0_id'], str(bin_to_uuid(agg['id'])))
    )
    res = dictcursor.fetchall()[0]
    assert res['provider'] == org['name']
    for key in ('name', 'variable', 'interval_length', 'interval_label',
                'extra_parameters', 'description', 'timezone',
                'aggregate_type'):
        assert res[key] == agg[key]
    assert 'observations' in res
    obs_ids = [str(bin_to_uuid(obs['id'])) for obs in agg['obs_list']]
    res_obs = json.loads(res['observations'])
    assert len(res_obs) == len(agg['obs_list'])
    assert len(res_obs) > 0
    for obsd in res_obs:
        assert obsd['observation_id'] in obs_ids
        assert obsd['created_at']
        assert obsd['effective_from']
        assert obsd['effective_until'] is None
        assert obsd['observation_deleted_at'] is None


def test_read_aggregate_obs_deleted(
        dictcursor, allow_read_aggregates, insertuser):
    org = insertuser[4]
    user = insertuser[0]
    agg = insertuser[8]
    dictcursor.execute(
        'DELETE FROM observations WHERE id = %s', agg['obs_list'][0]['id']
    )
    dictcursor.callproc(
        'read_aggregate', (user['auth0_id'], str(bin_to_uuid(agg['id'])))
    )
    res = dictcursor.fetchall()[0]
    assert res['provider'] == org['name']
    for key in ('name', 'variable', 'interval_length', 'interval_label',
                'extra_parameters'):
        assert res[key] == agg[key]
    assert 'observations' in res
    obs_ids = [str(bin_to_uuid(obs['id'])) for obs in agg['obs_list']]
    res_obs = json.loads(res['observations'])
    assert len(res_obs) == len(agg['obs_list'])
    assert len(res_obs) > 0
    for obsd in res_obs:
        assert obsd['observation_id'] in obs_ids
        assert obsd['created_at']
        assert obsd['effective_from']
        if obsd['observation_id'] == str(bin_to_uuid(agg['obs_list'][0]['id'])):  # NOQA
            assert obsd['observation_deleted_at'] is not None
        else:
            assert obsd['observation_deleted_at'] is None
        assert obsd['effective_until'] is None


def test_read_aggregate_obs_deleted_removed(
        dictcursor, allow_read_aggregates, insertuser,
        allow_update_aggregates):
    org = insertuser[4]
    user = insertuser[0]
    agg = insertuser[8]
    oid = agg['obs_list'][0]['id']
    dictcursor.execute(
        'DELETE FROM observations WHERE id = %s', oid)
    dictcursor.callproc('remove_observation_from_aggregate',
                        (user['auth0_id'], str(bin_to_uuid(agg['id'])),
                         str(bin_to_uuid(oid)), '2019-09-30 00:00'))
    dictcursor.callproc(
        'read_aggregate', (user['auth0_id'], str(bin_to_uuid(agg['id'])))
    )
    res = dictcursor.fetchall()[0]
    assert res['provider'] == org['name']
    for key in ('name', 'variable', 'interval_length', 'interval_label',
                'extra_parameters'):
        assert res[key] == agg[key]
    assert 'observations' in res
    obs_ids = [str(bin_to_uuid(obs['id'])) for obs in agg['obs_list']]
    res_obs = json.loads(res['observations'])
    assert len(res_obs) == len(agg['obs_list'])
    assert len(res_obs) > 0
    for obsd in res_obs:
        assert obsd['observation_id'] in obs_ids
        assert obsd['created_at']
        assert obsd['effective_from']
        if obsd['observation_id'] == str(bin_to_uuid(agg['obs_list'][0]['id'])):  # NOQA
            assert obsd['observation_deleted_at'] is not None
            assert obsd['effective_until'] is not None
        else:
            assert obsd['observation_deleted_at'] is None
            assert obsd['effective_until'] is None


def test_read_aggregate_obs_removed(
        dictcursor, allow_read_aggregates, insertuser,
        allow_update_aggregates):
    org = insertuser[4]
    user = insertuser[0]
    agg = insertuser[8]
    oid = agg['obs_list'][0]['id']
    dictcursor.callproc('remove_observation_from_aggregate',
                        (user['auth0_id'], str(bin_to_uuid(agg['id'])),
                         str(bin_to_uuid(oid)), '2019-09-30 00:00'))
    dictcursor.callproc(
        'read_aggregate', (user['auth0_id'], str(bin_to_uuid(agg['id'])))
    )
    res = dictcursor.fetchall()[0]
    assert res['provider'] == org['name']
    for key in ('name', 'variable', 'interval_length', 'interval_label',
                'extra_parameters'):
        assert res[key] == agg[key]
    assert 'observations' in res
    obs_ids = [str(bin_to_uuid(obs['id'])) for obs in agg['obs_list']]
    res_obs = json.loads(res['observations'])
    assert len(res_obs) == len(agg['obs_list'])
    assert len(res_obs) > 0
    for obsd in res_obs:
        assert obsd['observation_id'] in obs_ids
        assert obsd['created_at']
        assert obsd['effective_from']
        if obsd['observation_id'] == str(bin_to_uuid(agg['obs_list'][0]['id'])):  # NOQA
            assert obsd['effective_until'] is not None
        else:
            assert obsd['effective_until'] is None
        assert obsd['observation_deleted_at'] is None


def test_read_aggregate_denied(dictcursor, insertuser):
    user = insertuser[0]
    agg = insertuser[8]
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc(
            'read_aggregate', (user['auth0_id'], str(bin_to_uuid(agg['id'])))
        )
    assert e.value.args[0] == 1142


@pytest.fixture()
def agg_values(new_observation, new_aggregate, insertuser, new_organization,
               cursor, new_permission, obs_values):
    org = insertuser[4]
    role = insertuser[5]
    obss = [new_observation(org=org) for _ in range(3)]
    norg = new_organization()
    nobs = new_observation(org=norg)
    obss += [nobs]
    perm = new_permission('read_values', 'observations', False, org=norg)
    cursor.execute(
        'INSERT INTO role_permission_mapping (role_id, permission_id) '
        'VALUES (%s, %s)', (role['id'], perm['id']))
    cursor.execute(
        'INSERT INTO permission_object_mapping (permission_id, object_id)'
        'VALUES (%s, %s)', (perm['id'], nobs['id'])
    )
    agg = new_aggregate(obs_list=obss, org=org)
    obsids = [str(bin_to_uuid(obs['id'])) for obs in obss]
    auth0id, obsid, vals, start, end = obs_values(obsids[0])
    vals = list(vals)
    for oid in obsids[1:]:
        vals += list(obs_values(oid)[2])
    return agg, auth0id, tuple(vals), start, end, obsids, perm


def test_read_aggregate_values(
        cursor, allow_read_aggregate_values,
        allow_read_observation_values, agg_values):
    agg, auth0id, vals, start, end, obsids, _ = agg_values
    cursor.callproc(
        'read_aggregate_values', (
            auth0id, str(bin_to_uuid(agg['id'])),
            start, end)
    )
    res = cursor.fetchall()
    assert res == vals
    ids = {r[0] for r in res}
    assert len(ids) == 4
    assert ids == set(obsids)


@pytest.mark.parametrize('start,end,theslice', [
    (dt.datetime(2020, 1, 30, 12, 20), dt.datetime(2020, 2, 10, 12, 20),
     slice(10)),
    (dt.datetime(2020, 1, 30, 12, 30), dt.datetime(2020, 1, 30, 12, 40),
     slice(2, 10)),
    (dt.datetime(2020, 1, 30, 12, 30), dt.datetime(2020, 1, 30, 12, 30),
     slice(0)),
    (dt.datetime(2020, 1, 30, 12, 30), dt.datetime(2020, 1, 29, 12, 30),
     slice(0)),
    (dt.datetime(2020, 1, 30, 12, 30), dt.datetime(2020, 1, 30, 12, 35),
     slice(2, 7)),
])
def test_read_aggregate_values_time_limits(
        cursor, allow_read_aggregate_values,
        allow_read_observation_values, agg_values,
        start, end, theslice):
    agg, auth0id, vals, _, _, obsids, _ = agg_values
    cursor.callproc(
        'read_aggregate_values', (
            auth0id, str(bin_to_uuid(agg['id'])),
            start, end)
    )
    res = cursor.fetchall()
    nvals = []
    for i in range(4):
        nvals += list(vals[10 * i: 10 * (i + 1)][theslice])
    assert res == tuple(nvals)


def test_read_aggregate_values_removed(
        cursor, allow_read_aggregate_values, allow_read_observation_values,
        obs_values, new_aggregate, new_observation, user_org_role):
    org = user_org_role[1]
    obs = new_observation(org=org)
    auth0id, obsid, vals, start, end = obs_values(str(bin_to_uuid(obs['id'])))
    agg = new_aggregate(obs_list=[obs], org=org)
    cursor.callproc(
        'read_aggregate_values', (
            auth0id, str(bin_to_uuid(agg['id'])),
            start, end)
    )
    res = cursor.fetchall()
    assert res == vals
    cursor.execute(
        "UPDATE aggregate_observation_mapping SET effective_until = TIMESTAMP('2020-01-30 12:30')"  # NOQA
    )
    cursor.callproc(
        'read_aggregate_values', (
            auth0id, str(bin_to_uuid(agg['id'])),
            start, end)
    )
    res = cursor.fetchall()
    assert res == vals[:2]
    # readd and see
    cursor.execute(
        "INSERT INTO aggregate_observation_mapping "
        "(aggregate_id, observation_id, _incr, effective_from) VALUES"
        " (%s, %s, 1, TIMESTAMP('2020-01-30 12:35'))",
        (agg['id'], obs['id'])
    )
    cursor.callproc(
        'read_aggregate_values', (
            auth0id, str(bin_to_uuid(agg['id'])),
            start, end)
    )
    res = cursor.fetchall()
    assert res == tuple(list(vals[:2]) + list(vals[-3:]))


def test_read_aggregate_values_removed_overlap(
        cursor, allow_read_aggregate_values, allow_read_observation_values,
        obs_values, new_aggregate, new_observation, user_org_role):
    org = user_org_role[1]
    obs = new_observation(org=org)
    auth0id, obsid, vals, start, end = obs_values(str(bin_to_uuid(obs['id'])))
    agg = new_aggregate(obs_list=[obs], org=org)
    cursor.callproc(
        'read_aggregate_values', (
            auth0id, str(bin_to_uuid(agg['id'])),
            start, end)
    )
    res = cursor.fetchall()
    assert res == vals
    cursor.execute(
        "UPDATE aggregate_observation_mapping SET effective_until = TIMESTAMP('2020-01-30 12:30')"  # NOQA
    )  # 12:28 and 12:29 extra
    cursor.execute(
        "INSERT INTO aggregate_observation_mapping "
        "(aggregate_id, observation_id, _incr, effective_from) VALUES"
        " (%s, %s, 1, TIMESTAMP('2020-01-30 11:00'))",
        (agg['id'], obs['id'])
    )
    cursor.callproc(
        'read_aggregate_values', (
            auth0id, str(bin_to_uuid(agg['id'])),
            start, end)
    )
    res = cursor.fetchall()
    assert len(res) == len(vals) + 2
    assert set(res) == set(vals)


def test_read_aggregate_values_full_overlap(
        cursor, allow_read_aggregate_values, allow_read_observation_values,
        obs_values, new_aggregate, new_observation, user_org_role):
    org = user_org_role[1]
    obs = new_observation(org=org)
    auth0id, obsid, vals, start, end = obs_values(str(bin_to_uuid(obs['id'])))
    agg = new_aggregate(obs_list=[obs], org=org)
    cursor.callproc(
        'read_aggregate_values', (
            auth0id, str(bin_to_uuid(agg['id'])),
            start, end)
    )
    res = cursor.fetchall()
    assert res == vals
    cursor.execute(
        "UPDATE aggregate_observation_mapping SET effective_from = TIMESTAMP('2020-01-30 12:29'), effective_until = TIMESTAMP('2020-01-30 12:30')"  # NOQA
    )
    cursor.execute(
        "INSERT INTO aggregate_observation_mapping "
        "(aggregate_id, observation_id, _incr, effective_from) VALUES"
        f" (%s, %s, 1, TIMESTAMP('{start.strftime('%Y-%m-%d %H:%M')}'))",
        (agg['id'], obs['id'])
    )
    cursor.callproc(
        'read_aggregate_values', (
            auth0id, str(bin_to_uuid(agg['id'])),
            start, end)
    )
    res = cursor.fetchall()
    assert len(res) == len(vals) + 1
    assert set(res) == set(vals)


def test_read_aggregate_values_deleted(
        cursor, allow_read_aggregate_values, allow_read_observation_values,
        obs_values, new_aggregate, new_observation, user_org_role):
    org = user_org_role[1]
    obs = new_observation(org=org)
    auth0id, obsid, vals, start, end = obs_values(str(bin_to_uuid(obs['id'])))
    agg = new_aggregate(obs_list=[obs], org=org)
    cursor.callproc(
        'read_aggregate_values', (
            auth0id, str(bin_to_uuid(agg['id'])),
            start, end)
    )
    res = cursor.fetchall()
    assert res == vals
    cursor.execute(
        "UPDATE aggregate_observation_mapping SET observation_deleted_at = TIMESTAMP('2020-01-30 12:30')"  # NOQA
    )
    obs1 = new_observation(org=org)
    _, _, v2, *_ = obs_values(str(bin_to_uuid(obs1['id'])))
    cursor.execute(
        "INSERT INTO aggregate_observation_mapping "
        "(aggregate_id, observation_id, _incr, created_at) VALUES"
        " (%s, %s, 1, TIMESTAMP('2020-01-30 12:20'))",
        (agg['id'], obs1['id'])
    )
    cursor.callproc(
        'read_aggregate_values', (
            auth0id, str(bin_to_uuid(agg['id'])),
            start, end)
    )
    res = cursor.fetchall()
    assert res == tuple(list(vals[:2]) + list(v2))


def test_read_aggregate_values_partial_perms(
        cursor, allow_read_aggregate_values,
        allow_read_observation_values, agg_values):
    agg, auth0id, vals, start, end, obsids, newperm = agg_values
    cursor.execute(
        'DELETE FROM permissions WHERE id = %s', newperm['id']
    )
    cursor.callproc(
        'read_aggregate_values', (
            auth0id, str(bin_to_uuid(agg['id'])),
            start, end)
    )
    res = cursor.fetchall()
    assert res == vals[:-10]
    ids = {r[0] for r in res}
    assert len(ids) == 3
    assert ids == set(obsids[:-1])
    assert obsids[-1] not in ids


def test_read_aggregate_values_no_obs_perm(
        cursor, allow_read_aggregate_values, agg_values
):
    agg, auth0id, vals, start, end, obsids, newperm = agg_values
    cursor.execute(
        'DELETE FROM permissions WHERE id = %s', newperm['id']
    )
    cursor.callproc(
        'read_aggregate_values', (
            auth0id, str(bin_to_uuid(agg['id'])),
            start, end)
    )
    res = cursor.fetchall()
    assert len(res) == 0


def test_read_aggregate_values_no_agg_perms(
        cursor, allow_read_observation_values, agg_values
):
    agg, auth0id, vals, start, end, obsids, newperm = agg_values
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc(
            'read_aggregate_values', (
                auth0id, str(bin_to_uuid(agg['id'])),
                start, end)
        )
    assert e.value.args[0] == 1142


@pytest.mark.parametrize('org,expected', [
    (True, 1), (False, 0),
])
def test_role_granted_to_external_users(
        cursor, valueset, new_role, insertuser, new_organization,
        new_user, allow_grant_roles, org, expected):
    organization = insertuser[4]
    if org:
        external_user = new_user(org=new_organization())
    else:
        external_user = new_user(org=organization)
    role_to_share = new_role(org=organization)
    cursor.execute(
        'INSERT INTO user_role_mapping (user_id, role_id) VALUES '
        '(%s, %s)', (external_user['id'], role_to_share['id']))
    cursor.execute(
        'SELECT arbiter_data.role_granted_to_external_users(%s)',
        role_to_share['id'])
    granted = cursor.fetchone()
    assert granted[0] == expected


def test_role_granted_to_external_users_multiple_users(
        cursor, valueset, new_role, insertuser, new_organization,
        new_user, allow_grant_roles):
    organization = insertuser[4]
    role = new_role(org=organization)
    internal_users = [new_user(org=organization) for _ in range(4)]
    external_users = [new_user() for _ in range(4)]
    users = internal_users + external_users
    for user in users:
        cursor.execute(
            'INSERT INTO user_role_mapping (user_id, role_id) VALUES '
            '(%s, %s)', (user['id'], role['id']))
    cursor.execute(
        'SELECT arbiter_data.role_granted_to_external_users(%s)',
        role['id'])
    granted = cursor.fetchone()
    assert granted[0] == 1


@pytest.mark.parametrize('action', [
    'read', 'create', 'delete', 'update', 'read_values',
    'write_values', 'grant', 'revoke'])
@pytest.mark.parametrize('object_type,expected', [
    ('roles', 1), ('users', 1), ('permissions', 1),
    ('forecasts', 0), ('observations', 0), ('cdf_forecasts', 0),
    ('aggregates', 0), ('sites', 0)
])
def test_role_contains_rbac_permissions(
        cursor, valueset, new_role, insertuser,
        new_permission, object_type, action, expected):
    organization = insertuser[4]
    role = new_role(org=organization)
    perms = [new_permission(action, object_type, True, org=organization)]
    for obj_type in ['sites', 'observations', 'forecasts',
                     'cdf_forecasts', 'aggregates']:
        perms.append(new_permission(action, obj_type, True, org=organization))
    for perm in perms:
        cursor.execute(
            'INSERT INTO role_permission_mapping (role_id, permission_id) '
            'VALUES (%s, %s)', (role['id'], perm['id']))
    cursor.execute(
        'SELECT arbiter_data.role_contains_rbac_permissions(%s)',
        role['id'])
    contains_rbac = cursor.fetchone()[0]
    if action == 'read':
        assert contains_rbac == 0
    else:
        assert contains_rbac == expected


@pytest.mark.parametrize('action', [
    'create', 'delete', 'update', 'read_values', 'write_values',
    'grant', 'revoke'
])
def test_role_contains_rbac_permissions_multiple_rbac_perms(
        cursor, valueset, new_role, insertuser,
        new_permission, action):
    organization = insertuser[4]
    role = new_role(org=organization)
    rbac_object_types = ['users', 'roles', 'permissions']
    perms = [new_permission(action, object_type, True, org=organization)
             for object_type in rbac_object_types]
    for perm in perms:
        cursor.execute(
            'INSERT INTO role_permission_mapping(role_id, permission_id) '
            'VALUES (%s, %s)', (role['id'], perm['id']))
    cursor.execute(
        'SELECT arbiter_data.role_contains_rbac_permissions(%s)',
        role['id'])
    contains_rbac = cursor.fetchone()[0]
    assert contains_rbac == 1


def test_get_reference_role_id(dictcursor):
    dictcursor.execute('SELECT get_reference_role_id()')
    roleid = dictcursor.fetchone()['get_reference_role_id()']
    dictcursor.execute(
        'SELECT * FROM arbiter_data.roles WHERE id = %s',
        roleid)
    role = dictcursor.fetchone()
    assert role['name'] == 'Read Reference Data'


def test_get_current_user_info(dictcursor, allow_read_users, insertuser):
    user = insertuser[0]
    org = insertuser[4]
    auth0id = user['auth0_id']
    dictcursor.callproc('get_current_user_info', (auth0id,))
    user_info = dictcursor.fetchone()
    assert user_info['user_id'] == str(bin_to_uuid(user['id']))
    assert user_info['organization'] == org['name']
    assert user_info['auth0_id'] == user['auth0_id']


@pytest.mark.parametrize('accepted', [True, False])
def test_user_org_accepted_tou(
        dictcursor, new_user, new_organization_no_tou, accepted):
    if accepted:
        user = new_user()
    else:
        user = new_user(org=new_organization_no_tou())
    dictcursor.execute(
        'SELECT user_org_accepted_tou(%s) as accepted',
        user['id'])
    assert (dictcursor.fetchone()['accepted'] == 1) is accepted


@pytest.fixture()
def allow_write_values(insertuser, new_permission, cursor):
    perms = [new_permission('write_values', obj, True, org=insertuser.org)
             for obj in ('forecasts', 'observations',
                         'cdf_forecasts', 'reports')]
    cursor.executemany(
        'INSERT INTO role_permission_mapping (role_id, permission_id) '
        'VALUES (%s, %s)',
        [(insertuser.role['id'], perm['id']) for perm in perms])


def test_read_metadata_for_value_write_fx(
        dictcursor, insertuser, allow_write_values):
    time_ = dt.datetime(2019, 9, 30, 12, 45)
    dictcursor.execute(
        'INSERT INTO forecasts_values (id, timestamp, value) VALUES'
        ' (%s, %s, %s)', (insertuser.fx['id'], time_, 0))
    dictcursor.callproc('read_metadata_for_value_write',
                        (insertuser.auth0id, insertuser.fx['strid'],
                         'forecasts', '2019-09-30 13:00'))
    res = dictcursor.fetchone()
    assert isinstance(res['interval_length'], int)
    assert res['previous_time'] == time_
    assert isinstance(res['extra_parameters'], str)


def test_read_metadata_for_value_write_fx_before(
        dictcursor, insertuser, allow_write_values):
    time_ = dt.datetime(2019, 9, 30, 12, 45)
    dictcursor.execute(
        'INSERT INTO forecasts_values (id, timestamp, value) VALUES'
        ' (%s, %s, %s)', (insertuser.fx['id'], time_, 0))
    dictcursor.callproc('read_metadata_for_value_write',
                        (insertuser.auth0id, insertuser.fx['strid'],
                         'forecasts',
                         '2019-09-30 12:00'))
    res = dictcursor.fetchone()
    assert isinstance(res['interval_length'], int)
    assert res['previous_time'] is None
    assert isinstance(res['extra_parameters'], str)


def test_read_metadata_for_value_write_fx_no_vals(
        dictcursor, insertuser, allow_write_values):
    dictcursor.callproc('read_metadata_for_value_write',
                        (insertuser.auth0id,
                         insertuser.fx['strid'], 'forecasts',
                         '2019-09-30 13:00'))
    res = dictcursor.fetchone()
    assert isinstance(res['interval_length'], int)
    assert res['previous_time'] is None
    assert isinstance(res['extra_parameters'], str)


def test_read_metadata_for_value_write_fx_no_write(
        cursor, insertuser):
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_metadata_for_value_write',
                        (insertuser.auth0id,
                         insertuser.fx['strid'], 'forecasts',
                         '2019-09-30 13:00'))
    assert e.value.args[0] == 1142


def test_read_metadata_for_value_write_obs(
        dictcursor, insertuser, allow_write_values):
    time_ = dt.datetime(2019, 9, 30, 12, 45)
    dictcursor.execute(
        'INSERT INTO observations_values (id, timestamp, value, quality_flag)'
        ' VALUES (%s, %s, %s, %s)', (insertuser.obs['id'], time_, 0, 0))
    dictcursor.callproc('read_metadata_for_value_write',
                        (insertuser.auth0id,
                         insertuser.obs['strid'], 'observations',
                         '2019-09-30 13:00'))
    res = dictcursor.fetchone()
    assert isinstance(res['interval_length'], int)
    assert res['previous_time'] == time_
    assert isinstance(res['extra_parameters'], str)


def test_read_metadata_for_value_write_obs_before(
        dictcursor, insertuser, allow_write_values):
    time_ = dt.datetime(2019, 9, 30, 12, 45)
    dictcursor.execute(
        'INSERT INTO observations_values (id, timestamp, value, quality_flag)'
        ' VALUES (%s, %s, %s, %s)', (insertuser.obs['id'], time_, 0, 0))
    dictcursor.callproc('read_metadata_for_value_write',
                        (insertuser.auth0id,
                         insertuser.obs['strid'], 'observations',
                         '2019-09-30 12:00'))
    res = dictcursor.fetchone()
    assert isinstance(res['interval_length'], int)
    assert res['previous_time'] is None
    assert isinstance(res['extra_parameters'], str)


def test_read_metadata_for_value_write_obs_no_vals(
        dictcursor, insertuser, allow_write_values):
    dictcursor.callproc('read_metadata_for_value_write',
                        (insertuser.auth0id,
                         insertuser.obs['strid'], 'observations',
                         '2019-09-30 13:00'))
    res = dictcursor.fetchone()
    assert isinstance(res['interval_length'], int)
    assert res['previous_time'] is None
    assert isinstance(res['extra_parameters'], str)


def test_read_metadata_for_value_write_obs_no_write(
        cursor, insertuser):
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_metadata_for_value_write',
                        (insertuser.auth0id,
                         insertuser.obs['strid'], 'observations',
                         '2019-09-30 13:00'))
    assert e.value.args[0] == 1142


def test_read_metadata_for_value_write_cdf(
        dictcursor, insertuser, allow_write_values):
    time_ = dt.datetime(2019, 9, 30, 12, 45)
    cdf_id = list(insertuser.cdf['constant_values'].keys())[0]
    dictcursor.execute(
        'INSERT INTO cdf_forecasts_values (id, timestamp, value) VALUES'
        ' (UUID_TO_BIN(%s, 1), %s, %s)', (cdf_id, time_, 0))
    dictcursor.callproc('read_metadata_for_value_write',
                        (insertuser.auth0id, cdf_id,
                         'cdf_forecasts',
                         '2019-09-30 13:00'))
    res = dictcursor.fetchone()
    assert isinstance(res['interval_length'], int)
    assert res['previous_time'] == time_
    assert isinstance(res['extra_parameters'], str)


def test_read_metadata_for_value_write_cdf_before(
        dictcursor, insertuser, allow_write_values):
    time_ = dt.datetime(2019, 9, 30, 12, 45)
    cdf_id = list(insertuser.cdf['constant_values'].keys())[0]
    dictcursor.execute(
        'INSERT INTO cdf_forecasts_values (id, timestamp, value) VALUES'
        ' (UUID_TO_BIN(%s, 1), %s, %s)', (cdf_id, time_, 0))
    dictcursor.callproc('read_metadata_for_value_write',
                        (insertuser.auth0id, cdf_id,
                         'cdf_forecasts',
                         '2019-09-30 12:00'))
    res = dictcursor.fetchone()
    assert isinstance(res['interval_length'], int)
    assert res['previous_time'] is None
    assert isinstance(res['extra_parameters'], str)


def test_read_metadata_for_value_write_cdf_no_vals(
        dictcursor, insertuser, allow_write_values):
    cdf_id = list(insertuser.cdf['constant_values'].keys())[0]
    dictcursor.callproc('read_metadata_for_value_write',
                        (insertuser.auth0id, cdf_id,
                         'cdf_forecasts',
                         '2019-09-30 12:00'))
    res = dictcursor.fetchone()
    assert isinstance(res['interval_length'], int)
    assert res['previous_time'] is None
    assert isinstance(res['extra_parameters'], str)


def test_read_metadata_for_value_write_cdf_fx_no_write(
        cursor, insertuser):
    cdf_id = list(insertuser.cdf['constant_values'].keys())[0]
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_metadata_for_value_write',
                        (insertuser.auth0id, cdf_id,
                         'cdf_forecasts',
                         '2019-09-30 12:00'))
    assert e.value.args[0] == 1142


def test_read_metadata_for_value_write_invalid(cursor, insertuser):
    with pytest.raises(pymysql.err.ProgrammingError) as e:
        cursor.callproc('read_metadata_for_value_write',
                        (insertuser.auth0id, insertuser.fx['strid'],
                         'sites',
                         '2019-09-30 12:00'))
    assert e.value.args[0] == 1146


def test_read_metadata_for_value_write_different_type(dictcursor, insertuser,
                                                      allow_write_values):
    time_ = dt.datetime(2019, 9, 30, 12, 45)
    dictcursor.execute(
        'INSERT INTO observations_values (id, timestamp, value, quality_flag)'
        ' VALUES (%s, %s, %s, %s)', (insertuser.obs['id'], time_, 0, 0))
    dictcursor.callproc('read_metadata_for_value_write',
                        (insertuser.auth0id,
                         insertuser.obs['strid'], 'observations',
                         '2019-09-30 13:00'))    
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc('read_metadata_for_value_write',
                            (insertuser.auth0id,
                             insertuser.obs['strid'], 'forecasts',
                             '2019-09-30 13:00'))
    assert e.value.args[0] == 1142
    

def test_read_user_id(cursor, insertuser, new_user):
    u2 = new_user()
    cursor.callproc('read_user_id', (insertuser.auth0id, u2['auth0_id']))
    u2id = cursor.fetchone()[0]
    assert u2id == bin_to_uuid(u2['id'])


def test_read_user_id_other_unaffiliated(cursor, insertuser,
                                         new_unaffiliated_user):
    u2 = new_unaffiliated_user()
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_user_id', (insertuser.auth0id, u2['auth0_id']))
    assert e.value.args[0] == 1142


def test_read_user_id_caller_unaffiliated(cursor, insertuser,
                                          new_unaffiliated_user):
    u2 = new_unaffiliated_user()
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_user_id', (u2['auth0_id'], insertuser.auth0id))
    assert e.value.args[0] == 1142


def test_read_auth0id(cursor, insertuser, new_user):
    u2 = new_user()
    cursor.callproc('read_auth0id', (insertuser.auth0id, bin_to_uuid(u2['id'])))
    u2auth0id = cursor.fetchone()[0]
    assert u2auth0id == u2['auth0_id']


def test_read_auth0id_other_unaffiliated(cursor, insertuser,
                                         new_unaffiliated_user):
    u2 = new_unaffiliated_user()
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_auth0id', (insertuser.auth0id, bin_to_uuid(u2['id'])))
    assert e.value.args[0] == 1142


def test_read_auth0id_caller_unaffiliated(cursor, insertuser,
                                          new_unaffiliated_user):
    u2 = new_unaffiliated_user()
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_auth0id', (u2['auth0_id'], bin_to_uuid(insertuser.user['id'])))
    assert e.value.args[0] == 1142


all_actions = ['read', 'update', 'delete', 'read_values',
               'write_values', 'delete_values', 'grant', 'revoke']

def action_combinations():
    combos = []
    for i in range(1, 9):
        combos = combos + list(itertools.combinations(all_actions, i))
    return combos

@pytest.mark.parametrize('granted', action_combinations())
def test_get_user_actions_on_object(
        dictcursor, user_org_role, new_role, add_perm, granted):
    user, org, _ = user_org_role
    auth0id = user['auth0_id']
    role = new_role(org=org)
    role_id = bin_to_uuid(role['id'])

    for action in granted:
        add_perm(action, 'roles')

    dictcursor.callproc('get_user_actions_on_object', (auth0id, role_id))
    actions = dictcursor.fetchall()
    assert actions == [{'action': action} for action in granted]


def test_get_user_actions_on_object_no_permissions(
        dictcursor, user_org_role, new_forecast):
    user, org, _ = user_org_role
    auth0id = user['auth0_id']
    forecast = new_forecast(org=org)
    forecast_id = bin_to_uuid(forecast['id'])
    
    dictcursor.callproc('get_user_actions_on_object', (auth0id, forecast_id))
    actions = dictcursor.fetchall()
    assert not actions

    
@pytest.fixture()
def remove_perm(cursor):
    def fcn(action, what):
        cursor.execute(
            'DELETE FROM permissions WHERE action=%s and object_type=%s',
            (action, what))
    return fcn


def test_get_user_actions_on_object_after_removal(
        dictcursor, user_org_role, new_role, add_perm, remove_perm):
    user, org, _ = user_org_role
    auth0id = user['auth0_id']
    role = new_role(org=org)
    role_id = bin_to_uuid(role['id'])

    to_grant = all_actions.copy()
    for action in to_grant:
        add_perm(action, 'roles')

    dictcursor.callproc('get_user_actions_on_object', (auth0id, role_id))
    actions = dictcursor.fetchall()
    assert actions == [{'action': action} for action in to_grant]

    for action in to_grant:
        remove_perm(action, 'roles')
        dictcursor.callproc('get_user_actions_on_object', (auth0id, role_id))
        actions = dictcursor.fetchall()
        assert action not in [x['action'] for x in actions]


def test_read_latest_observation_values(cursor, obs_values, insertuser,
                                        allow_read_observation_values):
    auth0id, obsid, vals, *_ = obs_values(insertuser[3]['strid'])
    cursor.callproc('read_latest_observation_value', (auth0id, obsid))
    res = cursor.fetchall()
    assert len(res) == 1
    assert res[0] == vals[-1]
    time_ = dt.datetime.now().replace(microsecond=0)
    cursor.execute(
        'INSERT INTO observations_values (id, timestamp, value, quality_flag)'
        ' VALUES (UUID_TO_BIN(%s, 1), %s, %s, %s)', (obsid, time_, 0, 0))
    cursor.callproc('read_latest_observation_value', (auth0id, obsid))
    res = cursor.fetchall()
    assert res[0] == (obsid, time_, 0, 0)


def test_read_latest_observation_values_no_data(
        cursor, obs_values, insertuser, allow_read_observation_values):
    auth0id, obsid, vals, *_ = obs_values(insertuser[3]['strid'])
    cursor.execute(
        'DELETE from observations_values where id = UUID_TO_BIN(%s, 1)',
        (obsid,))
    cursor.callproc('read_latest_observation_value', (auth0id, obsid))
    res = cursor.fetchall()
    assert len(res) == 0


def test_read_latest_observation_values_denied(cursor, obs_values, insertuser):
    auth0id, obsid, vals, start, end = obs_values(insertuser[3]['strid'])
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_latest_observation_value',
                        (auth0id, obsid))
    assert e.value.args[0] == 1142


    
def test_read_observation_latest_fxid(cursor, obs_values, insertuser,
                                      allow_read_observation_values,
                                      allow_read_forecast_values):
    auth0id, obsid, vals, start, end = obs_values(insertuser[3]['strid'])
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_latest_observation_value',
                        (auth0id, insertuser.fx['strid']))
    assert e.value.args[0] == 1142

    
def test_read_latest_observation_values_denied_can_read_meta(
        cursor, obs_values, allow_read_observations, insertuser):
    auth0id, obsid, vals, start, end = obs_values(insertuser[3]['strid'])
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_latest_observation_value',
                        (auth0id, obsid))
    assert e.value.args[0] == 1142


def test_read_latest_forecast_values(cursor, fx_values, insertuser,
                                     allow_read_forecast_values):
    auth0id, fxid, vals, *_ = fx_values
    cursor.callproc('read_latest_forecast_value', (auth0id, fxid))
    res = cursor.fetchall()
    assert len(res) == 1
    assert res[0] == vals[-1]
    time_ = dt.datetime.now().replace(microsecond=0)
    cursor.execute(
        'INSERT INTO forecasts_values (id, timestamp, value)'
        ' VALUES (UUID_TO_BIN(%s, 1), %s, %s)', (fxid, time_, 1.8))
    cursor.callproc('read_latest_forecast_value', (auth0id, fxid))
    res = cursor.fetchall()
    assert res[0] == (fxid, time_, 1.8)


def test_read_latest_forecast_values_no_data(
        cursor, fx_values, insertuser, allow_read_forecast_values):
    auth0id, fxid, vals, *_ = fx_values
    cursor.execute(
        'DELETE from forecasts_values where id = UUID_TO_BIN(%s, 1)',
        (fxid,))
    cursor.callproc('read_latest_forecast_value', (auth0id, fxid))
    res = cursor.fetchall()
    assert len(res) == 0


def test_read_latest_forecast_values_denied(cursor, fx_values, insertuser):
    auth0id, fxid, vals, start, end = fx_values
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_latest_forecast_value',
                        (auth0id, fxid))
    assert e.value.args[0] == 1142


def test_read_latest_forecast_values_obsid(cursor, fx_values, insertuser,
                                           allow_read_forecast_values,
                                           allow_read_observation_values):
    auth0id, fxid, vals, start, end = fx_values
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_latest_forecast_value',
                        (auth0id, insertuser.obs['strid']))
    assert e.value.args[0] == 1142


def test_read_latest_forecast_values_denied_can_read_meta(
        cursor, fx_values, allow_read_forecasts, insertuser):
    auth0id, fxid, vals, start, end = fx_values
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_latest_forecast_value',
                        (auth0id, fxid))
    assert e.value.args[0] == 1142


def test_read_latest_cdf_forecast_values(
        cursor, cdf_fx_values, insertuser, allow_read_cdf_forecast_values):
    auth0id, cdf_fxid, vals, *_ = cdf_fx_values
    cursor.callproc('read_latest_cdf_forecast_value', (auth0id, cdf_fxid))
    res = cursor.fetchall()
    assert len(res) == 1
    assert res[0] == vals[-1]
    time_ = dt.datetime.now().replace(microsecond=0)
    cursor.execute(
        'INSERT INTO cdf_forecasts_values (id, timestamp, value)'
        ' VALUES (UUID_TO_BIN(%s, 1), %s, %s)', (cdf_fxid, time_, 1.8))
    cursor.callproc('read_latest_cdf_forecast_value', (auth0id, cdf_fxid))
    res = cursor.fetchall()
    assert res[0] == (cdf_fxid, time_, 1.8)


def test_read_latest_cdf_forecast_values_no_data(
        cursor, cdf_fx_values, insertuser, allow_read_cdf_forecast_values):
    auth0id, cdf_fxid, vals, *_ = cdf_fx_values
    cursor.execute(
        'DELETE from cdf_forecasts_values where id = UUID_TO_BIN(%s, 1)',
        (cdf_fxid,))
    cursor.callproc('read_latest_cdf_forecast_value', (auth0id, cdf_fxid))
    res = cursor.fetchall()
    assert len(res) == 0


def test_read_latest_cdf_forecast_values_denied(
        cursor, cdf_fx_values, insertuser):
    auth0id, cdf_fxid, vals, start, end = cdf_fx_values
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_latest_cdf_forecast_value',
                        (auth0id, cdf_fxid))
    assert e.value.args[0] == 1142

    
def test_read_latest_cdf_forecast_values_obsid(
        cursor, cdf_fx_values, insertuser,
        allow_read_cdf_forecast_values,
        allow_read_observation_values):
    auth0id, fxid, vals, start, end = cdf_fx_values
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_latest_cdf_forecast_value',
                        (auth0id, insertuser.obs['strid']))
    assert e.value.args[0] == 1142


def test_read_latest_cdf_forecast_values_denied_can_read_meta(
        cursor, cdf_fx_values, allow_read_cdf_forecasts, insertuser):
    auth0id, cdf_fxid, vals, start, end = cdf_fx_values
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_latest_cdf_forecast_value',
                        (auth0id, cdf_fxid))
    assert e.value.args[0] == 1142


def test_read_observation_range(
        cursor, obs_values, insertuser, allow_read_observation_values):
    auth0id, obsid, vals, *_ = obs_values(insertuser[3]['strid'])
    cursor.callproc('read_observation_time_range', (auth0id, obsid))
    res = cursor.fetchall()
    assert len(res) == 1
    assert res[0] == (dt.datetime(2020, 1, 3, 10), vals[-1][1])
    early = dt.datetime(1989, 3, 2, 12, 22)
    time_ = dt.datetime.now().replace(microsecond=0)
    cursor.executemany(
        'INSERT INTO observations_values (id, timestamp, value, quality_flag)'
        ' VALUES (UUID_TO_BIN(%s, 1), %s, %s, %s)', (
            (obsid, early, 0, 0), (obsid, time_, 0, 0)))
    cursor.callproc('read_observation_time_range', (auth0id, obsid))
    res = cursor.fetchall()
    assert res[0] == (early, time_)


def test_read_observation_range_no_data(
        cursor, obs_values, insertuser, allow_read_observation_values):
    auth0id, obsid, vals, *_ = obs_values(insertuser[3]['strid'])
    cursor.execute(
        'DELETE from observations_values where id = UUID_TO_BIN(%s, 1)',
        (obsid,))
    cursor.callproc('read_observation_time_range', (auth0id, obsid))
    res = cursor.fetchall()
    assert len(res) == 1
    assert res[0] == (None, None)


def test_read_observation_time_range_denied(cursor, obs_values, insertuser):
    auth0id, obsid, vals, start, end = obs_values(insertuser[3]['strid'])
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_observation_time_range', (auth0id, obsid))
    assert e.value.args[0] == 1142


def test_read_observation_time_range_fxid(cursor, obs_values, insertuser,
                                          allow_read_observation_values,
                                          allow_read_forecast_values):
    auth0id, obsid, vals, start, end = obs_values(insertuser[3]['strid'])
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_observation_time_range',
                        (auth0id, insertuser.fx['strid']))
    assert e.value.args[0] == 1142


def test_read_observation_time_range_denied_can_read_meta(
        cursor, obs_values, allow_read_observations, insertuser):
    auth0id, obsid, vals, start, end = obs_values(insertuser[3]['strid'])
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_observation_time_range', (auth0id, obsid))
    assert e.value.args[0] == 1142


def test_read_cdf_forecast_range(
        cursor, cdf_fx_values, insertuser, allow_read_cdf_forecast_values):
    auth0id, cdf_fxid, vals, *_ = cdf_fx_values
    cursor.callproc('read_cdf_forecast_time_range', (auth0id, cdf_fxid))
    res = cursor.fetchall()
    assert len(res) == 1
    assert res[0] == (dt.datetime(2020, 1, 3, 18, 1), vals[-1][1])
    early = dt.datetime(1989, 3, 2, 12, 22)
    time_ = dt.datetime.now().replace(microsecond=0)
    cursor.executemany(
        'INSERT INTO cdf_forecasts_values (id, timestamp, value)'
        ' VALUES (UUID_TO_BIN(%s, 1), %s, %s)', (
            (cdf_fxid, early, 0), (cdf_fxid, time_, 0)))
    cursor.callproc('read_cdf_forecast_time_range', (auth0id, cdf_fxid))
    res = cursor.fetchall()
    assert res[0] == (early, time_)


def test_read_cdf_forecast_range_no_data(
        cursor, cdf_fx_values, insertuser, allow_read_cdf_forecast_values):
    auth0id, cdf_fxid, vals, *_ = cdf_fx_values
    cursor.execute(
        'DELETE from cdf_forecasts_values where id = UUID_TO_BIN(%s, 1)',
        (cdf_fxid,))
    cursor.callproc('read_cdf_forecast_time_range', (auth0id, cdf_fxid))
    res = cursor.fetchall()
    assert len(res) == 1
    assert res[0] == (None, None)


def test_read_cdf_forecast_time_range_denied(
        cursor, cdf_fx_values, insertuser):
    auth0id, cdf_fxid, vals, start, end = cdf_fx_values
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_cdf_forecast_time_range', (auth0id, cdf_fxid))
    assert e.value.args[0] == 1142


def test_read_cdf_forecast_time_range_obs_id(
        cursor, cdf_fx_values, insertuser, allow_read_cdf_forecast_values,
        allow_read_observation_values):
    auth0id, *_ = cdf_fx_values
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_cdf_forecast_time_range',
                        (auth0id, insertuser.obs['strid']))
    assert e.value.args[0] == 1142
    

def test_read_cdf_forecast_time_range_denied_can_read_meta(
        cursor, cdf_fx_values, allow_read_cdf_forecasts, insertuser):
    auth0id, cdf_fxid, vals, start, end = cdf_fx_values
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_cdf_forecast_time_range', (auth0id, cdf_fxid))
    assert e.value.args[0] == 1142

    
def test_read_forecast_range(
        cursor, fx_values, insertuser, allow_read_forecast_values):
    auth0id, fxid, vals, *_ = fx_values
    cursor.callproc('read_forecast_time_range', (auth0id, fxid))
    res = cursor.fetchall()
    assert len(res) == 1
    assert res[0] == (dt.datetime(2020, 1, 1, 11, 3), vals[-1][1])
    early = dt.datetime(1989, 3, 2, 12, 22)
    time_ = dt.datetime.now().replace(microsecond=0)
    cursor.executemany(
        'INSERT INTO forecasts_values (id, timestamp, value)'
        ' VALUES (UUID_TO_BIN(%s, 1), %s, %s)', (
            (fxid, early, 0), (fxid, time_, 0)))
    cursor.callproc('read_forecast_time_range', (auth0id, fxid))
    res = cursor.fetchall()
    assert res[0] == (early, time_)


def test_read_forecast_range_no_data(
        cursor, fx_values, insertuser, allow_read_forecast_values):
    auth0id, fxid, vals, *_ = fx_values
    cursor.execute(
        'DELETE from forecasts_values where id = UUID_TO_BIN(%s, 1)',
        (fxid,))
    cursor.callproc('read_forecast_time_range', (auth0id, fxid))
    res = cursor.fetchall()
    assert len(res) == 1
    assert res[0] == (None, None)


def test_read_forecast_time_range_denied(
        cursor, fx_values, insertuser):
    auth0id, fxid, vals, start, end = fx_values
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_forecast_time_range', (auth0id, fxid))
    assert e.value.args[0] == 1142


def test_read_forecast_time_range_obs_id(
        cursor, fx_values, insertuser, allow_read_forecast_values,
        allow_read_observation_values):
    auth0id, *_ = fx_values
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_forecast_time_range',
                        (auth0id, insertuser.obs['strid']))
    assert e.value.args[0] == 1142
    

def test_read_forecast_time_range_denied_can_read_meta(
        cursor, fx_values, allow_read_forecasts, insertuser):
    auth0id, fxid, vals, start, end = fx_values
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('read_forecast_time_range', (auth0id, fxid))
    assert e.value.args[0] == 1142


def test_find_unflagged_observation_dates(cursor, obs_values, insertuser,
                                          allow_read_observation_values):
    auth0id, obsid, vals, start, end = obs_values(insertuser[3]['strid'])
    cursor.execute(
        'UPDATE observations_values SET quality_flag = 1 '
        'WHERE id = UUID_TO_BIN(%s, 1)', obsid)
    cursor.callproc('find_unflagged_observation_dates',
                    (auth0id, obsid, start, end, 1, 'UTC'))
    assert len(cursor.fetchall()) == 0
    cursor.callproc('find_unflagged_observation_dates',
                    (auth0id, obsid, start, end, 2, 'UTC'))
    assert cursor.fetchall()[0] == (start.date(),)
    cursor.callproc('find_unflagged_observation_dates',
                    (auth0id, obsid, start, end, 3, 'UTC'))
    assert cursor.fetchall()[0] == (start.date(),)
    cursor.callproc('find_unflagged_observation_dates',
                    (auth0id, obsid, start, end, 2, 'Etc/GMT+7'))
    assert cursor.fetchall()[0] == (start.date(),)
    cursor.callproc('find_unflagged_observation_dates',
                    (auth0id, obsid, start, end, 2, 'Etc/GMT-12'))
    assert cursor.fetchall()[0] == (start.date() + dt.timedelta(days=1),)
    

def test_find_unflagged_observation_dates_denied(
        cursor, obs_values, insertuser, allow_read_observations):
    auth0id, obsid, vals, start, end = obs_values(insertuser[3]['strid'])
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('find_unflagged_observation_dates',
                        (auth0id, obsid, start, end, 1, 'UTC'))
    assert e.value.args[0] == 1142


def test_find_observation_gaps(
        cursor, obs_values, insertuser, allow_read_observations,
        allow_read_observation_values):
    auth0id, obsid, vals, start, end = obs_values(insertuser[3]['strid'])
    start = start - dt.timedelta(minutes=10)
    end = end + dt.timedelta(days=36)
    mid = start + dt.timedelta(minutes=10)
    cursor.executemany(
        'INSERT INTO observations_values (id, timestamp, value, quality_flag)'
        ' VALUES (uuid_to_bin(%s, 1), %s, 0, 0)', (
            (obsid, start), (obsid, end + dt.timedelta(minutes=5)),
            (obsid, str(mid))))
    cursor.callproc('find_observation_gaps',
                    (auth0id, obsid, start, end))
    out = cursor.fetchall()
    assert len(out) == 2
    assert out[0] == (start, mid)
    assert out[1] == (mid, mid + dt.timedelta(seconds=20, minutes=8))

    # single value
    start = start + dt.timedelta(days=30)
    cursor.execute(
        'INSERT INTO observations_values (id, timestamp, value, quality_flag)'
        ' VALUES (uuid_to_bin(%s, 1), %s, 0, 0)', (obsid, start))
    cursor.callproc('find_observation_gaps',
                    (auth0id, obsid, start, end))
    assert len(cursor.fetchall()) == 0


def test_find_observation_gaps_no_read_obs(
        cursor, obs_values, insertuser, 
        allow_read_observation_values):
    auth0id, obsid, vals, start, end = obs_values(insertuser[3]['strid'])
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('find_observation_gaps',
                        (auth0id, obsid, start, end))
    assert e.value.args[0] == 1142


def test_find_observation_gaps_no_read_obs_vals(
        cursor, obs_values, insertuser, 
        allow_read_observations):
    auth0id, obsid, vals, start, end = obs_values(insertuser[3]['strid'])
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('find_observation_gaps',
                        (auth0id, obsid, start, end))
    assert e.value.args[0] == 1142


def test_find_observation_gaps_is_fx(
        cursor, obs_values, insertuser, allow_read_forecast_values,
        allow_read_forecasts):
    auth0id, obsid, vals, start, end = obs_values(insertuser.obs['strid'])
    fxid = insertuser.fx['strid']
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('find_observation_gaps',
                        (auth0id, fxid, start, end))
    assert e.value.args[0] == 1142


def test_find_forecast_gaps(
        cursor, fx_values, insertuser, allow_read_forecasts,
        allow_read_forecast_values):
    auth0id, fxid, vals, start, end = fx_values
    start = start - dt.timedelta(hours=3)
    end = end + dt.timedelta(days=36)
    mid = start + dt.timedelta(hours=2)
    cursor.executemany(
        'INSERT INTO forecasts_values (id, timestamp, value)'
        ' VALUES (uuid_to_bin(%s, 1), %s, 0)', (
            (fxid, start), (fxid, end + dt.timedelta(minutes=5)),
            (fxid, str(mid))))
    cursor.callproc('find_forecast_gaps',
                    (auth0id, fxid, start, end))
    out = cursor.fetchall()
    assert len(out) == 2
    assert out[0] == (start, mid)
    assert out[1] == (mid, mid + dt.timedelta(hours=1, seconds=20, minutes=8))

    # single value
    start = start + dt.timedelta(days=30)
    cursor.execute(
        'INSERT INTO forecasts_values (id, timestamp, value)'
        ' VALUES (uuid_to_bin(%s, 1), %s, 0)', (fxid, start))
    cursor.callproc('find_forecast_gaps',
                    (auth0id, fxid, start, end))
    assert len(cursor.fetchall()) == 0


def test_find_forecast_gaps_no_read_fx(
        cursor, fx_values, insertuser, 
        allow_read_forecast_values):
    auth0id, fxid, vals, start, end = fx_values
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('find_forecast_gaps',
                        (auth0id, fxid, start, end))
    assert e.value.args[0] == 1142


def test_find_forecast_gaps_no_read_fx_vals(
        cursor, fx_values, insertuser, 
        allow_read_forecasts):
    auth0id, fxid, vals, start, end = fx_values
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('find_forecast_gaps',
                        (auth0id, fxid, start, end))
    assert e.value.args[0] == 1142


def test_find_forecast_gaps_is_obs(
        cursor, fx_values, insertuser, allow_read_forecast_values,
        allow_read_forecasts):
    auth0id, fxid, vals, start, end = fx_values
    obsid = insertuser.obs['strid']
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('find_forecast_gaps',
                        (auth0id, obsid, start, end))
    assert e.value.args[0] == 1142


def test_find_cdf_single_forecast_gaps(
        cursor, cdf_fx_values, insertuser, allow_read_cdf_forecasts,
        allow_read_cdf_forecast_values):
    auth0id, cdf_fxid, vals, start, end = cdf_fx_values
    start = start - dt.timedelta(hours=3)
    end = end + dt.timedelta(days=36)
    mid = start + dt.timedelta(hours=2)
    cursor.executemany(
        'INSERT INTO cdf_forecasts_values (id, timestamp, value)'
        ' VALUES (uuid_to_bin(%s, 1), %s, 0)', (
            (cdf_fxid, start), (cdf_fxid, end + dt.timedelta(minutes=5)),
            (cdf_fxid, str(mid))))
    cursor.callproc('find_cdf_single_forecast_gaps',
                    (auth0id, cdf_fxid, start, end))
    out = cursor.fetchall()
    assert len(out) == 2
    assert out[0] == (start, mid)
    assert out[1] == (mid, mid + dt.timedelta(hours=1, seconds=20, minutes=8))

    # singles value
    start = start + dt.timedelta(days=30)
    cursor.execute(
        'INSERT INTO cdf_forecasts_values (id, timestamp, value)'
        ' VALUES (uuid_to_bin(%s, 1), %s, 0)', (cdf_fxid, start))
    cursor.callproc('find_cdf_single_forecast_gaps',
                    (auth0id, cdf_fxid, start, end))
    assert len(cursor.fetchall()) == 0


def test_find_cdf_single_forecast_gaps_no_read_cdf_fx(
        cursor, cdf_fx_values, insertuser, 
        allow_read_cdf_forecast_values):
    auth0id, cdf_fxid, vals, start, end = cdf_fx_values
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('find_cdf_single_forecast_gaps',
                        (auth0id, cdf_fxid, start, end))
    assert e.value.args[0] == 1142


def test_find_cdf_single_forecast_gaps_no_read_cdf_fx_vals(
        cursor, cdf_fx_values, insertuser,
        allow_read_cdf_forecasts):
    auth0id, cdf_fxid, vals, start, end = cdf_fx_values
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('find_cdf_single_forecast_gaps',
                        (auth0id, cdf_fxid, start, end))
    assert e.value.args[0] == 1142


def test_find_cdf_single_forecast_gaps_is_obs(
        cursor, cdf_fx_values, insertuser, allow_read_cdf_forecast_values,
        allow_read_cdf_forecasts):
    auth0id, cdf_fxid, vals, start, end = cdf_fx_values
    obsid = insertuser.obs['strid']
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('find_cdf_single_forecast_gaps',
                        (auth0id, obsid, start, end))
    assert e.value.args[0] == 1142


@pytest.fixture()
def cdf_grp_fx_values(cursor, insertuser, request):
    auth0id = insertuser[0]['auth0_id']
    forecast = insertuser.cdf
    strid = forecast['strid']
    start = dt.datetime(2020, 1, 30, 12, 20)
    for sid in forecast['constant_values'].keys():
        vals = tuple([
            (sid, start + dt.timedelta(hours=i),
             float(random.randint(0, 100))) for i in range(10)])
        cursor.executemany(
            'INSERT INTO cdf_forecasts_values (id, timestamp, value) '
            'VALUES (UUID_TO_BIN(%s, 1), %s, %s)', vals)
    end = dt.datetime(2020, 1, 30, 23, 20)
    return auth0id, strid, vals, start, end


def test_find_cdf_forecast_gaps(
        cursor, cdf_grp_fx_values, insertuser, allow_read_cdf_forecasts,
        allow_read_cdf_forecast_values):
    auth0id, cdf_fxid, vals, start, end = cdf_grp_fx_values
    start = start - dt.timedelta(hours=6)
    end = end + dt.timedelta(days=36)
    mid = start + dt.timedelta(hours=2)
    for sid in insertuser.cdf['constant_values'].keys():
        cursor.executemany(
            'INSERT INTO cdf_forecasts_values (id, timestamp, value)'
            ' VALUES (uuid_to_bin(%s, 1), %s, 0)', (
                (sid, start), (sid, end + dt.timedelta(hours=1)),
                (sid, str(mid))))
    cursor.callproc('find_cdf_forecast_gaps',
                    (auth0id, cdf_fxid, start, end))
    out = cursor.fetchall()
    assert len(out) == 2
    assert out[0] == (start, mid)
    assert out[1] == (mid, mid + dt.timedelta(hours=4))
    
    # difference between singles
    start = start + dt.timedelta(days=2)
    mid = start + dt.timedelta(hours=2)
    fin = mid + dt.timedelta(hours=8)

    cursor.callproc('find_cdf_forecast_gaps',
                    (auth0id, cdf_fxid, start, end))
    out = cursor.fetchall()
    assert len(out) == 0

    sid = list(insertuser.cdf['constant_values'].keys())[0]
    cursor.executemany(
        'INSERT INTO cdf_forecasts_values (id, timestamp, value)'
        ' VALUES (uuid_to_bin(%s, 1), %s, 0)', (
            (sid, start), (sid, mid), (sid, fin)))
    cursor.callproc('find_cdf_forecast_gaps',
                    (auth0id, cdf_fxid, start, end))
    out = cursor.fetchall()
    assert len(out) == 2
    assert out[0] == (start, mid)
    assert out[1] == (mid, fin)

    # add some data to a different cv
    sid = list(insertuser.cdf['constant_values'].keys())[1]
    inter = mid + dt.timedelta(hours=2)
    cursor.executemany(
        'INSERT INTO cdf_forecasts_values (id, timestamp, value)'
        ' VALUES (uuid_to_bin(%s, 1), %s, 0)', (
            (sid, start), (sid, inter)))
    cursor.callproc('find_cdf_forecast_gaps',
                    (auth0id, cdf_fxid, start, end))
    out = cursor.fetchall()
    assert len(out) == 3
    assert out[0] == (start, mid)
    assert out[1] == (mid, inter)
    assert out[2] == (inter, fin)

    # single value
    start = start + dt.timedelta(days=30)
    for sid in insertuser.cdf['constant_values'].keys():
        cursor.execute(
            'INSERT INTO cdf_forecasts_values (id, timestamp, value)'
            ' VALUES (uuid_to_bin(%s, 1), %s, 0)', (sid, start))
    cursor.callproc('find_cdf_forecast_gaps',
                    (auth0id, cdf_fxid, start, end))
    assert len(cursor.fetchall()) == 0


def test_find_cdf_forecast_gaps_no_read_cdf_fx(
        cursor, cdf_grp_fx_values, insertuser, 
        allow_read_cdf_forecast_values):
    auth0id, cdf_fxid, vals, start, end = cdf_grp_fx_values
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('find_cdf_forecast_gaps',
                        (auth0id, cdf_fxid, start, end))
    assert e.value.args[0] == 1142


def test_find_cdf_forecast_gaps_no_read_cdf_fx_vals(
        cursor, cdf_grp_fx_values, insertuser,
        allow_read_cdf_forecasts):
    auth0id, cdf_fxid, vals, start, end = cdf_grp_fx_values
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('find_cdf_forecast_gaps',
                        (auth0id, cdf_fxid, start, end))
    assert e.value.args[0] == 1142


def test_find_cdf_forecast_gaps_is_obs(
        cursor, cdf_grp_fx_values, insertuser, allow_read_cdf_forecast_values,
        allow_read_cdf_forecasts):
    auth0id, cdf_fxid, vals, start, end = cdf_grp_fx_values
    obsid = insertuser.obs['strid']
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('find_cdf_forecast_gaps',
                        (auth0id, obsid, start, end))
    assert e.value.args[0] == 1142


all_object_types = ['forecasts', 'observations', 'cdf_forecasts',
                    'aggregates', 'reports', 'users', 'permissions', 'roles']


def object_combinations():
    combos = []
    for i in range(1, 9):
        combos = combos + list(itertools.combinations(all_object_types, i))
    return combos


@pytest.mark.parametrize('object_types', object_combinations())
def test_get_user_creatable_types(
        cursor, insertuser, add_perm, object_types):
    cursor.execute('DELETE FROM permissions WHERE action = "create"')
    for object_type in object_types:
        add_perm('create', object_type)
    auth0id = insertuser[0]['auth0_id']
    cursor.callproc('get_user_creatable_types', (auth0id,))
    create_perms = cursor.fetchall()
    assert tuple([tup[0] for tup in create_perms]) == object_types


@pytest.fixture(params=['forecasts', 'observations', 'cdf_forecasts',
                        'aggregates', 'reports', 'users', 'permissions',
                        'roles', 'users'])
def perm_object_type(request):
    return request.param


@pytest.fixture(params=action_combinations()[::10])
def generate_object_and_perms(
        request, cursor, getfcn, user_org_role, new_permission):
    new_func, object_type = getfcn
    _, _, role = user_org_role

    cursor.execute('DELETE FROM permissions')

    new_obj = new_func()
    all_actions = list(request.param)
    object_id = bin_to_uuid(new_obj['id'])
    for action in request.param:
        new_perm = new_permission(action, object_type, False)
        cursor.execute(
            'INSERT INTO permission_object_mapping (permission_id, object_id) '
            'VALUES (%s, %s)', (new_perm['id'], new_obj['id']))
        cursor.execute(
            'INSERT INTO role_permission_mapping (role_id, permission_id) '
            'VALUES (%s, %s)', (role['id'], new_perm['id']))
    return object_type, object_id, all_actions


def test_list_actions_on_all_objects_of_type(
        dictcursor, user_org_role, generate_object_and_perms):
    auth0id = user_org_role[0]['auth0_id']

    object_type, object_id, actions = generate_object_and_perms
    dictcursor.callproc('list_actions_on_all_objects_of_type',
                        (auth0id, object_type))
    result = dictcursor.fetchall()

    the_object = result[0]
    assert the_object['id'] == object_id
    assert json.loads(the_object['actions']).sort() == (actions).sort()


@pytest.fixture
def make_lots_of_one_thing(cursor, getfcn, user_org_role, new_permission):
    _, org, role = user_org_role

    action_sets = action_combinations()[::7][5:]
    new_func, object_type = getfcn
    the_objects = {}

    for i in range(0, 7):
        new_obj = new_func()
        actions_on_new_obj = list(action_sets[i])
        for action in actions_on_new_obj:
            new_perm = new_permission(action, object_type, False, org)
            cursor.execute(
                'INSERT INTO permission_object_mapping (permission_id, '
                'object_id) VALUES (%s, %s)', (new_perm['id'], new_obj['id']))
            cursor.execute(
                'INSERT INTO role_permission_mapping (role_id, permission_id) '
                'VALUES (%s, %s)', (role['id'], new_perm['id']))
        the_objects[bin_to_uuid(new_obj['id'])] = actions_on_new_obj.sort()
    return the_objects, object_type


def test_list_actions_on_all_objects_of_type_multiple_objects(
        dictcursor, user_org_role, make_lots_of_one_thing):
    auth0id = user_org_role[0]['auth0_id']

    objects, object_type = make_lots_of_one_thing
    dictcursor.callproc('list_actions_on_all_objects_of_type',
                        (auth0id, object_type))
    result = dictcursor.fetchall()
    id_action_dict = {res['id']: json.loads(res['actions']).sort()
                      for res in result}
    for k, v in objects.items():
        assert id_action_dict[k] == v
