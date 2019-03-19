"""
Test that mysql references between tables are properly set to cascade delete
or restrict
"""
import pytest
import pymysql
from conftest import (ORGANIZATIONS, ROLES, USERS, PERMISSIONS, SITES,
                      FX_OBJS, OBS_OBJS)


def check_table_for_org(cursor, oid, table):
    if oid is not None:
        cursor.execute(
            f'SELECT COUNT(*) FROM {table} WHERE organization_id = %s',
            oid)
    else:
        cursor.execute(f'SELECT COUNT(*) from {table}')
    return cursor.fetchone()[0]


@pytest.mark.parametrize('test', [
    'users', 'roles', 'permissions', 'sites',
    'forecasts'])
def test_drop_org(insertvals, cursor, test):
    oid, name = ORGANIZATIONS[0][:2]
    assert check_table_for_org(cursor, oid, test) > 0
    cursor.execute('DELETE FROM organizations WHERE name = %s', name)
    assert check_table_for_org(cursor, oid, test) == 0


def test_drop_user(insertvals, cursor):
    """Check that the user is remove from the user_role_mapping table"""
    user = USERS[0][0]
    cursor.execute('SELECT COUNT(*) FROM user_role_mapping WHERE user_id = %s',
                   user)
    before = cursor.fetchone()[0]
    assert before > 0
    cursor.execute('DELETE FROM users WHERE id = %s', user)
    cursor.execute('SELECT COUNT(*) FROM user_role_mapping WHERE user_id = %s',
                   user)
    after = cursor.fetchone()[0]
    assert after == 0


@pytest.mark.parametrize('test', [
    'roles', 'permissions', 'sites', 'observations',
    'forecasts', 'aggregates', 'organizations',
    'permission_object_mapping', 'role_permission_mapping'])
def test_drop_user_same_count(insertvals, cursor, test):
    """Check that tables remain unchanged when removing a user"""
    user = USERS[0][0]
    before = check_table_for_org(cursor, None, test)
    cursor.execute('DELETE FROM users where id = %s', user)
    after = check_table_for_org(cursor, None, test)
    assert before == after


def test_drop_role(insertvals, cursor):
    """
    Test that the role is remove from the role_permission_mapping
    and user_permission_mapping tables when dropped
    """
    role = ROLES[0][0]
    cursor.execute('SELECT COUNT(*) FROM user_role_mapping WHERE role_id = %s',
                   role)
    before_urm = cursor.fetchone()[0]
    assert before_urm > 0
    cursor.execute(
        'SELECT COUNT(*) FROM role_permission_mapping WHERE role_id = %s',
        role)
    before_rpm = cursor.fetchone()[0]
    assert before_rpm > 0
    cursor.execute('DELETE FROM roles WHERE id = %s', role)
    cursor.execute('SELECT COUNT(*) FROM user_role_mapping WHERE role_id = %s',
                   role)
    after_urm = cursor.fetchone()[0]
    assert after_urm == 0
    cursor.execute(
        'SELECT COUNT(*) FROM role_permission_mapping WHERE role_id = %s',
        role)
    after_rpm = cursor.fetchone()[0]
    assert after_rpm == 0


@pytest.mark.parametrize('test', [
    'users', 'permissions', 'sites', 'observations',
    'forecasts', 'aggregates', 'organizations',
    'permission_object_mapping'])
def test_drop_role_same_count(insertvals, cursor, test):
    """Check that tables remain unchanged when removing a role"""
    role = ROLES[0][0]
    before = check_table_for_org(cursor, None, test)
    cursor.execute('DELETE FROM roles WHERE id = %s', role)
    after = check_table_for_org(cursor, None, test)
    assert before == after


def test_drop_permissions(insertvals, cursor):
    """
    Test that dropping a permission also removes it from
    role_permission_mapping and permission_object_mapping
    """
    perm = PERMISSIONS[0][0]
    cursor.execute(
        'SELECT COUNT(*) FROM role_permission_mapping WHERE permission_id = %s',  # NOQA
        perm)
    before_rpm = cursor.fetchone()[0]
    assert before_rpm > 0
    cursor.execute(
        'SELECT COUNT(*) FROM permission_object_mapping WHERE permission_id = %s',  # NOQA
        perm)
    before_pom = cursor.fetchone()[0]
    assert before_pom > 0
    cursor.execute('DELETE FROM permissions WHERE id = %s', perm)
    cursor.execute(
        'SELECT COUNT(*) FROM role_permission_mapping WHERE permission_id = %s',  # NOQA
        perm)
    after_rpm = cursor.fetchone()[0]
    assert after_rpm == 0
    cursor.execute(
        'SELECT COUNT(*) FROM permission_object_mapping WHERE permission_id = %s',  # NOQA
        perm)
    after_pom = cursor.fetchone()[0]
    assert after_pom == 0


@pytest.mark.parametrize('test', [
    'users', 'roles', 'sites', 'observations',
    'forecasts', 'aggregates', 'organizations',
    'user_role_mapping'])
def test_drop_permission_same_count(insertvals, cursor, test):
    """Check that tables remain unchanged when removing a permission"""
    permission = PERMISSIONS[0][0]
    before = check_table_for_org(cursor, None, test)
    cursor.execute('DELETE FROM permissions WHERE id = %s', permission)
    after = check_table_for_org(cursor, None, test)
    assert before == after


@pytest.mark.parametrize('delt', [
    None, 'forecasts', 'observations'
])
def test_drop_site_fail(insertvals, cursor, delt):
    """
    Test that a site cannot be dropped before forecasts or observations
    that reference it."""
    site = SITES[0][0]
    if delt is not None:
        cursor.execute(f'DELETE FROM {delt} WHERE site_id = %s', site)
    with pytest.raises(pymysql.err.IntegrityError):
        cursor.execute('DELETE FROM sites WHERE id = %s', site)


def test_drop_site(insertvals, cursor):
    """
    Test that a site can be deleted with no forecast/observations
    """
    site = SITES[0][0]
    cursor.execute('DELETE FROM forecasts WHERE site_id = %s', site)
    cursor.execute('DELETE FROM observations WHERE site_id = %s', site)
    cursor.execute('DELETE FROM sites WHERE id = %s', site)


@pytest.mark.parametrize('test', [
    'users', 'roles', 'sites', 'observations',
    'permissions', 'aggregates', 'organizations',
    'user_role_mapping'])
def test_drop_forecast(insertvals, cursor, test):
    """Check that tables remain unchanged when removing a forecast"""
    forecast = FX_OBJS[0][0]
    before = check_table_for_org(cursor, None, test)
    cursor.execute('DELETE FROM forecasts WHERE id = %s', forecast)
    after = check_table_for_org(cursor, None, test)
    assert before == after


@pytest.mark.parametrize('test', [
    'users', 'roles', 'sites', 'forecasts',
    'permissions', 'aggregates', 'organizations',
    'user_role_mapping'])
def test_drop_observation(insertvals, cursor, test):
    """Check that tables remain unchanged when removing a observation"""
    observation = OBS_OBJS[0][0]
    before = check_table_for_org(cursor, None, test)
    cursor.execute('DELETE FROM observations WHERE id = %s', observation)
    after = check_table_for_org(cursor, None, test)
    assert before == after
