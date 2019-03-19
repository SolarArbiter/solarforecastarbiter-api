"""
Test that object inserts and removals trigger updates to
permission_object_mapping
"""
from collections import OrderedDict


import pymysql
import pytest


from conftest import newuuid


@pytest.fixture(scope='session')
def anint():
    i = 0
    yield i
    i += 1


@pytest.fixture(scope='function')
def new_organization(cursor, anint):
    def fnc(i=anint):
        out = OrderedDict(id=newuuid(), name=f'org{i}')
        cursor.execute('INSERT INTO organizations (id, name) VALUES (%s, %s)',
                       list(out.values()))
        return out
    return fnc


@pytest.fixture()
def new_user(cursor, new_organization, anint):
    def fcn(org=None, i=anint):
        if org is None:
            org = new_organization(i=i)
        out = OrderedDict(id=newuuid(), auth0_id=f'authid{i}',
                          organization_id=org['id'])
        cursor.execute(
            'INSERT INTO users (id, auth0_id, organization_id) VALUES '
            '(%s, %s, %s)', list(out.values()))
        return out
    return fcn


@pytest.fixture()
def new_role(cursor, new_organization, anint):
    def fcn(org=None, i=anint):
        if org is None:
            org = new_organization(i=i)
        out = OrderedDict(id=newuuid(), name=f'role{i}',
                          description='therole',
                          organization_id=org['id'])
        cursor.execute(
            'INSERT INTO roles (id, name, description, organization_id) '
            'VALUES (%s, %s, %s, %s)', list(out.values()))
        return out
    return fcn


@pytest.fixture()
def new_permission(cursor, new_organization, anint):
    def fcn(action, object_type, applies_to_all, org=None, i=anint):
        if org is None:
            org = new_organization(i=i)
        out = OrderedDict(id=newuuid(), description='perm',
                          organization_id=org['id'],
                          action=action, object_type=object_type,
                          applies_to_all=applies_to_all)
        cursor.execute(
            'INSERT INTO permissions (id, description, organization_id, action'
            ', object_type, applies_to_all) VALUES (%s, %s, %s, %s, %s, %s)',
            list(out.values()))
        return out
    return fcn


@pytest.fixture()
def new_site(cursor, new_organization, anint):
    def fcn(org=None, i=anint):
        if org is None:
            org = new_organization(i=i)
        out = OrderedDict(id=newuuid(), organization_id=org['id'],
                          name=f'site{i}')
        cursor.execute(
            'INSERT INTO sites (id, organization_id, name) VALUES '
            '(%s, %s, %s)', list(out.values()))
        return out
    return fcn


@pytest.fixture()
def new_forecast(cursor, new_site, anint):
    def fcn(site=None, org=None, i=anint):
        if site is None:
            site = new_site(org)
        out = OrderedDict(
            id=newuuid(), organization_id=site['organization_id'],
            site_id=site['id'], name=f'forecast{i}')
        cursor.execute(
            'INSERT INTO forecasts (id, organization_id, site_id, name) VALUES '
            '(%s, %s, %s, %s)', list(out.values()))
        return out
    return fcn


@pytest.fixture()
def new_observation(cursor, new_site, anint):
    def fcn(site=None, org=None, i=anint):
        if site is None:
            site = new_site(org)
        out = OrderedDict(
            id=newuuid(), organization_id=site['organization_id'],
            site_id=site['id'], name=f'observation{i}')
        cursor.execute(
            'INSERT INTO observations (id, organization_id, site_id, name) '
            'VALUES (%s, %s, %s, %s)', list(out.values()))
        return out
    return fcn


def test_permissions_not_updatable(cursor, new_permission):
    """Test that permission objects  cant be updated"""
    perm = new_permission('read', 'forecasts', False)
    with pytest.raises(pymysql.err.IntegrityError):
        cursor.execute(
            'UPDATE permissions SET action = "delete" WHERE id = %s',
            perm['id'])


