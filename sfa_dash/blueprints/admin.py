from flask import (Blueprint, render_template, request,
                   url_for, redirect, session)
from sfa_dash.api_interface import (
    sites, observations, forecasts,
    cdf_forecast_groups, roles, users,
    permissions, reports, aggregates
)
from sfa_dash.blueprints.base import BaseView
from sfa_dash.blueprints.util import filter_form_fields, handle_response
from sfa_dash.errors import DataRequestException


class AdminView(BaseView):
    subnav_format = {
        '{users_url}': 'Users',
        '{roles_url}': 'Roles',
        '{permissions_url}': 'Permissions',
    }

    def get_api_handler(self, object_type):
        if object_type == 'sites':
            api_handler = sites
        elif object_type == 'observations':
            api_handler = observations
        elif object_type == 'forecasts':
            api_handler = forecasts
        elif object_type == 'cdf_forecasts':
            api_handler = cdf_forecast_groups
        elif object_type == 'users':
            api_handler = users
        elif object_type == 'permissions':
            api_handler = permissions
        elif object_type == 'roles':
            api_handler = roles
        elif object_type == 'reports':
            api_handler = reports
        elif object_type == 'aggregates':
            api_handler = aggregates
        else:
            raise ValueError('Invalid object_type')
        return api_handler

    def current_user(self):
        """Get user organization from the api
        """
        user_request = users.current()
        user = user_request.json()
        return user

    def filter_by_org(self, object_list, org_key='organization'):
        """Filter function for comparing the organization of an
        object to hide roles/permissions/objects from view so that
        they do not attempt to add objects they can view, but do
        not have permission to administer.
        """
        # TODO: find a better way to store user data for
        #       dashboard purposes to eliminate multiple
        #       api calls
        # TODO: fix org key to be consistent across types
        user_data = users.current().json()
        organization = user_data['organization']

        def compare_org_to_user(object_dict):
            return organization == object_dict.get(org_key, None)
        return list(filter(compare_org_to_user, object_list))

    def template_args(self):
        subnav_kwargs = {
            'users_url': url_for('admin.users'),
            'roles_url': url_for('admin.roles'),
            'permissions_url': url_for('admin.permissions'),
        }
        return {'subnav': self.format_subnav(**subnav_kwargs)}

    def get(self):
        return render_template('forms/admin/admin.html',
                               **self.template_args())


# Users Views
class UserListing(AdminView):
    def get(self):
        users_list = users.list_metadata().json()
        if 'errors' in users_list:
            users_list = None
        return render_template('forms/admin/users.html',
                               table_data=users_list,
                               **self.template_args())


class UserView(AdminView):
    def get(self, uuid):
        temp_args = self.template_args()
        try:
            user = handle_response(users.get_metadata(uuid))
            role_list = handle_response(roles.list_metadata())
        except DataRequestException as e:
            temp_args.update({'errors': e.errors})
            return render_template('forms/admin/user.html',
                                   **temp_args)
        else:
            role_map = {role['role_id']: role for role in role_list}
            user['roles'] = {k: {'added_to_user': v, **role_map[k]}
                             for k, v in user['roles'].items()
                             if k in role_map}
        return render_template('forms/admin/user.html',
                               user=user, **temp_args)


class UserRoleAddition(AdminView):
    template = 'forms/admin/user_role_addition.html'

    def get(self, uuid, **kwargs):
        """Form for adding roles to a user.
        """
        try:
            user = handle_response(users.get_metadata(uuid))
            all_roles = handle_response(roles.list_metadata())
        except DataRequestException as e:
            return render_template(
                self.template, errors=e.errors, **self.template_args())
        else:
            user_roles = list(user['roles'].keys())
            role_request = roles.list_metadata()
            all_roles = role_request.json()
            all_roles = self.filter_by_org(all_roles, 'organization')
            # remove any roles the user already has
            all_roles = [role for role in all_roles
                         if role['role_id'] not in user_roles]
        return render_template(self.template,
                               user=user,
                               table_data=all_roles,
                               **self.template_args(),
                               **kwargs)

    def post(self, uuid):
        """Parses a list of role ids and attempts to add them to
        a user.
        """
        form_data = request.form
        roles = filter_form_fields('user-role-', form_data)
        messages = {}
        errors = {}
        for role in roles:
            try:
                handle_response(users.add_role(uuid, role))
            except DataRequestException:
                errors[role] = [f'Failed to add role {role} to user.']
            else:
                messages[role] = f'Successfully added role {role} to user.'
        if errors:
            return self.get(
                uuid, errors=errors, messages=messages, form_data=form_data)
        return redirect(url_for('admin.user_view', uuid=uuid))


