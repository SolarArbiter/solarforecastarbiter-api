from collections import OrderedDict
import datetime as dt
import json
import random
import uuid


import pytest
import pymysql


from conftest import bin_to_uuid, uuid_to_bin, newuuid


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
    agg = valueset[9][0]
    for thing in (user, site, fx, obs, agg):
        thing['strid'] = str(bin_to_uuid(thing['id']))
    cursor.execute(
        'DELETE FROM permissions WHERE action = "create" and '
        'object_type = "forecasts"')
    return user, site, fx, obs, org, role, cdf, report, agg


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
def allow_read_reports(add_perm):
    add_perm('read', 'reports')


@pytest.fixture()
def allow_read_aggregate(add_perm):
    add_perm('read', 'aggregates')


@pytest.fixture()
def allow_create(add_perm):
    [add_perm('create', obj)
     for obj in ('sites', 'forecasts', 'observations',
                 'cdf_forecasts', 'roles', 'permissions',
                 'reports', 'aggregates')]


@pytest.fixture()
def allow_write_values(add_perm):
    [add_perm('write_values', obj)
     for obj in ('forecasts', 'observations',
                 'cdf_forecasts', 'reports')]


@pytest.fixture()
def allow_delete_values(add_perm):
    [add_perm('delete_values', obj)
     for obj in ('forecasts', 'observations', 'cdf_forecasts')]


@pytest.fixture()
def allow_read_observations(add_perm):
    add_perm('read', 'observations')


@pytest.fixture()
def allow_read_observation_values(add_perm):
    add_perm('read_values', 'observations')


@pytest.fixture()
def allow_update_cdf(add_perm):
    add_perm('update', 'cdf_forecasts')


@pytest.fixture()
def allow_update_permissions(add_perm):
    add_perm('update', 'permissions')


@pytest.fixture()
def allow_update_roles(add_perm):
    add_perm('update', 'roles')


@pytest.fixture()
def allow_update_users(add_perm):
    add_perm('update', 'users')


@pytest.fixture()
def allow_update_reports(add_perm):
    add_perm('update', 'reports')


@pytest.fixture()
def allow_update_aggregates(add_perm):
    add_perm('update', 'aggregates')


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


@pytest.fixture(params=[1, 0])
def fx_callargs(insertuser, request):
    auth0id = insertuser[0]['auth0_id']
    site_id = insertuser[1]['strid']
    agg_id = insertuser[8]['strid']
    if request.param:
        sa_id = site_id
        ref_site = True
    else:
        sa_id = agg_id
        ref_site = False
    callargs = OrderedDict(
        auth0id=auth0id, strid=str(uuid.uuid1()), site_or_agg_id=sa_id,
        name='The site', variable='power',
        issue_time_of_day='12:00',
        lead_time_to_start=60, interval_label='beginning',
        interval_length=5, run_length=60,
        interval_value_type='interval_mean', extra_parameters='',
        references_site=ref_site)
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
def agg_callargs(insertuser, new_aggregate, valueset):
    auth0id = insertuser[0]['auth0_id']
    obs = valueset[6]
    aggargs = new_aggregate(obs_list=obs)
    del aggargs['id']
    del aggargs['organization_id']
    del aggargs['obs_list']
    del aggargs['interval_value_type']
    callargs = OrderedDict(auth0id=auth0id, strid=str(uuid.uuid1()))
    callargs.update(aggargs)
    return callargs


@pytest.fixture()
def cdf_fx_callargs(fx_callargs):
    cdfargs = fx_callargs.copy()
    rf = cdfargs.pop('references_site')
    cdfargs['axis'] = 'x'
    cdfargs['references_site'] = rf
    return cdfargs


@pytest.fixture()
def cdf_single_callargs(cdf_fx_callargs):
    group_id = cdf_fx_callargs['strid']
    callargs = OrderedDict(
        auth0id=cdf_fx_callargs['auth0id'], strid=str(uuid.uuid1()),
        parent_id=group_id, constant_value=3.0)
    return callargs


@pytest.fixture()
def report_callargs(insertuser, new_report):
    auth0id = insertuser[0]['auth0_id']
    report_args = new_report()
    del report_args['id']
    del report_args['organization_id']
    callargs = OrderedDict(auth0id=auth0id, strid=str(uuid.uuid1()))
    callargs.update(report_args)
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
    assert e.value.args[0] == 1142


def test_store_observation_denied_cant_read_sites(dictcursor, obs_callargs,
                                                  allow_create):
    """Don't allow a user to create an observation if they can not also read the
    site metadata"""
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc('store_observation', list(obs_callargs.values()))
    assert e.value.args[0] == 1143


def test_store_forecast(dictcursor, fx_callargs, allow_read_sites,
                        allow_read_aggregate, allow_create):
    dictcursor.callproc('store_forecast', list(fx_callargs.values()))
    dictcursor.execute(
        'SELECT * FROM arbiter_data.forecasts WHERE id = UUID_TO_BIN(%s, 1)',
        (fx_callargs['strid'],))
    res = dictcursor.fetchall()[0]
    if fx_callargs['references_site']:
        assert bin_to_uuid(res['site_id']) == fx_callargs['site_or_agg_id']
        assert res['aggregate_id'] is None
    else:
        assert bin_to_uuid(res['aggregate_id']) == fx_callargs['site_or_agg_id']
        assert res['site_id'] is None
    for key in ('variable', 'name', 'interval_label', 'interval_length',
                'interval_value_type', 'issue_time_of_day', 'run_length',
                'lead_time_to_start', 'extra_parameters'):
        assert res[key] == fx_callargs[key]


def test_store_forecast_denied_cant_create(
        dictcursor, fx_callargs, allow_read_aggregate, allow_read_sites):
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc('store_forecast', list(fx_callargs.values()))
    assert e.value.args[0] == 1142


def test_store_forecast_denied_cant_read_sites(dictcursor, fx_callargs,
                                               allow_create):
    """Don't allow a user to create an forecast if they can not also read the
    site metadata"""
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc('store_forecast', list(fx_callargs.values()))
    assert e.value.args[0] == 1143


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
    assert e.value.args[0] == 1142


@pytest.fixture()
def observation_values(insertuser):
    auth0id = insertuser[0]['auth0_id']
    obsid = insertuser[3]['strid']
    obsbinid = insertuser[3]['id']
    expected = []
    now = dt.datetime.utcnow().replace(microsecond=0)
    for i in range(100):
        now += dt.timedelta(minutes=5)
        expected.append(
            (obsbinid, now, float(random.randint(0, 100)),
             random.randint(0, 100)))
    testobs = json.dumps(
        [{'ts': r[1].strftime('%Y-%m-%dT%H:%M:%S'),
          'v': r[2], 'qf': r[3]}
         for r in expected])
    return auth0id, obsid, obsbinid, testobs, expected


