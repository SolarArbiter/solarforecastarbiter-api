from uuid import UUID


import pytest


from conftest import newuuid, uuid_to_bin


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


@pytest.fixture()
def make_test_permissions(cursor, new_organization, new_permission,
                          new_user, new_role, new_forecast, new_site,
                          new_observation, new_cdf_forecast,
                          new_aggregate, request):
    def make(org):
        user = new_user(org=org)
        role0 = new_role(org=org)
        perm0 = new_permission('read', 'observations', False, org=org)
        obj0 = new_observation(org=org)
        obj1 = new_observation(org=org)
        role1 = new_role(org=org)
        perm1 = new_permission('create', 'forecasts', True, org=org)
        perm2 = new_permission('read', 'forecasts', True, org=org)
        perm3 = new_permission('read', 'cdf_forecasts', True, org=org)
        cursor.executemany(
            'INSERT INTO user_role_mapping (user_id, role_id) VALUES (%s, %s)',
            [(user['id'], role0['id']), (user['id'], role1['id'])])
        cursor.executemany(
            'INSERT INTO role_permission_mapping (role_id, permission_id) '
            'VALUES (%s, %s)', [(role0['id'], perm0['id']),
                                (role1['id'], perm1['id']),
                                (role1['id'], perm2['id']),
                                (role1['id'], perm3['id'])])
        cursor.executemany(
            'INSERT INTO permission_object_mapping (permission_id, object_id)'
            ' VALUES (%s, %s)',
            [(perm0['id'], obj0['id']), (perm0['id'], obj1['id'])])
        fx = new_forecast(org=org)
        cdf = new_cdf_forecast(org=org)
        site = new_site(org=org)
        agg = new_aggregate(obs_list=[obj0, obj1])
        return {'user': user,
                'roles': [role0, role1],
                'sites': [site],
                'observations': [obj0, obj1],
                'forecasts': [fx],
                'cdf_forecasts': [cdf],
                'aggregates': [agg],
                'permissions': [perm0, perm1, perm2, perm3]}
    return make


def test_list_objects_user_can_read_diff_org(cursor, make_test_permissions,
                                             new_organization):
    """Test list_objects_user_can_read for two users in different orgs"""
    org0 = new_organization()
    user0 = make_test_permissions(org0)
    org1 = new_organization()
    user1 = make_test_permissions(org1)
    for otype in ['observations', 'forecasts', 'cdf_forecasts']:
        for udict in [user0, user1]:
            objs = {obj['id'] for obj in udict[otype]}
            authid = udict['user']['auth0_id']
            cursor.callproc('list_objects_user_can_read', (authid, otype))
            out = {o[0] for o in cursor.fetchall()}
            assert out == objs


def test_list_objects_user_can_read_same_org(cursor, make_test_permissions,
                                             new_organization):
    """
    Test list_objects_user_can_read for two users in same orgs
    with read all forecasts permissions
    """
    org0 = new_organization()
    user0 = make_test_permissions(org0)
    user1 = make_test_permissions(org0)
    fxobjs = {fx['id'] for user in [user0, user1] for fx in user['forecasts']}
    for udict in [user0, user1]:
        objs = {obj['id'] for obj in udict['observations']}
        authid = udict['user']['auth0_id']
        cursor.callproc('list_objects_user_can_read', (authid, 'observations'))
        out = {o[0] for o in cursor.fetchall()}
        assert out == objs

        cursor.callproc('list_objects_user_can_read', (authid, 'forecasts'))
        out = {o[0] for o in cursor.fetchall()}
        assert out == fxobjs


@pytest.mark.parametrize('action', ['read', 'update', 'delete',
                                    'read_values', 'write_values'])
@pytest.mark.parametrize('other', ['read', 'update', 'delete',
                                   'read_values', 'write_values'])
def test_can_user_perform_action(cursor, make_user_roles, action, getfcn,
                                 other):
    """That that a user can (and can not) perform the specified action"""
    newfcn, obj_type = getfcn
    info = make_user_roles(action, obj_type, True)
    authid = info['user']['auth0_id']
    obj = newfcn(org=info['org'])
    cursor.execute('SELECT can_user_perform_action(%s, %s, %s)',
                   (authid, obj['id'], other))
    if action == other:
        assert cursor.fetchone()[0] == 1
    else:
        assert cursor.fetchone()[0] == 0