class UserRoleRemoval(AdminView):
    template = "forms/admin/user_role_removal.html"

    def get(self, uuid, role_id, **kwargs):
        """Confirmation view for removing a role from a user
        """
        user_req = users.get_metadata(uuid)
        # Check if the user is readable. For roles shared outside
        # an org this may not be true, but we still need to pass
        # user_id to the template for building urls and display.
        if user_req.status_code == 200:
            user = user_req.json()
        else:
            user = {'user_id': uuid}
        role_req = roles.get_metadata(role_id)
        role = role_req.json()
        redirect_link = request.headers.get(
            'Referer', url_for('admin.roles'))
        # set a redirect link, because we can be directed here
        # from a role or user page.
        session['redirect_link'] = redirect_link
        return render_template(self.template,
                               user=user,
                               role=role,
                               redirect_link=redirect_link,
                               **kwargs,
                               **self.template_args())

    def post(self, uuid, role_id):
        """Removes a role from a user
        """
        confirmation_url = url_for(
            'admin.user_role_removal',
            _external=True,
            uuid=uuid,
            role_id=role_id)
        if request.headers.get('Referer') != confirmation_url:
            redirect(confirmation_url)
        delete_request = users.remove_role(uuid, role_id)
        if delete_request.status_code != 204:
            errors = delete_request.json()
            return self.get(uuid, role_id, errors=errors)
        redirect_url = session.pop(
            'redirect_link',
            url_for("admin.user_view", uuid=uuid))
        return redirect(redirect_url)


# Roles Views
class RoleListing(AdminView):
    def get(self):
        roles_list = roles.list_metadata().json()
        if 'errors' in roles_list:
            roles_list = None
        return render_template('forms/admin/roles.html',
                               table_data=roles_list,
                               **self.template_args())


class RoleView(AdminView):
    template = 'forms/admin/role.html'

    def get_email(self, user_id):
        try:
            email = handle_response(users.get_email(user_id))
        except DataRequestException:
            return 'Email Unavailable'
        else:
            return email

    def get(self, uuid, **kwargs):
        role_table = request.args.get('table', 'permissions')
        try:
            role = handle_response(roles.get_metadata(uuid))
            permission_list = handle_response(
                permissions.list_metadata())
        except DataRequestException as e:
            return render_template(self.template, errors=e.errors)
        else:
            permission_map = {perm['permission_id']: perm
                              for perm in permission_list}
            role['permissions'] = {k: {'added_to_role': v, **permission_map[k]}
                                   for k, v in role['permissions'].items()
                                   if k in permission_map}
            user_list = users.list_metadata().json()
            user_map = {user['user_id']: user
                        for user in user_list}
            role_users = {}
            for uid, user in role['users'].items():
                user_dict = user_map.get(uid, {})
                email = user_dict.get('email', None)
                if email is None:
                    email = self.get_email(uid)
                role_users[uid] = {
                    'user_id': uid,
                    'added_to_user': user,
                    'email': email,
                    'organization': user_dict.get(
                        'organization', 'Organization Unavailable')}
            role['users'] = role_users
        return render_template(self.template,
                               role=role,
                               role_table=role_table,
                               **kwargs,
                               **self.template_args())


