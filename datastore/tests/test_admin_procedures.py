import pytest


from conftest import bin_to_uuid, newuuid
import pymysql


def assert_no_rbac(dictcursor, orgid):
    dictcursor.execute(
        'SELECT * FROM roles WHERE organization_id = %s', orgid)
    assert len(dictcursor.fetchall()) == 0
    dictcursor.execute(
        'SELECT * FROM permissions WHERE organization_id = %s', orgid)
    assert len(dictcursor.fetchall()) == 0


def test_create_org(dictcursor):
    dictcursor.callproc('create_organization', ('test_org',))
    dictcursor.execute('SELECT * FROM arbiter_data.organizations '
                       'WHERE name = "test_org"')
    org = dictcursor.fetchone()
    assert org['name'] == 'test_org'
    assert not org['accepted_tou']
    orgid = org['id']
    dictcursor.execute('SELECT * FROM arbiter_data.roles '
                       'WHERE organization_id = %s', orgid)
    org_roles = dictcursor.fetchall()
    assert 'Read all' in [r['name'] for r in org_roles]
    assert 'Write all values' in [r['name'] for r in org_roles]
    assert 'Create metadata' in [r['name'] for r in org_roles]
    assert 'Delete metadata' in [r['name'] for r in org_roles]
    assert 'Administer data access controls' in [r['name'] for r in org_roles]


def test_create_org_name_exists(dictcursor):
    dictcursor.callproc('create_organization', ('test_org',))
    with pytest.raises(pymysql.err.IntegrityError) as e:
        dictcursor.callproc('create_organization', ('test_org',))
    assert e.value.args[0] == 1062


def test_create_default_read_role(dictcursor, new_organization):
    org = new_organization()
    orgid = org['id']
    assert_no_rbac(dictcursor, orgid)
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
    assert len(permission_ids) == 11
    perm_objects = []
    for permid in [p['permission_id'] for p in permission_ids]:
        dictcursor.execute('SELECT * FROM permissions WHERE id = %s', permid)
        perm = dictcursor.fetchone()
        perm_objects.append(perm)
    perms = {p['description']: p for p in perm_objects}
    for perm in perms.values():
        assert perm['applies_to_all'] == 1
        assert perm['organization_id'] == orgid
    read_sites = perms['Read all sites']
    assert read_sites['object_type'] == 'sites'
    assert read_sites['action'] == 'read'
    read_obs = perms['Read all observations']
    assert read_obs['object_type'] == 'observations'
    assert read_obs['action'] == 'read'
    read_obs_values = perms['Read all observation values']
    assert read_obs_values['object_type'] == 'observations'
    assert read_obs_values['action'] == 'read_values'
    read_fx = perms['Read all forecasts']
    assert read_fx['object_type'] == 'forecasts'
    assert read_fx['action'] == 'read'
    read_fx_values = perms['Read all forecast values']
    assert read_fx_values['object_type'] == 'forecasts'
    assert read_fx_values['action'] == 'read_values'
    read_cdf = perms['Read all probabilistic forecasts']
    assert read_cdf['object_type'] == 'cdf_forecasts'
    assert read_cdf['action'] == 'read'
    read_cdf_values = perms['Read all probabilistic forecast values']
    assert read_cdf_values['object_type'] == 'cdf_forecasts'
    assert read_cdf_values['action'] == 'read_values'
    read_reports = perms['Read all reports']
    assert read_reports['object_type'] == 'reports'
    assert read_reports['action'] == 'read'
    read_report_values = perms['Read all report values']
    assert read_report_values['object_type'] == 'reports'
    assert read_report_values['action'] == 'read_values'
    read_agg = perms['Read all aggregates']
    assert read_agg['object_type'] == 'aggregates'
    assert read_agg['action'] == 'read'
    read_agg_values = perms['Read all aggregate values']
    assert read_agg_values['object_type'] == 'aggregates'
    assert read_agg_values['action'] == 'read_values'


