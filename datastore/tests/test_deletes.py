from uuid import UUID


import pytest
import pymysql


from conftest import bin_to_uuid, newuuid, uuid_to_bin


@pytest.fixture()
def site_obj(cursor, valueset, new_site):
    org = valueset[0][0]
    user = valueset[1][0]
    auth0id = user['auth0_id']
    site = new_site(org=org, latitude=32, longitude=-110)
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
def cdf_obj(site_obj, new_cdf_forecast):
    auth0id, _, site = site_obj
    cdf = new_cdf_forecast(site=site)
    return auth0id, str(bin_to_uuid(cdf['id'])), cdf


@pytest.fixture()
def report_obj(site_obj, valueset, new_report, new_observation, new_forecast):
    auth0_id, _, site = site_obj
    obs = new_observation(site=site)
    fx = new_forecast(site=site)
    report = new_report(valueset[0][0], obs, [fx])
    return auth0_id, str(bin_to_uuid(report['id'])), report


@pytest.fixture()
def agg_obj(site_obj, new_observation, new_aggregate):
    auth0id, _, site = site_obj
    obs0 = new_observation(site=site)
    obs1 = new_observation(site=site)
    agg = new_aggregate(obs_list=[obs0, obs1])
    return auth0id, str(bin_to_uuid(agg['id'])), agg


@pytest.fixture()
def allow_create(cursor, new_permission, valueset):
    def do(what):
        org = valueset[0][0]
        role = valueset[2][0]
        perm = new_permission('create', what, False, org=org)
        cursor.execute(
            'INSERT INTO role_permission_mapping (role_id, permission_id)'
            ' VALUES (%s, %s)', (role['id'], perm['id']))
    return do


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


@pytest.fixture()
def allow_delete_cdf_group(allow_delete):
    allow_delete('cdf_forecasts')


@pytest.fixture()
def allow_delete_report(allow_delete):
    allow_delete('reports')


@pytest.fixture()
def allow_delete_aggregate(allow_delete):
    allow_delete('aggregates')


@pytest.fixture()
def allow_update_aggregate(cursor, new_permission, valueset):
    org = valueset[0][0]
    role = valueset[2][0]
    perm = new_permission('update', 'aggregates', True, org=org)
    cursor.execute(
        'INSERT INTO role_permission_mapping (role_id, permission_id)'
        ' VALUES (%s, %s)', (role['id'], perm['id']))


@pytest.fixture()
def allow_update_cdf_group(cursor, valueset, new_permission):
    org = valueset[0][0]
    role = valueset[2][0]
    perm = new_permission('update', 'cdf_forecasts', True, org=org)
    cursor.execute(
        'INSERT INTO role_permission_mapping (role_id, permission_id)'
        ' VALUES (%s, %s)', (role['id'], perm['id']))


def test_delete_site(cursor, site_obj, allow_delete_site):
    auth0id, siteid, *_ = site_obj
    cursor.execute(
        'SELECT COUNT(id) FROM arbiter_data.sites WHERE id = UUID_TO_BIN(%s, 1)',  # NOQA
        siteid)
    assert cursor.fetchone()[0] > 0
    cursor.execute(
        'SELECT COUNT(site_id) FROM arbiter_data.site_zone_mapping WHERE'
        ' site_id = UUID_TO_BIN(%s, 1)',
        siteid)
    assert cursor.fetchone()[0] > 0
    cursor.callproc('delete_site', (auth0id, siteid))
    cursor.execute(
        'SELECT COUNT(id) FROM arbiter_data.sites WHERE id = UUID_TO_BIN(%s, 1)',  # NOQA
        siteid)
    assert cursor.fetchone()[0] == 0
    cursor.execute(
        'SELECT COUNT(site_id) FROM arbiter_data.site_zone_mapping WHERE'
        ' site_id = UUID_TO_BIN(%s, 1)',
        siteid)
    assert cursor.fetchone()[0] == 0


def test_delete_site_with_forecast(cursor, site_obj, allow_delete_site,
                                   new_forecast):
    auth0id, siteid, site = site_obj
    fx = new_forecast(site=site)
    cursor.execute(
        'SELECT COUNT(id) FROM arbiter_data.sites WHERE id = UUID_TO_BIN(%s, 1)',  # NOQA
        siteid)
    assert cursor.fetchone()[0] > 0
    cursor.execute(
        'SELECT COUNT(id) FROM arbiter_data.forecasts WHERE site_id = UUID_TO_BIN(%s, 1)',  # NOQA
        siteid)
    assert cursor.fetchone()[0] > 0
    cursor.callproc('delete_site', (auth0id, siteid))
    cursor.execute(
        'SELECT COUNT(id) FROM arbiter_data.sites WHERE id = UUID_TO_BIN(%s, 1)',  # NOQA
        siteid)
    assert cursor.fetchone()[0] == 0
    cursor.execute('SELECT site_id FROM arbiter_data.forecasts where id = %s',
                   fx['id'])
    assert cursor.fetchone()[0] is None


