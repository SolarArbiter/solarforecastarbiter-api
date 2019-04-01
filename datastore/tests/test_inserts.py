from collections import OrderedDict
import datetime as dt
import random
import uuid


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
    for thing in (user, site, fx, obs):
        thing['strid'] = str(bin_to_uuid(thing['id']))
    cursor.execute(
        'DELETE FROM permissions WHERE action = "create" and '
        'object_type = "forecasts"')
    return user, site, fx, obs, org, role, cdf


@pytest.fixture()
def allow_read_sites(cursor, new_permission, insertuser):
    user, site, fx, obs, org, role, cdf = insertuser
    perm = new_permission('read', 'sites', True, org=org)
    cursor.execute(
        'INSERT INTO role_permission_mapping (role_id, permission_id) VALUES '
        '(%s, %s)', (role['id'], perm['id']))


@pytest.fixture()
def allow_create(insertuser, new_permission, cursor):
    user, site, fx, obs, org, role, cdf = insertuser
    perms = [new_permission('create', obj, True, org=org)
             for obj in ('sites', 'forecasts', 'observations',
                         'cdf_forecasts')]
    cursor.executemany(
        'INSERT INTO role_permission_mapping (role_id, permission_id) '
        'VALUES (%s, %s)',
        [(role['id'], perm['id']) for perm in perms])


@pytest.fixture()
def allow_write_values(insertuser, new_permission, cursor):
    user, site, fx, obs, org, role, cdf = insertuser
    perms = [new_permission('write_values', obj, True, org=org)
             for obj in ('forecasts', 'observations', 'cdf_forecasts')]
    cursor.executemany(
        'INSERT INTO role_permission_mapping (role_id, permission_id) '
        'VALUES (%s, %s)',
        [(role['id'], perm['id']) for perm in perms])


@pytest.fixture()
def allow_delete_values(insertuser, new_permission, cursor):
    user, site, fx, obs, org, role, cdf = insertuser
    perms = [new_permission('delete_values', obj, True, org=org)
             for obj in ('forecasts', 'observations', 'cdf_forecasts')]
    cursor.executemany(
        'INSERT INTO role_permission_mapping (role_id, permission_id) '
        'VALUES (%s, %s)',
        [(role['id'], perm['id']) for perm in perms])


@pytest.fixture()
def allow_update_cdf(cursor, new_permission, insertuser):
    user, site, fx, obs, org, role, cdf = insertuser
    perm = new_permission('update', 'cdf_forecasts', True, org=org)
    cursor.execute(
        'INSERT INTO role_permission_mapping (role_id, permission_id) VALUES '
        '(%s, %s)', (role['id'], perm['id']))


@pytest.fixture()
def obs_callargs(insertuser):
    auth0id = insertuser[0]['auth0_id']
    site_id = insertuser[1]['strid']
    callargs = OrderedDict(
        auth0id=auth0id, strid=str(uuid.uuid1()), variable='power',
        site_id=site_id, name='The site', interval_label='beginning',
        interval_length=5, interval_value_type='interval_mean',
        uncertainty=0.1,
        extra_parameters='')
    return callargs


@pytest.fixture()
def fx_callargs(insertuser):
    auth0id = insertuser[0]['auth0_id']
    site_id = insertuser[1]['strid']
    callargs = OrderedDict(
        auth0id=auth0id, strid=str(uuid.uuid1()), site_id=site_id,
        name='The site', variable='power',
        issue_time_of_day='12:00',
        lead_time_to_start=60, interval_label='beginning',
        interval_length=5, run_length=60,
        interval_value_type='interval_mean', extra_parameters='')
    return callargs


@pytest.fixture()
def site_callargs(insertuser, new_site):
    auth0id = insertuser[0]['auth0_id']
    siteargs = new_site()
    del siteargs['id']
    del siteargs['organization_id']
    callargs = OrderedDict(auth0id=auth0id, strid=str(uuid.uuid1()))
    callargs.update(siteargs)
    return callargs


@pytest.fixture()
def cdf_fx_callargs(fx_callargs):
    cdfargs = fx_callargs.copy()
    cdfargs['axis'] = 'x'
    return cdfargs


@pytest.fixture()
def cdf_single_callargs(cdf_fx_callargs):
    group_id = cdf_fx_callargs['strid']
    callargs = OrderedDict(
        auth0id=cdf_fx_callargs['auth0id'], strid=str(uuid.uuid1()),
        parent_id=group_id, constant_value=3.0)
    return callargs


def test_store_observation(dictcursor, obs_callargs, allow_read_sites,
                           allow_create):
    dictcursor.callproc('store_observation', list(obs_callargs.values()))
    dictcursor.execute(
        'SELECT * FROM arbiter_data.observations WHERE id = UUID_TO_BIN(%s, 1)',  # NOQA
        (obs_callargs['strid'],))
    res = dictcursor.fetchall()[0]
    for key in ('variable', 'name', 'interval_label', 'interval_length',
                'interval_value_type', 'uncertainty', 'extra_parameters'):
        assert res[key] == obs_callargs[key]


