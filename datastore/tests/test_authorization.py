from uuid import uuid1


import pytest
import pymysql


@pytest.fixture(scope='session')
def connection():
    connection = pymysql.connect(host='127.0.0.1',
                                 port=3306,
                                 user='root',
                                 password='testpassword',
                                 database='arbiter_data',
                                 binary_prefix=True)
    # with no connection.commit(), no data should stay in db
    return connection


@pytest.fixture()
def cursor(connection):
    connection.rollback()
    return connection.cursor()


def uuid_to_bin(uuid):
    """Copy mysql UUID_TO_BIN with time swap of hi and low"""
    return uuid.bytes[6:8] + uuid.bytes[4:6] + uuid.bytes[:4] + uuid.bytes[8:]


def newuuid():
    return uuid_to_bin(uuid1())


@pytest.mark.parametrize('uuid', [uuid1() for i in range(5)])
def test_uuid_to_bin(cursor, uuid):
    cursor.execute('SELECT UUID_TO_BIN(%s, 1)', str(uuid))
    assert uuid_to_bin(uuid) == cursor.fetchone()[0]
    cursor.execute('SELECT BIN_TO_UUID(%s, 1)', uuid_to_bin(uuid))
    assert str(uuid) == cursor.fetchone()[0]


ORGANIZATIONS = [(newuuid(), f'org{i}') for i in range(2)]
USERS = [(newuuid(), f'authid{i}', org[0])
         for i, org in enumerate(ORGANIZATIONS)]
ROLES = [(newuuid(), f'role{i}', f'org{i} role', org[0])
         for i, org in enumerate(ORGANIZATIONS)]
ROLES += [(newuuid(), 'role2', 'limited read from org0',
           ORGANIZATIONS[0][0])]
USER_ROLE_MAP = [(USERS[0][0], ROLES[0][0]), (USERS[1][0], ROLES[1][0]),
                 (USERS[1][0], ROLES[2][0])]

READ_PERMISSIONS = [(newuuid(), 'Read org0 fx group 1', ORGANIZATIONS[0][0],
                     'read', 'forecasts', False),
                    (newuuid(), 'Read org0 fx group 2', ORGANIZATIONS[0][0],
                     'read', 'forecasts', False),
                    (newuuid(), 'Read org1 all fx', ORGANIZATIONS[1][0],
                     'read', 'forecasts', True),
                    (newuuid(), 'Read org0 fx 0', ORGANIZATIONS[0][0],
                     'read', 'forecasts', False)]
CREATE_PERMISSIONS = [(newuuid(), 'Create fx org0', ORGANIZATIONS[0][0],
                       'create', 'forecasts', True)]
PERMISSIONS = READ_PERMISSIONS + CREATE_PERMISSIONS
# roles, permissions, and objects must have same org! user and role do not
ROLE_PERM_MAP = [(ROLES[0][0], READ_PERMISSIONS[0][0]),
                 (ROLES[0][0], READ_PERMISSIONS[1][0]),
                 (ROLES[1][0], READ_PERMISSIONS[2][0]),
                 (ROLES[2][0], READ_PERMISSIONS[3][0]),
                 (ROLES[0][0], CREATE_PERMISSIONS[0][0]),
                 (ROLES[1][0], CREATE_PERMISSIONS[0][0])]  # not permitted
FX_OBJS = [newuuid() for i in range(8)]
PERM_OBJ_MAP = [(READ_PERMISSIONS[0][0], FX_OBJS[0]),
                (READ_PERMISSIONS[0][0], FX_OBJS[1]),
                (READ_PERMISSIONS[1][0], FX_OBJS[2]),
                (READ_PERMISSIONS[1][0], FX_OBJS[3]),
                (READ_PERMISSIONS[2][0], FX_OBJS[4]),
                (READ_PERMISSIONS[2][0], FX_OBJS[5]),
                (READ_PERMISSIONS[2][0], FX_OBJS[6]),
                (READ_PERMISSIONS[2][0], FX_OBJS[7]),
                (READ_PERMISSIONS[3][0], FX_OBJS[0])]


@pytest.fixture(scope='function')
def insertvals(cursor):
    cursor.executemany("INSERT INTO organizations (id, name) VALUES (%s, %s)",
                       ORGANIZATIONS)
    cursor.executemany(
        "INSERT INTO users (id, auth0_id, organization_id) VALUES (%s, %s, %s)", # NOQA
        USERS)
    cursor.executemany(
        "INSERT INTO roles (id, name, description, organization_id) VALUES "
        "(%s, %s, %s, %s)",
        ROLES)
    cursor.executemany(
        "INSERT INTO user_role_mapping (user_id, role_id) VALUES (%s, %s)",
        USER_ROLE_MAP)
    cursor.executemany(
        "INSERT INTO permissions (id, description, organization_id, action, "
        "object_type, applies_to_all) VALUES (%s, %s, %s, %s, %s, %s)",
        PERMISSIONS)
    cursor.executemany(
        "INSERT INTO role_permission_mapping (role_id, permission_id) "
        "VALUES (%s, %s)",
        ROLE_PERM_MAP)
    cursor.executemany(
        "INSERT INTO permission_object_mapping (permission_id, object_id) "
        "VALUES (%s, %s)", PERM_OBJ_MAP)


