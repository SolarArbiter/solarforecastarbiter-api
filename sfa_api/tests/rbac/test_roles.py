import pytest


from sfa_api.conftest import BASE_URL
from sfa_api.tests.rbac.conftest import ROLE


def get_role(api, role_id):
    return api.get(f'/roles/{role_id}', BASE_URL)


def get_perm(api, perm_id):
    return api.get(f'/permissions/{perm_id}', BASE_URL)


def test_list_roles(api):
    roles = api.get('/roles/',
                    BASE_URL)
    assert roles.json[0]['name'] == 'Test user role'
    assert roles.status_code == 200


def test_get_role(api, new_role):
    role_id = new_role()
    get_role = api.get(f'/roles/{role_id}', BASE_URL)
    assert get_role.status_code == 200
    role = get_role.json
    assert role['name'] == ROLE['name']
    assert role['description'] == ROLE['description']
    assert role['organization'] == 'Organization 1'
    assert type(role['permissions']) == dict
    assert len(role['permissions'].keys()) == 1
    assert type(role['users']) == dict
    assert role['created_at'].endswith('+00:00')
    assert role['modified_at'].endswith('+00:00')


def test_list_roles_missing_perms(api, user_id, remove_perms):
    remove_perms('read', 'roles')
    roles = api.get('/roles/', BASE_URL)
    assert roles.status_code == 200
    user_roles = roles.json
    assert len(user_roles) == 1
    assert user_roles[0]['name'] == f'DEFAULT User role {user_id}'


def test_create_delete_role(api):
    new_role_id = api.post('/roles/', BASE_URL, json=ROLE)
    assert new_role_id.status_code == 201
    new_role_id = new_role_id.data.decode('utf-8')
    new_role = api.get(f'/roles/{new_role_id}', BASE_URL)
    assert new_role.status_code == 200
    deleted = api.delete(f'/roles/{new_role_id}', BASE_URL)
    assert deleted.status_code == 204
    role_dne = api.get(f'/roles/{new_role_id}', BASE_URL)
    assert role_dne.status_code == 404


@pytest.mark.parametrize('role,error', [
    ({'name': 'brad'}, '{"description":["Missing data for required field."]}'),
    ({'description': 'brad role'},
     '{"name":["Missing data for required field."]}'),
    ({'name': '!@$^Y', 'description': 'description'},
     '{"name":["Invalid characters in string."]}'),
])
def test_create_role_invalid_json(api, role, error):
    failed_role = api.post('/roles/', BASE_URL, json=role)
    assert failed_role.status_code == 400
    assert failed_role.get_data(as_text=True) == f'{{"errors":{error}}}\n'


def test_create_role_missing_perms(api, remove_perms):
    remove_perms('create', 'roles')
    failed_role = api.post(f'/roles/', BASE_URL, json=ROLE)
    assert failed_role.status_code == 404


def test_get_role_dne(api, missing_id):
    missing = api.get(f'/roles/{missing_id}', BASE_URL)
    assert missing.status_code == 404


def test_get_role_missing_perms(api, new_role, remove_perms):
    role_id = new_role()
    assert api.get(f'/roles/{role_id}', BASE_URL).status_code == 200
    remove_perms('read', 'roles')
    assert api.get(f'/roles/{role_id}', BASE_URL).status_code == 404


def test_delete_role(api, new_role):
    role_id = new_role()
    assert api.get(f'/roles/{role_id}', BASE_URL).status_code == 200
    deleted = api.delete(f'/roles/{role_id}', BASE_URL)
    assert deleted.status_code == 204
    assert api.get(f'/roles/{role_id}', BASE_URL).status_code == 404


def test_delete_role_dne(api, missing_id):
    missing = api.delete(f'/roles/{missing_id}', BASE_URL)
    assert missing.status_code == 404


def test_delete_role_missing_perms(api, new_role, remove_perms):
    role_id = new_role()
    remove_perms('delete', 'roles')
    failed_delete = api.delete(f'/roles/{role_id}', BASE_URL)
    assert failed_delete.status_code == 404


def test_add_perm_to_role(api, new_role, new_perm, missing_id):
    role_id = new_role()
    perm_id = new_perm()
    perms = api.get('/permissions/', BASE_URL)
    assert perm_id in [perm['permission_id'] for perm in perms.json]
    added_perm = api.post(f'/roles/{role_id}/permissions/{perm_id}',
                          BASE_URL)
    assert added_perm.status_code == 204
    role = get_role(api, role_id).json
    permissions_on_role = role['permissions'].keys()
    assert perm_id in permissions_on_role