def test_create_default_read_role_role_exists(dictcursor, new_organization):
    org = new_organization()
    orgid = org['id']
    assert_no_rbac(dictcursor, orgid)
    dictcursor.callproc('create_default_read_role', (orgid,))
    dictcursor.execute(
        'SELECT * FROM roles WHERE name = "Read all" and organization_id = %s',
        orgid)
    read_roles = dictcursor.fetchall()
    read_all_role = read_roles[0]
    role_id = read_all_role['id']
    dictcursor.execute(
        'SELECT permission_id FROM role_permission_mapping WHERE role_id = %s',
        role_id)
    permission_ids = dictcursor.fetchall()
    assert len(permission_ids) == 11

    with pytest.raises(pymysql.err.IntegrityError) as e:
        dictcursor.callproc('create_default_read_role', (orgid,))
    assert e.value.args[0] == 1062

    role_id = read_all_role['id']
    dictcursor.execute(
        'SELECT permission_id FROM role_permission_mapping WHERE role_id = %s',
        role_id)
    permission_ids = dictcursor.fetchall()
    assert len(permission_ids) == 11


def test_create_default_write_role(dictcursor, new_organization):
    org = new_organization()
    orgid = org['id']
    assert_no_rbac(dictcursor, orgid)
    dictcursor.callproc('create_default_write_role', (orgid,))
    dictcursor.execute(
        'SELECT * FROM roles WHERE name = "Write all values" AND '
        'organization_id = %s', orgid)
    read_roles = dictcursor.fetchall()
    assert len(read_roles) == 1
    write_all_role = read_roles[0]
    role_description = 'Allows the user to submit data within the organization'
    assert write_all_role['description'] == role_description
    assert write_all_role['organization_id'] == orgid
    role_id = write_all_role['id']
    dictcursor.execute(
        'SELECT permission_id FROM role_permission_mapping WHERE role_id = %s',
        role_id)
    permission_ids = dictcursor.fetchall()
    assert len(permission_ids) == 5
    perm_objects = []
    for permid in [p['permission_id'] for p in permission_ids]:
        dictcursor.execute('SELECT * FROM permissions WHERE id = %s', permid)
        perm = dictcursor.fetchone()
        perm_objects.append(perm)
    perms = {p['description']: p for p in perm_objects}
    for perm in perms.values():
        assert perm['applies_to_all'] == 1
        assert perm['organization_id'] == orgid
        assert perm['action'] == 'write_values'
    write_obs = perms['Submit values to all observations']
    assert write_obs['object_type'] == 'observations'
    write_fx = perms['Submit values to all forecasts']
    assert write_fx['object_type'] == 'forecasts'
    write_cdf = perms['Submit values to all probabilistic forecasts']
    assert write_cdf['object_type'] == 'cdf_forecasts'
    write_aggregates = perms['Submit values to all aggregates']
    assert write_aggregates['object_type'] == 'aggregates'
    write_reports = perms['Submit values to all reports']
    assert write_reports['object_type'] == 'reports'


def test_create_default_write_role_role_exists(dictcursor, new_organization):
    org = new_organization()
    orgid = org['id']
    assert_no_rbac(dictcursor, orgid)
    dictcursor.callproc('create_default_write_role', (orgid,))
    dictcursor.execute(
        'SELECT * FROM roles WHERE name = "Write all values" AND '
        'organization_id = %s', orgid)
    read_roles = dictcursor.fetchall()
    assert len(read_roles) == 1
    write_all_role = read_roles[0]
    role_description = 'Allows the user to submit data within the organization'
    assert write_all_role['description'] == role_description
    assert write_all_role['organization_id'] == orgid
    role_id = write_all_role['id']
    dictcursor.execute(
        'SELECT permission_id FROM role_permission_mapping WHERE role_id = %s',
        role_id)
    permission_ids = dictcursor.fetchall()
    assert len(permission_ids) == 5

    with pytest.raises(pymysql.err.IntegrityError) as e:
        dictcursor.callproc('create_default_write_role', (orgid,))
    assert e.value.args[0] == 1062

    dictcursor.execute(
        'SELECT permission_id FROM role_permission_mapping WHERE role_id = %s',
        role_id)
    permission_ids = dictcursor.fetchall()
    assert len(permission_ids) == 5


