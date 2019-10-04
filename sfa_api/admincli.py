import sys


import click
from flask import Flask
from flask.cli import AppGroup
import pymysql


from sfa_api.utils.errors import StorageAuthError


app = Flask(__name__)
admin_cli = AppGroup(
    'admin',
    help="Tool for administering the Solar Forecast Arbiter Framework")


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
        else:
            raise
    else:
        click.echo(f'Created organization {organization_name}.')


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
        else:
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
        else:
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
    organization and organization id.
    """
    import sfa_api.utils.storage_interface as storage
    users = storage._call_procedure('list_all_users', with_current_user=False)
    table_format = '{:<34}|{:<38}|{:<34}|{:<38}'
    headers = table_format.format(
        'auth0_id', 'User ID', 'Organization Name', 'Organization ID')
    click.echo(headers)
    click.echo('-' * len(headers))
    for user in users:
        click.echo(table_format.format(
            user['auth0_id'], user['id'], user['organization_name'],
            user['organization_id']))


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
        else:
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
        else:
            raise
    else:
        click.echo(f'User {user_id} deleted successfully.')


app.cli.add_command(admin_cli)
