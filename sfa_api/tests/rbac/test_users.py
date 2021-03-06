import pytest


from sfa_api.conftest import BASE_URL


@pytest.fixture()
def mock_email_funcs(mocker, auth0id, user_email, external_auth0id,
                     user_id):
    def check(email):
        if email == user_email:
            return auth0id
        elif email == 'reference@solarforecastarbiter.org':
            return external_auth0id
        elif email == 'unaffiliated@what.com':
            return 'auth0|test_public'
        else:
            return 'Unable to retrieve'

    mocker.patch('sfa_api.users.get_auth0_id_of_user',
                 new=check)
    mocker.patch('sfa_api.users.get_email_of_user',
                 return_value=user_email)


@pytest.fixture()
def api(api, mock_email_funcs):
    return api


@pytest.fixture(params=['id', 'email'])
def both_paths(request):
    def f(id_, email):
        if request.param == 'id':
            return f'/users/{id_}'
        else:
            return f'/users-by-email/{email}'
    return f


@pytest.fixture()
def normal_paths(both_paths, user_id, user_email):
    return both_paths(user_id, user_email)


@pytest.fixture()
def dne_paths(both_paths, missing_id):
    return both_paths(missing_id, 'no@no.com')


@pytest.fixture()
def external_paths(both_paths, external_userid):
    return both_paths(external_userid, 'reference@solarforecastarbiter.org')


def test_get_user(api, user_id, user_email, normal_paths):
    get_user = api.get(normal_paths, BASE_URL)
    assert get_user.status_code == 200
    user_fields = get_user.get_json()
    assert user_fields['user_id'] == user_id
    assert 'organization' in user_fields
    assert 'created_at' in user_fields
    assert 'modified_at' in user_fields
    assert 'roles' in user_fields
    assert user_fields['email'] == user_email
    assert 'auth0_id' not in user_fields
    assert user_fields['created_at'].endswith('+00:00')
    assert user_fields['modified_at'].endswith('+00:00')


def test_get_user_dne(api, dne_paths):
    get_user = api.get(dne_paths, BASE_URL)
    assert get_user.status_code == 404


def test_get_user_no_perms(
        api, remove_perms_from_current_role, external_paths):
    remove_perms_from_current_role('read', 'users')
    get_user = api.get(external_paths, BASE_URL)
    assert get_user.status_code == 404


def test_list_users(api, user_id):
    get_users = api.get('/users/', BASE_URL)
    assert get_users.status_code == 200
    user_list = get_users.json
    assert len(user_list) > 0
    assert user_id in [user['user_id'] for user in user_list]
    assert all([user.get('email', False) for user in user_list])


def test_list_users_no_perm(api, remove_perms_from_current_role, user_id):
    remove_perms_from_current_role('read', 'users')
    get_users = api.get('/users/', BASE_URL)
    assert get_users.status_code == 200
    only_self = get_users.json
    assert len(only_self) == 1
    the_user = only_self[0]
    assert the_user['user_id'] == user_id


def test_add_role_to_user(api, new_role, normal_paths):
    role_id = new_role()
    add_role = api.post(normal_paths + f'/roles/{role_id}',
                        BASE_URL)
    assert add_role.status_code == 204
    get_user = api.get(normal_paths, BASE_URL)
    user = get_user.json
    roles_on_user = user['roles'].keys()
    assert role_id in roles_on_user


def test_add_role_to_user_user_dne(api, new_role, dne_paths):
    role_id = new_role()
    add_role = api.post(dne_paths + f'/roles/{role_id}', BASE_URL)
    assert add_role.status_code == 404


def test_add_role_to_user_role_dne(api, missing_id, normal_paths):
    add_role = api.post(normal_paths + f'/roles/{missing_id}', BASE_URL)
    assert add_role.status_code == 404


def test_add_role_to_user_no_perms(
        api, normal_paths, new_role, remove_perms_from_current_role):
    role_id = new_role()
    remove_perms_from_current_role('grant', 'roles')
    add_role = api.post(normal_paths + f'/roles/{role_id}', BASE_URL)
    assert add_role.status_code == 404
    get_user = api.get(normal_paths, BASE_URL)
    user = get_user.json
    roles_on_user = user['roles'].keys()
    assert role_id not in roles_on_user


@pytest.mark.parametrize('path', ('/users/{id_}', '/users-by-email/{email}'))
def test_add_role_to_user_no_tou(
        api, unaffiliated_userid, new_role, remove_perms_from_current_role,
        path):
    role_id = new_role()
    remove_perms_from_current_role('grant', 'roles')
    add_role = api.post(
        path.format(id_=unaffiliated_userid, email='unaffiliated@what.com') +
        f'/roles/{role_id}',
        BASE_URL)
    assert add_role.status_code == 404