def test_create_default_create_role(dictcursor, new_organization):
    org = new_organization()
    orgid = org['id']
    assert_no_rbac(dictcursor, orgid)
    dictcursor.callproc('create_default_create_role', (orgid,))
    dictcursor.execute(
        'SELECT * FROM roles WHERE name = "Create metadata" AND '
        'organization_id = %s', orgid)
    create_roles = dictcursor.fetchall()
    assert len(create_roles) == 1
    create_all_role = create_roles[0]
    role_description = 'Allows the user to create metadata types'
    assert create_all_role['description'] == role_description
    assert create_all_role['organization_id'] == orgid
    role_id = create_all_role['id']
    dictcursor.execute(
        'SELECT permission_id FROM role_permission_mapping WHERE role_id = %s',
        role_id)
    permission_ids = dictcursor.fetchall()
    assert len(permission_ids) == 6
    perm_objects = []
    for permid in [p['permission_id'] for p in permission_ids]:
        dictcursor.execute('SELECT * FROM permissions WHERE id = %s', permid)
        perm = dictcursor.fetchone()
        perm_objects.append(perm)
    perms = {p['description']: p for p in perm_objects}
    for perm in perms.values():
        assert perm['applies_to_all'] == 1
        assert perm['organization_id'] == orgid
        assert perm['action'] == 'create'
    create_obs = perms['Create observations']
    assert create_obs['object_type'] == 'observations'
    create_fx = perms['Create forecasts']
    assert create_fx['object_type'] == 'forecasts'
    create_cdf = perms['Create probabilistic forecasts']
    assert create_cdf['object_type'] == 'cdf_forecasts'
    create_aggregates = perms['Create aggregates']
    assert create_aggregates['object_type'] == 'aggregates'
    create_reports = perms['Create reports']
    assert create_reports['object_type'] == 'reports'
    create_sites = perms['Create sites']
    assert create_sites['object_type'] == 'sites'


def test_create_default_create_role_role_exists(dictcursor, new_organization):
    org = new_organization()
    orgid = org['id']
    assert_no_rbac(dictcursor, orgid)
    dictcursor.callproc('create_default_create_role', (orgid,))
    dictcursor.execute(
        'SELECT * FROM roles WHERE name = "Create metadata" and '
        'organization_id = %s', orgid)
    create_roles = dictcursor.fetchall()
    create_all_role = create_roles[0]
    role_id = create_all_role['id']
    dictcursor.execute(
        'SELECT permission_id FROM role_permission_mapping WHERE role_id = %s',
        role_id)
    permission_ids = dictcursor.fetchall()
    assert len(permission_ids) == 6

    with pytest.raises(pymysql.err.IntegrityError) as e:
        dictcursor.callproc('create_default_create_role', (orgid,))
    assert e.value.args[0] == 1062

    dictcursor.execute(
        'SELECT permission_id FROM role_permission_mapping WHERE role_id = %s',
        role_id)
    permission_ids = dictcursor.fetchall()
    assert len(permission_ids) == 6


