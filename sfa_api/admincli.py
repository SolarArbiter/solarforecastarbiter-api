import uuid
import os


import click
from flask.cli import AppGroup
import pymysql


from sfa_api import create_app
from sfa_api.utils.errors import StorageAuthError


config = os.getenv('SFA_CLI_CONFIG', 'ProductionConfig')
app = create_app(config)
admin_cli = AppGroup(
    'admin',
    help="Tool for administering the Solar Forecast Arbiter Framework")


@admin_cli.command('create-organization')
@click.argument('organization_name', required=True)
def create_organization(organization_name):
    """Creates a new organization.
    """
    from sfa_api.utils.storage import get_storage
    storage = get_storage()
    try:
        storage._call_procedure_without_user(
            'create_organization', organization_name)
    except pymysql.err.DataError:
        click.echo("Organization name must be 32 characters or fewer.")
    except pymysql.err.IntegrityError as e:
        if e.args[0] == 1062:
            click.echo(f'Organization {organization_name} already exists.')
        else:
            raise
    else:
        click.echo(f'Created organization {organization_name}.')


@admin_cli.command('add-user-to-org')
@click.argument('user_id', required=True)
@click.argument('organization_id', required=True)
def add_user_to_org(user_id, organization_id):
    """
    Adds a user to an organization. The user must currently be
    unaffiliated.
    """
    try:
        uuid.UUID(user_id, version=1)
    except ValueError:
        click.echo('Badly formed user_id')
        return
    try:
        uuid.UUID(organization_id, version=1)
    except ValueError:
        click.echo('Badly formed organization_id')
        return
    from sfa_api.utils.storage import get_storage
    storage = get_storage()

    try:
        storage._call_procedure_without_user(
            'add_user_to_org', user_id, organization_id)
    except pymysql.err.IntegrityError as e:
        if e.args[0] == 1452:
            click.echo('Organization does not exist')
        else:
            raise
    except StorageAuthError as e:
        click.echo(e.args[0])
    else:
        click.echo(f'Added user {user_id} to organization {organization_id}')


@admin_cli.command('promote-user-to-org-admin')
@click.argument('user_id', required=True)
@click.argument('organization_id', required=True)
def promote_to_admin(user_id, organization_id):
    """
    Grants a user admin permissions in the organizations.
    """
    try:
        uuid.UUID(user_id, version=1)
    except ValueError:
        click.echo('Badly formed user_id')
        return
    try:
        uuid.UUID(organization_id, version=1)
    except ValueError:
        click.echo('Badly formed organization_id')
        return
    from sfa_api.utils.storage import get_storage
    storage = get_storage()
    try:
        storage._call_procedure_without_user(
            'promote_user_to_org_admin',
            user_id, organization_id)
    except pymysql.err.IntegrityError as e:
        if e.args[0] == 1062:
            click.echo('User already granted admin permissions.')
        else:
            raise
    except StorageAuthError as e:
        click.echo(e.args[0])
    else:
        click.echo(f'Promoted user {user_id} to administrate '
                   f'organization {organization_id}')


@admin_cli.command('move-to-unaffiliated')
@click.argument('user_id', required=True)
def move_user_to_unaffiliated(user_id):
    """
    Moves a user to the Unaffiliated organization and removes access
    to all data except for the reference data set.
    """
    try:
        uuid.UUID(user_id, version=1)
    except ValueError:
        click.echo('Badly formed user_id')
        return
    from sfa_api.utils.storage import get_storage
    storage = get_storage()
    storage._call_procedure_without_user(
        'move_user_to_unaffiliated', user_id)
    click.echo(f'User {user_id} moved to unaffiliated organization.')


@admin_cli.command('list-users')
def list_users():
    """
    Prints a table of user information including auth0 id, user id,
    organization and organization id.
    """
    from sfa_api.utils.storage import get_storage
    storage = get_storage()
    users = storage._call_procedure_without_user('list_all_users')
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
def list_organizations():
    """
    Prints a table of organization names and ids.
    """
    from sfa_api.utils.storage import get_storage
    storage = get_storage()
    organizations = storage._call_procedure_without_user(
        'list_all_organizations')
    table_format = '{:<34}|{:<38}|{:<12}'
    headers = table_format.format('Name', 'Organization ID', 'Accepted TOU')
    click.echo(headers)
    click.echo('-' * len(headers))
    for org in organizations:
        click.echo(table_format.format(
            org['name'], org["id"], str(bool(org['accepted_tou']))))


@admin_cli.command('set-org-accepted-tou')
@click.argument('organization_id', required=True)
def set_org_accepted_tou(organization_id):
    try:
        uuid.UUID(organization_id, version=1)
    except ValueError:
        click.echo('Badly formed orgid')
        return
    from sfa_api.utils.storage import get_storage
    storage = get_storage()
    try:
        storage._call_procedure_without_user(
            'set_org_accepted_tou', (organization_id,))
    except pymysql.err.InternalError as e:
        if e.args[0] == 1305:
            click.echo(e.args[1])
        else:
            raise
    else:
        click.echo(f'Organization {organization_id} has been marked '
                   'as accepting the terms of use.')


@admin_cli.command('delete-user')
@click.argument('user_id', required=True)
def delete_user(user_id):
    """
    Remove a user from the framework.
    """
    try:
        uuid.UUID(user_id, version=1)
    except ValueError:
        click.echo('Badly formed user_id')
        return
    from sfa_api.utils.storage import get_storage
    storage = get_storage()
    try:
        storage._call_procedure_without_user(
            'delete_user', user_id)
    except pymysql.err.InternalError as e:
        if e.args[0] == 1305:
            click.echo(e.args[1])
        else:
            raise
    else:
        click.echo(f'User {user_id} deleted successfully.')


app.cli.add_command(admin_cli)
