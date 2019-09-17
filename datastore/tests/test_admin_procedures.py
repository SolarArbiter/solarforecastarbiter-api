import pytest


def test_create_org(dictcursor):
    dictcursor.callproc('create_organization', ('test_org',))
    # assert org exists
    dictcursor.execute('SELECT * FROM arbiter_data.organizations '
                   'WHERE name = "test_org"')
    org = dictcursor.fetchone()
    assert org['name'] == 'test_org'
    orgid = org['id']
    dictcursor.execute('SELECT * FROM arbiter_data.roles '
                       'WHERE organization_id = %s', orgid)
    org_roles = dictcursor.fetchall()
    assert 'Read all' in [r['name'] for r in org_roles]
    assert 'Write all values' in [r['name'] for r in org_roles]
    assert 'Create metadata' in [r['name'] for r in org_roles]
    assert 'Delete metadata' in [r['name'] for r in org_roles]
    assert 'Administer data access controls' in [r['name'] for r in org_roles]


def test_create_default_read_role(dictcursor, new_organization):
    org = new_organization()
    orgid = org['id']
    dictcursor.callproc('create_default_read_role', (orgid,))
    dictcursor.execute(
        'SELECT * FROM roles WHERE name = "Read all" and organization_id = %s',
        orgid)
    read_roles = dictcursor.fetchall()
    assert len(read_roles) == 1
    read_all_role = read_roles[0]
    assert read_all_role['description'] == 'View all data and metadata'
    assert read_all_role['organization_id'] == orgid
    role_id = read_all_role['id']
    dictcursor.execute(
        'SELECT permission_id FROM role_permission_mapping WHERE role_id = %s',
        role_id)
    permission_ids = dictcursor.fetchall()
    for permid in [p['permission_id'] for p in permission_ids]:
        dictcursor.execute('SELECT * FROM permissions WHERE id = %s', permid)
        perm = dictcursor.fetchone()
        assert perm == {}


def test_create_default_write_role():
    pass


def test_create_default_create_role():
    pass


def test_create_default_delete_role():
    pass


def test_create_default_admin_role():
    pass


def test_get_org_role_by_name():
    pass


def test_promote_user_to_org_admin():
    pass


def test_get_unaffiliated_orgid():
    pass


def test_add_user_to_org():
    pass


def test_remove_org_roles_from_user():
    pass


def test_move_user_to_unaffiliated():
    pass


def test_remove_user_from_org():
    pass


def test_delete_user():
    pass
