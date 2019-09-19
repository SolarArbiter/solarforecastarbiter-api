import uuid


import click
from flask.cli import AppGroup
import pymysql


from sfa_api import create_app
from sfa_api.utils.errors import StorageAuthError


app = create_app('AdminTestConfig')
admin_cli = AppGroup('admin')


@admin_cli.command('create-organization')
@click.argument('organization_name', required=True)
def create_organization(organization_name):
    from sfa_api.utils.storage import get_storage
    storage = get_storage()
    try:
        storage._call_procedure_without_user(
            'create_organization', organization_name)
    except pymysql.err.DataError as e:
        click.echo(e.args[1])
        return
    except pymysql.err.IntegrityError as e:
        if e.args[0] == 1062:
            click.echo(f'Organization {organization_name} alread exists.')
        else:
            raise
    else:
        click.echo(f'Created organization {organization_name}.')


@admin_cli.command('add-user-to-org')
@click.argument('user_id', required=True)
@click.argument('organization_id', required=True)
def add_user_to_org(user_id, organization_id):
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
        click.echo(e.args[1])
    except StorageAuthError as e:
        click.echo(e.args[0])


@admin_cli.command('promote-user-to-org-admin')
@click.argument('user_id', required=True)
@click.argument('organization_id', required=True)
def promote_to_admin(user_id, organization_id):
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
    except Exception as e:
        click.echo(e.args[0])


@admin_cli.command('delete-user')
@click.argument('user_id', required=True)
def move_user_to_unaffiliated(user_id):
    try:
        uuid.UUID(user_id, version=1)
    except ValueError:
        click.echo('Badly formed user_id')
        return
    from sfa_api.utils.storage import get_storage
    storage = get_storage()
    storage._call_procedure_without_user(
        'delete_user', user_id)


app.cli.add_command(admin_cli)