def test_store_observation_values(cursor, allow_write_values,
                                  observation_values):
    auth0id, obsid, obsbinid, testobs, expected = observation_values
    cursor.callproc('store_observation_values', (auth0id, obsid, testobs))
    cursor.execute(
        'SELECT * FROM arbiter_data.observations_values WHERE id = %s AND'
        ' timestamp > CURRENT_TIMESTAMP()',
        obsbinid)
    res = cursor.fetchall()
    assert res == tuple(expected)


def test_store_observation_values_null(cursor, allow_write_values,
                                       observation_values):
    auth0id, obsid, obsbinid, testobs, expected = observation_values
    good = '[{"ts": "2020-01-01T00:00:00", "qf": 0}]'
    cursor.callproc('store_observation_values', (auth0id, obsid, good))
    cursor.execute(
        'SELECT value, quality_flag FROM arbiter_data.observations_values '
        'WHERE id = %s AND timestamp = TIMESTAMP("2020-01-01T00:00:00")',
        obsbinid)
    res = cursor.fetchone()
    assert res == (None, 0)
    bad = '[{"ts": "2020-01-01T00:00:00", "qf": 0, "v": null}]'
    with pytest.raises(pymysql.err.InternalError):
        cursor.callproc('store_observation_values', (auth0id, obsid, bad))
    with pytest.raises(pymysql.err.InternalError):
        cursor.callproc('store_observation_values', (
            auth0id, obsid, '[{"ts": "2020-01-01T00:00:00"}]'))
    with pytest.raises(pymysql.err.InternalError):
        cursor.callproc('store_observation_values', (
            auth0id, obsid, '[{"qf": 0}]'))


def test_store_observation_values_duplicates(cursor, allow_write_values,
                                             observation_values):
    auth0id, obsid, obsbinid, testobs, expected = observation_values
    # first insert
    cursor.callproc('store_observation_values', (auth0id, obsid, testobs))
    cursor.execute(
        'SELECT * FROM arbiter_data.observations_values WHERE id = %s AND'
        ' timestamp > CURRENT_TIMESTAMP()',
        obsbinid)
    res = cursor.fetchall()
    assert res == tuple(expected)
    # second insert
    alt = []
    for r in expected:
        alt.append((r[0], r[1], r[2] + 0.9, r[3] + 1))
    nextobs = json.dumps(
        [{'ts': r[1].strftime('%Y-%m-%dT%H:%M:%S'),
          'v': r[2], 'qf': r[3]}
         for r in alt])
    cursor.callproc('store_observation_values', (auth0id, obsid, nextobs))
    cursor.execute(
        'SELECT * FROM arbiter_data.observations_values WHERE id = %s AND'
        ' timestamp > CURRENT_TIMESTAMP()',
        obsbinid)
    res = cursor.fetchall()
    assert res == tuple(alt)


def test_store_observation_values_cant_write(cursor, observation_values):
    auth0id, obsid, obsbinid, testobs, expected = observation_values
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('store_observation_values', (auth0id, obsid, testobs))
    assert e.value.args[0] == 1142


def test_store_observation_values_cant_write_cant_delete(
        cursor, observation_values, allow_delete_values):
    auth0id, obsid, obsbinid, testobs, expected = observation_values
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('store_observation_values', (auth0id, obsid, testobs))
    assert e.value.args[0] == 1142


@pytest.fixture()
def forecast_values(insertuser):
    auth0id = insertuser[0]['auth0_id']
    fxid = insertuser[2]['strid']
    fxbinid = insertuser[2]['id']
    expected = []
    now = dt.datetime.utcnow().replace(microsecond=0)
    for i in range(100):
        now += dt.timedelta(minutes=5)
        expected.append(
            (fxbinid, now, float(random.randint(0, 100))))
    testfx = json.dumps(
        [{'ts': r[1].strftime('%Y-%m-%dT%H:%M:%S'),
          'v': r[2]} for r in expected])
    return auth0id, fxid, fxbinid, testfx, expected


def test_store_forecast_values(cursor, allow_write_values,
                               forecast_values):
    auth0id, fxid, fxbinid, testfx, expected = forecast_values
    cursor.callproc('store_forecast_values', (auth0id, fxid, testfx))
    cursor.execute(
        'SELECT * FROM arbiter_data.forecasts_values WHERE id = %s AND'
        ' timestamp > CURRENT_TIMESTAMP()',
        fxbinid)
    res = cursor.fetchall()
    assert res == tuple(expected)


def test_store_forecast_values_null(cursor, allow_write_values,
                                    forecast_values):
    auth0id, fxid, fxbinid, testfx, expected = forecast_values
    good = '[{"ts": "2020-01-01T00:00:00"}]'
    cursor.callproc('store_forecast_values', (auth0id, fxid, good))
    cursor.execute(
        'SELECT value FROM arbiter_data.forecasts_values '
        'WHERE id = %s AND timestamp = TIMESTAMP("2020-01-01T00:00:00")',
        fxbinid)
    res = cursor.fetchone()
    assert res == (None,)
    bad = '[{"ts": "2020-01-01T00:00:00", "v": null}]'
    with pytest.raises(pymysql.err.InternalError):
        cursor.callproc('store_forecast_values', (auth0id, fxid, bad))
    with pytest.raises(pymysql.err.InternalError):
        cursor.callproc('store_forecast_values', (
            auth0id, fxid, '[{"v": 1.0}]'))


def test_store_forecast_values_duplicates(cursor, allow_write_values,
                                          forecast_values):
    auth0id, fxid, fxbinid, testfx, expected = forecast_values
    # first insert
    cursor.callproc('store_forecast_values', (auth0id, fxid, testfx))
    cursor.execute(
        'SELECT * FROM arbiter_data.forecasts_values WHERE id = %s AND'
        ' timestamp > CURRENT_TIMESTAMP()',
        fxbinid)
    res = cursor.fetchall()
    assert res == tuple(expected)

    # second insert
    alt = []
    for r in expected:
        alt.append((r[0], r[1], r[2] + 0.9))
    nextfx = json.dumps(
        [{'ts': r[1].strftime('%Y-%m-%dT%H:%M:%S'),
          'v': r[2]} for r in alt])
    cursor.callproc('store_forecast_values', (auth0id, fxid, nextfx))
    cursor.execute(
        'SELECT * FROM arbiter_data.forecasts_values WHERE id = %s AND'
        ' timestamp > CURRENT_TIMESTAMP()',
        fxbinid)
    res = cursor.fetchall()
    assert res == tuple(alt)


