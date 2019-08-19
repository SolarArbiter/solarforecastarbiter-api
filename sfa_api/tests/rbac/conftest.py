import pytest


from flask import _request_ctx_stack


from sfa_api.conftest import BASE_URL, VALID_OBS_JSON


ROLE = {
    "name": "test created role",
    "description": "testing role creation",
}

PERMISSION = {
    "action": "read",
    "applies_to_all": False,
    "description": "test created permission",
    "object_type": "observations",
}


@pytest.fixture()
def user_id():
    return '0c90950a-7cca-11e9-a81f-54bf64606445'


# User id of a permission-less unaffiliated user.
@pytest.fixture()
def external_userid():
    return 'ef026b76-c049-11e9-9c7e-0242ac120002'


@pytest.fixture()
def api(sql_app_no_commit, mocker):
    def add_user():
        _request_ctx_stack.top.user = 'auth0|5be343df7025406237820b85'
        return True

    verify = mocker.patch('sfa_api.utils.auth.verify_access_token')
    verify.side_effect = add_user
    yield sql_app_no_commit.test_client()


@pytest.fixture
def new_role(api):
    def fn(**kwargs):
        role_json = ROLE.copy()
        role_json.update(kwargs)
        role = api.post(f'/roles/', BASE_URL, json=role_json)
        role_id = role.data.decode('utf-8')
        return role_id
    return fn


@pytest.fixture
def new_observation(api):
    def fn():
        obs = api.post(f'/observations/', BASE_URL, json=VALID_OBS_JSON)
        obs_id = obs.data.decode('utf-8')
        return obs_id
    return fn


@pytest.fixture
def new_perm(api):
    def fn(**kwargs):
        perm_json = PERMISSION.copy()
        perm_json.update(kwargs)
        perm = api.post(f'/permissions/', BASE_URL, json=perm_json)
        perm_id = perm.data.decode('utf-8')
        return perm_id
    return fn


@pytest.fixture
def current_role(api):
    roles_req = api.get('/roles/', BASE_URL)
    role = roles_req.json[0]
    return role['role_id']


@pytest.fixture
def remove_perms(api, current_role):
    def fn(action, object_type):
        perm_req = api.get('/permissions/', BASE_URL)
        perms = perm_req.json
        to_remove = [perm['permission_id'] for perm in perms
                     if perm['object_type'] == object_type
                     and perm['action'] == action]
        for perm_id in to_remove:
            api.delete(f'/roles/{current_role}/permissions/{perm_id}',
                       BASE_URL)
    return fn