def test_create_default_delete_role(dictcursor, new_organization):
    org = new_organization()
    orgid = org['id']
    assert_no_rbac(dictcursor, orgid)
    dictcursor.callproc('create_default_delete_role', (orgid,))
    dictcursor.execute(
        'SELECT * FROM roles WHERE name = "Delete metadata" AND '
        'organization_id = %s', orgid)
    delete_roles = dictcursor.fetchall()
    assert len(delete_roles) == 1
    delete_all_role = delete_roles[0]
    role_description = 'Allows the user to delete metadata'
    assert delete_all_role['description'] == role_description
    assert delete_all_role['organization_id'] == orgid
    role_id = delete_all_role['id']
    dictcursor.execute(
        'SELECT permission_id FROM role_permission_mapping WHERE role_id = %s',
        role_id)
    permission_ids = dictcursor.fetchall()
    assert len(permission_ids) == 6
    perm_objects = []
    for permid in [p['permission_id'] for p in permission_ids]:
        dictcursor.execute('SELECT * FROM permissions WHERE id = %s', permid)
        perm = dictcursor.fetchone()
        perm_objects.append(perm)
    perms = {p['description']: p for p in perm_objects}
    for perm in perms.values():
        assert perm['applies_to_all'] == 1
        assert perm['organization_id'] == orgid
        assert perm['action'] == 'delete'
    delete_obs = perms['Delete observations']
    assert delete_obs['object_type'] == 'observations'
    delete_fx = perms['Delete forecasts']
    assert delete_fx['object_type'] == 'forecasts'
    delete_cdf = perms['Delete probabilistic forecasts']
    assert delete_cdf['object_type'] == 'cdf_forecasts'
    delete_aggregates = perms['Delete aggregates']
    assert delete_aggregates['object_type'] == 'aggregates'
    delete_reports = perms['Delete reports']
    assert delete_reports['object_type'] == 'reports'
    delete_sites = perms['Delete sites']
    assert delete_sites['object_type'] == 'sites'


def test_create_default_delete_role_role_exists(dictcursor, new_organization):
    org = new_organization()
    orgid = org['id']
    assert_no_rbac(dictcursor, orgid)
    dictcursor.callproc('create_default_delete_role', (orgid,))
    dictcursor.execute(
        'SELECT * FROM roles WHERE name = "Delete metadata" AND '
        'organization_id = %s', orgid)
    delete_roles = dictcursor.fetchall()
    delete_all_role = delete_roles[0]
    role_id = delete_all_role['id']
    dictcursor.execute(
        'SELECT permission_id FROM role_permission_mapping WHERE role_id = %s',
        role_id)
    permission_ids = dictcursor.fetchall()
    assert len(permission_ids) == 6

    with pytest.raises(pymysql.err.IntegrityError) as e:
        dictcursor.callproc('create_default_delete_role', (orgid,))
    assert e.value.args[0] == 1062

    dictcursor.execute(
        'SELECT permission_id FROM role_permission_mapping WHERE role_id = %s',
        role_id)
    permission_ids = dictcursor.fetchall()
    assert len(permission_ids) == 6


