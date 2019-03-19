import pytest
from conftest import USERS, FX_OBJS


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
    assert len(out) == 1
    assert len(out[0]) == 1
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
    assert len(out) == 1
    assert len(out[0]) == 1
    assert not out[0][0]


def test_user_can_create(insertvals, cursor):
    cursor.execute('SELECT user_can_create(%s, %s)',
                   (USERS[0][1], 'forecasts'))
    out = cursor.fetchall()
    assert len(out) == 1
    assert len(out[0]) == 1
    assert out[0][0]


def test_user_can_create_diff_org(insertvals, cursor):
    cursor.execute('SELECT user_can_create(%s, %s)',
                   (USERS[1][1], 'forecasts'))
    out = cursor.fetchall()
    assert len(out) == 1
    assert len(out[0]) == 1
    assert not out[0][0]


@pytest.mark.parametrize('user', [USERS[0][1], USERS[1][1]])
@pytest.mark.parametrize('type_', [
    'roles', 'users', 'permissions', 'observations', 'mappings',
    'sites', 'aggregates'])
def test_user_can_create_other_objs(insertvals, cursor, user, type_):
    cursor.execute('SELECT user_can_create(%s, %s)',
                   (user, type_))
    out = cursor.fetchall()
    assert len(out) == 1
    assert len(out[0]) == 1
    assert not out[0][0]
