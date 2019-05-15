from random import shuffle


import pytest


from conftest import bin_to_uuid


@pytest.fixture()
def readall(cursor, new_organization, new_user, new_role, new_permission,
            new_site, new_forecast, new_observation, new_cdf_forecast):
    # remove test data
    cursor.execute('DELETE FROM organizations')

    def make():
        org = new_organization()
        user = new_user(org=org)
        role = new_role(org=org)
        cursor.execute(
            'INSERT INTO user_role_mapping (user_id, role_id) VALUES (%s, %s)',
            (user['id'], role['id']))
        items = ['users', 'roles', 'permissions',
                 'forecasts', 'observations', 'sites',
                 'cdf_forecasts']
        shuffle(items)
        perms = [new_permission('read', obj, True, org=org)
                 for obj in items]

        cursor.executemany(
            'INSERT INTO role_permission_mapping (role_id, permission_id)'
            ' VALUES (%s, %s)', [(role['id'], perm['id']) for perm in perms])
        sites = [new_site(org=org) for _ in range(2)]
        fx = [new_forecast(site=site) for site in sites for _ in range(2)]
        obs = [new_observation(site=site) for site in sites for _ in range(2)]
        cdf = [new_cdf_forecast(site=site) for site in sites for _ in range(2)]
        return user, role, perms, sites, fx, obs, cdf
    return make


@pytest.fixture()
def twosets(readall):
    user, role, perms, sites, fx, obs, cdf = readall()
    dummy = readall()
    return user, role, perms, sites, fx, obs, cdf, dummy


@pytest.mark.parametrize('type_', ['permissions', 'sites', 'forecasts',
                                   'observations'])
def test_items_present(cursor, twosets, type_):
    cursor.execute(f'SELECT DISTINCT(organization_id) FROM {type_}')
    assert len(cursor.fetchall()) == 2


def test_list_users(dictcursor, twosets):
    user = twosets[0]
    authid = twosets[0]['auth0_id']
    dictcursor.callproc('list_users', (authid,))
    res = dictcursor.fetchall()[0]
    del res['created_at']
    del res['modified_at']
    del res['organization']
    del user['organization_id']
    user['user_id'] = str(bin_to_uuid(user.pop('id')))
    assert res == user


def test_list_roles(dictcursor, twosets):
    authid = twosets[0]['auth0_id']
    role = twosets[1]
    dictcursor.callproc('list_roles', (authid,))
    res = dictcursor.fetchall()[0]
    del res['created_at']
    del res['modified_at']
    del res['organization']
    del role['organization_id']
    role['role_id'] = str(bin_to_uuid(role.pop('id')))
    assert res == role


def test_list_permissions(dictcursor, twosets):
    authid = twosets[0]['auth0_id']
    perms = twosets[2]
    dictcursor.callproc('list_permissions', (authid,))
    res = dictcursor.fetchall()
    for r in res:
        del r['created_at']
        del r['organization']
    for p in perms:
        p['permission_id'] = str(bin_to_uuid(p.pop('id')))
        del p['organization_id']
    assert res == perms


def test_list_sites(dictcursor, twosets):
    authid = twosets[0]['auth0_id']
    sites = twosets[3]
    dictcursor.callproc('list_sites', (authid,))
    res = dictcursor.fetchall()
    assert [str(bin_to_uuid(site['id'])) for site in sites] == [
        r['site_id'] for r in res]
    assert (
        set(res[0].keys()) - set(
            ('created_at', 'modified_at', 'provider', 'site_id')) ==
        set(sites[0].keys()) - set(('organization_id', 'id')))


def test_list_forecasts(dictcursor, twosets):
    authid = twosets[0]['auth0_id']
    fxs = twosets[4]
    dictcursor.callproc('list_forecasts', (authid,))
    res = dictcursor.fetchall()
    assert ([str(bin_to_uuid(fx['id'])) for fx in fxs] ==
            [r['forecast_id'] for r in res])
    assert (
        set(res[0].keys()) - set(
            ('created_at', 'modified_at', 'provider', 'forecast_id'))
        == set(fxs[0].keys()) - set(('organization_id', 'id')))


def test_list_observations(dictcursor, twosets):
    authid = twosets[0]['auth0_id']
    obs = twosets[5]
    dictcursor.callproc('list_observations', (authid,))
    res = dictcursor.fetchall()
    assert ([str(bin_to_uuid(ob['id'])) for ob in obs] ==
            [r['observation_id'] for r in res])
    assert (
        set(res[0].keys()) - set(
            ('created_at', 'modified_at', 'provider', 'observation_id')) ==
        set(obs[0].keys()) - set(('organization_id', 'id')))


def test_list_cdf_forecast_groups(dictcursor, twosets):
    authid = twosets[0]['auth0_id']
    cdf = twosets[6]
    dictcursor.callproc('list_cdf_forecasts_groups', (authid,))
    res = dictcursor.fetchall()
    assert ([str(bin_to_uuid(fx['id'])) for fx in cdf] ==
            [r['forecast_id'] for r in res])
    assert (
        set(res[0].keys()) - set(
            ('created_at', 'modified_at', 'provider', 'forecast_id'))
        == set(cdf[0].keys()) - set(('organization_id', 'id')))


def test_list_cdf_forecast_groups_no_singles(dictcursor, twosets):
    authid = twosets[0]['auth0_id']
    cdf = twosets[6]
    dictcursor.execute('DELETE FROM cdf_forecasts_singles')
    dictcursor.callproc('list_cdf_forecasts_groups', (authid,))
    res = dictcursor.fetchall()
    assert ([str(bin_to_uuid(fx['id'])) for fx in cdf] ==
            [r['forecast_id'] for r in res])
    assert (
        set(res[0].keys()) - set(
            ('created_at', 'modified_at', 'provider', 'forecast_id',))
        == set(cdf[0].keys()) - set(('organization_id', 'id')))


def test_list_cdf_forecast_singles(dictcursor, twosets):
    authid = twosets[0]['auth0_id']
    cdf = twosets[6]
    dictcursor.callproc('list_cdf_forecasts_singles', (authid,))
    res = dictcursor.fetchall()
    input_ids = [b for a in cdf for b in list(a['constant_values'].keys())]
    assert input_ids == [r['forecast_id'] for r in res]
    assert (
        set(res[0].keys()) - set(
            ('created_at', 'modified_at', 'provider', 'forecast_id',
             'constant_value', 'parent'))
        == set(cdf[0].keys()) - set(('organization_id', 'id',
                                     'constant_values')))