def test_store_forecast_values_cant_write(cursor, forecast_values):
    auth0id, fxid, fxbinid, testfx, expected = forecast_values
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('store_forecast_values', (auth0id, fxid, testfx))
    assert e.value.args[0] == 1142


def test_store_forecast_values_cant_write_cant_delete(
        cursor, forecast_values, allow_delete_values):
    auth0id, fxid, fxbinid, testfx, expected = forecast_values
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('store_forecast_values', (auth0id, fxid, testfx))
    assert e.value.args[0] == 1142


def test_store_cdf_forecast(dictcursor, cdf_fx_callargs, allow_read_sites,
                            allow_read_aggregate, allow_create,
                            default_user_role):
    dictcursor.execute(
        "SELECT can_user_perform_action(%s, UUID_TO_BIN(%s, 1), 'update') as can",  # NOQA
        (default_user_role['auth0_id'], cdf_fx_callargs['strid'])
    )
    assert not dictcursor.fetchone()['can']
    dictcursor.callproc('store_cdf_forecasts_group',
                        list(cdf_fx_callargs.values()))
    dictcursor.execute(
        'SELECT * FROM arbiter_data.cdf_forecasts_groups WHERE '
        'id = UUID_TO_BIN(%s, 1)',
        (cdf_fx_callargs['strid'],))
    res = dictcursor.fetchall()[0]
    if cdf_fx_callargs['references_site']:
        assert bin_to_uuid(res['site_id']) == cdf_fx_callargs['site_or_agg_id']
        assert res['aggregate_id'] is None
    else:
        assert bin_to_uuid(res['aggregate_id']) == cdf_fx_callargs[
            'site_or_agg_id']
        assert res['site_id'] is None
    for key in ('variable', 'name', 'interval_label', 'interval_length',
                'interval_value_type', 'issue_time_of_day', 'run_length',
                'lead_time_to_start', 'extra_parameters', 'axis'):
        assert res[key] == cdf_fx_callargs[key]
    dictcursor.execute(
        "SELECT can_user_perform_action(%s, UUID_TO_BIN(%s, 1), 'update') as can",  # NOQA
        (default_user_role['auth0_id'], cdf_fx_callargs['strid'])
    )
    assert dictcursor.fetchone()['can']


def test_store_cdf_forecast_no_update(
        dictcursor, cdf_fx_callargs, allow_read_sites,
        allow_read_aggregate, allow_create,
        insertuser):
    dictcursor.execute(
        "SELECT can_user_perform_action(%s, UUID_TO_BIN(%s, 1), 'update') as can",  # NOQA
        (insertuser[0]['auth0_id'], cdf_fx_callargs['strid'])
    )
    assert not dictcursor.fetchone()['can']
    dictcursor.callproc('store_cdf_forecasts_group',
                        list(cdf_fx_callargs.values()))
    dictcursor.execute(
        'SELECT * FROM arbiter_data.cdf_forecasts_groups WHERE '
        'id = UUID_TO_BIN(%s, 1)',
        (cdf_fx_callargs['strid'],))
    res = dictcursor.fetchall()[0]
    if cdf_fx_callargs['references_site']:
        assert bin_to_uuid(res['site_id']) == cdf_fx_callargs['site_or_agg_id']
        assert res['aggregate_id'] is None
    else:
        assert bin_to_uuid(res['aggregate_id']) == cdf_fx_callargs[
            'site_or_agg_id']
        assert res['site_id'] is None
    for key in ('variable', 'name', 'interval_label', 'interval_length',
                'interval_value_type', 'issue_time_of_day', 'run_length',
                'lead_time_to_start', 'extra_parameters', 'axis'):
        assert res[key] == cdf_fx_callargs[key]
    dictcursor.execute(
        "SELECT can_user_perform_action(%s, UUID_TO_BIN(%s, 1), 'update') as can",  # NOQA
        (insertuser[0]['auth0_id'], cdf_fx_callargs['strid'])
    )
    assert not dictcursor.fetchone()['can']


def test_store_cdf_forecast_denied_cant_create(
        dictcursor, cdf_fx_callargs, allow_read_aggregate, allow_read_sites):
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc('store_cdf_forecasts_group',
                            list(cdf_fx_callargs.values()))
    assert e.value.args[0] == 1142


def test_store_cdf_forecast_denied_cant_read_sites(dictcursor, cdf_fx_callargs,
                                                   allow_create):
    """Don't allow a user to create an forecast if they can not also read the
    site metadata"""
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc('store_cdf_forecasts_group',
                            list(cdf_fx_callargs.values()))
    assert e.value.args[0] == 1143


def test_store_cdf_forecast_single(dictcursor, cdf_single_callargs,
                                   cdf_fx_callargs, allow_read_sites,
                                   allow_read_aggregate,
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
        dictcursor, cdf_single_callargs, allow_read_sites, allow_update_cdf,
        allow_read_aggregate):
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc('store_cdf_forecasts_single',
                            list(cdf_single_callargs.values()))
    assert e.value.args[0] == 1142


def test_store_cdf_forecast_single_denied_cant_read_sites(
        dictcursor, cdf_single_callargs, allow_create, allow_update_cdf):
    """Don't allow a user to create an forecast if they can not also read the
    site metadata"""
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc('store_cdf_forecasts_single',
                            list(cdf_single_callargs.values()))
    assert e.value.args[0] == 1143


def test_store_cdf_forecast_single_denied_cant_update_group(
        dictcursor, cdf_single_callargs, allow_create, allow_read_sites,
        allow_read_aggregate):
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc('store_cdf_forecasts_single',
                            list(cdf_single_callargs.values()))
    assert e.value.args[0] == 1143


@pytest.fixture(params=[0, 1, 2])
def cdf_forecast_values(insertuser, request):
    auth0id = insertuser[0]['auth0_id']
    fxid = list(insertuser[6]['constant_values'].keys())[request.param]
    fxbinid = uuid_to_bin(uuid.UUID(fxid))
    expected = []
    now = dt.datetime.utcnow().replace(microsecond=0)
    for i in range(100):
        now += dt.timedelta(minutes=5)
        expected.append(
            (fxbinid, now, float(random.randint(0, 100))))
    testfx = json.dumps(
        [{'ts': r[1].strftime('%Y-%m-%dT%H:%M:%S'),
          'v': r[2]} for r in expected])
    return auth0id, fxid, fxbinid, testfx, expected


def test_store_cdf_forecast_values(
        cursor, allow_write_values, cdf_forecast_values):
    auth0id, fxid, fxbinid, testfx, expected = cdf_forecast_values
    cursor.callproc('store_cdf_forecast_values', (auth0id, fxid, testfx))
    cursor.execute(
        'SELECT id, timestamp, value '
        'FROM arbiter_data.cdf_forecasts_values WHERE id = %s'
        ' AND timestamp > CURRENT_TIMESTAMP()',
        fxbinid)
    res = cursor.fetchall()
    assert res == tuple(expected)