class RoleGrant(AdminView):
    template = 'forms/admin/role_grant.html'

    def get(self, uuid, **kwargs):
        template_args = self.template_args()
        try:
            role = handle_response(roles.get_metadata(uuid))
        except DataRequestException as e:
            template_args['errors'] = e.errors
        redirect_link = request.headers.get(
            'Referer', url_for('admin.roles'))
        # set a redirect link, because we can be directed here
        # from a role or user page.
        session['redirect_link'] = redirect_link
        return render_template(self.template,
                               role=role,
                               **kwargs,
                               redirect_link=redirect_link,
                               **template_args)

    def post(self, uuid):
        form_data = request.form
        user_email = form_data.get('user_email', '')
        try:
            handle_response(users.add_role_by_email(user_email, uuid))
        except DataRequestException:
            role = roles.get_metadata(uuid).json()
            errors = {
                'Error': ['Failed to grant role.'],
            }
            return render_template(
                self.template,
                role=role,
                errors=errors,
                form_data=form_data,
                **self.template_args())
        redirect_url = session.pop(
            'redirect_link',
            url_for('admin.role_view', uuid=uuid))
        return redirect(redirect_url)


class RoleCreation(AdminView):
    template = "/forms/admin/role_form.html"

    def get(self, **kwargs):
        list_request = permissions.list_metadata()
        table_data = list_request.json()
        table_data = self.filter_by_org(table_data, 'organization')
        return render_template(self.template, table_data=table_data,
                               **self.template_args(), **kwargs)

    def post(self):
        form_data = request.form
        role = {
            'name': form_data['name'],
            'description': form_data['description'],
        }
        try:
            role_id = handle_response(roles.post_metadata(role))
        except DataRequestException as e:
            return self.get(errors=e.errors)
        errors = {}
        messages = {}
        permissions = filter_form_fields('role-permission-', form_data)
        for perm_id in permissions:
            try:
                handle_response(
                    roles.add_permission(role_id, perm_id))
            except DataRequestException:
                errors[perm_id] = [
                    f'Failed to add permission {perm_id} to role.']
            else:
                messages[perm_id] = [
                    f'Successfully added permission {perm_id} to role.']
        if errors:
            return self.get(
                form_data=form_data, errors=errors, messages=messages)
        messages = {'Success': f'Role {role["name"]} created.'}
        return redirect(url_for('admin.roles',
                                messages=messages))


class RolePermissionAddition(AdminView):
    template = 'forms/admin/role_permission_addition.html'

    def get(self, uuid, **kwargs):
        try:
            role = handle_response(roles.get_metadata(uuid))
            all_perms = handle_response(
                permissions.list_metadata())
        except DataRequestException as e:
            return render_template(self.template, errors=e.errors)
        else:
            role_perms = list(role['permissions'].keys())
            all_perms = self.filter_by_org(all_perms, 'organization')
            # remove any roles the user already has
            all_perms = [perm for perm in all_perms
                         if perm['permission_id'] not in role_perms]
        return render_template(self.template,
                               role=role,
                               table_data=all_perms,
                               **self.template_args(),
                               **kwargs)

    def post(self, uuid):
        form_data = request.form
        perms = filter_form_fields('role-permission-', form_data)
        errors = {}
        messages = {}
        for perm in perms:
            try:
                handle_response(roles.add_permission(uuid, perm))
            except DataRequestException:
                errors[perm] = [f'Failed to add perm {perm} to role.']
            else:
                messages[perm] = [f'Successfully added perm {perm} to role.']
        if errors:
            return self.get(
                uuid, errors=errors, messages=messages, form_data=form_data)
        return redirect(url_for('admin.role_view', uuid=uuid))


