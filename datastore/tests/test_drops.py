"""
Test that mysql references between tables are properly set to cascade delete
or restrict
"""
import json
import pytest
import pymysql
from uuid import UUID

from conftest import uuid_to_bin


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
    'forecasts', 'cdf_forecasts_groups', 'reports',
    'aggregates'])
def test_drop_org(cursor, valueset_org, test):
    oid = valueset_org['id']
    name = valueset_org['name']
    assert check_table_for_org(cursor, oid, test) > 0
    cursor.execute('DELETE FROM organizations WHERE name = %s', name)
    assert check_table_for_org(cursor, oid, test) == 0


@pytest.mark.skip(reason="Foreign Key constraint does not currently "
                         "work with data sharing")
@pytest.mark.parametrize('test', [
    'users', 'roles', 'permissions', 'sites',
    'forecasts', 'permission_object_mapping',
    'user_role_mapping', 'role_permission_mapping',
    'cdf_forecasts_groups', 'reports', 'aggregates'])
def test_drop_all_orgs_all_tables(cursor, valueset_org, test):
    cursor.execute('DELETE FROM organizations')
    check_table_for_org(cursor, None, test)


def test_drop_user(cursor, valueset_user):
    """Check that the user is remove from the user_role_mapping table"""
    user = valueset_user['id']
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
    'cdf_forecasts_groups', 'reports',
    'permission_object_mapping', 'role_permission_mapping'])
def test_drop_user_same_count(cursor, valueset_user, test):
    """Check that tables remain unchanged when removing a user"""
    user = valueset_user['id']
    before = check_table_for_org(cursor, None, test)
    cursor.execute('DELETE FROM users where id = %s', user)
    after = check_table_for_org(cursor, None, test)
    assert before == after


def test_drop_role(cursor, valueset_role):
    """
    Test that the role is remove from the role_permission_mapping
    and user_permission_mapping tables when dropped
    """
    role = valueset_role['id']
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
    'cdf_forecasts_groups', 'reports',
    'permission_object_mapping'])
def test_drop_role_same_count(cursor, test, valueset_role):
    """Check that tables remain unchanged when removing a role"""
    role = valueset_role['id']
    before = check_table_for_org(cursor, None, test)
    cursor.execute('DELETE FROM roles WHERE id = %s', role)
    after = check_table_for_org(cursor, None, test)
    assert before == after


def test_drop_permissions(cursor, valueset_permission):
    """
    Test that dropping a permission also removes it from
    role_permission_mapping and permission_object_mapping
    """
    perm = valueset_permission['id']
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
    'cdf_forecasts_groups', 'reports',
    'user_role_mapping'])
def test_drop_permission_same_count(cursor, test, valueset_permission):
    """Check that tables remain unchanged when removing a permission"""
    perm = valueset_permission['id']
    before = check_table_for_org(cursor, None, test)
    cursor.execute('DELETE FROM permissions WHERE id = %s', perm)
    after = check_table_for_org(cursor, None, test)
    assert before == after


@pytest.mark.parametrize('delt', [
    None, 'forecasts', 'observations', 'cdf_forecasts_groups'
])
def test_drop_site_fail(cursor, delt, valueset_site):
    """
    Test that a site cannot be dropped before forecasts or observations
    that reference it."""
    site = valueset_site['id']
    if delt is not None:
        cursor.execute(f'DELETE FROM {delt} WHERE site_id = %s', site)
    with pytest.raises(pymysql.err.IntegrityError):
        cursor.execute('DELETE FROM sites WHERE id = %s', site)


def test_drop_site(cursor, valueset_site):
    """
    Test that a site can be deleted with no forecast/observations
    """
    site = valueset_site['id']
    cursor.execute('DELETE FROM forecasts WHERE site_id = %s', site)
    cursor.execute('DELETE FROM observations WHERE site_id = %s', site)
    cursor.execute('DELETE FROM cdf_forecasts_groups WHERE site_id = %s', site)
    cursor.execute('DELETE FROM sites WHERE id = %s', site)


@pytest.mark.parametrize('test', [
    'users', 'roles', 'sites', 'observations',
    'permissions', 'aggregates', 'organizations',
    'cdf_forecasts_groups', 'reports',
    'user_role_mapping'])
def test_drop_forecast(cursor, test, valueset_forecast):
    """Check that tables remain unchanged when removing a forecast"""
    forecast = valueset_forecast['id']
    before = check_table_for_org(cursor, None, test)
    cursor.execute('DELETE FROM forecasts WHERE id = %s', forecast)
    after = check_table_for_org(cursor, None, test)
    assert before == after