def _drop_selects(cond, cursor, tests):
    oid = ORGANIZATIONS[0][0]
    if 'users' in tests:
        cursor.execute(
            'SELECT COUNT(id) FROM users WHERE organization_id = %s',
            oid)
        assert cond(cursor.fetchone()[0])
    if 'roles' in tests:
        cursor.execute(
            'SELECT COUNT(id) FROM roles WHERE organization_id = %s',
            oid)
        assert cond(cursor.fetchone()[0])
    if 'urm' in tests:
        cursor.execute(
            'SELECT COUNT(user_id) FROM user_role_mapping WHERE user_id = %s',
            USERS[0][0])
        assert cond(cursor.fetchone()[0])
    if 'permissions' in tests:
        cursor.execute(
            'SELECT COUNT(id) FROM permissions WHERE organization_id = %s',
            oid)
        assert cond(cursor.fetchone()[0])
    if 'rpm' in tests:
        cursor.execute(
            'SELECT COUNT(*) FROM role_permission_mapping WHERE role_id = %s',
            ROLES[0][0])
        assert cond(cursor.fetchone()[0])
    if 'pom' in tests:
        cursor.execute(
            'SELECT COUNT(*) FROM permission_object_mapping WHERE permission_id = %s',  # NOQA
            READ_PERMISSIONS[0][0])
        assert cond(cursor.fetchone()[0])


def test_drop_org(insertvals, cursor):
    name = ORGANIZATIONS[0][1]
    tests = ['users', 'roles', 'urm', 'permissions', 'rpm', 'pom']
    _drop_selects(lambda x: x >= 1, cursor, tests)
    cursor.execute('DELETE FROM organizations WHERE name = %s', name)
    _drop_selects(lambda x: x == 0, cursor, tests)


def test_drop_user(insertvals, cursor):
    user = USERS[0][0]
    changes = ['urm']
    same = ['roles', 'permissions', 'rpm', 'pom']
    _drop_selects(lambda x: x >= 1, cursor, changes)
    _drop_selects(lambda x: x >= 1, cursor, same)
    cursor.execute('DELETE FROM users WHERE id = %s', user)
    _drop_selects(lambda x: x == 0, cursor, changes)
    _drop_selects(lambda x: x >= 1, cursor, same)


def test_drop_role(insertvals, cursor):
    role = ROLES[0][0]
    changes = ['urm', 'rpm']
    same = ['permissions', 'pom', 'users']
    _drop_selects(lambda x: x >= 1, cursor, changes)
    _drop_selects(lambda x: x >= 1, cursor, same)
    cursor.execute('DELETE FROM roles WHERE id = %s', role)
    _drop_selects(lambda x: x == 0, cursor, changes)
    _drop_selects(lambda x: x >= 1, cursor, same)


def test_drop_permissions(insertvals, cursor):
    perm = READ_PERMISSIONS[0][0]
    changes = ['rpm', 'pom']
    same = ['roles', 'users', 'urm']
    _drop_selects(lambda x: x >= 1, cursor, changes)
    _drop_selects(lambda x: x >= 1, cursor, same)
    cursor.execute('DELETE FROM permissions WHERE id = %s', perm)
    _drop_selects(lambda x: x == 0, cursor, ['pom'])
    # only one of the three permissions are dropped
    _drop_selects(lambda x: x == 2, cursor, ['rpm'])
    _drop_selects(lambda x: x >= 1, cursor, same)


@pytest.mark.parametrize('user,objs', [
    [USERS[0][1], FX_OBJS[:4]],
    [USERS[1][1], FX_OBJS[4:8] + FX_OBJS[0:1]],
])
def test_list_objects_user_can_read(cursor, insertvals, user, objs):
    cursor.callproc('list_objects_user_can_read', (user, 'forecasts'))
    out = {o[0] for o in cursor.fetchall()}
    assert out == set(objs)


@pytest.mark.parametrize('user,obj,action', [
    [USERS[0][1], FX_OBJS[0], 'read'],
    [USERS[0][1], FX_OBJS[1], 'read'],
    [USERS[0][1], FX_OBJS[2], 'read'],
    [USERS[1][1], FX_OBJS[6], 'read'],
    [USERS[1][1], FX_OBJS[7], 'read'],
    [USERS[1][1], FX_OBJS[0], 'read'],
])
def test_can_user_perform_action(insertvals, cursor, user, obj, action):
    cursor.execute('SELECT can_user_perform_action(%s, %s, %s)',
                   (user, obj, action))
    out = cursor.fetchall()
    assert len(out) == 1
    assert len(out[0]) == 1
    assert out[0][0]


@pytest.mark.parametrize('user,obj,action', [
    [USERS[0][1], FX_OBJS[0], 'create'],
    [USERS[0][1], FX_OBJS[0], 'update'],
    [USERS[0][1], FX_OBJS[0], 'delete'],
    [USERS[0][1], FX_OBJS[5], 'read'],
    [USERS[0][1], USERS[0][0], 'read'],
    [USERS[1][1], FX_OBJS[1], 'read'],
    [USERS[1][1], FX_OBJS[7], 'delete']
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