class RoleDeletionView(AdminView):
    meta_template = 'data/metadata/role_metadata.html'
    template = 'forms/admin/admin_deletion_form.html'

    def get(self, uuid):
        try:
            role = handle_response(
                roles.get_metadata(uuid))
        except DataRequestException as e:
            return render_template(
                self.template, errors=e.errors)
        else:
            metadata = render_template(
                self.meta_template,
                data_type="role",
                role=role)
            return render_template(
                self.template, uuid=role['role_id'],
                data_type='role', metadata=metadata)

    def post(self, uuid):
        confirmation_url = url_for(
            'admin.delete_role',
            _external=True,
            uuid=uuid)
        if request.headers['Referer'] != confirmation_url:
            return redirect(confirmation_url)
        try:
            handle_response(roles.delete(uuid))
        except DataRequestException as e:
            return self.get(uuid, errors=e.errors)
        else:
            return redirect(url_for('admin.roles'))


class RolePermissionRemoval(AdminView):
    template = "forms/admin/role_permission_removal.html"

    def get(self, uuid, permission_id, **kwargs):
        """Confirmation view for removing permission from a role
        """
        try:
            role = handle_response(roles.get_metadata(uuid))
            permission = handle_response(
                permissions.get_metadata(permission_id))
        except DataRequestException as e:
            return render_template(self.template, errors=e.errors)
        perm_req = permissions.get_metadata(permission_id)
        permission = perm_req.json()
        return render_template(self.template,
                               role=role,
                               perm=permission,
                               **kwargs,
                               **self.template_args())

    def post(self, uuid, permission_id):
        """Remove a permission from a role by passing the request through
        to the API
        """
        try:
            roles.remove_permission(uuid, permission_id)
        except DataRequestException as e:
            return render_template(self.template, errors=e.errors)
        return redirect(url_for("admin.role_view", uuid=uuid))


# Permissions Views
class PermissionsListing(AdminView):
    template = 'forms/admin/permissions.html'

    def get(self):
        try:
            permissions_list = permissions.list_metadata().json()
        except DataRequestException as e:
            return render_template(self.template, errors=e.errors)
        return render_template(self.template,
                               table_data=permissions_list,
                               **self.template_args())


class PermissionView(AdminView):
    template = 'forms/admin/permission.html'

    def get(self, uuid, **kwargs):
        try:
            permission = handle_response(permissions.get_metadata(uuid))
        except DataRequestException as e:
            return render_template(self.template, errors=e.errors)
        else:
            api_handler = self.get_api_handler(permission['object_type'])
            # dashboard uses singular object names as labels to differentiate
            # single views from listings
            object_type = permission['object_type'][:-1]
            if 'forecast' in object_type:
                id_key = 'forecast_id'
            else:
                id_key = f'{object_type}_id'
            # create a dict of objects where keys are uuid and values are
            # objects
            if object_type == 'report':
                object_list = api_handler.list_metadata()
                object_map = {obj.to_dict()[id_key]: obj.to_dict()
                              for obj in object_list}
            else:
                objects = api_handler.list_metadata()
                object_list = objects.json()
                object_map = {obj[id_key]: obj
                              for obj in object_list}
            # rebuild the 'objects' dict with the uuid: object structure
            # instead of uuid: created_at
            permission['objects'] = {
                k: {'added_to_permission': v, **object_map[k]}
                for k, v in permission['objects'].items()
                if k in object_map
            }
        return render_template(self.template,
                               permission=permission,
                               dashboard_type=object_type,
                               **self.template_args())


