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
    mocker.patch('sfa_api.users.list_user_emails',
                 return_value={user_id: user_email})


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


def test_get_user_no_perms(api, remove_perms, external_paths):
    remove_perms('read', 'users')
    get_user = api.get(external_paths, BASE_URL)
    assert get_user.status_code == 404


def test_list_users(api, user_id):
    get_users = api.get('/users/', BASE_URL)
    assert get_users.status_code == 200
    user_list = get_users.json
    assert len(user_list) > 0
    assert user_id in [user['user_id'] for user in user_list]
    assert all([user.get('email', False) for user in user_list])


def test_list_users_no_perm(api, remove_perms, user_id):
    remove_perms('read', 'users')
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


def test_add_role_to_user_no_perms(api, normal_paths, new_role, remove_perms):
    role_id = new_role()
    remove_perms('grant', 'roles')
    add_role = api.post(normal_paths + f'/roles/{role_id}', BASE_URL)
    assert add_role.status_code == 404
    get_user = api.get(normal_paths, BASE_URL)
    user = get_user.json
    roles_on_user = user['roles'].keys()
    assert role_id not in roles_on_user


@pytest.mark.parametrize('path', ('/users/{id_}', '/users-by-email/{email}'))
def test_add_role_to_user_no_tou(
        api, unaffiliated_userid, new_role, remove_perms, path):
    role_id = new_role()
    remove_perms('grant', 'roles')
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
                                        remove_perms):
    role_id = new_role()
    add_role = api.post(normal_paths + f'/roles/{role_id}', BASE_URL)
    assert add_role.status_code == 204
    remove_perms('revoke', 'roles')
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
        api, user_id, new_role, remove_perms, normal_paths):
    role_id = new_role()
    add_role = api.post(normal_paths + f'/roles/{role_id}', BASE_URL)
    assert add_role.status_code == 204
    get_user = api.get(normal_paths, BASE_URL)
    user = get_user.json
    roles_on_user = user['roles'].keys()
    remove_perms('grant', 'roles')
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