def test_delete_site_with_cdf_forecast(cursor, site_obj, allow_delete_site,
                                       new_cdf_forecast):
    auth0id, siteid, site = site_obj
    fx = new_cdf_forecast(site=site)
    cursor.execute(
        'SELECT COUNT(id) FROM arbiter_data.sites WHERE id = UUID_TO_BIN(%s, 1)',  # NOQA
        siteid)
    assert cursor.fetchone()[0] > 0
    cursor.execute(
        'SELECT COUNT(id) FROM arbiter_data.cdf_forecasts_groups WHERE site_id = UUID_TO_BIN(%s, 1)',  # NOQA
        siteid)
    assert cursor.fetchone()[0] > 0
    cursor.callproc('delete_site', (auth0id, siteid))
    cursor.execute(
        'SELECT COUNT(id) FROM arbiter_data.sites WHERE id = UUID_TO_BIN(%s, 1)',  # NOQA
        siteid)
    assert cursor.fetchone()[0] == 0
    cursor.execute('SELECT site_id FROM arbiter_data.cdf_forecasts_groups where id = %s',  # NOQA
                   fx['id'])
    assert cursor.fetchone()[0] is None


def test_delete_site_denied(cursor, site_obj):
    auth0id, siteid, *_ = site_obj
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('delete_site', (auth0id, siteid))
    assert e.value.args[0] == 1142


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
    assert e.value.args[0] == 1142


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
    assert e.value.args[0] == 1142


def test_delete_aggregate(cursor, agg_obj, allow_delete_aggregate):
    auth0id, aggid, _ = agg_obj
    cursor.execute(
        'SELECT COUNT(id) FROM arbiter_data.aggregates WHERE id = '
        'UUID_TO_BIN(%s, 1)',
        aggid)
    assert cursor.fetchone()[0] > 0
    cursor.callproc('delete_aggregate', (auth0id, aggid))
    cursor.execute(
        'SELECT COUNT(id) FROM arbiter_data.aggregates WHERE id = '
        'UUID_TO_BIN(%s, 1)',
        aggid)
    assert cursor.fetchone()[0] == 0


def test_delete_aggregate_with_forecast(
        cursor, agg_obj, allow_delete_aggregate, new_forecast):
    auth0id, aggregateid, aggregate = agg_obj
    fx = new_forecast(aggregate=aggregate)
    cursor.execute(
        'SELECT COUNT(id) FROM arbiter_data.aggregates WHERE id = UUID_TO_BIN(%s, 1)',  # NOQA
        aggregateid)
    assert cursor.fetchone()[0] > 0
    cursor.execute(
        'SELECT COUNT(id) FROM arbiter_data.forecasts WHERE aggregate_id = UUID_TO_BIN(%s, 1)',  # NOQA
        aggregateid)
    assert cursor.fetchone()[0] > 0
    cursor.callproc('delete_aggregate', (auth0id, aggregateid))
    cursor.execute(
        'SELECT COUNT(id) FROM arbiter_data.aggregates WHERE id = UUID_TO_BIN(%s, 1)',  # NOQA
        aggregateid)
    assert cursor.fetchone()[0] == 0
    cursor.execute('SELECT aggregate_id FROM arbiter_data.forecasts where id = %s',
                   fx['id'])
    assert cursor.fetchone()[0] is None


def test_delete_aggregate_with_cdf_forecast(
        cursor, agg_obj, allow_delete_aggregate, new_cdf_forecast):
    auth0id, aggregateid, aggregate = agg_obj
    fx = new_cdf_forecast(aggregate=aggregate)
    cursor.execute(
        'SELECT COUNT(id) FROM arbiter_data.aggregates WHERE id = UUID_TO_BIN(%s, 1)',  # NOQA
        aggregateid)
    assert cursor.fetchone()[0] > 0
    cursor.execute(
        'SELECT COUNT(id) FROM arbiter_data.cdf_forecasts_groups WHERE aggregate_id = UUID_TO_BIN(%s, 1)',  # NOQA
        aggregateid)
    assert cursor.fetchone()[0] > 0
    cursor.callproc('delete_aggregate', (auth0id, aggregateid))
    cursor.execute(
        'SELECT COUNT(id) FROM arbiter_data.aggregates WHERE id = UUID_TO_BIN(%s, 1)',  # NOQA
        aggregateid)
    assert cursor.fetchone()[0] == 0
    cursor.execute('SELECT aggregate_id FROM arbiter_data.cdf_forecasts_groups where id = %s',  # NOQA
                   fx['id'])
    assert cursor.fetchone()[0] is None