def test_add_perm_to_role_role_dne(api, missing_id, new_perm):
    perm_id = new_perm()
    role_dne = api.post(f'/roles/{missing_id}/permissions/{perm_id}',
                        BASE_URL)
    assert role_dne.status_code == 404


def test_add_perm_to_role_perm_dne(api, missing_id, new_role):
    role_id = new_role()
    perm_dne = api.post(f'/roles/{role_id}/permissions/{missing_id}',
                        BASE_URL)
    assert perm_dne.status_code == 404


@pytest.mark.parametrize('object_type', [
    'roles', 'permissions', 'users']
)
def test_add_perm_to_role_external_role_admin_perm(
        api, new_role, new_perm, external_userid, object_type):
    role_id = new_role()
    permission_id = new_perm(object_type=object_type, action='create')
    add_role_to_user = api.post(
        f'/users/{external_userid}/roles/{role_id}',
        BASE_URL)
    assert add_role_to_user.status_code == 204
    add_perm_to_role = api.post(
        f'/roles/{role_id}/permissions/{permission_id}',
        BASE_URL)
    assert add_perm_to_role.status_code == 404


def test_remove_perm_from_role(api, new_role, new_perm):
    role_id = new_role()
    perm_id = new_perm()
    added_perm = api.post(f'roles/{role_id}/permissions/{perm_id}',
                          BASE_URL)
    assert added_perm.status_code == 204
    removed_perm = api.delete(f'/roles/{role_id}/permissions/{perm_id}',
                              BASE_URL)
    assert removed_perm.status_code == 204
    role = get_role(api, role_id).json
    permissions_on_role = role['permissions'].keys()
    assert perm_id not in permissions_on_role


def test_remove_perm_from_role_role_dne(api, missing_id, new_perm):
    perm_id = new_perm()
    removed_perm = api.delete(f'/roles/{missing_id}/permissions/{perm_id}',
                              BASE_URL)
    assert removed_perm.status_code == 404


def test_remove_perm_from_role_perm_dne(api, new_role, missing_id):
    # test that perms aren't modified even though a 204 is returned
    role_id = new_role()
    get_role = api.get(f'/roles/{role_id}', BASE_URL)
    role = get_role.json
    perms_on_role = role['permissions']
    removed_perm = api.delete(f'/roles/{role_id}/permissions/{missing_id}',
                              BASE_URL)
    assert removed_perm.status_code == 204
    get_role = api.get(f'/roles/{role_id}', BASE_URL)
    role = get_role.json
    new_perms_on_role = role['permissions']
    assert perms_on_role == new_perms_on_role


def test_add_perm_to_role_missing_perm(api, new_role, new_perm, remove_perms):
    remove_perms('update', 'roles')
    role_id = new_role()
    perm_id = new_perm()
    failed_add = api.post(f'/roles/{role_id}/permissions/{perm_id}',
                          BASE_URL)
    assert failed_add.status_code == 404


def test_add_perm_to_role_already_granted(api, new_role, new_perm, missing_id):
    role_id = new_role()
    perm_id = new_perm()
    perms = api.get('/permissions/', BASE_URL)
    assert perm_id in [perm['permission_id'] for perm in perms.json]
    added_perm = api.post(f'/roles/{role_id}/permissions/{perm_id}',
                          BASE_URL)
    assert added_perm.status_code == 204
    added_perm = api.post(f'/roles/{role_id}/permissions/{perm_id}',
                          BASE_URL)
    assert added_perm.status_code == 400
    assert added_perm.json == {"errors": {
        "role": ["Role already contains permission."]}}


def test_add_perm_to_role_already_granted_lost_perms(
        api, new_role, new_perm, missing_id, remove_perms):
    role_id = new_role()
    perm_id = new_perm()
    perms = api.get('/permissions/', BASE_URL)
    assert perm_id in [perm['permission_id'] for perm in perms.json]
    added_perm = api.post(f'/roles/{role_id}/permissions/{perm_id}',
                          BASE_URL)
    assert added_perm.status_code == 204
    remove_perms('update', 'roles')
    added_perm = api.post(f'/roles/{role_id}/permissions/{perm_id}',
                          BASE_URL)
    assert added_perm.status_code == 404
