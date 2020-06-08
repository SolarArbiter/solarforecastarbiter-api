import json
from random import shuffle


import pytest


from conftest import bin_to_uuid


@pytest.fixture()
def readall(cursor, new_organization, new_user, new_role, new_permission,
            new_site, new_forecast, new_observation, new_cdf_forecast,
            new_report, new_aggregate):
    # remove test data
    # temporarily remove fx, obs and cdf to avoid foreign key constraint
    cursor.execute('DELETE FROM forecasts')
    cursor.execute('DELETE FROM observations')
    cursor.execute('DELETE FROM cdf_forecasts_groups')
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
                 'cdf_forecasts', 'reports', 'aggregates']
        shuffle(items)
        perms = [new_permission('read', obj, True, org=org)
                 for obj in items]

        cursor.executemany(
            'INSERT INTO role_permission_mapping (role_id, permission_id)'
            ' VALUES (%s, %s)', [(role['id'], perm['id']) for perm in perms])
        sites = [new_site(org=org) for _ in range(2)]
        obs = [new_observation(site=site) for site in sites for _ in range(2)]
        aggregates = [new_aggregate(obs_list=obs[i:i + 2]) for i in range(2)]
        fx = [new_forecast(site=sites[0]),
              new_forecast(aggregate=aggregates[0])]
        cdf = [new_cdf_forecast(site=sites[1]),
               new_cdf_forecast(aggregate=aggregates[1])]
        reports = [new_report(org, obs[i], [fx[i]], [cdf[i]])
                   for i in range(2)]
        return user, role, perms, sites, fx, obs, cdf, reports, org, aggregates
    return make


@pytest.fixture()
def twosets(readall):
    user, role, perms, sites, fx, obs, cdf, reports, org, aggs = readall()
    dummy = readall()
    return user, role, perms, sites, fx, obs, cdf, reports, org, aggs, dummy


@pytest.mark.parametrize('type_', ['permissions', 'sites', 'forecasts',
                                   'observations', 'reports', 'aggregates'])
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
    del res['roles']
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
    del res['permissions']
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
        del r['objects']
    for p in perms:
        p['permission_id'] = str(bin_to_uuid(p.pop('id')))
        del p['organization_id']
    assert res == perms


def test_list_sites(dictcursor, twosets, new_site):
    authid = twosets[0]['auth0_id']
    sites = twosets[3]
    org = twosets[-3]
    for site in sites: site['climate_zones'] = '[]'  # NOQA
    sites += [new_site(org=org, latitude=32, longitude=-110)]
    sites[-1]['climate_zone'] = '["Reference Region 3"]'
    dictcursor.callproc('list_sites', (authid,))
    res = dictcursor.fetchall()
    assert [str(bin_to_uuid(site['id'])) for site in sites] == [
        r['site_id'] for r in res]
    assert (
        set(res[0].keys()) - set(
            ('created_at', 'modified_at', 'provider', 'site_id')) ==
        set(sites[0].keys()) - set(('organization_id', 'id')))


def test_list_sites_in_zone(dictcursor, twosets, new_site):
    authid = twosets[0]['auth0_id']
    org = twosets[-3]
    new_site(org=org, latitude=42, longitude=-103)
    sites = [new_site(org=org, latitude=32, longitude=-110),
             new_site(org=org, latitude=33, longitude=-115)]
    for site in sites:  site['climate_zones'] = '["Reference Region 3"]'  # NOQA
    dictcursor.callproc('list_sites_in_zone', (authid, 'Reference Region 3'))
    res = dictcursor.fetchall()
    assert [str(bin_to_uuid(site['id'])) for site in sites] == [
        r['site_id'] for r in res]
    assert (
        set(res[0].keys()) - set(
            ('created_at', 'modified_at', 'provider', 'site_id')) ==
        set(sites[0].keys()) - set(('organization_id', 'id')))


def test_list_climate_zones(dictcursor, new_climzone):
    zones = {f'Reference Region {i}' for i in range(1, 10)}
    new_climzone('other')
    zones.add('other')
    dictcursor.callproc('list_climate_zones')
    assert {r['name'] for r in dictcursor.fetchall()} == zones


def test_list_forecasts(dictcursor, twosets):
    authid = twosets[0]['auth0_id']
    fxs = twosets[4]
    dictcursor.callproc('list_forecasts', (authid,))
    res = dictcursor.fetchall()
    assert res[0]['site_id'] is not None
    assert res[0]['aggregate_id'] is None
    assert res[1]['site_id'] is None
    assert res[1]['aggregate_id'] is not None
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
    assert res[0]['site_id'] is not None
    assert res[0]['aggregate_id'] is None
    assert res[1]['site_id'] is None
    assert res[1]['aggregate_id'] is not None
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


def test_list_reports(dictcursor, twosets):
    authid = twosets[0]['auth0_id']
    reports = twosets[7]
    dictcursor.callproc('list_reports', (authid,))
    res = dictcursor.fetchall()
    assert ([str(bin_to_uuid(rep['id'])) for rep in reports] ==
            [r['report_id'] for r in res])
    assert (
        set(res[0].keys()) - set(
            ('created_at', 'modified_at', 'provider', 'report_id'))
        == ((set(reports[0].keys()) | set(('status',))) -
            set(('organization_id', 'id'))))


def test_list_aggregates(dictcursor, twosets):
    authid = twosets[0]['auth0_id']
    agg = twosets[9]
    dictcursor.callproc('list_aggregates', (authid, ))
    res = dictcursor.fetchall()
    assert ([str(bin_to_uuid(a['id'])) for a in agg] ==
            [r['aggregate_id'] for r in res])
    assert (
        set(res[0].keys()) - set(
            ('created_at', 'modified_at', 'provider', 'aggregate_id',
             'observations'))
        == set(agg[0].keys()) - set(('organization_id', 'id', 'obs_list')))
    assert ([str(bin_to_uuid(o['id'])) for a in agg for o in a['obs_list']] ==
            [b['observation_id'] for r in res for b in
             json.loads(r['observations'])])


def test_list_jobs(dictcursor, new_job, new_user):
    user = new_user()
    job0 = new_job(user, 'job0')
    job1 = new_job(user, 'job1')
    job2 = new_job(user, 'job2')
    job3 = new_job(None, 'job3')

    dictcursor.callproc('list_jobs')
    out = dictcursor.fetchall()
    keys = {'id', 'organization_id', 'organization_name',
            'user_id', 'name',
            'job_type', 'parameters', 'schedule',
            'version', 'created_at', 'modified_at'}
    assert keys == set(out[0].keys())

    out_job_ids = {o['id'] for o in out}
    for j in (job0, job1, job2, job3):
        assert bin_to_uuid(j['id']) in out_job_ids