def test_delete_aggregate_fail(cursor, agg_obj):
    auth0id, aggid, _ = agg_obj
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('delete_aggregate', (auth0id, aggid))
    assert e.value.args[0] == 1142


def test_delete_aggregate_obs(cursor, agg_obj, allow_delete_observation):
    auth0id, aggid, agg = agg_obj
    cursor.execute(
        'SELECT COUNT(*) FROM arbiter_data.aggregate_observation_mapping '
        'WHERE aggregate_id = UUID_TO_BIN(%s, 1) AND observation_deleted_at is'
        ' NULL', aggid)
    assert cursor.fetchone()[0] == 2
    cursor.callproc('delete_observation',
                    (auth0id, str(bin_to_uuid(agg['obs_list'][0]['id']))))
    cursor.execute(
        'SELECT COUNT(*) FROM arbiter_data.aggregate_observation_mapping '
        'WHERE aggregate_id = UUID_TO_BIN(%s, 1) AND observation_deleted_at is'
        ' NULL', aggid)
    assert cursor.fetchone()[0] == 1


def test_remove_observation_from_aggregate(cursor, agg_obj,
                                           allow_update_aggregate):
    auth0id, aggid, agg = agg_obj
    cursor.execute(
        'SELECT COUNT(*) FROM arbiter_data.aggregate_observation_mapping '
        'WHERE aggregate_id = UUID_TO_BIN(%s, 1) AND effective_until is'
        ' NULL', aggid)
    assert cursor.fetchone()[0] == 2
    cursor.callproc('remove_observation_from_aggregate',
                    (auth0id, aggid,
                     str(bin_to_uuid(agg['obs_list'][0]['id'])),
                     '2019-09-30 00:00'))
    cursor.execute(
        'SELECT COUNT(*) FROM arbiter_data.aggregate_observation_mapping '
        'WHERE aggregate_id = UUID_TO_BIN(%s, 1) AND effective_until is'
        ' NULL', aggid)
    assert cursor.fetchone()[0] == 1


def test_remove_observation_from_aggregate_denied(cursor, agg_obj,
                                                  allow_delete_aggregate):
    auth0id, aggid, agg = agg_obj
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc(
            'remove_observation_from_aggregate',
            (auth0id, aggid, str(bin_to_uuid(agg['obs_list'][0]['id'])),
             '2019-09-30 00:00'))
    assert e.value.args[0] == 1142


def test_delete_observation_from_aggregate(cursor, agg_obj,
                                           allow_update_aggregate):
    auth0id, aggid, agg = agg_obj
    # add more of same obs to verify all are deleted
    for i in range(1, 3):
        cursor.execute(
            'INSERT INTO arbiter_data.aggregate_observation_mapping '
            '(aggregate_id, observation_id, _incr) VALUES '
            '(UUID_TO_BIN(%s, 1), %s, %s)',
            (aggid, agg['obs_list'][0]['id'], i))
    cursor.execute(
        'SELECT COUNT(*) FROM arbiter_data.aggregate_observation_mapping '
        'WHERE aggregate_id = UUID_TO_BIN(%s, 1) and observation_id = %s',
        (aggid, agg['obs_list'][0]['id']))
    assert cursor.fetchone()[0] == 3
    cursor.execute(
        'SELECT COUNT(*) FROM arbiter_data.aggregate_observation_mapping '
        'WHERE aggregate_id = UUID_TO_BIN(%s, 1) and observation_id != %s',
        (aggid, agg['obs_list'][0]['id']))
    assert cursor.fetchone()[0] == 1

    cursor.callproc('delete_observation_from_aggregate',
                    (auth0id, aggid,
                     str(bin_to_uuid(agg['obs_list'][0]['id']))))
    cursor.execute(
        'SELECT COUNT(*) FROM arbiter_data.aggregate_observation_mapping '
        'WHERE aggregate_id = UUID_TO_BIN(%s, 1) and observation_id=%s',
        (aggid, agg['obs_list'][0]['id']))
    assert cursor.fetchone()[0] == 0

    cursor.execute(
        'SELECT COUNT(*) FROM arbiter_data.aggregate_observation_mapping '
        'WHERE aggregate_id = UUID_TO_BIN(%s, 1) and observation_id != %s',
        (aggid, agg['obs_list'][0]['id']))
    assert cursor.fetchone()[0] == 1


