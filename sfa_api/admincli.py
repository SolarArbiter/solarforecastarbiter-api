import sys


import click
from flask import Flask
from flask.cli import FlaskGroup
import pandas as pd
import pymysql


from sfa_api.utils.errors import StorageAuthError


app = Flask(__name__)


@click.group(cls=FlaskGroup, create_app=lambda: app,
             add_default_commands=False)
def admin_cli():  # pragma: no cover
    """Tool for administering the Solar Forecast Arbiter Framework"""
    pass


config_opt = click.option(
    '--config', default='ProductionConfig', show_envvar=True,
    callback=lambda _, y, x: app.config.from_object(f'sfa_api.config.{x}'),
    envvar='SFA_CLI_CONFIG', is_eager=True)
username_opt = click.option(
    '--username', required=True, show_envvar=True, envvar='MYSQL_USER',
    callback=lambda _, y, x: app.config.update({'MYSQL_USER': x}))
password_opt = click.option(
    '--password', prompt=True, required=True,
    hide_input=True, envvar='MYSQL_PASSWORD',
    callback=lambda _, y, x: app.config.update({'MYSQL_PASSWORD': x}))


def with_default_options(func):
    """Decorator adds the username and password options to a cli
    command.
    """
    for option in [password_opt, username_opt, config_opt]:
        func = option(func)
    return func


def fail(message):
    click.echo(message, err=True)
    sys.exit(1)


@admin_cli.command('create-organization')
@with_default_options
@click.argument('organization_name', required=True)
def create_organization(organization_name, **kwargs):
    """Creates a new organization.
    """
    import sfa_api.utils.storage_interface as storage
    try:
        storage._call_procedure(
            'create_organization', organization_name,
            with_current_user=False)
    except pymysql.err.DataError:
        fail("Organization name must be 32 characters or fewer.")
    except pymysql.err.IntegrityError as e:
        if e.args[0] == 1062:
            fail(f'Organization {organization_name} already exists.')
        else:  # pragma: no cover
            raise
    else:
        click.echo(f'Created organization {organization_name}.')


@admin_cli.command('create-user')
@with_default_options
@click.argument('auth0_id', required=True)
def create_user(auth0_id, **kwargs):
    """
    Creates a new user in the Unaffiliated organization for
    the given Auth0 id.
    """
    import sfa_api.utils.storage_interface as storage
    try:
        user_id = storage._call_procedure_for_single(
            'create_user_if_not_exists', auth0_id,
            with_current_user=False).get('user_id')
    except StorageAuthError:
        fail(f'User already exists for {auth0_id}')
    else:
        click.echo(f'Created user {user_id} for {auth0_id}')


@admin_cli.command('add-user-to-org')
@with_default_options
@click.argument('user_id', required=True, type=click.UUID)
@click.argument('organization_id', required=True, type=click.UUID)
def add_user_to_org(
        user_id, organization_id, **kwargs):
    """
    Adds a user to an organization. The user must currently be
    unaffiliated.
    """
    import sfa_api.utils.storage_interface as storage
    try:
        storage._call_procedure(
            'add_user_to_org', str(user_id), str(organization_id),
            with_current_user=False)
    except pymysql.err.IntegrityError as e:
        if e.args[0] == 1452:
            fail('Organization does not exist')
        else:  # pragma: no cover
            raise
    except StorageAuthError as e:
        fail(e.args[0])
    else:
        click.echo(f'Added user {user_id} to organization {organization_id}')


@admin_cli.command('promote-user-to-org-admin')
@with_default_options
@click.argument('user_id', required=True, type=click.UUID)
@click.argument('organization_id', required=True, type=click.UUID)
def promote_to_admin(user_id, organization_id, **kwargs):
    """
    Grants a user admin permissions in the organizations.
    """
    import sfa_api.utils.storage_interface as storage
    try:
        storage._call_procedure(
            'promote_user_to_org_admin',
            str(user_id), str(organization_id),
            with_current_user=False)
    except pymysql.err.IntegrityError as e:
        if e.args[0] == 1062:
            fail('User already granted admin permissions.')
        else:  # pragma: no cover
            raise
    except StorageAuthError as e:
        click.echo(e.args[0])
    else:
        click.echo(f'Promoted user {user_id} to administrate '
                   f'organization {organization_id}')


@admin_cli.command('move-to-unaffiliated')
@with_default_options
@click.argument('user_id', required=True, type=click.UUID)
def move_user_to_unaffiliated(user_id, **kwargs):
    """
    Moves a user to the Unaffiliated organization and removes access
    to all data except for the reference data set.
    """
    import sfa_api.utils.storage_interface as storage
    storage._call_procedure(
        'move_user_to_unaffiliated', str(user_id),
        with_current_user=False)
    click.echo(f'User {user_id} moved to unaffiliated organization.')