def test_store_cdf_forecast_values_null(cursor, allow_write_values,
                                        cdf_forecast_values):
    auth0id, fxid, fxbinid, testfx, expected = cdf_forecast_values
    good = '[{"ts": "2020-01-01T00:00:00"}]'
    cursor.callproc('store_cdf_forecast_values', (auth0id, fxid, good))
    cursor.execute(
        'SELECT value FROM arbiter_data.cdf_forecasts_values '
        'WHERE id = %s AND timestamp = TIMESTAMP("2020-01-01T00:00:00")',
        fxbinid)
    res = cursor.fetchone()
    assert res == (None,)
    bad = '[{"ts": "2020-01-01T00:00:00", "v": null}]'
    with pytest.raises(pymysql.err.InternalError):
        cursor.callproc('store_cdf_forecast_values', (auth0id, fxid, bad))
    with pytest.raises(pymysql.err.InternalError):
        cursor.callproc('store_cdf_forecast_values', (
            auth0id, fxid, '[{"v": 1.0}]'))


def test_store_cdf_forecast_values_duplicates(
        cursor, allow_write_values, cdf_forecast_values):
    auth0id, fxid, fxbinid, testfx, expected = cdf_forecast_values
    cursor.callproc('store_cdf_forecast_values', (auth0id, fxid, testfx))
    cursor.execute(
        'SELECT id, timestamp, value '
        'FROM arbiter_data.cdf_forecasts_values WHERE id = %s'
        ' AND timestamp > CURRENT_TIMESTAMP()',
        fxbinid)
    res = cursor.fetchall()
    assert res == tuple(expected)
    # duplicate
    alt = []
    for r in expected[::-1]:
        alt.append((r[0], r[1], r[2] + 9.9))
    nextfx = json.dumps(
        [{'ts': r[1].strftime('%Y-%m-%dT%H:%M:%S'),
          'v': r[2]} for r in alt])
    cursor.callproc('store_cdf_forecast_values', (auth0id, fxid, nextfx))
    cursor.execute(
        'SELECT id, timestamp, value '
        'FROM arbiter_data.cdf_forecasts_values WHERE id = %s'
        ' AND timestamp > CURRENT_TIMESTAMP()',
        fxbinid)
    res = cursor.fetchall()
    assert res == tuple(alt[::-1])


def test_store_cdf_forecast_values_cant_write(cursor, cdf_forecast_values):
    auth0id, fxid, fxbinid, testfx, expected = cdf_forecast_values
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('store_cdf_forecast_values', (auth0id, fxid, testfx))
    assert e.value.args[0] == 1142


def test_store_aggregate(dictcursor, agg_callargs, allow_create):
    dictcursor.callproc('store_aggregate', list(agg_callargs.values()))
    dictcursor.execute(
        'SELECT * FROM arbiter_data.aggregates WHERE id = UUID_TO_BIN(%s, 1)',
        (agg_callargs['strid'],))
    res = dictcursor.fetchall()[0]
    for key in ('variable', 'name', 'interval_label', 'interval_length',
                'extra_parameters', 'aggregate_type'):
        assert res[key] == agg_callargs[key]
    dictcursor.execute(
        'SELECT COUNT(*) as nu FROM arbiter_data.aggregate_observation_mapping'
        ' WHERE aggregate_id = UUID_TO_BIN(%s, 1)', (agg_callargs['strid'],))
    assert dictcursor.fetchone()['nu'] == 0


def test_store_aggregate_denied(dictcursor, agg_callargs):
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc('store_aggregate', list(agg_callargs.values()))
    assert e.value.args[0] == 1142


def test_add_observation_to_aggregate(dictcursor, insertuser,
                                      new_observation,
                                      allow_update_aggregates,
                                      allow_read_observations):
    auth0id = insertuser[0]['auth0_id']
    agg = insertuser[8]
    obs = new_observation(site=insertuser[1])
    dictcursor.execute(
        'SELECT COUNT(*) as nu FROM arbiter_data.aggregate_observation_mapping'
        ' WHERE aggregate_id = UUID_TO_BIN(%s, 1)', (agg['strid'],))
    before = dictcursor.fetchone()['nu']
    dictcursor.callproc('add_observation_to_aggregate',
                        (auth0id, agg['strid'], str(bin_to_uuid(obs['id'])),
                         '2019-01-01 00:00'))
    dictcursor.execute(
        'SELECT observation_id as oi FROM '
        'arbiter_data.aggregate_observation_mapping'
        ' WHERE aggregate_id = UUID_TO_BIN(%s, 1)',
        (agg['strid'],))
    res = dictcursor.fetchall()
    assert len(res) == before + 1
    assert obs['id'] in [d['oi'] for d in res]


def test_add_observation_to_aggregate_present(
        dictcursor, insertuser, new_observation, allow_update_aggregates,
        allow_read_observations):
    auth0id = insertuser[0]['auth0_id']
    agg = insertuser[8]
    obs = new_observation(site=insertuser[1])
    dictcursor.callproc('add_observation_to_aggregate',
                        (auth0id, agg['strid'], str(bin_to_uuid(obs['id'])),
                         '2019-01-01 00:00'))
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc(
            'add_observation_to_aggregate',
            (auth0id, agg['strid'], str(bin_to_uuid(obs['id'])),
             '2019-01-01'))
    assert e.value.args[0] == 1142


def test_add_observation_to_aggregate_again(
        dictcursor, insertuser, new_observation, allow_update_aggregates,
        allow_read_observations):
    auth0id = insertuser[0]['auth0_id']
    agg = insertuser[8]
    obs = new_observation(site=insertuser[1])
    dictcursor.execute(
        'SELECT COUNT(*) as nu FROM arbiter_data.aggregate_observation_mapping'
        ' WHERE aggregate_id = UUID_TO_BIN(%s, 1)', (agg['strid'],))
    before = dictcursor.fetchone()['nu']
    dictcursor.callproc('add_observation_to_aggregate',
                        (auth0id, agg['strid'], str(bin_to_uuid(obs['id'])),
                         '2019-01-01 00:00'))
    dictcursor.callproc('remove_observation_from_aggregate',
                        (auth0id, agg['strid'], str(bin_to_uuid(obs['id'])),
                         '2019-01-01 00:00'))
    dictcursor.callproc('add_observation_to_aggregate',
                        (auth0id, agg['strid'], str(bin_to_uuid(obs['id'])),
                         '2019-01-01 00:00'))
    dictcursor.callproc('remove_observation_from_aggregate',
                        (auth0id, agg['strid'], str(bin_to_uuid(obs['id'])),
                         '2019-01-01 00:00'))
    dictcursor.callproc('add_observation_to_aggregate',
                        (auth0id, agg['strid'], str(bin_to_uuid(obs['id'])),
                         '2019-01-01 00:00'))
    dictcursor.execute(
        'SELECT observation_id as oi, effective_until, _incr FROM '
        'arbiter_data.aggregate_observation_mapping'
        ' WHERE aggregate_id = UUID_TO_BIN(%s, 1) ORDER BY _incr',
        (agg['strid'],))
    res = dictcursor.fetchall()
    assert len(res) == before + 3
    news = []
    for d in res:
        if d['oi'] == obs['id']:
            news.append(d['effective_until'] is None)
    assert news == [False, False, True]


