from sfa_api.conftest import BASE_URL


def test_get_user(api, user_id):
    get_user = api.get(f'/users/{user_id}', BASE_URL)
    assert get_user.status_code == 200
    user_fields = get_user.json.keys()
    assert 'user_id' in user_fields
    assert 'organization' in user_fields
    assert 'created_at' in user_fields
    assert 'modified_at' in user_fields
    assert 'roles' in user_fields


def test_get_user_dne(api, missing_id):
    get_user = api.get(f'/users/{missing_id}', BASE_URL)
    assert get_user.status_code == 404


def test_get_user_no_perms(api, user_id, external_userid, remove_perms):
    remove_perms('read', 'users')
    get_user = api.get(f'/users/{external_userid}', BASE_URL)
    assert get_user.status_code == 404


def test_list_users(api, user_id):
    get_users = api.get('/users/', BASE_URL)
    assert get_users.status_code == 200
    user_list = get_users.json
    assert len(user_list) > 0
    assert user_id in [user['user_id'] for user in user_list]


def test_list_users_no_perm(api, remove_perms, user_id):
    remove_perms('read', 'users')
    get_users = api.get('/users/', BASE_URL)
    assert get_users.status_code == 200
    only_self = get_users.json
    assert len(only_self) == 1
    the_user = only_self[0]
    assert the_user['user_id'] == user_id


def test_add_role_to_user(api, user_id, new_role):
    role_id = new_role()
    add_role = api.post(f'/users/{user_id}/roles/{role_id}', BASE_URL)
    assert add_role.status_code == 204
    get_user = api.get(f'/users/{user_id}', BASE_URL)
    user = get_user.json
    roles_on_user = user['roles'].keys()
    assert role_id in roles_on_user


def test_add_role_to_user_user_dne(api, missing_id, new_role):
    role_id = new_role()
    add_role = api.post(f'/users/{missing_id}/roles/{role_id}', BASE_URL)
    assert add_role.status_code == 404


def test_add_role_to_user_role_dne(api, user_id, missing_id):
    add_role = api.post(f'/users/{user_id}/roles/{missing_id}', BASE_URL)
    assert add_role.status_code == 404


def test_add_role_to_user_no_perms(api, user_id, new_role, remove_perms):
    role_id = new_role()
    remove_perms('grant', 'roles')
    add_role = api.post(f'/users/{user_id}/roles/{role_id}', BASE_URL)
    assert add_role.status_code == 404
    get_user = api.get(f'/users/{user_id}', BASE_URL)
    user = get_user.json
    roles_on_user = user['roles'].keys()
    assert role_id not in roles_on_user


def test_add_role_to_user_no_tou(
        api, unaffiliated_userid, new_role, remove_perms):
    role_id = new_role()
    remove_perms('grant', 'roles')
    add_role = api.post(
        f'/users/{unaffiliated_userid}/roles/{role_id}',
        BASE_URL)
    assert add_role.status_code == 404


def test_remove_role_from_user(api, user_id, new_role):
    role_id = new_role()
    add_role = api.post(f'/users/{user_id}/roles/{role_id}', BASE_URL)
    assert add_role.status_code == 204
    remove_role = api.delete(f'/users/{user_id}/roles/{role_id}', BASE_URL)
    assert remove_role.status_code == 204
    get_user = api.get(f'/users/{user_id}', BASE_URL)
    user = get_user.json
    roles_on_user = user['roles'].keys()
    assert role_id not in roles_on_user


def test_remove_role_from_user_user_dne(api, missing_id, new_role):
    role_id = new_role()
    add_role = api.delete(f'/users/{missing_id}/roles/{role_id}', BASE_URL)
    assert add_role.status_code == 204


def test_remove_role_from_user_role_dne(api, user_id, missing_id):
    get_user = api.get(f'/users/{user_id}', BASE_URL)
    user = get_user.json
    roles_on_user = user['roles'].keys()
    assert missing_id not in roles_on_user

    add_role = api.delete(f'/users/{user_id}/roles/{missing_id}', BASE_URL)
    assert add_role.status_code == 404


def test_remove_role_from_user_no_perms(api, user_id, new_role, remove_perms):
    role_id = new_role()
    add_role = api.post(f'/users/{user_id}/roles/{role_id}', BASE_URL)
    assert add_role.status_code == 204
    remove_perms('revoke', 'roles')
    remove_role = api.delete(f'/users/{user_id}/roles/{role_id}', BASE_URL)
    assert remove_role.status_code == 404


def test_current_user(api):
    user_req = api.get('/users/current', BASE_URL)
    user = user_req.json
    assert user['auth0_id'] == 'auth0|5be343df7025406237820b85'
    assert user['organization'] == 'Organization 1'
    assert user['user_id'] == '0c90950a-7cca-11e9-a81f-54bf64606445'


def test_add_role_to_user_already_granted(api, user_id, new_role):
    role_id = new_role()
    add_role = api.post(f'/users/{user_id}/roles/{role_id}', BASE_URL)
    assert add_role.status_code == 204
    get_user = api.get(f'/users/{user_id}', BASE_URL)
    user = get_user.json
    roles_on_user = user['roles'].keys()
    assert role_id in roles_on_user
    add_role = api.post(f'/users/{user_id}/roles/{role_id}', BASE_URL)
    assert add_role.status_code == 400
    assert add_role.json == {"errors": {
        "user": ["User already granted role."]}}