class PermissionsCreation(AdminView):
    template = "forms/admin/permissions_form.html"
    allowed_data_types = ['site', 'observation',
                          'forecast', 'cdf_forecast_group',
                          'report', 'aggregate']

    def __init__(self, data_type):
        if data_type not in self.allowed_data_types:
            raise ValueError('invalid data_type')
        else:
            if data_type == 'observation':
                self.api_handle = observations
            elif data_type == 'forecast':
                self.api_handle = forecasts
            elif data_type == 'site':
                self.api_handle = sites
            elif data_type == 'cdf_forecast_group':
                self.api_handle = cdf_forecast_groups
            elif data_type == 'report':
                self.api_handle = reports
            elif data_type == 'aggregate':
                self.api_handle = aggregates
            self.data_type = data_type

    def get(self, **kwargs):
        """Render a permissions form with all of the available
        objects from the
        """
        if self.data_type == 'report':
            table_data = self.api_handle.list_metadata()
            table_data = [report.to_dict() for report in table_data]
        else:
            try:
                table_data = handle_response(self.api_handle.list_metadata())
            except DataRequestException as e:
                return render_template(self.template, errors=e.errors)
            table_data = self.filter_by_org(table_data, 'provider')
        return render_template(self.template,
                               table_data=table_data,
                               data_type=self.data_type,
                               **self.template_args(),
                               **kwargs)

    def parsePermission(self, form_data):
        """Parse a valid payload to send as the request body to
        the /permissions endpoint of the api.
        """
        permission = {
            'description': form_data['description'],
            'action': form_data['action'],
            'applies_to_all': ('applies-to-all' in form_data),
            'object_type': self.data_type + 's',
        }
        if self.data_type == 'cdf_forecast_group':
            permission.update({'object_type': 'cdf_forecasts'})
        return permission

    def post(self):
        """Parse the requests form data to create a payload for
        the permission endpoint and then post each selected object
        to add it to the permission.
        """
        form_data = request.form
        permission = self.parsePermission(form_data)
        try:
            permission_id = handle_response(
                permissions.post_metadata(permission))
        except DataRequestException as e:
            return render_template(
                self.template, form_data=form_data, errors=e.errors)
        objects = filter_form_fields('objects-list-', form_data)
        errors = {}
        messages = {}
        for object_id in objects:
            try:
                handle_response(permissions.add_object(
                    permission_id, object_id))
            except DataRequestException:
                errors[object_id] = [
                    f'Failed to add {self.data_type} to permission.']
            else:
                messages[object_id] = [
                    f'Added {self.data_type} to permission.']
        if errors:
            return render_template(
                self.template, errors=errors, messages=messages)
        messages = {'Success': 'Permission created.'}
        return redirect(url_for('admin.permissions',
                                messages=messages))


class PermissionDeletionView(AdminView):
    meta_template = 'data/metadata/permission_metadata.html'
    template = 'forms/admin/admin_deletion_form.html'

    def get(self, uuid):
        temp_args = {}
        try:
            perm = handle_response(permissions.get_metadata(uuid))
        except DataRequestException as e:
            temp_args['errors'] = e.errors
        else:
            temp_args['metadata'] = render_template(
                self.meta_template,
                data_type="permission",
                permission=perm)
            temp_args['uuid'] = perm['permission_id']
            temp_args['data_type'] = 'permission'
        return render_template(self.template, **temp_args)

    def post(self, uuid):
        confirmation_url = url_for(
            'admin.delete_permission',
            _external=True,
            uuid=uuid)
        if request.headers['Referer'] != confirmation_url:
            return redirect(confirmation_url)
        try:
            handle_response(permissions.delete(uuid))
        except DataRequestException as e:
            return render_template(self.template, errors=e.errors)
        else:
            return redirect(url_for('admin.permissions'))


class PermissionObjectAddition(PermissionView):
    template = 'forms/admin/permission_object_addition.html'

    def get(self, uuid, **kwargs):
        try:
            permission = handle_response(
                permissions.get_metadata(uuid))
        except DataRequestException as e:
            return render_template(self.template, errors=e.errors)
        else:
            data_type = permission['object_type'][:-1]
            api = self.get_api_handler(permission['object_type'])
            perm_objects = list(permission['objects'].keys())
            if data_type == 'report':
                all_objects = api.list_metadata()
                all_objects = [rep.to_dict() for rep in all_objects]
            else:
                all_objects = handle_response(api.list_metadata())
                all_objects = self.filter_by_org(all_objects, 'provider')
            # remove any objects alread on the permission
            object_id_key = f"{data_type}_id"
            all_objects = [obj for obj in all_objects
                           if obj[object_id_key] not in perm_objects]
        return render_template(self.template,
                               permission=permission,
                               table_data=all_objects,
                               data_type=data_type,
                               **self.template_args(),
                               **kwargs)

    def post(self, uuid):
        form_data = request.form
        objects = filter_form_fields('objects-list-', form_data)
        for obj in objects:
            try:
                permissions.add_object(uuid, obj)
            except DataRequestException as e:
                return render_template(self.template, errors=e.errors)
        return redirect(url_for('admin.permission_view', uuid=uuid))