@admin_cli.command('list-users')
@with_default_options
def list_users(**kwargs):
    """
    Prints a table of user information including auth0 id, user id,
    organization and organization id. AUTH0_CLIENT_ID and AUTH0_CLIENT_SECRET
    must be properly set to retrieve emails.
    """
    import sfa_api.utils.storage_interface as storage
    from sfa_api.utils.auth0_info import list_user_emails
    import logging
    logging.getLogger('sfa_api.utils.auth0_info').setLevel('CRITICAL')
    users = storage._call_procedure('list_all_users', with_current_user=False)
    emails = list_user_emails([u['auth0_id'] for u in users])

    table_format = '{:<34}|{:<38}|{:<44}|{:<34}|{:<38}'
    headers = table_format.format(
        'auth0_id', 'User ID', 'User Email', 'Organization Name',
        'Organization ID'
    )
    click.echo(headers)
    click.echo('-' * len(headers))
    for user in users:
        click.echo(table_format.format(
            user['auth0_id'], user['id'], emails[user['auth0_id']],
            user['organization_name'], user['organization_id']))


@admin_cli.command('list-organizations')
@with_default_options
def list_organizations(**kwargs):
    """
    Prints a table of organization names and ids.
    """
    import sfa_api.utils.storage_interface as storage
    organizations = storage._call_procedure(
        'list_all_organizations', with_current_user=False)
    table_format = '{:<34}|{:<38}|{:<12}'
    headers = table_format.format('Name', 'Organization ID', 'Accepted TOU')
    click.echo(headers)
    click.echo('-' * len(headers))
    for org in organizations:
        click.echo(table_format.format(
            org['name'], org["id"], str(bool(org['accepted_tou']))))


@admin_cli.command('set-org-accepted-tou')
@with_default_options
@click.argument('organization_id', required=True, type=click.UUID)
def set_org_accepted_tou(organization_id, **kwargs):
    """
    Sets an organizaiton's accepted terms of use field to true.
    """
    import sfa_api.utils.storage_interface as storage
    try:
        storage._call_procedure(
            'set_org_accepted_tou',
            str(organization_id),
            with_current_user=False)
    except pymysql.err.InternalError as e:
        if e.args[0] == 1305:
            fail(e.args[1])
        else:  # pragma: no cover
            raise
    else:
        click.echo(f'Organization {organization_id} has been marked '
                   'as accepting the terms of use.')


@admin_cli.command('delete-user')
@with_default_options
@click.argument('user_id', required=True, type=click.UUID)
def delete_user(user_id, **kwargs):
    """
    Remove a user from the framework.
    """
    import sfa_api.utils.storage_interface as storage
    try:
        storage._call_procedure(
            'delete_user', str(user_id),
            with_current_user=False)
    except pymysql.err.InternalError as e:
        if e.args[0] == 1305:
            fail(e.args[1])
        else:  # pragma: no cover
            raise
    else:
        click.echo(f'User {user_id} deleted successfully.')


@admin_cli.group()
def jobs():  # pragma: no cover
    """Tools for administering the SFA jobs"""
    pass


@jobs.command('create-user')
@with_default_options
@click.option(
    '--encryption-key', prompt=False, required=True,
    envvar='TOKEN_ENCRYPTION_KEY')
@click.argument('organization_name', required=True)
def create_job_user(organization_name, encryption_key, **kwargs):
    """
    Creates a new user in Auth0 to run background jobs for the organization.
    Make sure AUTH0_CLIENT_ID and AUTH0_CLIENT_SECRET are properly set.
    """
    from sfa_api.utils import auth0_info
    import sfa_api.utils.storage_interface as storage

    org_id = None
    for org in storage._call_procedure(
            'list_all_organizations', with_current_user=False):
        if org['name'] == organization_name:
            org_id = org['id']
            break
    if org_id is None:
        fail(f'Organization {organization_name} not found')

    username = (
        'job-execution@' +
        organization_name.lower().replace(" ", "-") +
        '.solarforecastarbiter.org'
    )

    passwd = auth0_info.random_password()
    user_id, auth0_id = storage.create_job_user(
        username, passwd, org_id, encryption_key)
    click.echo(f'Created user {username} with Auth0 ID {auth0_id}')


@jobs.command('add-role')
@with_default_options
@click.argument('user_id', required=True, type=click.UUID)
@click.argument('role_name', nargs=-1, type=click.Choice(
    ['Recompute reports', 'Validate observations',
     'Generate reference forecasts']))
def add_job_role(user_id, role_name, **kwargs):
    """
    Add a job role(s) (ROLE_NAME) to a job execution user (USER_ID)
    """
    import sfa_api.utils.storage_interface as storage
    for role in role_name:
        storage._call_procedure('grant_job_role', str(user_id), role,
                                with_current_user=False)
        click.echo(f'Added role {role} to user {user_id}')


@jobs.command('list')
@with_default_options
def list_jobs(**kwargs):
    """
    List information for all jobs
    """
    import pprint
    import sfa_api.utils.storage_interface as storage
    jobs = storage._call_procedure('list_jobs',
                                   with_current_user=False)
    # a table would be too wide, so pretty print instead
    click.echo(pprint.pformat(jobs))


