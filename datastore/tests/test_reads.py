from collections import namedtuple
import datetime as dt
import json
import random


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
    report = valueset[8][0]
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
        start = dt.datetime(2019, 1, 30, 12, 28, 20)
        vals = tuple([
            (obsid, start + dt.timedelta(minutes=i),
             float(random.randint(0, 100)), 0) for i in range(10)])
        cursor.executemany(
            'INSERT INTO observations_values (id, timestamp, value, '
            'quality_flag) VALUES (UUID_TO_BIN(%s, 1), %s, %s, %s)',
            vals)
        start = dt.datetime(2019, 1, 30, 12, 20)
        end = dt.datetime(2019, 1, 30, 12, 40)
        return auth0id, obsid, vals, start, end
    return insert


def test_read_observation_values(cursor, obs_values, insertuser,
                                 allow_read_observation_values):
    auth0id, obsid, vals, start, end = obs_values(insertuser[3]['strid'])
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
    assert res['metrics'] == '{}'
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
        "UPDATE aggregate_observation_mapping SET effective_until = TIMESTAMP('2019-01-30 12:30')"  # NOQA
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
        " (%s, %s, 1, TIMESTAMP('2019-01-30 12:35'))",
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
        "UPDATE aggregate_observation_mapping SET effective_until = TIMESTAMP('2019-01-30 12:30')"  # NOQA
    )
    cursor.execute(
        "INSERT INTO aggregate_observation_mapping "
        "(aggregate_id, observation_id, _incr, effective_from) VALUES"
        " (%s, %s, 1, TIMESTAMP('2019-01-30 11:00'))",
        (agg['id'], obs['id'])
    )
    cursor.callproc(
        'read_aggregate_values', (
            auth0id, str(bin_to_uuid(agg['id'])),
            start, end)
    )
    res = cursor.fetchall()
    assert res == vals


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
        "UPDATE aggregate_observation_mapping SET effective_from = TIMESTAMP('2019-01-30 12:29'), effective_until = TIMESTAMP('2019-01-30 12:30')"  # NOQA
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
    assert res == vals


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
        "UPDATE aggregate_observation_mapping SET observation_deleted_at = TIMESTAMP('2019-01-30 12:30')"  # NOQA
    )
    obs1 = new_observation(org=org)
    _, _, v2, *_ = obs_values(str(bin_to_uuid(obs1['id'])))
    cursor.execute(
        "INSERT INTO aggregate_observation_mapping "
        "(aggregate_id, observation_id, _incr, created_at) VALUES"
        " (%s, %s, 1, TIMESTAMP('2019-01-30 12:20'))",
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


def test_read_metadata_for_value_write_fx_no_vals(
        dictcursor, insertuser, allow_write_values):
    dictcursor.callproc('read_metadata_for_value_write',
                        (insertuser.auth0id,
                         insertuser.fx['strid'], 'forecasts',
                         '2019-09-30 13:00'))
    res = dictcursor.fetchone()
    assert isinstance(res['interval_length'], int)
    assert res['previous_time'] is None


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


def test_read_metadata_for_value_write_obs_no_vals(
        dictcursor, insertuser, allow_write_values):
    dictcursor.callproc('read_metadata_for_value_write',
                        (insertuser.auth0id,
                         insertuser.obs['strid'], 'observations',
                         '2019-09-30 13:00'))
    res = dictcursor.fetchone()
    assert isinstance(res['interval_length'], int)
    assert res['previous_time'] is None


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