def test_can_user_perform_action_multiple_permissions(
        cursor, make_user_roles, new_permission, new_forecast):
    """
    Test that can_user_perform_action works when one object is assigned
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
    assert cursor.fetchone()[0] == 1


def test_can_user_perform_not_create(cursor, make_user_roles, getfcn):
    """Make sure can_user_perform fails on create"""
    newfcn, obj_type = getfcn
    info = make_user_roles('create', obj_type, True)
    authid = info['user']['auth0_id']
    obj = newfcn(org=info['org'])
    cursor.execute('SELECT can_user_perform_action(%s, %s, %s)',
                   (authid, obj['id'], 'create'))
    assert cursor.fetchone()[0] == 0


def test_user_can_create(cursor, make_user_roles, getfcn):
    """Make sure can_user_perform fails on create"""
    newfcn, obj_type = getfcn
    info = make_user_roles('create', obj_type, True)
    authid = info['user']['auth0_id']
    newfcn(org=info['org'])
    cursor.execute('SELECT user_can_create(%s, %s)',
                   (authid, obj_type))
    assert cursor.fetchone()[0] == 1


def test_user_can_create_diff_org(cursor, make_test_permissions,
                                  new_organization, new_permission):
    """Make sure user can't create objects in another org even with
    permissions"""
    org0 = new_organization()
    user0 = make_test_permissions(org0)
    authid = user0['user']['auth0_id']
    org1 = new_organization()
    perm = new_permission('create', 'roles', True, org=org1)
    cursor.execute(
        'INSERT INTO role_permission_mapping (role_id, permission_id) VALUES'
        ' (%s, %s)', (user0['roles'][0]['id'], perm['id']))
    cursor.execute(
        'SELECT user_can_create(%s, %s)', (authid, 'roles'))
    assert cursor.fetchone()[0] == 0
    cursor.execute(
        'SELECT user_can_create(%s, %s)', (authid, 'forecasts'))
    assert cursor.fetchone()[0] == 1


@pytest.mark.parametrize('type_', [
    'roles', 'users', 'permissions', 'observations', 'mappings',
    'sites', 'aggregates', 'cdf_forecasts'])
def test_user_can_create_other_objs_denied(
        cursor, type_, make_test_permissions, new_organization):
    org = new_organization()
    user0 = make_test_permissions(org)
    authid = user0['user']['auth0_id']
    cursor.execute('SELECT user_can_create(%s, %s)',
                   (authid, type_))
    assert cursor.fetchone()[0] == 0


def test_user_can_create_multiple_permissions(cursor, make_user_roles,
                                              new_role, new_permission):
    """Make sure user_can_create works when duplicated create permission"""
    info = make_user_roles('create', 'forecasts')
    org = info['org']
    user = info['user']
    cursor.execute(
        'SELECT user_can_create(%s, %s)',
        (user['auth0_id'], 'forecasts'))
    assert cursor.fetchone()[0] == 1
    role = new_role(org=org)
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
    assert cursor.fetchone()[0] == 1


@pytest.mark.parametrize('otype', ['users', 'permissions', 'roles'])
def test_get_rbac_object_organization(cursor, make_user_roles, otype):
    vals = make_user_roles('read', onall=False)
    oid = vals[otype.rstrip('s')]['id']
    cursor.execute('SELECT get_rbac_object_organization(%s, %s)', (oid, otype))
    assert cursor.fetchone()[0] == vals['org']['id']


@pytest.mark.parametrize('otype', ['users', 'permissions', 'roles'])
def test_get_rbac_object_organization_fake(cursor, otype):
    oid = newuuid()
    cursor.execute('SELECT get_rbac_object_organization(%s, %s)', (oid, otype))
    assert cursor.fetchone()[0] is None


@pytest.mark.parametrize('otype', ['forecasts', 'observations',
                                   'cdf_forecasts', 'sites', 'aggregates'])
def test_get_rbac_object_organization_other_types(cursor, otype,
                                                  new_organization,
                                                  make_test_permissions):
    org = new_organization()
    others = make_test_permissions(org)
    oid = others[otype][0]['id']
    cursor.execute('SELECT get_rbac_object_organization(%s, %s)', (oid, otype))
    assert cursor.fetchone()[0] is None


@pytest.mark.parametrize('otype', ['forecasts', 'observations',
                                   'cdf_forecasts', 'sites', 'aggregates'])
def test_get_nonrbac_object_organization(cursor, otype,
                                         new_organization,
                                         make_test_permissions):
    org = new_organization()
    others = make_test_permissions(org)
    oid = others[otype][0]['id']
    cursor.execute('SELECT get_nonrbac_object_organization(%s, %s)',
                   (oid, otype))
    assert cursor.fetchone()[0] == org['id']


@pytest.mark.parametrize('otype', ['users', 'permissions', 'roles'])
def test_get_nonrbac_object_organization_other_types(cursor, otype,
                                                     new_organization,
                                                     make_test_permissions):
    org = new_organization()
    others = make_test_permissions(org)
    if otype == 'users':
        oid = others['user']['id']
    else:
        oid = others[otype][0]['id']
    cursor.execute('SELECT get_nonrbac_object_organization(%s, %s)',
                   (oid, otype))
    assert cursor.fetchone()[0] is None


@pytest.mark.parametrize('otype', ['forecasts', 'observations',
                                   'cdf_forecasts', 'sites', 'aggregates',
                                   'users', 'roles', 'permissions'])
def test_get_object_organization(cursor, otype,
                                 new_organization,
                                 make_test_permissions):
    org = new_organization()
    others = make_test_permissions(org)
    if otype == 'users':
        oid = others['user']['id']
    else:
        oid = others[otype][0]['id']
    cursor.execute('SELECT get_object_organization(%s, %s)',
                   (oid, otype))
    assert cursor.fetchone()[0] == org['id']


@pytest.mark.parametrize('otype', ['forecasts', 'observations',
                                   'cdf_forecasts', 'sites',
                                   'users', 'roles', 'permissions',
                                   'blah', 'aggregates'])
def test_get_object_organization_fake(cursor, otype):
    oid = newuuid()
    cursor.execute('SELECT get_object_organization(%s, %s)', (oid, otype))
    assert cursor.fetchone()[0] is None


@pytest.fixture()
def rbac_user(cursor, make_user_roles, new_permission):
    def f(read_obj_type, read_obj=True):
        vals = make_user_roles('update', 'permissions', True)
        if read_obj:
            perm = new_permission('read', read_obj_type, True, org=vals['org'])
            cursor.execute(
                'INSERT INTO role_permission_mapping (role_id, permission_id )'
                ' VALUES (%s, %s)', (vals['role']['id'], perm['id']))
        return vals['user']['auth0_id'], vals['org']
    return f


@pytest.mark.parametrize('action', ['create', 'update', 'read', 'delete'])
@pytest.mark.parametrize('otype', ['forecasts', 'observations',
                                   'cdf_forecasts', 'sites', 'aggregates',
                                   'users', 'roles', 'permissions'])
def test_is_permission_allowed(cursor, otype, rbac_user,
                               make_test_permissions,
                               new_permission, action):
    auth0id, org = rbac_user(otype)
    others = make_test_permissions(org)
    perm = new_permission(action, otype, False, org=org)
    if otype == 'users':
        oid = others['user']['id']
    else:
        oid = others[otype][0]['id']
    cursor.execute('SELECT is_permission_allowed(%s, %s, %s)',
                   (auth0id, perm['id'], oid))
    assert cursor.fetchone()[0] == 1


def test_is_permission_allowed_cantread(cursor, rbac_user,
                                        make_test_permissions,
                                        new_permission):
    action = 'read'
    otype = 'observations'
    auth0id, org = rbac_user(otype, False)
    others = make_test_permissions(org)
    perm = new_permission(action, otype, False, org=org)
    oid = others[otype][0]['id']
    cursor.execute('SELECT is_permission_allowed(%s, %s, %s)',
                   (auth0id, perm['id'], oid))
    assert cursor.fetchone()[0] == 0


def test_is_permission_allowed_diff_user_org(cursor, rbac_user,
                                             make_test_permissions,
                                             new_permission,
                                             new_user):
    action = 'create'
    otype = 'forecasts'
    _, org = rbac_user(otype)
    auth0id = new_user()['auth0_id']
    others = make_test_permissions(org)
    perm = new_permission(action, otype, False, org=org)
    oid = others[otype][0]['id']
    cursor.execute('SELECT is_permission_allowed(%s, %s, %s)',
                   (auth0id, perm['id'], oid))
    assert cursor.fetchone()[0] == 0


def test_is_permission_allowed_diff_perm_org(cursor, rbac_user,
                                             make_test_permissions,
                                             new_permission):

    action = 'read'
    otype = 'sites'
    auth0id, org = rbac_user(otype)
    others = make_test_permissions(org)
    perm = new_permission(action, otype, False)
    oid = others[otype][0]['id']
    cursor.execute('SELECT is_permission_allowed(%s, %s, %s)',
                   (auth0id, perm['id'], oid))
    assert cursor.fetchone()[0] == 0


def test_is_permission_allowed_diff_obj_org(cursor, rbac_user,
                                            make_test_permissions,
                                            new_permission,
                                            new_organization):
    action = 'delete'
    otype = 'roles'
    auth0id, org = rbac_user(otype)
    others = make_test_permissions(new_organization())
    perm = new_permission(action, otype, False, org=org)
    oid = others[otype][0]['id']
    cursor.execute('SELECT is_permission_allowed(%s, %s, %s)',
                   (auth0id, perm['id'], oid))
    assert cursor.fetchone()[0] == 0


def test_is_permission_allowed_cant_update_perm(
        cursor, make_user_roles, make_test_permissions,
        new_permission):
    action = 'read'
    otype = 'observations'
    vals = make_user_roles('read', otype, True)
    auth0id = vals['user']['auth0_id']
    org = vals['org']
    others = make_test_permissions(org)
    perm = new_permission(action, otype, False, org=org)
    oid = others[otype][0]['id']
    cursor.execute('SELECT is_permission_allowed(%s, %s, %s)',
                   (auth0id, perm['id'], oid))
    assert cursor.fetchone()[0] == 0


@pytest.mark.parametrize('other_obj', [
    'forecasts', 'observations', 'cdf_forecasts', 'aggregates', 'reports',
    'roles', 'users', 'sites'])
def test_is_read_values_any_allowed(
        cursor, make_user_roles, getfcn, other_obj):
    """That that a user can (and can not) perform the specified action"""
    newfcn, obj_type = getfcn
    info = make_user_roles('read_values', other_obj, True)
    authid = info['user']['auth0_id']
    obj = newfcn(org=info['org'])
    cursor.execute('SELECT is_read_values_any_allowed(%s, %s)',
                   (authid, obj['id']))
    if other_obj == obj_type:
        assert cursor.fetchone()[0] == 1
    else:
        assert cursor.fetchone()[0] == 0


@pytest.mark.parametrize('other_obj', [
    'forecasts', 'observations', 'cdf_forecasts', 'aggregates', 'reports',
    'roles', 'users', 'sites'])
def test_is_read_values_any_allowed_cdf_single(
        cursor, make_user_roles, new_cdf_forecast, other_obj):
    """That that a user can (and can not) perform the specified action"""
    info = make_user_roles('read_values', other_obj, True)
    authid = info['user']['auth0_id']
    obj = new_cdf_forecast(org=info['org'])
    for id_ in obj['constant_values'].keys():
        binid = uuid_to_bin(UUID(id_))
        cursor.execute('SELECT is_read_values_any_allowed(%s, %s)',
                       (authid, binid))
        if other_obj == 'cdf_forecasts':
            assert cursor.fetchone()[0] == 1
        else:
            assert cursor.fetchone()[0] == 0


@pytest.mark.parametrize('issame', [0, 1])
def test_is_read_values_any_allowed_cdf_single_specific(
        cursor, make_user_roles, new_cdf_forecast, issame):
    """That that a user can (and can not) perform the specified action"""
    perm = make_user_roles('read_values', 'cdf_forecasts', False)
    authid = perm['user']['auth0_id']
    firstobj = new_cdf_forecast(org=perm['org'])
    cursor.execute(
        'INSERT INTO permission_object_mapping (permission_id, object_id)'
        ' VALUES (%s, %s)', (perm['permission']['id'], firstobj['id'])
    )
    if issame:
        # permission has been added for firstobj cdf fx, but not
        obj = firstobj
    else:
        obj = new_cdf_forecast(org=perm['org'])

    for id_ in obj['constant_values'].keys():
        binid = uuid_to_bin(UUID(id_))
        cursor.execute('SELECT is_read_values_any_allowed(%s, %s)',
                       (authid, binid))
        assert cursor.fetchone()[0] == issame