def test_create_default_admin_role(dictcursor, new_organization):
    org = new_organization()
    orgid = org['id']
    assert_no_rbac(dictcursor, orgid)
    dictcursor.callproc('create_default_admin_role', (orgid,))
    dictcursor.execute(
        'SELECT * FROM roles WHERE name = "Administer data access controls" '
        'AND organization_id = %s', orgid)
    delete_roles = dictcursor.fetchall()
    assert len(delete_roles) == 1
    delete_all_role = delete_roles[0]
    role_description = 'Administer users roles and permissions'
    assert delete_all_role['description'] == role_description
    assert delete_all_role['organization_id'] == orgid
    role_id = delete_all_role['id']
    dictcursor.execute(
        'SELECT permission_id FROM role_permission_mapping WHERE role_id = %s',
        role_id)
    permission_ids = dictcursor.fetchall()
    assert len(permission_ids) == 11
    perm_objects = []
    for permid in [p['permission_id'] for p in permission_ids]:
        dictcursor.execute('SELECT * FROM permissions WHERE id = %s', permid)
        perm = dictcursor.fetchone()
        perm_objects.append(perm)
    perms = {p['description']: p for p in perm_objects}
    for perm in perms.values():
        assert perm['applies_to_all'] == 1
        assert perm['organization_id'] == orgid
    create_roles = perms['Create roles']
    assert create_roles['action'] == 'create'
    assert create_roles['object_type'] == 'roles'
    create_perms = perms['Create permissions']
    assert create_perms['action'] == 'create'
    assert create_perms['object_type'] == 'permissions'
    grant_roles = perms['Grant roles']
    assert grant_roles['action'] == 'grant'
    assert grant_roles['object_type'] == 'roles'
    revoke_roles = perms['Revoke roles']
    assert revoke_roles['action'] == 'revoke'
    assert revoke_roles['object_type'] == 'roles'
    update_roles = perms['Update roles']
    assert update_roles['action'] == 'update'
    assert update_roles['object_type'] == 'roles'
    update_permissions = perms['Update permissions']
    assert update_permissions['action'] == 'update'
    assert update_permissions['object_type'] == 'permissions'
    delete_roles = perms['Delete roles']
    assert delete_roles['action'] == 'delete'
    assert delete_roles['object_type'] == 'roles'
    delete_permissions = perms['Delete permissions']
    assert delete_permissions['action'] == 'delete'
    assert delete_permissions['object_type'] == 'permissions'
    read_users = perms['Read users']
    assert read_users['action'] == 'read'
    assert read_users['object_type'] == 'users'
    read_roles = perms['Read roles']
    assert read_roles['action'] == 'read'
    assert read_roles['object_type'] == 'roles'
    read_permissions = perms['Read permissions']
    assert read_permissions['action'] == 'read'
    assert read_permissions['object_type'] == 'permissions'


def test_create_default_admin_role_role_exists(dictcursor, new_organization):
    org = new_organization()
    orgid = org['id']
    assert_no_rbac(dictcursor, orgid)
    dictcursor.callproc('create_default_admin_role', (orgid,))
    dictcursor.execute(
        'SELECT * FROM roles WHERE name = "Administer data access controls" '
        'AND organization_id = %s',
        orgid)
    delete_roles = dictcursor.fetchall()
    assert len(delete_roles) == 1
    delete_all_role = delete_roles[0]
    role_id = delete_all_role['id']
    dictcursor.execute(
        'SELECT permission_id FROM role_permission_mapping WHERE role_id = %s',
        role_id)
    permission_ids = dictcursor.fetchall()
    assert len(permission_ids) == 11
    with pytest.raises(pymysql.err.IntegrityError) as e:
        dictcursor.callproc('create_default_admin_role', (orgid,))
    assert e.value.args[0] == 1062
    dictcursor.execute(
        'SELECT permission_id FROM role_permission_mapping WHERE role_id = %s',
        role_id)
    permission_ids = dictcursor.fetchall()
    assert len(permission_ids) == 11


@pytest.mark.parametrize('role_name', [
    'Read all', 'Write all values', 'Create metadata',
    'Delete metadata', 'Administer data access controls']
)
def test_get_org_role_by_name(dictcursor, role_name):
    dictcursor.callproc('create_organization', ('test_org',))
    dictcursor.execute('SELECT id FROM arbiter_data.organizations '
                       'WHERE name = "test_org"')
    orgid = dictcursor.fetchone()['id']
    dictcursor.execute(
        'SELECT arbiter_data.get_org_role_by_name(%s, %s) as roleid',
        (role_name, orgid))
    role = dictcursor.fetchone()['roleid']
    dictcursor.execute(
        'SELECT * FROM arbiter_data.roles WHERE id = %s', role)
    role = dictcursor.fetchone()
    assert role['name'] == role_name


@pytest.mark.parametrize('role_name', [
    'role1', 'role2', 'role3', 'role4'
])
def test_get_org_role_by_name_role_dne(dictcursor, role_name):
    dictcursor.callproc('create_organization', ('test_org',))
    dictcursor.execute('SELECT id FROM arbiter_data.organizations '
                       'WHERE name = "test_org"')
    orgid = dictcursor.fetchone()['id']
    dictcursor.execute(
        'SELECT arbiter_data.get_org_role_by_name(%s, %s) as roleid',
        (role_name, orgid))
    role = dictcursor.fetchone()
    assert role['roleid'] is None