def test_add_observation_to_aggregate_no_update(dictcursor, insertuser,
                                                new_observation,
                                                allow_read_observations):
    auth0id = insertuser[0]['auth0_id']
    agg = insertuser[8]
    obs = new_observation(site=insertuser[1])
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc(
            'add_observation_to_aggregate',
            (auth0id, agg['strid'], str(bin_to_uuid(obs['id'])),
             '2019-01-01 00:00'))
    assert e.value.args[0] == 1142


def test_add_observation_to_aggregate_no_read_obs(dictcursor, insertuser,
                                                  new_observation,
                                                  allow_update_aggregates):

    auth0id = insertuser[0]['auth0_id']
    agg = insertuser[8]
    obs = new_observation(site=insertuser[1])
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc(
            'add_observation_to_aggregate',
            (auth0id, agg['strid'], str(bin_to_uuid(obs['id'])),
             '2019-01-01 00:00'))
    assert e.value.args[0] == 1143


def test_create_user(dictcursor, valueset_org):
    userid = str(uuid.uuid1())
    auth0id = 'auth0|blahblah'
    dictcursor.callproc('create_user', (userid, auth0id,
                                        valueset_org['name']))
    dictcursor.execute(
        'SELECT * FROM arbiter_data.users WHERE id = UUID_TO_BIN(%s, 1)',
        (userid,))
    res = dictcursor.fetchall()[0]
    assert res['auth0_id'] == auth0id
    assert res['organization_id'] == valueset_org['id']
    assert 'id' in res


def test_create_role(dictcursor, allow_create, insertuser):
    auth0id = insertuser[0]['auth0_id']
    strid = str(bin_to_uuid(newuuid()))
    dictcursor.callproc('create_role', (auth0id, strid, 'newrole',
                                        'A brandh new role!'))
    dictcursor.execute(
        'SELECT * from arbiter_data.roles WHERE id = UUID_TO_BIN(%s, 1)',
        (strid,))
    res = dictcursor.fetchall()[0]
    assert res['name'] == 'newrole'
    assert res['description'] == 'A brandh new role!'
    assert res['organization_id'] == insertuser[4]['id']

    dictcursor.execute(
        'SELECT * FROM arbiter_data.role_permission_mapping '
        'WHERE role_id = UUID_TO_BIN(%s, 1)', (strid,))
    mapping = dictcursor.fetchone()
    read_perm_id = mapping['permission_id']
    dictcursor.execute(
        'SELECT * FROM arbiter_data.permissions WHERE '
        'id = %s', (read_perm_id,))
    read_role_perm = dictcursor.fetchone()
    assert read_role_perm['object_type'] == 'roles'
    assert read_role_perm['organization_id'] == insertuser[4]['id']
    assert read_role_perm['description'] == f'Read Role {strid}'
    assert read_role_perm['applies_to_all'] == 0
    assert 'created_at' in read_role_perm

    dictcursor.execute(
        'SELECT * FROM arbiter_data.permission_object_mapping '
        'WHERE permission_id = %s', (read_perm_id,))
    read_role_mapping = dictcursor.fetchone()
    assert read_role_mapping['permission_id'] == read_perm_id
    assert str(bin_to_uuid(read_role_mapping['object_id'])) == strid


def test_create_and_share_role(
        dictcursor, allow_create, allow_grant_roles, insertuser,
        new_user):
    auth0id = insertuser[0]['auth0_id']
    user = new_user()
    strid = str(bin_to_uuid(newuuid()))
    dictcursor.callproc('create_role', (auth0id, strid, 'newrole',
                                        'A brandh new role!'))
    dictcursor.callproc('add_role_to_user', (auth0id,
                                             str(bin_to_uuid(user['id'])),
                                             strid))
    dictcursor.execute(
        'SELECT * FROM user_role_mapping WHERE user_id = %s AND role_id = %s',
        (user['id'], uuid_to_bin(uuid.UUID(strid))))
    mappings = dictcursor.fetchall()
    roles = [str(bin_to_uuid(mapping['role_id'])) for mapping in mappings]
    assert strid in roles


def test_create_role_fail(dictcursor, insertuser):
    auth0id = insertuser[0]['auth0_id']
    strid = str(uuid.uuid1())
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc('create_role', (auth0id, strid, 'newrole',
                                            'A brandh new role!'))
    assert e.value.args[0] == 1142


def test_create_permission(dictcursor, allow_create, insertuser):
    auth0id = insertuser[0]['auth0_id']
    strid = str(uuid.uuid1())
    dictcursor.callproc('create_permission', (
        auth0id, strid, 'New permission', 'read', 'observations',
        False))
    dictcursor.execute(
        'SELECT * from arbiter_data.permissions WHERE id = UUID_TO_BIN(%s, 1)',
        (strid,))
    res = dictcursor.fetchall()[0]
    assert res['description'] == 'New permission'
    assert res['action'] == 'read'
    assert res['object_type'] == 'observations'
    assert not res['applies_to_all']


def test_create_permission_denied(dictcursor, insertuser):
    auth0id = insertuser[0]['auth0_id']
    strid = str(uuid.uuid1())
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc('create_permission', (
            auth0id, strid, 'New permission', 'read', 'observations',
            False))
    assert e.value.args[0] == 1142


def test_add_object_to_permission(cursor, getfcn, new_permission,
                                  allow_update_permissions, user_org_role):
    user, org, role = user_org_role
    fcn, obj_type = getfcn
    objid = fcn(org=org)['id']
    readperm = new_permission('read', obj_type, False, org=org)
    cursor.execute(
        'INSERT INTO permission_object_mapping (permission_id, object_id) '
        'VALUES (%s, %s)', (readperm['id'], objid))
    perm = new_permission('delete', obj_type, False, org=org)
    cursor.executemany(
        'INSERT INTO role_permission_mapping (role_id, permission_id) '
        'VALUES (%s, %s)',
        [(role['id'], perm['id']), (role['id'], readperm['id'])])
    cursor.callproc('add_object_to_permission',
                    (user['auth0_id'], str(bin_to_uuid(objid)),
                     str(bin_to_uuid(perm['id']))))
    res = cursor.execute("SELECT can_user_perform_action(%s, %s, 'delete')",
                         (user['auth0_id'], objid))
    assert res


