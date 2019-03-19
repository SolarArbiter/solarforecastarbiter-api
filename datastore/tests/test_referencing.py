"""
Test that mysql references between tables are properly set to cascade delete
or restrict
"""
from uuid import uuid1


import pytest
from conftest import uuid_to_bin, ORGANIZATIONS, ROLES, USERS, READ_PERMISSIONS


@pytest.mark.parametrize('uuid', [uuid1() for i in range(5)])
def test_uuid_to_bin(cursor, uuid):
    cursor.execute('SELECT UUID_TO_BIN(%s, 1)', str(uuid))
    assert uuid_to_bin(uuid) == cursor.fetchone()[0]
    cursor.execute('SELECT BIN_TO_UUID(%s, 1)', uuid_to_bin(uuid))
    assert str(uuid) == cursor.fetchone()[0]


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