@jobs.command('delete')
@with_default_options
@click.argument('job_id', required=True, type=click.UUID)
def delete_job(job_id, **kwargs):
    """
    Delete JOB_ID from the database
    """
    import sfa_api.utils.storage_interface as storage
    try:
        storage._call_procedure(
            'delete_job', str(job_id),
            with_current_user=False)
    except pymysql.err.InternalError as e:
        if e.args[0] == 1305:
            fail(e.args[1])
        else:  # pragma: no cover
            raise
    else:
        click.echo(f'Job {job_id} deleted successfully.')


@jobs.group('create')
def create_jobs():  # pragma: no cover
    """Create a job"""
    pass


class TimeDeltaParam(click.ParamType):
    """Ensure a string can be parsed by pandas.Timedelta"""
    name = 'TimeDeltaParam'

    def convert(self, value, param, ctx):
        try:
            pd.Timedelta(value)
        except ValueError:
            self.fail(f'{value} cannot be converted into a pandas.Timedelta',
                      param, ctx)
        else:
            return value


base_url = click.option(
    '--base-url', default='https://api.solarforecastarbiter.org')
timeout = click.option('--timeout')
name_arg = click.argument('name')
user_id_arg = click.argument('user_id', type=click.UUID)
cron_string = click.argument('cron_string')


@create_jobs.command('daily-validation',
                     context_settings={"ignore_unknown_options": True})
@with_default_options
@base_url
@timeout
@name_arg
@user_id_arg
@cron_string
@click.argument('start_td', type=TimeDeltaParam())
@click.argument('end_td', type=TimeDeltaParam())
def daily_validation_job(name, user_id, cron_string, start_td, end_td,
                         base_url, timeout, **kwargs):
    """
    Create a daily observation validation job named NAME to be executed by
    the USER_ID user on a scheduled according to CRON_STRING. Validation
    is performed from job_time + START_TD to job_time + END_TD, so
    both are likely negative.
    """
    from sfa_api.jobs import create_job
    id_ = create_job(
        'daily_observation_validation', name, user_id, cron_string, timeout,
        start_td=start_td, end_td=end_td, base_url=base_url)
    click.echo(f'Job created with id {id_}')


@create_jobs.command('reference-nwp')
@with_default_options
@base_url
@timeout
@name_arg
@user_id_arg
@cron_string
@click.argument('issue_time_buffer', type=TimeDeltaParam())
def reference_nwp_job(name, user_id, cron_string, issue_time_buffer,
                      base_url, timeout, **kwargs):
    """
    Create a reference nwp job named NAME to be executed by
    USER_ID on a scheduled defined by CRON_STRING. ISSUE_TIME_BUFFER
    is a timedelta added to the job run time to determine how far
    in advance a forecast can be made relative to the expected
    issue time the forecast.
    """
    from sfa_api.jobs import create_job
    id_ = create_job(
        'reference_nwp', name, user_id, cron_string, timeout,
        issue_time_buffer=issue_time_buffer, base_url=base_url)
    click.echo(f'Job created with id {id_}')


@create_jobs.command('periodic-report')
@with_default_options
@base_url
@timeout
@name_arg
@user_id_arg
@cron_string
@click.argument('report_id', type=click.UUID)
def periodic_report_job(name, user_id, cron_string, report_id,
                        base_url, timeout, **kwargs):
    """
    Create a job to periodically recreate a report given by REPORT_ID
    with job name NAME executed by user USER_ID on a schedule defined
    by CRON_STRING.
    """
    from sfa_api.jobs import create_job
    id_ = create_job(
        'periodic_report', name, user_id, cron_string, timeout,
        report_id=str(report_id), base_url=base_url)
    click.echo(f'Job created with id {id_}')


@create_jobs.command('reference-persistence')
@with_default_options
@base_url
@timeout
@name_arg
@user_id_arg
@cron_string
def reference_persistence_job(
        name, user_id, cron_string, base_url, timeout, **kwargs):
    """
    Create a reference persistence job named NAME to be executed by
    USER_ID on a scheduled defined by CRON_STRING. Persistence
    forecasts are made based on new observation values.
    """
    from sfa_api.jobs import create_job
    id_ = create_job(
        'reference_persistence', name, user_id, cron_string, timeout,
        base_url=base_url)
    click.echo(f'Job created with id {id_}')


@create_jobs.command('trial-data-copy')
@with_default_options
@base_url
@timeout
@name_arg
@user_id_arg
@cron_string
@click.argument('copy_from', type=click.UUID)
@click.argument('copy_to', type=click.UUID)
def trial_data_copy_job(
        name, user_id, cron_string, base_url, timeout, copy_from, copy_to, **kwargs):
    """
    Create a job to copy latest data from one observation to another.
    """
    from sfa_api.jobs import create_job
    id_ = create_job(
        'trial_data_copy', name, user_id, cron_string, timeout,
        copy_to=str(copy_to), copy_from=str(copy_from), base_url=base_url)
    click.echo(f'Job created with id {id_}')