def test_delete_observation_from_aggregate_denied(cursor, agg_obj,
                                                  allow_delete_aggregate):
    auth0id, aggid, agg = agg_obj
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc(
            'delete_observation_from_aggregate',
            (auth0id, aggid, str(bin_to_uuid(agg['obs_list'][0]['id']))))
    assert e.value.args[0] == 1142


def test_delete_cdf_forecast(cursor, cdf_obj, allow_delete_cdf_group):
    auth0id, cdfgroupid, _ = cdf_obj
    cursor.execute(
        'SELECT COUNT(id) FROM arbiter_data.cdf_forecasts_groups WHERE '
        'id = UUID_TO_BIN(%s, 1)',
        cdfgroupid)
    assert cursor.fetchone()[0] > 0
    cursor.callproc('delete_cdf_forecasts_group', (auth0id, cdfgroupid))
    cursor.execute(
        'SELECT COUNT(id) FROM arbiter_data.cdf_forecasts_groups WHERE '
        'id = UUID_TO_BIN(%s, 1)',
        cdfgroupid)
    assert cursor.fetchone()[0] == 0


def test_delete_cdf_forecast_denied(cursor, cdf_obj, allow_delete_forecast):
    auth0id, cdfgroupid, _ = cdf_obj
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('delete_cdf_forecasts_group', (auth0id, cdfgroupid))
    assert e.value.args[0] == 1142


def test_delete_cdf_forecast_single(cursor, cdf_obj, allow_delete_cdf_group,
                                    allow_update_cdf_group):
    auth0id, cdfgroupid, cdf = cdf_obj
    cdf_singles = list(cdf['constant_values'].keys())
    cursor.execute(
        'SELECT COUNT(id) FROM arbiter_data.cdf_forecasts_singles WHERE '
        'cdf_forecast_group_id = UUID_TO_BIN(%s, 1)',
        cdfgroupid)
    num = cursor.fetchone()[0]
    assert num > 0
    assert num == len(cdf_singles)
    for cid in cdf_singles:
        cursor.callproc('delete_cdf_forecasts_single', (auth0id, cid))
    cursor.execute(
        'SELECT COUNT(id) FROM arbiter_data.cdf_forecasts_singles WHERE '
        'cdf_forecast_group_id = UUID_TO_BIN(%s, 1)',
        cdfgroupid)
    assert cursor.fetchone()[0] == 0


def test_delete_cdf_forecast_single_in_report_vals(
        cursor, cdf_obj, allow_delete_cdf_group,
        allow_update_cdf_group, new_report):
    auth0id, cdfgroupid, cdf = cdf_obj
    cdf_singles = list(cdf['constant_values'].keys())
    cursor.execute(
        'SELECT COUNT(id) FROM arbiter_data.cdf_forecasts_singles WHERE '
        'cdf_forecast_group_id = UUID_TO_BIN(%s, 1)',
        cdfgroupid)
    num = cursor.fetchone()[0]
    assert num > 0
    assert num == len(cdf_singles)

    rep = new_report(forecasts=[], cdf_forecasts=[], cdf_forecast_single=[
        {'id': uuid_to_bin(UUID(c))} for c in cdf_singles])
    cursor.execute(
        'SELECT count(object_id) from arbiter_data.report_values '
        'WHERE report_id = %s', rep['id'])
    num_rep_items = cursor.fetchone()[0]
    assert num_rep_items == len(cdf_singles) + 1  # obs

    for cid in cdf_singles:
        cursor.callproc('delete_cdf_forecasts_single', (auth0id, cid))
    cursor.execute(
        'SELECT COUNT(id) FROM arbiter_data.cdf_forecasts_singles WHERE '
        'cdf_forecast_group_id = UUID_TO_BIN(%s, 1)',
        cdfgroupid)
    assert cursor.fetchone()[0] == 0

    cursor.execute(
        'SELECT count(object_id) from arbiter_data.report_values '
        'WHERE report_id = %s', rep['id'])
    num_rep_items = cursor.fetchone()[0]
    assert num_rep_items == 1  # only obs left


