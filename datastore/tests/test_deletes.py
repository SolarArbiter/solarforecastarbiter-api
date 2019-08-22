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
    cursor.callproc('delete_site', (auth0id, siteid))
    cursor.execute(
        'SELECT COUNT(id) FROM arbiter_data.sites WHERE id = UUID_TO_BIN(%s, 1)',  # NOQA
        siteid)
    assert cursor.fetchone()[0] == 0


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
])
def test_remove_role_from_user(
        cursor, valueset, new_role, allow_grant_revoke_roles,
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
    cursor.callproc('remove_role_from_user', (auth0id, uid, rid))
    cursor.execute(
        'SELECT COUNT(role_id) FROM arbiter_data.user_role_mapping WHERE'
        ' user_id = UUID_TO_BIN(%s, 1)', uid)
    assert cursor.fetchone()[0] == 0


@pytest.mark.parametrize('userorg,roleorg', [
    (False, False),
    (True, False),
])
def test_remove_role_from_user_bad_org(
        cursor, valueset, new_role, allow_grant_revoke_roles,
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
                        (auth0id, uid, rid))
    assert e.value.args[0] == 1142


def test_remove_role_from_user_denied(cursor, role_user_obj):
    auth0id, userid, roleid = role_user_obj
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc('remove_permission_from_role',
                        (auth0id, userid, roleid))
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