def test_remove_role_from_user(api, new_role, normal_paths):
    role_id = new_role()
    add_role = api.post(normal_paths + f'/roles/{role_id}', BASE_URL)
    assert add_role.status_code == 204
    remove_role = api.delete(normal_paths + f'/roles/{role_id}', BASE_URL)
    assert remove_role.status_code == 204
    get_user = api.get(normal_paths, BASE_URL)
    user = get_user.json
    roles_on_user = user['roles'].keys()
    assert role_id not in roles_on_user


def test_remove_role_from_user_user_dne(api, dne_paths, new_role):
    role_id = new_role()
    rm_role = api.delete(dne_paths + f'/roles/{role_id}', BASE_URL)
    assert rm_role.status_code == 204


def test_remove_role_from_user_role_dne(api, normal_paths, missing_id):
    get_user = api.get(normal_paths, BASE_URL)
    user = get_user.json
    roles_on_user = user['roles'].keys()
    assert missing_id not in roles_on_user

    rm_role = api.delete(normal_paths + f'/roles/{missing_id}', BASE_URL)
    assert rm_role.status_code == 404


def test_remove_role_from_user_no_perms(api, normal_paths, new_role,
                                        remove_perms_from_current_role):
    role_id = new_role()
    add_role = api.post(normal_paths + f'/roles/{role_id}', BASE_URL)
    assert add_role.status_code == 204
    remove_perms_from_current_role('revoke', 'roles')
    remove_role = api.delete(normal_paths + f'/roles/{role_id}', BASE_URL)
    assert remove_role.status_code == 404


def test_current_user(api):
    user_req = api.get('/users/current', BASE_URL)
    user = user_req.json
    assert 'created_at' in user
    assert 'modified_at' in user
    assert 'roles' in user
    assert 'email' in user
    assert 'auth0_id' not in user
    assert user['organization'] == 'Organization 1'
    assert user['user_id'] == '0c90950a-7cca-11e9-a81f-54bf64606445'


def test_add_role_to_user_already_granted(api, new_role, normal_paths):
    role_id = new_role()
    add_role = api.post(normal_paths + f'/roles/{role_id}', BASE_URL)
    assert add_role.status_code == 204
    get_user = api.get(normal_paths, BASE_URL)
    user = get_user.json
    roles_on_user = user['roles'].keys()
    assert role_id in roles_on_user
    add_role = api.post(normal_paths + f'/roles/{role_id}', BASE_URL)
    assert add_role.status_code == 400
    assert add_role.json == {"errors": {
        "user": ["User already granted role."]}}


def test_add_role_to_user_already_granted_lost_perms(
        api, user_id, new_role, remove_perms_from_current_role, normal_paths):
    role_id = new_role()
    add_role = api.post(normal_paths + f'/roles/{role_id}', BASE_URL)
    assert add_role.status_code == 204
    get_user = api.get(normal_paths, BASE_URL)
    user = get_user.json
    roles_on_user = user['roles'].keys()
    remove_perms_from_current_role('grant', 'roles')
    assert role_id in roles_on_user
    add_role = api.post(normal_paths + f'/roles/{role_id}', BASE_URL)
    assert add_role.status_code == 404


def test_user_email(api, user_id):
    res = api.get(f'/users/{user_id}/email', BASE_URL)
    assert res.data.decode('utf-8') == 'testing@solarforecastarbiter.org'


def test_user_email_user_dne(api, missing_id):
    res = api.get(f'/users/{missing_id}/email', BASE_URL)
    assert res.status_code == 404


def test_user_email_user_unaffiliated(api, unaffiliated_userid):
    res = api.get(f'/users/{unaffiliated_userid}/email', BASE_URL)
    assert res.status_code == 404


def test_get_user_actions_on_object(api, forecast_id):
    res = api.get(f'/users/actions-on/{forecast_id}', BASE_URL)
    json_res = res.json
    assert json_res['object_id'] == forecast_id
    assert sorted(json_res['actions']) == sorted(['delete', 'write_values',
                                                  'delete_values', 'read',
                                                  'read_values', 'update'])


def test_get_user_actions_on_object_404_missing(api, missing_id):
    res = api.get(f'/users/actions-on/{missing_id}', BASE_URL)
    assert res.status_code == 404


def test_get_user_actions_on_object_404_no_permissions(
        api, forecast_id, remove_perms_from_current_role):
    res = api.get(f'/users/actions-on/{forecast_id}', BASE_URL)
    for action in res.json['actions'][:-1]:
        remove_perms_from_current_role(action, 'forecasts')
        less_one = api.get(f'/users/actions-on/{forecast_id}', BASE_URL)
        assert action not in less_one.json['actions']
    # the last action should result in a 404 to this endpoint
    remove_perms_from_current_role(res.json['actions'][-1], 'forecasts')
    res = api.get(f'/users/actions-on/{forecast_id}', BASE_URL)
    assert res.status_code == 404