def test_store_observation_denied_cant_create(dictcursor, obs_callargs,
                                              allow_read_sites):
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc('store_observation', list(obs_callargs.values()))
        assert e.errcode == 1142


def test_store_observation_denied_cant_read_sites(dictcursor, obs_callargs,
                                                  allow_create):
    """Don't allow a user to create an observation if they can not also read the
    site metadata"""
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc('store_observation', list(obs_callargs.values()))
        assert e.errcode == 1143


def test_store_forecast(dictcursor, fx_callargs, allow_read_sites,
                        allow_create):
    dictcursor.callproc('store_forecast', list(fx_callargs.values()))
    dictcursor.execute(
        'SELECT * FROM arbiter_data.forecasts WHERE id = UUID_TO_BIN(%s, 1)',
        (fx_callargs['strid'],))
    res = dictcursor.fetchall()[0]
    for key in ('variable', 'name', 'interval_label', 'interval_length',
                'interval_value_type', 'issue_time_of_day', 'run_length',
                'lead_time_to_start', 'extra_parameters'):
        assert res[key] == fx_callargs[key]


def test_store_forecast_denied_cant_create(dictcursor, fx_callargs,
                                           allow_read_sites):
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc('store_forecast', list(fx_callargs.values()))
        assert e.errcode == 1142


def test_store_forecast_denied_cant_read_sites(dictcursor, fx_callargs,
                                               allow_create):
    """Don't allow a user to create an forecast if they can not also read the
    site metadata"""
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc('store_forecast', list(fx_callargs.values()))
        assert e.errcode == 1143


def test_store_site(dictcursor, site_callargs, allow_create):
    dictcursor.callproc('store_site', list(site_callargs.values()))
    dictcursor.execute(
        'SELECT * FROM arbiter_data.sites WHERE id = UUID_TO_BIN(%s, 1)',
        (site_callargs['strid'],))
    keys = list(site_callargs.keys())[2:]
    res = dictcursor.fetchall()[0]
    for key in keys:
        assert res[key] == site_callargs[key]


def test_store_site_denied_cant_create(dictcursor, site_callargs):
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc('store_site', list(site_callargs.values()))
        assert e.errcode == 1142


@pytest.fixture()
def observation_values(insertuser):
    def make(auth0id, obsid):
        now = dt.datetime.utcnow().replace(microsecond=0)
        for i in range(100):
            now += dt.timedelta(minutes=5)
            yield auth0id, obsid, now, float(random.randint(0, 100)), 0

    auth0id = insertuser[0]['auth0_id']
    obsid = insertuser[3]['strid']
    obsbinid = insertuser[3]['id']
    testobs = make(auth0id, obsid)
    return obsbinid, testobs


def test_store_observation_values(cursor, allow_write_values,
                                  observation_values):
    obsbinid, testobs = observation_values
    expected = []
    for to in testobs:
        expected.append((obsbinid, *to[-3:]))
        cursor.callproc('store_observation_values', to)
    cursor.execute(
        'SELECT * FROM arbiter_data.observations_values WHERE id = %s AND'
        ' timestamp > CURRENT_TIMESTAMP()',
        obsbinid)
    res = cursor.fetchall()
    assert res == tuple(expected)


def test_store_observation_values_cant_write(cursor, observation_values):
    obsbinid, testobs = observation_values
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('store_observation_values', list(testobs)[0])
        assert e.errcode == 1142


def test_store_observation_values_cant_write_cant_delete(
        cursor, observation_values, allow_delete_values):
    obsbinid, testobs = observation_values
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('store_observation_values', list(testobs)[0])
        assert e.errcode == 1142


@pytest.fixture()
def forecast_values(insertuser):
    def make(auth0id, fxid):
        now = dt.datetime.utcnow().replace(microsecond=0)
        for i in range(100):
            now += dt.timedelta(minutes=5)
            yield auth0id, fxid, now, float(random.randint(0, 100))

    auth0id = insertuser[0]['auth0_id']
    fxid = insertuser[2]['strid']
    fxbinid = insertuser[2]['id']
    testfx = make(auth0id, fxid)
    return fxbinid, testfx


def test_store_forecast_values(cursor, allow_write_values,
                               forecast_values):
    fxbinid, testfx = forecast_values
    expected = []
    for tf in testfx:
        expected.append((fxbinid, *tf[2:]))
        cursor.callproc('store_forecast_values', tf)
    cursor.execute(
        'SELECT * FROM arbiter_data.forecasts_values WHERE id = %s AND'
        ' timestamp > CURRENT_TIMESTAMP()',
        fxbinid)
    res = cursor.fetchall()
    assert res == tuple(expected)