def test_delete_cdf_forecast_single_denied_no_delete(
        cursor, cdf_obj, allow_update_cdf_group):
    auth0id, cdfgroupid, cdf = cdf_obj
    cdf_singles = list(cdf['constant_values'].keys())
    for cid in cdf_singles:
        with pytest.raises(pymysql.err.OperationalError) as e:
            cursor.callproc('delete_cdf_forecasts_single', (auth0id, cid))
        assert e.value.args[0] == 1142


def test_delete_cdf_forecast_single_denied_no_update(
        cursor, cdf_obj, allow_delete_cdf_group):
    auth0id, cdfgroupid, cdf = cdf_obj
    cdf_singles = list(cdf['constant_values'].keys())
    for cid in cdf_singles:
        with pytest.raises(pymysql.err.OperationalError) as e:
            cursor.callproc('delete_cdf_forecasts_single', (auth0id, cid))
        assert e.value.args[0] == 1142


@pytest.fixture()
def role_obj(valueset, new_role):
    org = valueset[0][0]
    user = valueset[1][0]
    auth0id = user['auth0_id']
    role = new_role(org=org)
    return auth0id, str(bin_to_uuid(role['id'])), role


@pytest.fixture()
def allow_delete_role(allow_delete):
    allow_delete('roles')


def test_delete_role(cursor, role_obj, allow_delete_role):
    auth0id, roleid, role = role_obj
    cursor.execute(
        'SELECT COUNT(id) FROM arbiter_data.roles WHERE id = %s',
        role['id'])
    assert cursor.fetchone()[0] > 0
    cursor.callproc('delete_role', (auth0id, roleid))
    cursor.execute(
        'SELECT COUNT(id) FROM arbiter_data.roles WHERE id = %s',
        role['id'])
    assert cursor.fetchone()[0] == 0


def test_delete_role_no_perm(cursor, role_obj):
    auth0id, roleid, role = role_obj
    cursor.execute(
        'SELECT COUNT(id) FROM arbiter_data.roles WHERE id = %s',
        role['id'])
    assert cursor.fetchone()[0] > 0
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('delete_role', (auth0id, roleid))
    assert e.value.args[0] == 1142


@pytest.fixture()
def permission_obj(valueset, new_permission):
    org = valueset[0][0]
    user = valueset[1][0]
    auth0id = user['auth0_id']
    permission = new_permission('read', 'forecasts', False, org=org)
    return auth0id, str(bin_to_uuid(permission['id'])), permission


@pytest.fixture()
def allow_delete_permission(allow_delete):
    allow_delete('permissions')


def test_delete_permission(cursor, permission_obj, allow_delete_permission):
    auth0id, permissionid, permission = permission_obj
    cursor.execute(
        'SELECT COUNT(id) FROM arbiter_data.permissions WHERE id = %s',
        permission['id'])
    assert cursor.fetchone()[0] > 0
    cursor.callproc('delete_permission', (auth0id, permissionid))
    cursor.execute(
        'SELECT COUNT(id) FROM arbiter_data.permissions WHERE id = %s',
        permission['id'])
    assert cursor.fetchone()[0] == 0


def test_delete_permission_no_perm(cursor, permission_obj):
    auth0id, permissionid, permission = permission_obj
    cursor.execute(
        'SELECT COUNT(id) FROM arbiter_data.permissions WHERE id = %s',
        permission['id'])
    assert cursor.fetchone()[0] > 0
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('delete_permission', (auth0id, permissionid))
    assert e.value.args[0] == 1142


@pytest.fixture()
def allow_update(cursor, new_permission, valueset):
    def do(what):
        org = valueset[0][0]
        role = valueset[2][0]
        perm = new_permission('update', what, True, org=org)
        cursor.execute(
            'INSERT INTO role_permission_mapping (role_id, permission_id)'
            ' VALUES (%s, %s)', (role['id'], perm['id']))
    return do


@pytest.fixture()
def role_user_obj(cursor, new_role, new_user, valueset):
    auth0id = valueset[1][0]['auth0_id']
    org = valueset[0][0]
    role = new_role(org=org)
    user = new_user(org=org)
    cursor.execute(
        'INSERT INTO user_role_mapping (user_id, role_id)'
        ' VALUES (%s, %s)', (user['id'], role['id']))
    return auth0id, str(bin_to_uuid(user['id'])), str(bin_to_uuid(role['id']))