def test_drop_forecast_values(cursor, valueset_forecast):
    forecast = valueset_forecast['id']
    cursor.execute('SELECT COUNT(*) from forecasts_values WHERE id = %s',
                   forecast)
    assert cursor.fetchone()[0] > 0
    cursor.execute('DELETE FROM forecasts WHERE id = %s', forecast)
    cursor.execute('SELECT COUNT(*) from forecasts_values WHERE id = %s',
                   forecast)
    assert cursor.fetchone()[0] == 0


@pytest.mark.parametrize('test', [
    'users', 'roles', 'sites', 'forecasts',
    'permissions', 'aggregates', 'organizations',
    'cdf_forecasts_groups', 'reports',
    'user_role_mapping'])
def test_drop_observation(cursor, test, valueset_observation):
    """Check that tables remain unchanged when removing a observation"""
    observation = valueset_observation['id']
    before = check_table_for_org(cursor, None, test)
    cursor.execute('DELETE FROM observations WHERE id = %s', observation)
    after = check_table_for_org(cursor, None, test)
    assert before == after


def test_drop_observation_values(cursor, valueset_observation):
    observation = valueset_observation['id']
    cursor.execute('SELECT COUNT(*) from observations_values WHERE id = %s',
                   observation)
    assert cursor.fetchone()[0] > 0
    cursor.execute('DELETE FROM observations WHERE id = %s', observation)
    cursor.execute('SELECT COUNT(*) from observations_values WHERE id = %s',
                   observation)
    assert cursor.fetchone()[0] == 0


def test_drop_aggregate_obs_mapping(cursor, valueset_aggregate):
    agg = valueset_aggregate['id']
    cursor.execute('SELECT COUNT(*) FROM aggregate_observation_mapping WHERE'
                   ' aggregate_id = %s', agg)
    assert cursor.fetchone()[0] > 0
    cursor.execute('DELETE FROM aggregates WHERE id = %s', agg)
    cursor.execute('SELECT COUNT(*) FROM aggregate_observation_mapping WHERE'
                   ' aggregate_id = %s', agg)
    assert cursor.fetchone()[0] == 0



def test_drop_report_values(cursor, valueset_report):
    report = valueset_report['id']
    cursor.execute('SELECT COUNT(*) FROM report_values WHERE report_id = %s',
                   report)
    assert cursor.fetchone()[0] > 0
    cursor.execute('DELETE FROM reports WHERE id = %s', report)
    cursor.execute('SELECT COUNT(*) FROM report_values WHERE report_id = %s',
                   report)
    assert cursor.fetchone()[0] == 0


def test_drop_report_values_on_observation_drop(cursor, valueset_report):
    report_params = json.loads(valueset_report['report_parameters'])
    object_pairs = report_params['object_pairs']
    observation = uuid_to_bin(UUID(object_pairs[0][0]))
    cursor.execute('SELECT COUNT(*) FROM report_values WHERE object_id = %s',
                   observation)
    assert cursor.fetchone()[0] > 0
    cursor.execute('DELETE FROM observations where id = %s', observation)
    cursor.execute('SELECT COUNT(*) FROM report_values WHERE object_id = %s',
                   observation)
    assert cursor.fetchone()[0] == 0


def test_drop_report_values_on_forecast_drop(cursor, valueset_report):
    report_params = json.loads(valueset_report['report_parameters'])
    object_pairs = report_params['object_pairs']
    forecast = uuid_to_bin(UUID(object_pairs[0][1]))
    cursor.execute('SELECT COUNT(*) FROM report_values WHERE object_id = %s',
                   forecast)
    assert cursor.fetchone()[0] > 0
    cursor.execute('DELETE FROM forecasts where id = %s', forecast)
    cursor.execute('SELECT COUNT(*) FROM report_values WHERE object_id = %s',
                   forecast)
    assert cursor.fetchone()[0] == 0


def test_drop_report_values_on_cdf_forecast_drop(
        cursor, valueset_report):
    report_params = json.loads(valueset_report['report_parameters'])
    object_pairs = report_params['object_pairs']
    cdf_group = uuid_to_bin(UUID(object_pairs[-1][1]))
    cursor.execute(
        'SELECT COUNT(*) FROM report_values WHERE object_id = %s',
        cdf_group)
    assert cursor.fetchone()[0] > 0
    cursor.execute(
        'DELETE FROM cdf_forecasts_groups where id = %s',
        cdf_group)
    cursor.execute(
        'SELECT COUNT(*) FROM report_values WHERE object_id = %s',
        cdf_group)
    assert cursor.fetchone()[0] == 0
