import pytest
from conftest import USERS, FX_OBJS


@pytest.fixture()
def make_user_roles(cursor, new_organization, new_permission, new_user,
                    new_role, new_forecast):
    def fcn(action, obj_type='forecasts', onall=True):
        org = new_organization()
        user = new_user(org=org)
        role = new_role(org=org)
        cursor.execute(
            'INSERT INTO user_role_mapping (user_id, role_id) VALUES (%s, %s)',
            (user['id'], role['id']))
        perm = new_permission(action, obj_type, onall, org=org)
        cursor.execute(
            'INSERT INTO role_permission_mapping (role_id, permission_id) '
            'VALUES (%s, %s)', (role['id'], perm['id']))
        return {'org': org, 'user': user, 'role': role, 'permission': perm}
    return fcn


@pytest.mark.parametrize('user,objs', [
    [USERS[0][1], [o[0] for o in FX_OBJS[:4]]],
    [USERS[1][1], [o[0] for o in FX_OBJS[4:8] + FX_OBJS[0:1]]],
])
def test_list_objects_user_can_read(cursor, insertvals, user, objs):
    cursor.callproc('list_objects_user_can_read', (user, 'forecasts'))
    out = {o[0] for o in cursor.fetchall()}
    assert out == set(objs)


@pytest.mark.parametrize('user,obj,action', [
    [USERS[0][1], FX_OBJS[0][0], 'read'],
    [USERS[0][1], FX_OBJS[1][0], 'read'],
    [USERS[0][1], FX_OBJS[2][0], 'read'],
    [USERS[1][1], FX_OBJS[6][0], 'read'],
    [USERS[1][1], FX_OBJS[7][0], 'read'],
    [USERS[1][1], FX_OBJS[0][0], 'read'],
])
def test_can_user_perform_action(insertvals, cursor, user, obj, action):
    cursor.execute('SELECT can_user_perform_action(%s, %s, %s)',
                   (user, obj, action))
    out = cursor.fetchall()
    assert out[0][0]


@pytest.mark.parametrize('user,obj,action', [
    [USERS[0][1], FX_OBJS[0][0], 'create'],
    [USERS[0][1], FX_OBJS[0][0], 'update'],
    [USERS[0][1], FX_OBJS[0][0], 'delete'],
    [USERS[0][1], FX_OBJS[5][0], 'read'],
    [USERS[0][1], USERS[0][0], 'read'],
    [USERS[1][1], FX_OBJS[1][0], 'read'],
    [USERS[1][1], FX_OBJS[7][0], 'delete']
])
def test_can_user_perform_action_denied(insertvals, cursor, user, obj, action):
    cursor.execute('SELECT can_user_perform_action(%s, %s, %s)',
                   (user, obj, action))
    out = cursor.fetchall()
    assert not out[0][0]


def test_can_user_perform_action_multiple_permissions(
        cursor, make_user_roles, new_permission, new_forecast):
    """
    Test that can_user_perform_action works when one objet is assigned
    to duplicate permissions
    """
    info = make_user_roles('read', 'forecasts', False)
    org = info['org']
    fx = new_forecast(org=org)
    perm = new_permission('read', 'forecasts', False, org=org)
    cursor.execute(
        'INSERT INTO role_permission_mapping (role_id, permission_id) VALUES '
        '(%s, %s)', (info['role']['id'], perm['id']))
    cursor.executemany(
        'INSERT INTO permission_object_mapping (permission_id, object_id)'
        ' VALUES (%s, %s)', [(perm['id'], fx['id']),
                             (info['permission']['id'], fx['id'])])
    cursor.execute('SELECT can_user_perform_action(%s, %s, %s)',
                   (info['user']['auth0_id'], fx['id'], 'read'))
    assert cursor.fetchone()[0]


def test_user_can_create(insertvals, cursor):
    cursor.execute('SELECT user_can_create(%s, %s)',
                   (USERS[0][1], 'forecasts'))
    out = cursor.fetchall()
    assert out[0][0]


def test_user_can_create_diff_org(insertvals, cursor):
    cursor.execute('SELECT user_can_create(%s, %s)',
                   (USERS[1][1], 'forecasts'))
    out = cursor.fetchall()
    assert not out[0][0]


@pytest.mark.parametrize('user', [USERS[0][1], USERS[1][1]])
@pytest.mark.parametrize('type_', [
    'roles', 'users', 'permissions', 'observations', 'mappings',
    'sites', 'aggregates'])
def test_user_can_create_other_objs_denied(insertvals, cursor, user, type_):
    cursor.execute('SELECT user_can_create(%s, %s)',
                   (user, type_))
    out = cursor.fetchall()
    assert not out[0][0]


def test_user_can_create_multiple_permissions(cursor, make_user_roles,
                                              new_role, new_permission):
    """Make sure user_can_create works when duplicated create permission"""
    info = make_user_roles('create', 'forecasts')
    org = info['org']
    user = info['user']
    cursor.execute(
        'SELECT user_can_create(%s, %s)',
        (user['auth0_id'], 'forecasts'))
    assert cursor.fetchone()[0]
    role = new_role(org=org, i=99)
    perm = new_permission('create', 'forecasts', True, org=org)
    cursor.execute(
        'INSERT INTO role_permission_mapping (role_id, permission_id) '
        'VALUES (%s, %s)', (role['id'], perm['id']))
    cursor.execute(
        'INSERT INTO user_role_mapping (user_id, role_id) VALUES (%s, %s)',
        (user['id'], role['id']))
    cursor.execute(
        'SELECT user_can_create(%s, %s)',
        (user['auth0_id'], 'forecasts'))
    assert cursor.fetchone()[0]
