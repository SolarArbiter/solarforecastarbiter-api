"""
Test that object inserts and removals trigger updates to
permission_object_mapping
"""
import pymysql
import pytest


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


def test_object_mapping_new_permission_other_objs(cursor, new_permission,
                                                  new_organization,
                                                  new_forecast):
    """
    Test adding permission_object_mapping for permissions
    when other objects already present and automattically
    added to permission_object_mapping by trigger
    """
    org = new_organization()
    perm0 = new_permission('read', 'forecasts', True, org=org)
    new_forecast(org=org)
    cursor.execute(
        'SELECT COUNT(*) from permission_object_mapping WHERE '
        'permission_id = %s', perm0['id'])
    assert cursor.fetchone()[0] == 1
    perm1 = new_permission('read', 'permissions', True, org=org)
    new_permission('read', 'observations', True, org=org)
    cursor.execute(
        'SELECT COUNT(*) from permission_object_mapping WHERE '
        'permission_id = %s', perm1['id'])
    # 3 permission objects that should be reference by perm1
    assert cursor.fetchone()[0] == 3


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
    [newfcn(org=org) for i in range(count)]
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
    if obj_type == 'cdf_forecasts':
        obj_type = 'cdf_forecasts_groups'
    cursor.execute(
        f'DELETE FROM {obj_type} WHERE id = %s', newthing['id'])
    cursor.execute(
        'SELECT object_id FROM permission_object_mapping WHERE '
        'permission_id = %s', perm['id'])
    assert cursor.fetchone() is None