def test_add_object_to_permission_denied_no_update(
        cursor, new_observation, new_permission,
        user_org_role):
    user, org, role = user_org_role
    objid = new_observation(org=org)['id']
    readperm = new_permission('read', 'observations', False, org=org)
    cursor.execute(
        'INSERT INTO permission_object_mapping (permission_id, object_id) '
        'VALUES (%s, %s)', (readperm['id'], objid))
    perm = new_permission('read', 'observations', False, org=org)
    cursor.executemany(
        'INSERT INTO role_permission_mapping (role_id, permission_id) '
        'VALUES (%s, %s)',
        [(role['id'], perm['id']), (role['id'], readperm['id'])])
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('add_object_to_permission',
                        (user['auth0_id'], str(bin_to_uuid(objid)),
                         str(bin_to_uuid(perm['id']))))
    assert e.value.args[0] == 1142


def test_add_object_to_permission_denied_no_read(
        cursor, new_observation, new_permission, allow_update_permissions,
        user_org_role):
    user, org, role = user_org_role
    objid = new_observation(org=org)['id']
    perm = new_permission('read', 'observations', False, org=org)
    cursor.execute(
        'INSERT INTO role_permission_mapping (role_id, permission_id) '
        'VALUES (%s, %s)',
        (role['id'], perm['id']))
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('add_object_to_permission',
                        (user['auth0_id'], str(bin_to_uuid(objid)),
                         str(bin_to_uuid(perm['id']))))
    assert e.value.args[0] == 1142


def test_add_object_to_permission_no_perm(
        cursor, new_site, new_permission, allow_update_permissions,
        user_org_role):
    user, org, role = user_org_role
    objid = new_site(org=org)['id']
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('add_object_to_permission',
                        (user['auth0_id'], str(bin_to_uuid(objid)),
                         str(uuid.uuid1())))
    assert e.value.args[0] == 1142


@pytest.mark.parametrize('obj_type', ['users', 'roles', 'forecasts',
                                      'permissions', 'observations',
                                      'cdf_forecasts', 'sites',
                                      'reports', 'aggregates'])
def test_add_permission_to_role(cursor, new_permission, obj_type,
                                allow_update_roles, user_org_role):
    user, org, role = user_org_role
    perm = new_permission('read', obj_type, False, org=org)
    cursor.callproc('add_permission_to_role', (
        user['auth0_id'], str(bin_to_uuid(role['id'])),
        str(bin_to_uuid(perm['id']))))
    cursor.execute(
        'SELECT 1 FROM role_permission_mapping WHERE role_id = %s and '
        'permission_id = %s', (role['id'], perm['id']))
    assert cursor.fetchall()[0][0]


def test_add_permission_to_role_wrong_org(cursor, new_permission,
                                          user_org_role,
                                          allow_update_roles):
    user, org, role = user_org_role
    perm = new_permission('read', 'sites', False)
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('add_permission_to_role', (
            user['auth0_id'], str(bin_to_uuid(role['id'])),
            str(bin_to_uuid(perm['id']))))
    assert e.value.args[0] == 1142


@pytest.mark.parametrize('object_type', [
    'roles', 'permissions', 'users']
)
def test_add_permission_to_role_rbac_on_external_role(
        cursor, new_permission, new_user, new_role,
        user_org_role, object_type):
    user, org, role = user_org_role
    perm = new_permission('create', object_type, False, org=org)
    share_user = new_user()
    role = new_role(org=org)
    cursor.execute('INSERT INTO arbiter_data.user_role_mapping '
                   '(user_id, role_id) VALUES (%s, %s)',
                   (share_user['id'], role['id']))
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('add_permission_to_role', (
            user['auth0_id'], str(bin_to_uuid(role['id'])),
            str(bin_to_uuid(perm['id']))))
        assert e.value.args[0] == 1142


def test_add_permission_to_role_denied(cursor, new_permission, user_org_role):
    user, org, role = user_org_role
    perm = new_permission('read', 'sites', False, org=org)
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('add_permission_to_role', (
            user['auth0_id'], str(bin_to_uuid(role['id'])),
            str(bin_to_uuid(perm['id']))))
    assert e.value.args[0] == 1142


def test_add_role_to_user(
        cursor, new_role, allow_create,
        allow_grant_roles, user_org_role):
    user, org, role = user_org_role
    role = new_role(org=org)
    cursor.callproc('add_role_to_user', (
        user['auth0_id'], str(bin_to_uuid(user['id'])),
        str(bin_to_uuid(role['id']))))
    cursor.execute('SELECT 1 from user_role_mapping where user_id = %s and '
                   'role_id = %s', (user['id'], role['id']))
    assert cursor.fetchall()[0][0]


def test_add_role_to_user_outside_org(
        cursor, new_role, allow_create, allow_grant_roles,
        new_user, user_org_role):
    user, org, role = user_org_role
    role = new_role(org=org)
    share_user = new_user()
    cursor.callproc('add_role_to_user', (
        user['auth0_id'], str(bin_to_uuid(share_user['id'])),
        str(bin_to_uuid(role['id']))))
    cursor.execute('SELECT 1 from user_role_mapping where user_id = %s and '
                   'role_id = %s', (share_user['id'], role['id']))
    assert cursor.fetchall()[0][0]


def test_add_role_to_user_admin_role(
        cursor, new_role, allow_create, allow_grant_roles,
        new_permission, user_org_role):
    user, org, role = user_org_role
    role = new_role(org=org)
    perm = new_permission('create', 'roles', True, org=org)
    cursor.execute(
        'INSERT INTO role_permission_mapping (role_id, permission_id) '
        f'VALUES(%s, %s)', (role['id'], perm['id']))
    cursor.callproc('add_role_to_user', (
        user['auth0_id'], str(bin_to_uuid(user['id'])),
        str(bin_to_uuid(role['id']))))
    cursor.execute('SELECT 1 from user_role_mapping where user_id = %s and '
                   'role_id = %s', (user['id'], role['id']))
    assert cursor.fetchall()[0][0]