def test_store_forecast_values_cant_write(cursor, forecast_values):
    fxbinid, testfx = forecast_values
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('store_forecast_values', list(testfx)[0])
        assert e.errcode == 1142


def test_store_forecast_values_cant_write_cant_delete(
        cursor, forecast_values, allow_delete_values):
    fxbinid, testfx = forecast_values
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('store_forecast_values', list(testfx)[0])
        assert e.errcode == 1142


def test_store_cdf_forecast(dictcursor, cdf_fx_callargs, allow_read_sites,
                            allow_create):
    dictcursor.callproc('store_cdf_forecasts_group',
                        list(cdf_fx_callargs.values()))
    dictcursor.execute(
        'SELECT * FROM arbiter_data.cdf_forecasts_groups WHERE '
        'id = UUID_TO_BIN(%s, 1)',
        (cdf_fx_callargs['strid'],))
    res = dictcursor.fetchall()[0]
    for key in ('variable', 'name', 'interval_label', 'interval_length',
                'interval_value_type', 'issue_time_of_day', 'run_length',
                'lead_time_to_start', 'extra_parameters', 'axis'):
        assert res[key] == cdf_fx_callargs[key]


def test_store_cdf_forecast_denied_cant_create(dictcursor, cdf_fx_callargs,
                                               allow_read_sites):
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc('store_cdf_forecasts_group',
                            list(cdf_fx_callargs.values()))
        assert e.errcode == 1142


def test_store_cdf_forecast_denied_cant_read_sites(dictcursor, cdf_fx_callargs,
                                                   allow_create):
    """Don't allow a user to create an forecast if they can not also read the
    site metadata"""
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc('store_cdf_forecasts_group',
                            list(cdf_fx_callargs.values()))
        assert e.errcode == 1143


def test_store_cdf_forecast_single(dictcursor, cdf_single_callargs,
                                   cdf_fx_callargs, allow_read_sites,
                                   allow_create, allow_update_cdf):
    # must first create parent...
    dictcursor.callproc('store_cdf_forecasts_group',
                        list(cdf_fx_callargs.values()))

    dictcursor.callproc('store_cdf_forecasts_single',
                        list(cdf_single_callargs.values()))
    dictcursor.execute(
        'SELECT constant_value, BIN_TO_UUID(cdf_forecast_group_id, 1) '
        'as parent_id FROM arbiter_data.cdf_forecasts_singles WHERE '
        'id = UUID_TO_BIN(%s, 1)',
        (cdf_single_callargs['strid'],))
    res = dictcursor.fetchall()[0]
    for key in ('constant_value', 'parent_id'):
        assert res[key] == cdf_single_callargs[key]


def test_store_cdf_forecast_single_denied_cant_create(
        dictcursor, cdf_single_callargs, allow_read_sites, allow_update_cdf):
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc('store_cdf_forecasts_single',
                            list(cdf_single_callargs.values()))
        assert e.errcode == 1142


def test_store_cdf_forecast_single_denied_cant_read_sites(
        dictcursor, cdf_single_callargs, allow_create, allow_update_cdf):
    """Don't allow a user to create an forecast if they can not also read the
    site metadata"""
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc('store_cdf_forecasts_single',
                            list(cdf_single_callargs.values()))
        assert e.errcode == 1143


def test_store_cdf_forecast_single_denied_cant_update_group(
        dictcursor, cdf_single_callargs, allow_create, allow_read_sites):
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc('store_cdf_forecasts_single',
                            list(cdf_single_callargs.values()))
        assert e.errcode == 1143


@pytest.fixture(params=[0, 1, 2])
def cdf_forecast_values(insertuser, request):
    def make(auth0id, fxid):
        now = dt.datetime.utcnow().replace(microsecond=0)
        for i in range(100):
            now += dt.timedelta(minutes=5)
            yield auth0id, fxid, now, float(random.randint(0, 100))

    auth0id = insertuser[0]['auth0_id']
    fxid = list(insertuser[6]['constant_values'].keys())[request.param]
    testfx = make(auth0id, fxid)
    return fxid, testfx


def test_store_cdf_forecast_values(
        cursor, allow_write_values, cdf_forecast_values):
    fxid, testfx = cdf_forecast_values
    expected = []
    for tf in testfx:
        expected.append((fxid, *tf[2:]))
        cursor.callproc('store_cdf_forecast_values', tf)
    cursor.execute(
        'SELECT BIN_TO_UUID(id, 1) as id, timestamp, value '
        'FROM arbiter_data.cdf_forecasts_values WHERE id = UUID_TO_BIN(%s, 1)'
        ' AND timestamp > CURRENT_TIMESTAMP()',
        fxid)
    res = cursor.fetchall()
    assert res == tuple(expected)


def test_store_cdf_forecast_values_cant_write(cursor, cdf_forecast_values):
    fxid, testfx = cdf_forecast_values
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('store_cdf_forecast_values', list(testfx)[0])
        assert e.errcode == 1142
