import pytest


import pymysql
from sfa_api import admincli
from sfa_api import create_app
from sfa_api.conftest import _make_nocommit_cursor
from sfa_api.utils import storage_interface


def org_dict(org_list):
    return {o['name']: o for o in org_list}


def user_dict(user_list):
    return {u['id']: u for u in user_list}


@pytest.fixture()
def app_cli_runner(mocker):
    app = create_app('AdminTestConfig')
    with app.app_context():
        try:
            storage_interface.mysql_connection()
        except pymysql.err.OperationalError:
            pytest.skip('No connection to test database')
        else:
            with _make_nocommit_cursor(mocker):
                yield app.test_cli_runner()


@pytest.fixture()
def dict_cursor():
    yield storage_interface.get_cursor('dict', commit=False)


def test_create_org(mocker, app_cli_runner, dict_cursor):
    r = app_cli_runner.invoke(admincli.create_organization, ['clitestorg'])
    assert 'Created organization clitestorg.\n' == r.output

    with dict_cursor as sql_cursor:
        sql_cursor.callproc('list_all_organizations')
        orgs = sql_cursor.fetchall()
        assert 'clitestorg' in [o['name'] for o in orgs]


def test_create_org_org_exists(mocker, app_cli_runner):
    r = app_cli_runner.invoke(admincli.create_organization, ['clitestorg'])
    assert 'Created organization clitestorg.\n' == r.output
    r = app_cli_runner.invoke(admincli.create_organization, ['clitestorg'])
    assert 'Organization clitestorg already exists.\n' == r.output


def test_create_org_name_too_long(mocker, app_cli_runner):
    r = app_cli_runner.invoke(
        admincli.create_organization,
        ['This organization name is too long and will error'])
    assert "Organization name must be 32 characters or fewer.\n" == r.output


def test_add_user_to_org(
        app_cli_runner, unaffiliated_userid, test_orgid,
        dict_cursor):
    r = app_cli_runner.invoke(
        admincli.add_user_to_org,
        [unaffiliated_userid, test_orgid])
    assert (f'Added user {unaffiliated_userid} to organization '
            f'{test_orgid}\n') == r.output
    with dict_cursor as cursor:
        cursor.callproc('list_all_users')
        users = cursor.fetchall()
        for user in users:
            if user['id'] == unaffiliated_userid:
                assert user['organization_id'] == test_orgid


def test_add_user_to_org_affiliated_user(
        app_cli_runner, user_id, test_orgid):
    r = app_cli_runner.invoke(
        admincli.add_user_to_org,
        [user_id, test_orgid])
    assert 'Cannot add affiliated user to organization\n' == r.output


def test_add_user_to_org_invalid_orgid(
        app_cli_runner, unaffiliated_userid):
    r = app_cli_runner.invoke(
        admincli.add_user_to_org,
        [unaffiliated_userid, 'invalid-uuid'])
    assert 'Badly formed organization_id\n' == r.output


def test_add_user_to_org_invalid_userid(
        app_cli_runner, test_orgid):
    r = app_cli_runner.invoke(
        admincli.add_user_to_org,
        ['invalid-uuid', test_orgid])
    assert 'Badly formed user_id\n' == r.output


def test_add_user_to_org_user_dne(
        app_cli_runner, missing_id, test_orgid):
    r = app_cli_runner.invoke(
        admincli.add_user_to_org,
        [missing_id, test_orgid])
    assert 'Cannot add affiliated user to organization\n' == r.output


def test_add_user_to_org_org_dne(
        app_cli_runner, unaffiliated_userid, missing_id):
    r = app_cli_runner.invoke(
        admincli.add_user_to_org,
        [unaffiliated_userid, missing_id])
    assert 'Organization does not exist\n' == r.output


@pytest.fixture(scope='function')
def new_org_with_user(dict_cursor, unaffiliated_userid):
    with dict_cursor as sql_cursor:
        sql_cursor.callproc('create_organization', ('clitestorg',))
        sql_cursor.callproc('list_all_organizations')
        orgid = [o['id'] for o in sql_cursor.fetchall()
                 if o['name'] == 'clitestorg'][0]
        sql_cursor.callproc('add_user_to_org', (unaffiliated_userid, orgid))
    return (orgid, unaffiliated_userid)


@pytest.fixture(scope='function')
def new_org_without_user(dict_cursor):
    with dict_cursor as sql_cursor:
        sql_cursor.callproc('create_organization', ('clitestorg',))
        sql_cursor.callproc('list_all_organizations')
        orgid = [o['id'] for o in sql_cursor.fetchall()
                 if o['name'] == 'clitestorg'][0]
    return orgid


def test_promote_to_admin(
        dict_cursor, app_cli_runner, new_org_with_user):
    orgid = new_org_with_user[0]
    userid = new_org_with_user[1]
    r = app_cli_runner.invoke(
        admincli.promote_to_admin,
        [userid, orgid])
    assert (f'Promoted user {userid} to administrate '
            f'organization {orgid}\n') == r.output