def test_add_role_to_user_admin_role_outside_org(
        allow_create, cursor, new_role, allow_grant_roles,
        new_user, new_permission, user_org_role):
    user, org, role = user_org_role
    share_user = new_user()
    role = new_role(org=org)
    perm = new_permission('create', 'roles', True, org=org)
    cursor.execute(
        'INSERT INTO role_permission_mapping (role_id, permission_id) '
        f'VALUES(%s, %s)', (role['id'], perm['id']))
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('add_role_to_user', (
            user['auth0_id'], str(bin_to_uuid(share_user['id'])),
            str(bin_to_uuid(role['id']))))
    assert e.value.args[0] == 1142


def test_add_role_to_user_missing_perm(
        cursor, new_role, user_org_role):
    user, org, role = user_org_role
    role = new_role(org=org)
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('add_role_to_user', (
            user['auth0_id'], str(bin_to_uuid(user['id'])),
            str(bin_to_uuid(role['id']))))
    assert e.value.args[0] == 1142


def test_add_role_to_user_user_dne(
        cursor, allow_create, new_role, allow_grant_roles,
        user_org_role):
    user, org, role = user_org_role
    role = new_role(org=org)
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('add_role_to_user', (
            user['auth0_id'], str(bin_to_uuid(newuuid())),
            str(bin_to_uuid(role['id']))))
    assert e.value.args[0] == 1142


def test_add_role_to_user_no_tou(
        cursor, allow_create, new_role, allow_grant_roles,
        user_org_role, new_user, new_organization_no_tou):
    user, org, role = user_org_role
    role = new_role(org=org)
    share_user = new_user(org=new_organization_no_tou())
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('add_role_to_user', (
            user['auth0_id'], str(bin_to_uuid(share_user['id'])),
            str(bin_to_uuid(role['id']))))
    assert e.value.args[0] == 1142


def test_store_report(dictcursor, report_callargs, allow_create,
                      default_user_role, insertuser):
    dictcursor.execute(
        "SELECT can_user_perform_action(%s, UUID_TO_BIN(%s, 1), 'update') as can",  # NOQA
        (insertuser[0]['auth0_id'], report_callargs['strid'])
    )
    assert not dictcursor.fetchone()['can']
    dictcursor.callproc('store_report', list(report_callargs.values()))
    dictcursor.execute(
        'SELECT * FROM arbiter_data.reports WHERE id = UUID_TO_BIN(%s, 1)',
        (report_callargs['strid'],))
    res = dictcursor.fetchall()[0]
    assert res['name'] == report_callargs['name']
    res_params = json.loads(res['report_parameters'])
    set_params = json.loads(report_callargs['report_parameters'])
    assert res_params == set_params
    dictcursor.execute(
        "SELECT can_user_perform_action(%s, UUID_TO_BIN(%s, 1), 'update') as can",  # NOQA
        (insertuser[0]['auth0_id'], report_callargs['strid'])
    )
    assert dictcursor.fetchone()['can']


def test_store_report_no_default(dictcursor, report_callargs, allow_create,
                                 insertuser):
    dictcursor.execute(
        "SELECT can_user_perform_action(%s, UUID_TO_BIN(%s, 1), 'update') as can",  # NOQA
        (insertuser[0]['auth0_id'], report_callargs['strid'])
    )
    assert not dictcursor.fetchone()['can']
    dictcursor.callproc('store_report', list(report_callargs.values()))
    dictcursor.execute(
        'SELECT * FROM arbiter_data.reports WHERE id = UUID_TO_BIN(%s, 1)',
        (report_callargs['strid'],))
    res = dictcursor.fetchall()[0]
    assert res['name'] == report_callargs['name']
    res_params = json.loads(res['report_parameters'])
    set_params = json.loads(report_callargs['report_parameters'])
    assert res_params == set_params
    dictcursor.execute(
        "SELECT can_user_perform_action(%s, UUID_TO_BIN(%s, 1), 'update') as can",  # NOQA
        (insertuser[0]['auth0_id'], report_callargs['strid'])
    )
    assert not dictcursor.fetchone()['can']


def test_store_report_denied(dictcursor, report_callargs, insertuser):
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc('store_report', list(report_callargs.values()))
    assert e.value.args[0] == 1142


def test_store_report_values(
        dictcursor, insertuser, allow_write_values,
        allow_read_observation_values, new_observation):
    user, _, _, obs, org, role, _, report, _ = insertuser
    value = b'\x00\x0F\xFF'
    value_id = newuuid()
    dictcursor.callproc(
        'store_report_values',
        (user['auth0_id'],
         str(bin_to_uuid(value_id)),
         str(bin_to_uuid(report['id'])),
         str(bin_to_uuid(obs['id'])),
         value)
    )
    dictcursor.execute(
        'SELECT * FROM arbiter_data.report_values WHERE id = %s',
        (value_id))
    res = dictcursor.fetchall()
    assert res[0]['id'] == value_id
    assert res[0]['processed_values'] == value
    assert res[0]['object_id'] == obs['id']
    assert res[0]['report_id'] == report['id']


def test_update_report_values(
        dictcursor, insertuser, allow_write_values,
        allow_read_observation_values):
    user, _, _, obs, org, role, _, report, _ = insertuser
    value = b'\x00\x0F\xFF'
    dictcursor.execute(
        'SELECT id FROM arbiter_data.report_values WHERE report_id = %s '
        'AND object_id = %s',
        (report['id'], obs['id'],)
    )
    value_id = dictcursor.fetchall()[0]['id']
    dictcursor.callproc(
        'store_report_values',
        (user['auth0_id'],
         str(bin_to_uuid(value_id)),
         str(bin_to_uuid(report['id'])),
         str(bin_to_uuid(obs['id'])),
         value)
    )
    dictcursor.execute(
        'SELECT * FROM arbiter_data.report_values WHERE id = %s',
        (value_id))
    res = dictcursor.fetchall()
    assert res[0]['id'] == value_id
    assert res[0]['processed_values'] == value
    assert res[0]['object_id'] == obs['id']
    assert res[0]['report_id'] == report['id']


def test_store_report_values_wrong_type(
        dictcursor, insertuser, allow_write_values,
        allow_read_observation_values):
    user, _, _, obs, org, role, cdf, report, _ = insertuser
    value = b'\x00\x0F\xFF'
    cdf_singles = list(cdf['constant_values'].keys())
    object_id = cdf_singles[0]
    with pytest.raises(pymysql.err.InternalError) as e:
        dictcursor.callproc(
            'store_report_values',
            (user['auth0_id'],
             str(uuid.uuid1()),
             str(bin_to_uuid(report['id'])),
             object_id,
             value)
        )
    assert e.value.args[0] == 1210


