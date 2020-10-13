import click
from cryptography.fernet import Fernet
import pytest
import pymysql


from sfa_api import admincli
from sfa_api import create_app
from sfa_api.conftest import _make_nocommit_cursor
from sfa_api.utils import storage_interface


TEST_USERNAME = 'frameworkadmin'
TEST_PASSWORD = 'thisisaterribleandpublicpassword'


auth_args = ['--username', TEST_USERNAME,
             '--password', TEST_PASSWORD]


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
    result = app_cli_runner.invoke(
        admincli.create_organization,
        ['clitestorg'] + auth_args)
    assert 'Created organization clitestorg.\n' == result.output

    with dict_cursor as sql_cursor:
        sql_cursor.callproc('list_all_organizations')
        assert 'clitestorg' in org_dict(sql_cursor.fetchall())


def test_create_org_org_exists(mocker, app_cli_runner):
    result = app_cli_runner.invoke(
        admincli.create_organization,
        ['clitestorg'] + auth_args)
    assert 'Created organization clitestorg.\n' == result.output
    result = app_cli_runner.invoke(
        admincli.create_organization,
        ['clitestorg'] + auth_args)
    assert 'Organization clitestorg already exists.\n' == result.output


def test_create_org_name_too_long(mocker, app_cli_runner):
    result = app_cli_runner.invoke(
        admincli.create_organization,
        ['This organization name is too long and will error'] + auth_args)
    assert ("Organization name must be 32 characters or "
            "fewer.\n") == result.output


def test_create_user(app_cli_runner, dict_cursor):
    result = app_cli_runner.invoke(
        admincli.create_user,
        ['auth0|newuser'] + auth_args)
    assert result.output.startswith('Created user ')
    user_id = result.output[13:49]
    with dict_cursor as cursor:
        cursor.callproc('list_all_users')
        users = user_dict(cursor.fetchall())
        assert user_id in users
        cursor.callproc('list_all_organizations')
        orgid =  list(filter(lambda x: x['name'] == 'Unaffiliated',
                             cursor.fetchall()))[0]['id']
        assert users[user_id]['organization_id'] == orgid


def test_create_user_already_exists(app_cli_runner, unaffiliated_userid):
    result = app_cli_runner.invoke(
        admincli.create_user,
        ['auth0|test_public'] + auth_args)
    assert 'User already exists for auth0|test_public\n' == result.output


def test_add_user_to_org(
        app_cli_runner, unaffiliated_userid, orgid,
        dict_cursor):
    result = app_cli_runner.invoke(
        admincli.add_user_to_org,
        [unaffiliated_userid, orgid] + auth_args)
    assert (f'Added user {unaffiliated_userid} to organization '
            f'{orgid}\n') == result.output
    with dict_cursor as cursor:
        cursor.callproc('list_all_users')
        users = user_dict(cursor.fetchall())
        assert unaffiliated_userid in users
        assert users[unaffiliated_userid]['organization_id'] == orgid


def test_add_user_to_org_affiliated_user(
        app_cli_runner, user_id, orgid):
    result = app_cli_runner.invoke(
        admincli.add_user_to_org,
        [user_id, orgid] + auth_args)
    assert 'Cannot add affiliated user to organization\n' == result.output


def test_add_user_to_org_invalid_orgid(
        app_cli_runner, unaffiliated_userid):
    result = app_cli_runner.invoke(
        admincli.add_user_to_org,
        [unaffiliated_userid, 'baduuid'] + auth_args)
    assert ("Error: Invalid value for 'ORGANIZATION_ID': baduuid "
            "is not a valid UUID value") in result.output


def test_add_user_to_org_invalid_userid(
        app_cli_runner, orgid):
    result = app_cli_runner.invoke(
        admincli.add_user_to_org,
        ['baduuid', orgid] + auth_args)
    assert ("Error: Invalid value for 'USER_ID': baduuid is "
            "not a valid UUID value") in result.output


def test_add_user_to_org_user_dne(
        app_cli_runner, missing_id, orgid):
    result = app_cli_runner.invoke(
        admincli.add_user_to_org,
        [missing_id, orgid] + auth_args)
    assert 'Cannot add affiliated user to organization\n' == result.output


