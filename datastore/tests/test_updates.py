from collections import namedtuple


import pymysql
import pytest


from conftest import bin_to_uuid


@pytest.fixture()
def insertuser(cursor, new_permission, valueset, new_user):
    AllMeta = namedtuple('AllMeta', ['user', 'site', 'fx', 'obs', 'org',
                                     'role', 'cdf', 'auth0id', 'agg_fx',
                                     'agg_cdf'])
    org = valueset[0][0]
    user = valueset[1][0]
    role = valueset[2][0]
    site = valueset[3][0]
    fx = valueset[5][0]
    agg_fx = valueset[5][-1]
    obs = valueset[6][0]
    cdf = valueset[7][0]
    agg_cdf = valueset[7][2]

    for thing in (user, site, fx, obs, cdf, agg_fx, agg_cdf):
        thing['strid'] = str(bin_to_uuid(thing['id']))
    cursor.execute(
        "DELETE FROM permissions WHERE action = 'update'")
    return AllMeta(user, site, fx, obs, org, role, cdf,
                   user['auth0_id'], agg_fx, agg_cdf)


@pytest.fixture()
def allow_update_observations(new_permission, cursor, insertuser):
    perm = new_permission('update', 'observations', True,
                          org=insertuser.org)
    cursor.execute(
        'INSERT INTO role_permission_mapping (role_id, permission_id) '
        'VALUES (%s, %s)', (insertuser.role['id'], perm['id']))


@pytest.mark.parametrize('name', [
    'New NAME', None, pytest.param(0, marks=pytest.mark.xfail(strict=True))])
@pytest.mark.parametrize('uncertainty', [
    1.9, None, pytest.param('a', marks=pytest.mark.xfail(strict=True))])
@pytest.mark.parametrize('extra_parameters', [
    'New extra', None, pytest.param(0, marks=pytest.mark.xfail(strict=True))])
def test_update_observation(dictcursor, insertuser, allow_update_observations,
                            name, uncertainty, extra_parameters):
    dictcursor.execute('SELECT * from arbiter_data.observations WHERE id = %s',
                       insertuser.obs['id'])
    expected = dictcursor.fetchall()[0]
    assert expected['name'] != name
    assert expected['uncertainty'] != uncertainty
    assert expected['extra_parameters'] != extra_parameters
    dictcursor.callproc(
        'update_observation', (
            insertuser.auth0id, insertuser.obs['strid'],
            name, uncertainty, extra_parameters
        ))
    dictcursor.execute('SELECT * from arbiter_data.observations WHERE id = %s',
                       insertuser.obs['id'])
    new = dictcursor.fetchall()[0]
    if name is not None:
        expected['name'] = name
    if uncertainty is not None:
        expected['uncertainty'] = uncertainty
    if extra_parameters is not None:
        expected['extra_parameters'] = extra_parameters
    assert new.pop('modified_at') >= expected.pop('modified_at')
    assert new == expected


def test_update_observation_denied(dictcursor, insertuser):
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc(
            'update_observation', (
                insertuser.auth0id, insertuser.obs['strid'],
                'new name', 0, 'new exxtra'
            ))
    assert e.value.args[0] == 1142