@pytest.fixture()
def allow_update_users(allow_update):
    allow_update('users')


@pytest.mark.parametrize('userorg,roleorg', [
    (False, True),
    (True, True),
    pytest.param(True, False, marks=pytest.mark.xfail(strict=True)),
    pytest.param(False, False, marks=pytest.mark.xfail(strict=True)),
])
def test_remove_role_from_user(
        cursor, valueset, new_role, allow_revoke_roles,
        new_user, new_permission, roleorg, userorg):
    org = valueset[0][0]
    user = valueset[1][0]
    auth0id = user['auth0_id']
    if roleorg:
        newrole = new_role(org=org)
    else:
        newrole = new_role()
    if userorg:
        newuser = new_user(org=org)
    else:
        newuser = new_user()
    cursor.execute(
        'INSERT INTO user_role_mapping (user_id, role_id) '
        'VALUES (%s, %s)', (newuser['id'], newrole['id']))
    uid = str(bin_to_uuid(newuser['id']))
    rid = str(bin_to_uuid(newrole['id']))
    cursor.execute(
        'SELECT COUNT(role_id) FROM arbiter_data.user_role_mapping WHERE'
        ' user_id = UUID_TO_BIN(%s, 1)', uid)
    assert cursor.fetchone()[0] > 0
    cursor.callproc('remove_role_from_user', (auth0id, rid, uid))
    cursor.execute(
        'SELECT COUNT(role_id) FROM arbiter_data.user_role_mapping WHERE'
        ' user_id = UUID_TO_BIN(%s, 1)', uid)
    assert cursor.fetchone()[0] == 0


@pytest.mark.parametrize('userorg,roleorg', [
    (False, False),
    pytest.param(False, True, marks=pytest.mark.xfail(strict=True)),
    pytest.param(True, True, marks=pytest.mark.xfail(strict=True)),
    (True, False),
])
def test_remove_role_from_user_bad_org(
        cursor, valueset, new_role, allow_revoke_roles,
        new_user, new_permission, roleorg, userorg):
    org = valueset[0][0]
    user = valueset[1][0]
    role = valueset[2][0]
    auth0id = user['auth0_id']
    permission = new_permission('update', 'users', False, org=org)
    cursor.execute(
        'INSERT INTO role_permission_mapping (role_id, permission_id) '
        'VALUES (%s, %s)', (role['id'], permission['id']))
    if roleorg:
        newrole = new_role(org=org)
    else:
        newrole = new_role()
    if userorg:
        newuser = new_user(org=org)
    else:
        newuser = new_user()
    cursor.execute(
        'INSERT INTO permission_object_mapping (permission_id, object_id) '
        'VALUES (%s, %s)', (permission['id'], newuser['id']))
    cursor.execute(
        'INSERT INTO user_role_mapping (user_id, role_id) '
        'VALUES (%s, %s)', (newuser['id'], newrole['id']))
    uid = str(bin_to_uuid(newuser['id']))
    rid = str(bin_to_uuid(newrole['id']))
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('remove_role_from_user',
                        (auth0id, rid, uid))
    assert e.value.args[0] == 1142


def test_remove_role_from_user_denied(cursor, role_user_obj):
    auth0id, userid, roleid = role_user_obj
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('remove_permission_from_role',
                        (auth0id, roleid, userid))
    assert e.value.args[0] == 1142


@pytest.fixture()
def perm_role_obj(role_obj, cursor, new_permission):
    auth0id, rolestrid, role = role_obj
    perm = new_permission('read', 'permissions', False)
    cursor.execute(
        'INSERT INTO role_permission_mapping (role_id, permission_id)'
        ' VALUES (%s, %s)', (role['id'], perm['id']))
    return auth0id, rolestrid, str(bin_to_uuid(perm['id']))


@pytest.fixture()
def allow_update_roles(allow_update):
    allow_update('roles')


def test_remove_permission_from_role(cursor, perm_role_obj,
                                     allow_update_roles):
    auth0id, roleid, permid = perm_role_obj
    cursor.execute(
        'SELECT COUNT(role_id) FROM arbiter_data.role_permission_mapping WHERE'
        ' role_id = UUID_TO_BIN(%s, 1)', roleid)
    assert cursor.fetchone()[0] > 0
    cursor.callproc('remove_permission_from_role', (auth0id, permid, roleid))
    cursor.execute(
        'SELECT COUNT(role_id) FROM arbiter_data.role_permission_mapping WHERE'
        ' role_id = UUID_TO_BIN(%s, 1)', roleid)
    assert cursor.fetchone()[0] == 0