def test_add_user_to_org_org_dne(
        app_cli_runner, unaffiliated_userid, missing_id):
    result = app_cli_runner.invoke(
        admincli.add_user_to_org,
        [unaffiliated_userid, missing_id] + auth_args)
    assert 'Organization does not exist\n' == result.output


@pytest.fixture(scope='function')
def new_org_with_user(dict_cursor, unaffiliated_userid):
    with dict_cursor as sql_cursor:
        sql_cursor.callproc('create_organization', ['clitestorg'])
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
        orgid = org_dict(sql_cursor.fetchall())['clitestorg']['id']
    return orgid


def test_promote_to_admin(
        dict_cursor, app_cli_runner, new_org_with_user):
    orgid = new_org_with_user[0]
    userid = new_org_with_user[1]
    result = app_cli_runner.invoke(
        admincli.promote_to_admin,
        [userid, orgid] + auth_args)
    assert (f'Promoted user {userid} to administrate '
            f'organization {orgid}\n') == result.output


def test_promote_to_admin_invalid_userid(
        dict_cursor, app_cli_runner, new_org_with_user):
    orgid = new_org_with_user[0]
    result = app_cli_runner.invoke(
        admincli.promote_to_admin,
        ['baduuid', orgid] + auth_args)
    assert ("Error: Invalid value for 'USER_ID': baduuid is not "
            "a valid UUID value") in result.output


def test_promote_to_admin_bad_orgid(
        dict_cursor, app_cli_runner, new_org_with_user):
    userid = new_org_with_user[1]
    result = app_cli_runner.invoke(
        admincli.promote_to_admin,
        [userid, 'baduuid'] + auth_args)
    assert ("Error: Invalid value for 'ORGANIZATION_ID': baduuid "
            "is not a valid UUID value") in result.output


def test_promote_to_admin_user_dne(
        dict_cursor, app_cli_runner, new_org_with_user, missing_id):
    orgid = new_org_with_user[0]
    result = app_cli_runner.invoke(
        admincli.promote_to_admin,
        [missing_id, orgid] + auth_args)
    assert result.output == ('Cannot promote admin from outside '
                             'organization.\n')


def test_promote_to_admin_already_granted(
        dict_cursor, app_cli_runner, new_org_with_user):
    orgid = new_org_with_user[0]
    userid = new_org_with_user[1]
    app_cli_runner.invoke(
        admincli.promote_to_admin,
        [userid, orgid] + auth_args)
    result = app_cli_runner.invoke(
        admincli.promote_to_admin,
        [userid, orgid] + auth_args)
    assert (f'User already granted admin permissions.\n') == result.output


def test_promote_to_admin_not_in_org(
        dict_cursor, app_cli_runner, unaffiliated_userid,
        new_org_without_user):
    result = app_cli_runner.invoke(
        admincli.promote_to_admin,
        [unaffiliated_userid, new_org_without_user] + auth_args)
    assert 'Cannot promote admin from outside organization.\n' == result.output


def test_promote_to_admin_org_dne(
        dict_cursor, app_cli_runner, new_org_with_user, missing_id):
    userid = new_org_with_user[1]
    result = app_cli_runner.invoke(
        admincli.promote_to_admin,
        [userid, missing_id] + auth_args)
    assert result.output == 'Cannot promote admin from outside organization.\n'


def test_list_all_users(app_cli_runner, dict_cursor, mocker):
    email = mocker.MagicMock()
    email.__getitem__ = lambda x, y: 'email'
    mocker.patch('sfa_api.utils.auth0_info.list_user_emails',
                 return_value=email)
    result = app_cli_runner.invoke(
        admincli.list_users,
        auth_args)
    assert result.exit_code == 0
    output_lines = result.output.split('\n')
    assert len(output_lines) == 9
    for line in output_lines[2:-1]:
        assert line.startswith('auth0|')
        assert len(line.split('|')) == 6