all_object_types = ['sites', 'aggregates', 'cdf_forecasts', 'forecasts',
                    'observations', 'roles', 'permissions', 'reports']


@pytest.mark.parametrize('to_remove', [
    ['sites'],
    ['forecasts'],
    ['roles', 'permissions'],
    ['forecasts', 'observations', 'aggregates', 'reports'],
])
def test_get_user_create_permissions(
        api, to_remove, remove_perms_from_current_role):
    for otype in to_remove:
        remove_perms_from_current_role('create', otype)
    res = api.get('/users/can-create/', BASE_URL)
    expected_types = [otype for otype in all_object_types
                      if otype not in to_remove]
    assert res.json == {'can_create': expected_types}


@pytest.mark.parametrize('object_type,expected_actions', [
    ('observations', ['create', 'read', 'delete', 'read_values',
                      'write_values', 'delete_values']),
    ('forecasts', ['create', 'read', 'delete', 'read_values', 'write_values',
                   'delete_values']),
    ('cdf_forecasts', ['create', 'read', 'update', 'delete', 'read_values',
                       'write_values', 'delete_values']),
    ('roles', ['create', 'read', 'update', 'delete', 'grant', 'revoke']),
    ('permissions', ['create', 'read', 'update', 'delete']),
    ('users', ['read', 'update']),
    ('reports', ['create', 'read', 'update', 'delete', 'read_values',
                 'write_values']),
])
def test_get_user_actions_on_type(
        api, object_type, expected_actions):
    res = api.get(f'/users/actions-on-type/{object_type}', BASE_URL)
    objects = res.json['objects']
    for object_dict in objects:
        assert object_dict['actions'].sort() == expected_actions.sort()


@pytest.mark.parametrize('object_type,expected_actions', [
    ('observations', ['create', 'read', 'delete', 'read_values',
                      'write_values', 'delete_values', 'update']),
    ('forecasts', ['create', 'read', 'delete', 'read_values', 'write_values',
                   'delete_values', 'update']),
    ('aggregates', ['create', 'read', 'update', 'delete', 'read_values',
                    'write_values', 'delete_values']),
    ('cdf_forecasts', ['create', 'read', 'update', 'delete', 'read_values',
                       'write_values', 'delete_values']),
    ('roles', ['create', 'grant', 'revoke', 'delete',  'read']),
    ('permissions', ['create', 'delete', 'update', 'read']),
    ('users', ['read', 'update']),
    ('reports', ['create', 'read', 'update', 'delete', 'read_values',
                 'write_values']),
])
def test_get_user_actions_on_type_minimum_test_perms(
        api, object_type, expected_actions, remove_all_perms, orgid):
    if object_type == 'cdf_forecasts':
        id_key = 'forecast_id'
        listing_path = '/forecasts/cdf/'
    else:
        if object_type == 'forecasts':
            listing_path = '/forecasts/single/'
        else:
            listing_path = f'/{object_type}/'
        id_key = f'{object_type[:-1]}_id'

    listing = api.get(listing_path, BASE_URL).json
    all_objects = {o[id_key]: o for o in listing}

    for action in expected_actions:
        remove_all_perms(action, object_type)
    res = api.get(f'/users/actions-on-type/{object_type}', BASE_URL)

    assert res.json['object_type'] == object_type

    objects_list = res.json['objects']
    objects = {o['object_id']: o['actions'] for o in objects_list}

    for k, v in objects.items():
        the_object = all_objects[k]
        org = the_object.get('provider', the_object.get('organization', None))
        if object_type == 'roles':
            # can't test roles for update, becasue removing it causes perm
            # removal to fail, and resets the nocommit cursor so instead test
            # that only these minimal permissions remain.
            assert v == ['update']
            assert the_object['name'] in [
                'Test user role',
                'Read Weather Station',
                'DEFAULT User role 0c90950a-7cca-11e9-a81f-54bf64606445']
        else:
            for action in v:
                assert action in ['read', 'read_values']
                assert org == 'Reference'


def test_get_user_actions_on_type_invalid_type(api):
    res = api.get('/users/actions-on-type/bad-type', BASE_URL)
    assert res.status_code == 400
    assert res.json == {
        'errors': {
            'object_type': ['Must be one of: sites, aggregates, forecasts, '
                            'observations, users, roles, permissions, '
                            'cdf_forecasts, reports'],
            }
        }


def test_get_user_actions_on_type_no_type(api):
    res = api.get('/users/actions-on-type/', BASE_URL)
    assert res.status_code == 404