def test_promote_to_admin_invalid_userid(
        dict_cursor, app_cli_runner, new_org_with_user):
    orgid = new_org_with_user[0]
    r = app_cli_runner.invoke(
        admincli.promote_to_admin,
        ['baduuid', orgid])
    assert r.output == 'Badly formed user_id\n'


def test_promote_to_admin_bad_orgid(
        dict_cursor, app_cli_runner, new_org_with_user):
    userid = new_org_with_user[1]
    r = app_cli_runner.invoke(
        admincli.promote_to_admin,
        [userid, 'baduuid'])
    assert r.output == 'Badly formed organization_id\n'


def test_promote_to_admin_user_dne(
        dict_cursor, app_cli_runner, new_org_with_user, missing_id):
    orgid = new_org_with_user[0]
    r = app_cli_runner.invoke(
        admincli.promote_to_admin,
        [missing_id, orgid])
    assert ('Cannot promote admin from outside organization.\n') == r.output


def test_promote_to_admin_already_granted(
        dict_cursor, app_cli_runner, new_org_with_user):
    orgid = new_org_with_user[0]
    userid = new_org_with_user[1]
    app_cli_runner.invoke(
        admincli.promote_to_admin,
        [userid, orgid])
    r = app_cli_runner.invoke(
        admincli.promote_to_admin,
        [userid, orgid])
    assert (f'User already granted admin permissions.\n') == r.output


def test_promote_to_admin_not_in_org(
        dict_cursor, app_cli_runner, unaffiliated_userid,
        new_org_without_user):
    r = app_cli_runner.invoke(
        admincli.promote_to_admin,
        [unaffiliated_userid, new_org_without_user])
    assert 'Cannot promote admin from outside organization.\n' == r.output


def test_promote_to_admin_org_dne(
        dict_cursor, app_cli_runner, new_org_with_user, missing_id):
    userid = new_org_with_user[1]
    r = app_cli_runner.invoke(
        admincli.promote_to_admin,
        [userid, missing_id])
    assert r.output == 'Cannot promote admin from outside organization.\n'


def test_list_all_users(app_cli_runner, dict_cursor):
    r = app_cli_runner.invoke(
        admincli.list_users)
    output_lines = r.output.split('\n')
    assert len(output_lines) == 9
    for line in output_lines[2:-1]:
        assert line.startswith('auth0|')
        assert len(line.split('|')) == 5


def test_list_all_organizations(app_cli_runner, dict_cursor):
    r = app_cli_runner.invoke(
        admincli.list_organizations)
    output_lines = r.output.split('\n')
    assert len(output_lines) == 9
    assert output_lines[0] == (
        "Name                              "
        "|Organization ID                       "
        "|Accepted TOU")
    for line in output_lines[2:-1]:
        assert len(line.split('|')) == 3


def test_set_org_accepted_tou(app_cli_runner, dict_cursor):
    with dict_cursor as sql_cursor:
        sql_cursor.callproc('create_organization', ('clitestorg',))
        sql_cursor.callproc('list_all_organizations')
        original_orgs = org_dict(sql_cursor.fetchall())
        assert original_orgs['clitestorg']['accepted_tou'] == 0
        r = app_cli_runner.invoke(
            admincli.set_org_accepted_tou,
            (original_orgs['clitestorg']['id']))
        sql_cursor.callproc('list_all_organizations')
        updated_orgs = org_dict(sql_cursor.fetchall())
        assert updated_orgs['clitestorg']['accepted_tou'] == 1
        assert r.output == (f"Organization {updated_orgs['clitestorg']['id']} "
                            "has been marked as accepting the terms of "
                            "use.\n")


def test_set_org_accepted_tou_org_dne(
        app_cli_runner, dict_cursor, missing_id):
    r = app_cli_runner.invoke(
        admincli.set_org_accepted_tou,
        (missing_id))
    assert r.output == "Organization does not exist\n"


def test_set_org_accepted_tou_bad_orgid(
        app_cli_runner, dict_cursor):
    r = app_cli_runner.invoke(
        admincli.set_org_accepted_tou,
        ('baduuid'))
    assert r.output == "Badly formed orgid\n"


def test_move_user_to_unaffiliated(
        app_cli_runner, dict_cursor, new_org_with_user):
    userid = new_org_with_user[1]
    r = app_cli_runner.invoke(
        admincli.move_user_to_unaffiliated,
        (userid))
    assert r.output == f'User {userid} moved to unaffiliated organization.\n'


def test_move_user_to_unaffiliated_invalid_userid(
        app_cli_runner, dict_cursor):
    r = app_cli_runner.invoke(
        admincli.move_user_to_unaffiliated,
        'baduuid')
    assert r.output == 'Badly formed user_id\n'