class PermissionObjectRemoval(AdminView):
    template = "forms/admin/permission_object_removal.html"

    def get(self, uuid, object_id, **kwargs):
        try:
            permission = handle_response(permissions.get_metadata(uuid))
            api = self.get_api_handler(permission['object_type'])
            object_data = handle_response(api.get_metadata(object_id))
        except DataRequestException as e:
            return render_template(self.template, errors=e.errors)
        else:
            return render_template(
                self.template,
                permission=permission,
                object_data=object_data,
                object_id=object_id,
                **kwargs,
                **self.template_args())

    def post(self, uuid, object_id):
        """Remove an object from a permission by passing the
        request through to the API
        """
        delete_request = permissions.remove_object(uuid, object_id)
        if delete_request.status_code != 204:
            errors = delete_request.json()
            return self.get(uuid, object_id, errors=errors)
        return redirect(url_for('admin.permission_view', uuid=uuid))


# Blueprint registration
admin_blp = Blueprint('admin', 'admin', url_prefix='/admin')
admin_blp.add_url_rule('/',
                       view_func=AdminView.as_view(
                           'admin'))
admin_blp.add_url_rule('/permissions/',
                       view_func=PermissionsListing.as_view(
                           'permissions'))
admin_blp.add_url_rule('/permissions/<uuid>',
                       view_func=PermissionView.as_view(
                           'permission_view'))
admin_blp.add_url_rule('/permissions/<uuid>/add',
                       view_func=PermissionObjectAddition.as_view(
                           'permission_object_addition'))
admin_blp.add_url_rule('/permissions/<uuid>/remove/<object_id>',
                       view_func=PermissionObjectRemoval.as_view(
                           'permission_object_removal'))
admin_blp.add_url_rule('/permissions/<uuid>/delete',
                       view_func=PermissionDeletionView.as_view(
                           'delete_permission'))
for data_type in PermissionsCreation.allowed_data_types:
    admin_blp.add_url_rule(f'/permissions/create/{data_type}',
                           view_func=PermissionsCreation.as_view(
                               f'{data_type}_permission',
                               data_type=data_type))

admin_blp.add_url_rule('/roles/',
                       view_func=RoleListing.as_view('roles'))
admin_blp.add_url_rule('/roles/create',
                       view_func=RoleCreation.as_view('create_role'))
admin_blp.add_url_rule('/roles/<uuid>/delete',
                       view_func=RoleDeletionView.as_view('delete_role'))
admin_blp.add_url_rule('/roles/<uuid>',
                       view_func=RoleView.as_view('role_view'))
admin_blp.add_url_rule('/roles/<uuid>/add/',
                       view_func=RolePermissionAddition.as_view(
                           'role_perm_addition'))
admin_blp.add_url_rule('/roles/<uuid>/remove/<permission_id>',
                       view_func=RolePermissionRemoval.as_view(
                           'role_perm_removal'))
admin_blp.add_url_rule('/roles/<uuid>/grant/',
                       view_func=RoleGrant.as_view(
                           'role_grant'))
admin_blp.add_url_rule('/users/',
                       view_func=UserListing.as_view('users'))
admin_blp.add_url_rule('/users/<uuid>',
                       view_func=UserView.as_view('user_view'))
admin_blp.add_url_rule('/users/<uuid>/remove/<role_id>',
                       view_func=UserRoleRemoval.as_view('user_role_removal'))
admin_blp.add_url_rule('/users/<uuid>/add/',
                       view_func=UserRoleAddition.as_view('user_role_update'))