def test_list_all_organizations(app_cli_runner, dict_cursor):
    result = app_cli_runner.invoke(
        admincli.list_organizations,
        auth_args)
    output_lines = result.output.split('\n')
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
        result = app_cli_runner.invoke(
            admincli.set_org_accepted_tou,
            [original_orgs['clitestorg']['id']] + auth_args)
        sql_cursor.callproc('list_all_organizations')
        updated_orgs = org_dict(sql_cursor.fetchall())
        assert updated_orgs['clitestorg']['accepted_tou'] == 1
        assert result.output == (
            f"Organization {updated_orgs['clitestorg']['id']} "
            "has been marked as accepting the terms of use.\n")


def test_set_org_accepted_tou_org_dne(
        app_cli_runner, dict_cursor, missing_id):
    result = app_cli_runner.invoke(
        admincli.set_org_accepted_tou,
        [missing_id] + auth_args)
    assert result.output == "Organization does not exist\n"


def test_set_org_accepted_tou_bad_orgid(
        app_cli_runner, dict_cursor):
    result = app_cli_runner.invoke(
        admincli.set_org_accepted_tou,
        ['baduuid'] + auth_args)
    assert ("Error: Invalid value for 'ORGANIZATION_ID': baduuid "
            "is not a valid UUID value") in result.output


def test_move_user_to_unaffiliated(
        app_cli_runner, dict_cursor, user_id):
    result = app_cli_runner.invoke(
        admincli.move_user_to_unaffiliated,
        [user_id] + auth_args)
    assert result.output == (f'User {user_id} moved to unaffiliated '
                             'organization.\n')
    with dict_cursor as sql_cursor:
        sql_cursor.callproc('list_all_users')
        user = user_dict(sql_cursor.fetchall())[user_id]
        assert user['organization_name'] == 'Unaffiliated'


def test_move_user_to_unaffiliated_invalid_userid(
        app_cli_runner, dict_cursor):
    result = app_cli_runner.invoke(
        admincli.move_user_to_unaffiliated,
        ['baduuid'] + auth_args)
    assert ("Error: Invalid value for 'USER_ID': baduuid is "
            "not a valid UUID value") in result.output


def test_delete_user(
        app_cli_runner, dict_cursor, user_id):
    result = app_cli_runner.invoke(
        admincli.delete_user,
        [user_id] + auth_args)
    assert result.output == (f'User {user_id} deleted successfully.\n')


def test_delete_user_user_dne(
        app_cli_runner, dict_cursor, missing_id):
    result = app_cli_runner.invoke(
        admincli.delete_user,
        [missing_id] + auth_args)
    assert result.output == (f'User does not exist\n')


def test_create_job_user(app_cli_runner, mocker):
    org = 'Organization 1'
    create = mocker.patch('sfa_api.utils.auth0_info.create_user',
                          return_value='auth0|createduser')

    def call_return(proc, *args, **kwargs):
        if proc == 'list_all_organizations':
            return [{'name': 'Organization 1', 'id': 'orgid'}]
        elif proc == 'store_token':
            assert args[1].startswith(b'gAAAA')  # encrypted
        elif proc == 'create_job_user':
            return [['user-id']]

    mocker.patch('sfa_api.utils.storage_interface._call_procedure',
                 new=call_return)
    refresh = mocker.patch('sfa_api.utils.auth0_info.get_refresh_token',
                           return_value='token')
    res = app_cli_runner.invoke(
        admincli.create_job_user,
        ['--encryption-key', Fernet.generate_key()] + auth_args + [org])
    assert res.exit_code == 0
    assert 'job-execution@organization-1.solarforecastarbiter.org' in res.output  # NOQA
    assert refresh.called
    assert create.called


def test_create_job_user_no_org(app_cli_runner, mocker):
    org = 'Organization 1'
    mocker.patch('sfa_api.utils.storage_interface._call_procedure',
                 return_value=[])
    res = app_cli_runner.invoke(
        admincli.create_job_user,
        ['--encryption-key', Fernet.generate_key()] + auth_args + [org])
    assert res.exit_code == 1
    assert 'Organization Organization 1 not found' in res.output