def test_add_user_to_org(
        dictcursor, new_organization, new_unaffiliated_user,
        unaffiliated_organization):
    userid = new_unaffiliated_user()['id']
    dictcursor.execute('SELECT organization_id FROM users WHERE id = %s',
                       userid)
    user_orgid = dictcursor.fetchone()['organization_id']
    assert user_orgid == unaffiliated_organization['id']

    orgid = new_organization()['id']
    strorgid = str(bin_to_uuid(orgid))
    struserid = str(bin_to_uuid(userid))
    dictcursor.callproc('add_user_to_org', (struserid, strorgid))

    dictcursor.execute('SELECT organization_id FROM users WHERE id = %s',
                       userid)
    new_user_orgid = dictcursor.fetchone()['organization_id']
    assert new_user_orgid == orgid


def test_add_user_to_org_affiliated_user(
        dictcursor, new_user, new_organization):
    user = new_user()
    org = new_organization()
    strorgid = str(bin_to_uuid(org['id']))
    struserid = str(bin_to_uuid(user['id']))
    with pytest.raises(pymysql.err.OperationalError) as e:
        dictcursor.callproc('add_user_to_org', (struserid, strorgid))
    assert e.value.args[0] == 1142
    assert e.value.args[1] == 'Cannot add affiliated user to organization'


def test_remove_org_roles_from_user(
        dictcursor, new_user, new_role, new_organization):
    role_ids = []
    for _ in range(5):
        org = new_organization()
        role = new_role(org)
        role_ids.append(role['id'])
    user_org = new_organization()
    user = new_user(org=user_org)
    org_role = new_role(org=user_org)
    dictcursor.execute(
        'SELECT id from organizations WHERE name = "Unaffiliated"')
    unaffiliated_org = dictcursor.fetchone()
    unaffiliated_role = new_role(org=unaffiliated_org)
    dictcursor.execute('SELECT id from organizations WHERE name = "Reference"')
    reference_org = dictcursor.fetchone()
    reference_role = new_role(org=reference_org)
    role_ids.append(org_role['id'])
    role_ids.append(reference_role['id'])
    role_ids.append(unaffiliated_role['id'])
    for rid in role_ids:
        dictcursor.execute(
            'INSERT INTO user_role_mapping(user_id, role_id) VALUES (%s, %s)',
            (user['id'], rid))
    dictcursor.execute(
        'SELECT * FROM user_role_mapping WHERE user_id = %s',
        (user['id'],))
    assert len(dictcursor.fetchall()) == 8
    dictcursor.callproc(
        'remove_org_roles_from_user', (user['id'],))
    dictcursor.execute(
        'SELECT * FROM user_role_mapping WHERE user_id = %s',
        (user['id'],))
    assert len(dictcursor.fetchall()) == 2


def test_move_user_to_unaffiliated(
        dictcursor, new_user, unaffiliated_organization,
        new_organization, new_role):
    org = new_organization()
    role = new_role(org=org)
    user = new_user(org=org)
    dictcursor.execute(
        'INSERT INTO user_role_mapping(user_id, role_id) VALUES (%s, %s)',
        (user['id'], role['id']))
    dictcursor.callproc(
        'move_user_to_unaffiliated', (str(bin_to_uuid(user['id'])),))
    dictcursor.execute(
        'SELECT organization_id FROM users where id = %s', (user['id'],))
    updated_user = dictcursor.fetchone()
    assert updated_user['organization_id'] == unaffiliated_organization['id']
    dictcursor.execute(
        'SELECT * FROM user_role_mapping WHERE user_id = %s AND '
        'role_id IN (SELECT id FROM roles WHERE organization_id != %s)',
        (user['id'], unaffiliated_organization['id']))
    assert len(dictcursor.fetchall()) == 0