def test_object_mapping_new_permission(cursor, new_permission,
                                       new_organization):
    """Test adding permission_object_mapping for permissions"""
    org = new_organization()
    perm0 = new_permission('read', 'permissions', False, org=org)
    cursor.execute(
        'SELECT COUNT(*) from permission_object_mapping WHERE '
        'permission_id = %s', perm0['id'])
    assert cursor.fetchone()[0] == 0
    perm1 = new_permission('read', 'permissions', True, org=org)
    cursor.execute(
        'SELECT COUNT(*) from permission_object_mapping WHERE '
        'permission_id = %s', perm1['id'])
    # 2 includes first permission and this second one with applies_to_all
    assert cursor.fetchone()[0] == 2


@pytest.fixture(params=['sites', 'users', 'roles', 'forecasts',
                        'observations'])
def getfcn(request, new_site, new_user, new_role, new_forecast,
           new_observation):
    if request.param == 'sites':
        return new_site, 'sites'
    elif request.param == 'users':
        return new_user, 'users'
    elif request.param == 'roles':
        return new_role, 'roles'
    elif request.param == 'forecasts':
        return new_forecast, 'forecasts'
    elif request.param == 'observations':
        return new_observation, 'observations'


@pytest.mark.parametrize('action', ['read', 'update', 'delete'])
@pytest.mark.parametrize('count', [1, 3])
def test_object_mapping_when_new_permission_applies_to_all(
        cursor, count, action, getfcn, new_organization, new_permission):
    """
    Make sure permission_object_mapping updated when a permission is
    added with applies_to_all = True for existing objects
    """
    newfcn, obj_type = getfcn
    org = new_organization()
    [newfcn(org=org, i=i) for i in range(count)]
    perm = new_permission(action, obj_type, True, org=org)
    cursor.execute(
        'SELECT COUNT(*) from permission_object_mapping WHERE '
        'permission_id = %s', perm['id'])
    assert cursor.fetchone()[0] == count


@pytest.mark.parametrize('action', ['read', 'update', 'delete', 'create'])
def test_object_mapping_when_new_permission_not_applies_to_all(
        cursor, action, getfcn, new_organization, new_permission):
    """
    Make sure nothing is added when the permission does not
    applies_to_all
    """
    newfcn, obj_type = getfcn
    org = new_organization()
    newfcn(org=org)
    perm = new_permission(action, obj_type, False, org=org)
    cursor.execute(
        'SELECT COUNT(*) from permission_object_mapping WHERE '
        'permission_id = %s', perm['id'])
    assert cursor.fetchone()[0] == 0


@pytest.mark.parametrize('action', ['create'])
def test_object_mapping_when_new_permission_create(
        cursor, new_organization, new_permission, action, getfcn):
    """
    Make sure nothing is added when action = 'create'
    """
    org = new_organization()
    newfcn, obj_type = getfcn
    newfcn(org=org)
    perm = new_permission(action, obj_type, True, org=org)
    cursor.execute(
        'SELECT COUNT(*) from permission_object_mapping WHERE '
        'permission_id = %s', perm['id'])
    assert cursor.fetchone()[0] == 0


@pytest.mark.parametrize('action', ['read', 'update', 'delete', 'create'])
def test_object_mapping_new_obj(cursor, action, getfcn, new_organization,
                                new_permission):
    """
    Make sure an object gets added to permission_object_mapping when
    a permission with applies_to_all exists
    """
    org = new_organization()
    newfcn, obj_type = getfcn
    perm = new_permission(action, obj_type, True, org=org)
    newthing = newfcn(org=org)
    cursor.execute(
        'SELECT object_id FROM permission_object_mapping WHERE '
        'permission_id = %s', perm['id'])
    if action != 'create':
        assert cursor.fetchone()[0] == newthing['id']
    else:
        assert cursor.fetchone() is None


@pytest.mark.parametrize('action', ['read', 'update', 'delete', 'create'])
def test_object_mapping_remove_obj(cursor, action, getfcn, new_permission,
                                   new_organization):
    """
    Make sure object is removed from permission_object_mapping
    when deleted
    """
    newfcn, obj_type = getfcn
    org = new_organization()
    perm = new_permission(action, obj_type, True, org=org)
    newthing = newfcn(org=org)
    cursor.execute(
        f'DELETE FROM {obj_type} WHERE id = %s', newthing['id'])
    cursor.execute(
        'SELECT object_id FROM permission_object_mapping WHERE '
        'permission_id = %s', perm['id'])
    assert cursor.fetchone() is None