@pytest.mark.parametrize('roleorg', [
    False,
    pytest.param(True, marks=pytest.mark.xfail(strict=True))
])
def test_remove_permission_from_role_bad_org(cursor, valueset,
                                             new_role, new_permission,
                                             roleorg):
    org = valueset[0][0]
    user = valueset[1][0]
    oldrole = valueset[2][0]
    auth0id = user['auth0_id']
    if roleorg:
        role = new_role(org=org)
    else:
        role = new_role()
    permission = new_permission('read', 'forecasts', False, org=org)
    updateperm = new_permission('update', 'roles', False, org=org)
    cursor.executemany(
        'INSERT INTO role_permission_mapping (role_id, permission_id) '
        'VALUES (%s, %s)', [(oldrole['id'], updateperm['id']),
                            (role['id'], permission['id'])])
    cursor.executemany(
        'INSERT INTO permission_object_mapping (permission_id, object_id) '
        'VALUES (%s, %s)', [(updateperm['id'], role['id'])])
    roleid = str(bin_to_uuid(role['id']))
    permid = str(bin_to_uuid(permission['id']))
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('remove_permission_from_role',
                        (auth0id, permid, roleid))
    assert e.value.args[0] == 1142


def test_remove_permission_from_role_denied(cursor, perm_role_obj):
    auth0id, roleid, permid = perm_role_obj
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('remove_permission_from_role',
                        (auth0id, permid, roleid))
    assert e.value.args[0] == 1142


@pytest.fixture()
def permission_object_obj(permission_obj, cursor, new_forecast):
    auth0id, permstrid, permission = permission_obj
    fx = new_forecast()
    cursor.execute(
        'INSERT INTO permission_object_mapping (permission_id, object_id)'
        ' VALUES (%s, %s)', (permission['id'], fx['id']))
    return auth0id, permstrid, str(bin_to_uuid(fx['id']))


@pytest.fixture()
def allow_update_permission(allow_update):
    allow_update('permissions')


def test_remove_object_from_permission(cursor, permission_object_obj,
                                       allow_update_permission):
    auth0id, permid, objid = permission_object_obj
    cursor.execute(
        'SELECT BIN_TO_UUID(object_id, 1) FROM '
        'arbiter_data.permission_object_mapping '
        'WHERE permission_id = UUID_TO_BIN(%s, 1)', permid)
    count = cursor.fetchall()[0]
    assert len(count) == 1
    assert count[0] == objid
    cursor.callproc('remove_object_from_permission', (auth0id, objid, permid))
    cursor.execute(
        'SELECT count(object_id) FROM arbiter_data.permission_object_mapping'
        ' WHERE permission_id = UUID_TO_BIN(%s, 1)', permid)
    assert cursor.fetchone()[0] == 0


@pytest.mark.parametrize('permorg', [
    False,
    pytest.param(True, marks=pytest.mark.xfail(strict=True))
])
def test_remove_object_from_permission_bad_org(cursor, valueset,
                                               new_permission,
                                               new_forecast,
                                               permorg):
    org = valueset[0][0]
    user = valueset[1][0]
    role = valueset[2][0]
    auth0id = user['auth0_id']
    if permorg:
        permission = new_permission('read', 'forecasts', False, org=org)
    else:
        permission = new_permission('read', 'forecasts', False)
    updateperm = new_permission('update', 'permissions', False, org=org)
    cursor.execute(
        'INSERT INTO role_permission_mapping (role_id, permission_id) '
        'VALUES (%s, %s)', (role['id'], updateperm['id']))
    fx = new_forecast(org=org)
    cursor.executemany(
        'INSERT INTO permission_object_mapping (permission_id, object_id) '
        'VALUES (%s, %s)', [(permission['id'], fx['id']),
                            (updateperm['id'], permission['id'])])
    objid = str(bin_to_uuid(fx['id']))
    permid = str(bin_to_uuid(permission['id']))
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('remove_object_from_permission',
                        (auth0id, objid, permid))
    assert e.value.args[0] == 1142


def test_remove_object_from_permission_denied(cursor, permission_object_obj):
    auth0id, permid, objid = permission_object_obj
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('remove_object_from_permission',
                        (auth0id, objid, permid))
    assert e.value.args[0] == 1142