@pytest.mark.parametrize('role', [
    'Recompute reports', 'Validate observations',
    'Generate reference forecasts'
])
def test_add_job_role(app_cli_runner, user_id, role):
    res = app_cli_runner.invoke(admincli.add_job_role,
                                auth_args + [user_id, role])
    assert res.exit_code == 0


def test_add_job_role_bad_role(app_cli_runner, user_id):
    res = app_cli_runner.invoke(admincli.add_job_role,
                                auth_args + [user_id, 'Read all'])
    assert res.exit_code != 0


def test_add_job_role_multiple(app_cli_runner, user_id):
    res = app_cli_runner.invoke(
        admincli.add_job_role,
        auth_args + [user_id, 'Recompute reports', 'Validate observations'])
    assert res.exit_code == 0


@pytest.mark.parametrize('role', [
    'Recompute reports', 'Validate observations',
    'Generate reference forecasts'
])
def test_add_job_role_already_present(app_cli_runner, user_id, role):
    res = app_cli_runner.invoke(admincli.add_job_role,
                                auth_args + [user_id, role])
    assert res.exit_code == 0
    res = app_cli_runner.invoke(admincli.add_job_role,
                                auth_args + [user_id, role])
    assert res.exit_code != 0


@pytest.mark.parametrize('role', [
    'Recompute reports', 'Validate observations',
    'Generate reference forecasts'
])
def test_add_job_role_user_dne(app_cli_runner, missing_id, role):
    res = app_cli_runner.invoke(admincli.add_job_role,
                                auth_args + [missing_id, role])
    assert res.exit_code != 0


def test_list_jobs(app_cli_runner):
    res = app_cli_runner.invoke(admincli.list_jobs,
                                auth_args)
    assert res.exit_code == 0


def test_delete_job(app_cli_runner, jobid):
    result = app_cli_runner.invoke(
        admincli.delete_job,
        [jobid] + auth_args)
    assert result.exit_code == 0
    assert result.output == (f'Job {jobid} deleted successfully.\n')


def test_delete_job_job_dne(app_cli_runner, missing_id):
    result = app_cli_runner.invoke(
        admincli.delete_job,
        [missing_id] + auth_args)
    assert result.exit_code != 0
    assert result.output == (f'Job does not exist\n')


def test_TimeDeltaParam():
    assert '1h' == admincli.TimeDeltaParam()('1h')
    with pytest.raises(click.exceptions.BadParameter):
        admincli.TimeDeltaParam()('what')


def test_daily_validation_job(app_cli_runner, mocker, user_id):
    mocker.patch('sfa_api.jobs.create_job', return_value='jobid')
    result = app_cli_runner.invoke(
        admincli.daily_validation_job,
        ['Val Job', user_id, '* * * * *', '-1d', '0h'] + auth_args)
    assert result.exit_code == 0
    assert result.output == 'Job created with id jobid\n'


def test_reference_nwp_job(app_cli_runner, mocker, user_id):
    mocker.patch('sfa_api.jobs.create_job', return_value='jobid')
    result = app_cli_runner.invoke(
        admincli.reference_nwp_job,
        ['Val Job', user_id, '* * * * *', '10min'] + auth_args)
    assert result.exit_code == 0
    assert result.output == 'Job created with id jobid\n'


def test_periodic_report_job(app_cli_runner, mocker, user_id,
                             missing_id):
    mocker.patch('sfa_api.jobs.create_job', return_value='jobid')
    result = app_cli_runner.invoke(
        admincli.periodic_report_job,
        ['Val Job', user_id, '* * * * *', missing_id] + auth_args)
    assert result.exit_code == 0
    assert result.output == 'Job created with id jobid\n'


def test_reference_persistence_job(app_cli_runner, mocker, user_id):
    mocker.patch('sfa_api.jobs.create_job', return_value='jobid',
                 autospec=True)
    result = app_cli_runner.invoke(
        admincli.reference_persistence_job,
        ['Val Job', user_id, '* * * * *', '--base-url', 'http://test']
        + auth_args)
    assert result.exit_code == 0
    assert result.output == 'Job created with id jobid\n'
