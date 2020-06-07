import json
import pytest


def test_get_default_user_role(valueset, default_user_role, cursor):
    user = valueset[1][0]
    cursor.execute('SELECT get_default_user_role(%s)', (user['auth0_id'],))
    assert cursor.fetchone()[0] is not None


def test_get_default_user_role_no_default(valueset, cursor):
    user = valueset[1][0]
    cursor.execute('SELECT get_default_user_role(%s)', (user['auth0_id'],))
    assert cursor.fetchone()[0] is None


def test_get_default_user_role_removed(valueset, cursor, default_user_role):
    user = valueset[1][0]
    cursor.execute('SELECT get_default_user_role(%s)', (user['auth0_id'],))
    assert cursor.fetchone()[0] is not None
    cursor.callproc('remove_user_facing_permissions_and_default_roles',
                    (user['id'], ))
    cursor.execute('SELECT get_default_user_role(%s)', (user['auth0_id'],))
    assert cursor.fetchone()[0] is None


def test_get_default_user_role_org_change(valueset, cursor, default_user_role,
                                          new_organization):
    user = valueset[1][0]
    cursor.execute('SELECT get_default_user_role(%s)', (user['auth0_id'],))
    prevroleid = cursor.fetchone()[0]
    assert prevroleid is not None
    org = new_organization()
    cursor.execute('UPDATE users SET organization_id = %s WHERE id = %s',
                   (org['id'], user['id']))
    cursor.execute('SELECT get_default_user_role(%s)', (user['auth0_id'],))
    newroleid = cursor.fetchone()[0]
    assert newroleid is not None
    assert newroleid != prevroleid


@pytest.mark.parametrize('action', [
    'read', 'update', 'delete', 'read_values', 'write_values', 'delete_values',
    'grant', 'revoke'  # may not make sense for most types but still allowed
])
def test_add_object_permission_to_default_user_role(
        valueset, cursor, default_user_role, action, getfcn):
    newfunc, object_type = getfcn
    org = valueset[0][0]
    user = valueset[1][0]
    obj = newfunc(org=org)
    cursor.callproc('add_object_permission_to_default_user_role',
                    (user['auth0_id'], obj['organization_id'], obj['id'],
                     object_type, action))
    cursor.execute('SELECT can_user_perform_action(%s, %s, %s)',
                   (user['auth0_id'], obj['id'], action))
    assert cursor.fetchone()[0]


@pytest.mark.parametrize('action', [
    'read', 'update', 'delete', 'read_values', 'write_values', 'delete_values',
    'grant', 'revoke'
])
def test_add_object_permission_to_default_user_role_diff_org(
        valueset, cursor, default_user_role, action, getfcn,
        new_organization):
    newfunc, object_type = getfcn
    user = valueset[1][0]
    obj = newfunc()
    cursor.callproc('add_object_permission_to_default_user_role',
                    (user['auth0_id'], obj['organization_id'], obj['id'],
                     object_type, action))
    cursor.execute('SELECT can_user_perform_action(%s, %s, %s)',
                   (user['auth0_id'], obj['id'], action))
    assert not cursor.fetchone()[0]


@pytest.mark.parametrize('action', [
    'read', 'update', 'delete', 'read_values', 'write_values', 'delete_values',
    'grant', 'revoke'
])
def test_add_object_permission_to_default_user_role_no_default(
        valueset, cursor, action, getfcn):
    newfunc, object_type = getfcn
    user = valueset[1][0]
    org = valueset[0][0]
    obj = newfunc(org=org)
    cursor.callproc('add_object_permission_to_default_user_role',
                    (user['auth0_id'], obj['organization_id'], obj['id'],
                     object_type, action))
    cursor.execute('SELECT can_user_perform_action(%s, %s, %s)',
                   (user['auth0_id'], obj['id'], action))
    assert not cursor.fetchone()[0]


def test_add_object_permission_to_default_user_role_create(
        valueset, cursor, getfcn):
    action = 'create'
    newfunc, object_type = getfcn
    user = valueset[1][0]
    org = valueset[0][0]
    obj = newfunc(org=org)
    cursor.callproc('add_object_permission_to_default_user_role',
                    (user['auth0_id'], obj['organization_id'], obj['id'],
                     object_type, action))
    cursor.execute('SELECT can_user_perform_action(%s, %s, %s)',
                   (user['auth0_id'], obj['id'], action))
    assert not cursor.fetchone()[0]


@pytest.mark.parametrize('lat,lon,zones', [
    (0, 0, set()),
    (32, -110, {'Reference Region 3', 'USA'}),
    (42, -110, {'Reference Region 2', 'USA'}),
    (19.6, -155.9, {'Reference Region 9'}),
    (25, -119, {'USA'}),
])
def test_find_climate_zones(lat, lon, zones, cursor, new_climzone):
    new_climzone()
    cursor.callproc('find_climate_zones', (lat, lon))
    assert set(json.loads(cursor.fetchone()[0])) == zones