def test_delete_user(dictcursor, new_user):
    user = new_user()
    dictcursor.callproc('delete_user', (str(bin_to_uuid(user['id'])),))
    dictcursor.execute('SELECT * FROM users WHERE id = %s', user['id'])
    assert len(dictcursor.fetchall()) == 0
    dictcursor.execute(
        'SELECT * FROM user_role_mapping WHERE user_id = %s', user['id'])
    assert len(dictcursor.fetchall()) == 0


def test_promote_user_to_org_admin(dictcursor, new_user):
    # depends on the roles provided by create_organization
    dictcursor.callproc('create_organization', ('test_org',))
    dictcursor.execute('SELECT * FROM arbiter_data.organizations '
                       'WHERE name = "test_org"')
    user = new_user(org=dictcursor.fetchone())
    dictcursor.callproc(
        'promote_user_to_org_admin',
        (str(bin_to_uuid(user['id'])),
         str(bin_to_uuid(user['organization_id']))))
    dictcursor.execute(
        'SELECT role_id FROM user_role_mapping WHERE user_id = %s',
        user['id'])
    role_ids = [r['role_id'] for r in dictcursor.fetchall()]
    assert len(role_ids) == 5
    dictcursor.execute(
        'SELECT name FROM roles WHERE id IN (%s,%s,%s,%s,%s)', role_ids)
    names = [r['name'] for r in dictcursor.fetchall()]
    assert 'Create metadata' in names
    assert 'Read all' in names
    assert 'Delete metadata' in names
    assert 'Write all values' in names
    assert 'Administer data access controls' in names


def test_promote_user_to_org_admin_external_user(
        cursor, new_user):
    # depends on the roles provided by create_organization
    cursor.callproc('create_organization', ('test_org',))
    cursor.execute('SELECT BIN_TO_UUID(id, 1) FROM arbiter_data.organizations '
                   'WHERE name = "test_org"')
    orgid = cursor.fetchone()
    user = new_user()
    with pytest.raises(pymysql.err.OperationalError) as e:
        cursor.callproc(
            'promote_user_to_org_admin',
            (str(bin_to_uuid(user['id'])), orgid))
    assert e.value.args[0] == 1142
    assert e.value.args[1] == 'Cannot promote admin from outside organization.'


def test_promote_user_to_org_admin_missing_roles(cursor, new_user):
    user = new_user()
    with pytest.raises(pymysql.err.IntegrityError) as e:
        cursor.callproc('promote_user_to_org_admin',
                        (str(bin_to_uuid(user['id'])),
                         str(bin_to_uuid(user['organization_id']))))
    assert e.value.args[0] == 1048
    assert e.value.args[1] == "Column 'role_id' cannot be null"


def test_list_all_users(dictcursor):
    dictcursor.callproc('list_all_users')
    users = dictcursor.fetchall()
    assert len(users) == 6
    for user in users:
        assert 'auth0_id' in user
        assert 'id' in user
        assert 'organization_id' in user
        assert 'organization_name' in user


def test_list_all_organizations(dictcursor):
    dictcursor.callproc('list_all_organizations')
    orgs = dictcursor.fetchall()
    assert len(orgs) == 6
    for org in orgs:
        assert 'name' in org
        assert 'id' in org


def test_set_org_accepted_tou(dictcursor):
    orgid = newuuid()
    dictcursor.execute(
        'INSERT INTO organizations (id, name, accepted_tou)'
        'VALUES (%s, %s, FALSE)', (orgid, "OrgHasntacceptedTOU"))
    dictcursor.callproc('set_org_accepted_tou', (str(bin_to_uuid(orgid)),))
    dictcursor.execute(
        'SELECT accepted_tou FROM organizations WHERE id = %s', orgid)
    assert dictcursor.fetchone()
