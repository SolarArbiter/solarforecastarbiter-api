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
        assert e.errcode == 1142


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
            assert e.errcode == 1142


def test_delete_cdf_forecast_single_denied_no_update(
        cursor, cdf_obj, allow_delete_cdf_group):
    auth0id, cdfgroupid, cdf = cdf_obj
    cdf_singles = list(cdf['constant_values'].keys())
    for cid in cdf_singles:
        with pytest.raises(pymysql.err.OperationalError) as e:
            cursor.callproc('delete_cdf_forecasts_single', (auth0id, cid))
            assert e.errcode == 1142


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
        assert e.errcode == 142


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
        assert e.errcode == 142