def test_remove_object_from_permission_applies_to_all(
        cursor, valueset, new_permission, fx_obj, allow_update_permission):
    org = valueset[0][0]
    permission = new_permission('read', 'forecasts', True, org=org)
    permuuid = permission['id']
    auth0id, fx = fx_obj
    cursor.execute('SELECT 1 FROM permission_object_mapping WHERE permission_id = %s'
                   ' AND object_id = UUID_TO_BIN(%s, 1)', (permuuid, fx))
    num = cursor.fetchone()[0]
    assert num

    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('remove_object_from_permission',
                        (auth0id, fx, str(bin_to_uuid(permuuid))))
        assert e.value.args[0] == 1142


def test_delete_report(cursor, report_obj, allow_delete_report):
    auth0id, report_id, _ = report_obj
    cursor.execute(
        'SELECT COUNT(id) FROM arbiter_data.reports '
        'WHERE id = UUID_TO_BIN(%s, 1)',
        report_id)
    assert cursor.fetchone()[0] > 0
    cursor.callproc('delete_report', (auth0id, report_id))
    cursor.execute(
        'SELECT COUNT(id) FROM arbiter_data.reports '
        'WHERE id = UUID_TO_BIN(%s, 1)',
        report_id)
    assert cursor.fetchone()[0] == 0


def test_delete_report_denied(cursor, report_obj):
    auth0id, report_id, _ = report_obj
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('delete_report', (auth0id, report_id))
    assert e.value.args[0] == 1142


def test_remove_user_facing_permissions_and_default_roles(
        cursor, new_user):
    user = new_user()
    cursor.callproc(
        'create_default_user_role',
        (user['id'], user['organization_id']))
    cursor.execute(
        ('SELECT 1 FROM arbiter_data.roles WHERE '
         'name = CONCAT("DEFAULT User role ", %s)'),
        str(bin_to_uuid(user['id'])))
    assert cursor.fetchone()[0] == 1
    cursor.execute(
        ('SELECT 1 FROM arbiter_data.permissions WHERE '
         'description = CONCAT("DEFAULT Read Self User ", %s)'),
        str(bin_to_uuid(user['id'])))
    assert cursor.fetchone()[0] == 1
    cursor.execute(
        ('SELECT 1 FROM arbiter_data.permissions WHERE '
         'description = CONCAT("DEFAULT Read User Role ", %s)'),
        str(bin_to_uuid(user['id'])))
    assert cursor.fetchone()[0] == 1

    cursor.callproc(
        'remove_user_facing_permissions_and_default_roles',
        (user['id'],))
    cursor.execute(
        ('SELECT 1 FROM arbiter_data.roles WHERE name '
         '= CONCAT("DEFAULT User role ", %s)'),
        str(bin_to_uuid(user['id'])))
    assert cursor.fetchone() is None
    cursor.execute(
        ('SELECT 1 FROM arbiter_data.permissions WHERE '
         'description = CONCAT("DEFAULT Read Self User ", %s)'),
        str(bin_to_uuid(user['id'])))
    assert cursor.fetchone() is None
    cursor.execute(
        ('SELECT 1 FROM arbiter_data.permissions WHERE '
         'description = CONCAT("DEFAULT Read User Role ", %s)'),
        str(bin_to_uuid(user['id'])))
    assert cursor.fetchone() is None


def test_delete_job(new_job, cursor):
    job = new_job()
    cursor.execute('select id from scheduled_jobs where id = %s', (job['id'],))
    out = cursor.fetchall()
    assert len(out) == 1
    assert out[0][0] == job['id']

    cursor.callproc('delete_job', (bin_to_uuid(job['id']),))
    cursor.execute('select id from scheduled_jobs where id = %s', (job['id'],))
    out = cursor.fetchall()
    assert len(out) == 0


def test_delete_job_job_dne(dictcursor):
    with pytest.raises(pymysql.err.InternalError) as e:
        dictcursor.callproc('delete_job', (str(bin_to_uuid(newuuid())),))
    assert e.value.args[0] == 1305
    assert e.value.args[1] == "Job does not exist"


def test_delete_climate_zone(cursor):
    cursor.execute(
        'SELECT COUNT(site_id) FROM site_zone_mapping WHERE '
        'zone = "Reference Region 2"')
    assert cursor.fetchone()[0] > 0
    cursor.execute(
        'DELETE FROM climate_zones WHERE name = "Reference Region 2"')
    cursor.execute(
        'SELECT COUNT(site_id) FROM site_zone_mapping WHERE '
        'zone = "Reference Region 2"')
    assert cursor.fetchone()[0] == 0
