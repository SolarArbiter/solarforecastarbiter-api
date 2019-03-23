from collections import OrderedDict
import datetime as dt
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
    for thing in (user, site, fx, obs):
        thing['strid'] = str(bin_to_uuid(thing['id']))
    cursor.execute(
        'DELETE FROM permissions WHERE action = "create" and '
        'object_type = "forecasts"')
    return user, site, fx, obs, org, role


@pytest.fixture()
def allow_read_sites(cursor, new_permission, insertuser):
    user, site, fx, obs, org, role = insertuser
    perm = new_permission('read', 'sites', True, org=org)
    cursor.execute(
        'INSERT INTO role_permission_mapping (role_id, permission_id) VALUES '
        '(%s, %s)', (role['id'], perm['id']))


@pytest.fixture()
def allow_create(insertuser, new_permission, cursor):
    user, site, fx, obs, org, role = insertuser
    perms = [new_permission('create', obj, True, org=org)
             for obj in ('sites', 'forecasts', 'observations')]
    cursor.executemany(
        'INSERT INTO role_permission_mapping (role_id, permission_id) '
        'VALUES (%s, %s)',
        [(role['id'], perm['id']) for perm in perms])


@pytest.fixture()
def obs_callargs(insertuser):
    auth0id = insertuser[0]['auth0_id']
    site_id = insertuser[1]['strid']
    callargs = OrderedDict(
        auth0id=auth0id, strid=str(uuid.uuid1()), variable='power',
        site_id=site_id, name='The site', interval_label='beginning',
        interval_length=5, value_type='interval_mean', uncertainty=0.1,
        extra_parameters='')
    return callargs


@pytest.fixture()
def fx_callargs(insertuser):
    auth0id = insertuser[0]['auth0_id']
    site_id = insertuser[1]['strid']
    callargs = OrderedDict(
        auth0id=auth0id, strid=str(uuid.uuid1()), site_id=site_id,
        name='The site', variable='power',
        issue_time_of_day=dt.time(hour=12),
        lead_time_to_start=60, interval_label='beginning',
        interval_length=5, run_length=60,
        value_type='interval_mean', extra_parameters='')
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


def test_store_observation(dictcursor, obs_callargs, allow_read_sites,
                           allow_create):
    dictcursor.callproc('store_observation', list(obs_callargs.values()))
    dictcursor.execute(
        'SELECT * FROM arbiter_data.observations WHERE id = UUID_TO_BIN(%s, 1)',  # NOQA
        (obs_callargs['strid'],))
    res = dictcursor.fetchall()[0]
    for key in ('variable', 'name', 'interval_label', 'interval_length',
                'value_type', 'uncertainty', 'extra_parameters'):
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
                'value_type', 'issue_time_of_day', 'run_length',
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