def test_store_report_values_no_write_report(
        dictcursor, insertuser, allow_read_observation_values):
    user, _, _, obs, org, role, _, report, _ = insertuser
    value = b'\x00\x0F\xFF'
    dictcursor.execute(
        'SELECT id FROM arbiter_data.report_values WHERE report_id = %s '
        'AND object_id = %s',
        (report['id'], obs['id'],)
    )
    value_id = dictcursor.fetchall()[0]['id']
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc(
            'store_report_values',
            (user['auth0_id'],
             str(bin_to_uuid(value_id)),
             str(bin_to_uuid(report['id'])),
             str(bin_to_uuid(obs['id'])),
             value)
        )
    assert e.value.args[0] == 1142


def test_store_raw_report(
        dictcursor, insertuser, allow_read_reports,
        allow_update_reports):
    user, _, _, obs, org, role, _, report, _ = insertuser
    raw_report = {"a": "b", "c": "d"}
    dictcursor.callproc(
        'store_raw_report',
        (user['auth0_id'],
         str(bin_to_uuid(report['id'])),
         json.dumps(raw_report))
    )
    dictcursor.execute(
        'SELECT * FROM arbiter_data.reports WHERE id = %s',
        (report['id'],))
    res = dictcursor.fetchall()[0]
    assert json.loads(res['raw_report']) == raw_report


def test_store_raw_report_no_update(
        dictcursor, insertuser, allow_read_reports):
    user, _, _, obs, org, role, _, report, _ = insertuser
    raw_report = {"a": "b", "c": "d"}
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc(
            'store_raw_report',
            (user['auth0_id'],
             str(bin_to_uuid(report['id'])),
             json.dumps(raw_report))
        )
    assert e.value.args[0] == 1142


@pytest.mark.parametrize('new_status', [
    'pending', 'complete', 'failed'])
def test_store_report_status(
        dictcursor, insertuser, allow_read_reports,
        allow_update_reports, new_status):
    user, _, _, obs, org, role, _, report, _ = insertuser
    dictcursor.callproc(
        'store_report_status',
        (user['auth0_id'],
         str(bin_to_uuid(report['id'])),
         new_status)
    )
    dictcursor.execute(
        'SELECT * FROM arbiter_data.reports WHERE id = %s',
        (report['id'],))
    res = dictcursor.fetchall()[0]
    assert res['status'] == new_status


@pytest.mark.parametrize('new_status', [
    'complete', 'failed'])
def test_store_report_status_denied(
        dictcursor, insertuser, allow_read_reports,
        new_status):
    user, _, _, obs, org, role, _, report, _ = insertuser
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc(
            'store_report_status',
            (user['auth0_id'],
             str(bin_to_uuid(report['id'])),
             new_status)
        )
    assert e.value.args[0] == 1142


def test_create_user_if_not_exist(dictcursor, valueset_org):
    dictcursor.execute(
        'SELECT id FROM arbiter_data.organizations '
        'WHERE name = "Unaffiliated"')
    unaffiliated_id = dictcursor.fetchone()['id']
    auth0id = 'auth0|blahblah'
    dictcursor.execute(
        'SELECT * FROM arbiter_data.users WHERE auth0_id = %s',
        (auth0id,))
    assert len(dictcursor.fetchall()) == 0
    dictcursor.callproc('create_user_if_not_exists', (auth0id,))
    dictcursor.execute(
        'SELECT * FROM arbiter_data.users WHERE auth0_id = %s',
        (auth0id,))
    user = dictcursor.fetchone()
    user_id = user['id']
    assert user['auth0_id'] == auth0id
    assert user['organization_id'] == unaffiliated_id
    dictcursor.execute(
        'SELECT * FROM arbiter_data.user_role_mapping WHERE '
        'user_id = %s', (user_id,))
    role_mappings = dictcursor.fetchall()
    assert len(role_mappings) == 2

    role_ids = [role['role_id'] for role in role_mappings]
    for role_id in role_ids:
        dictcursor.execute(
            'SELECT * FROM arbiter_data.roles WHERE id = %s',
            role_id)
        role = dictcursor.fetchone()
        if role['name'].startswith('DEFAULT User role'):
            default_role = role
        else:
            reference_role = role
    assert reference_role['name'] == 'Read Reference Data'
    assert (reference_role['description'] ==
            'Role to read reference sites, forecasts, and observations')
    assert default_role['description'] == 'Default role'
    assert default_role['organization_id'] == unaffiliated_id
    dictcursor.execute(
        'SELECT * FROM arbiter_data.permissions WHERE id IN '
        '(SELECT permission_id FROM arbiter_data.role_permission_mapping '
        'WHERE role_id = %s)',
        (default_role['id'],))
    default_permissions = dictcursor.fetchall()
    assert len(default_permissions) == 2

    for p in default_permissions:
        if (p['description'] ==
                f'DEFAULT Read Self User {str(bin_to_uuid(user["id"]))}'):
            read_self = p
        if (p['description'] ==
                f'DEFAULT Read User Role {str(bin_to_uuid(user["id"]))}'):
            read_role = p
    assert read_self['action'] == 'read'
    assert read_self['object_type'] == 'users'
    assert read_self['organization_id'] == unaffiliated_id
    assert read_role['action'] == 'read'
    assert read_role['object_type'] == 'roles'
    assert read_role['organization_id'] == unaffiliated_id

    dictcursor.execute(
        'SELECT object_id FROM arbiter_data.permission_object_mapping '
        'WHERE permission_id = %s', read_self['id'])
    perm_user_ids = dictcursor.fetchall()
    assert len(perm_user_ids) == 1
    assert perm_user_ids[0]['object_id'] == user_id
    dictcursor.execute(
        'SELECT object_id FROM arbiter_data.permission_object_mapping '
        'WHERE permission_id = %s', read_role['id'])
    perm_role_ids = dictcursor.fetchall()
    assert len(perm_role_ids) == 1
    assert perm_role_ids[0]['object_id'] == default_role['id']


def test_store_job(dictcursor, new_user):
    user = new_user()
    args = OrderedDict(
        id=bin_to_uuid(newuuid()),
        user_id=bin_to_uuid(user['id']),
        name='testjob',
        job_type='jobtype',
        parameters='{"start_td": "1h"}',
        schedule='{"type": "cron", "cron_schedule": "* * * * *"}',
        version=0
    )
    dictcursor.callproc('store_job', list(args.values()))
    dictcursor.execute('SELECT * from scheduled_jobs where user_id = %s',
                       (user['id'],))
    out = dictcursor.fetchone()
    for k, v in args.items():
        if k in ('user_id', 'id'):
            assert bin_to_uuid(out[k]) == v
        else:
            assert out[k] == v

    assert out['organization_id'] == user['organization_id']
    assert 'created_at' in out
    assert 'modified_at' in out
