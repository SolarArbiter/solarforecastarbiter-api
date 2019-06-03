from flask import (Blueprint, render_template, request, jsonify,
                   url_for)
from sfa_dash.api_interface import (
    sites, observations, forecasts,
    cdf_forecast_groups, roles, users,
    permissions
)
from sfa_dash.blueprints.base import BaseView


class AdminView(BaseView):
    subnav_format = {
        '{users_url}': 'Users',
        '{roles_url}': 'Roles',
        '{permissions_url}': 'Permissions',
    }

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


class PermissionsListing(AdminView):
    def get(self):
        permissions_list = permissions.list_metadata().json()
        if 'errors' in permissions_list:
            permissions_list = None
        return render_template('forms/admin/permissions.html',
                               table_data=permissions_list,
                               **self.template_args())


class PermissionView(AdminView):
    def get_api_handler(self, object_type):
        # The api interface should have a factory method to handle this logic
        # instead of repeating this logic everywhere
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
        else:
            raise ValueError('Invalid object_type')
        return api_handler

    def get(self, uuid):
        permission = permissions.get_metadata(uuid).json()
        if 'errors' in permission:
            permission = None
            object_type = None
        else:
            api_handler = self.get_api_handler(permission['object_type'])
            # dashboard uses singular object names as labels to differentiate
            # single views from listings
            object_type = permission['object_type'][:-1]
            # create a dict of objects where keys are uuid and values are
            # objects
            objects = api_handler.list_metadata()
            object_list = objects.json()
            object_map = {obj[f'{object_type}_id']: obj
                          for obj in object_list}
            # rebuild the 'objects' dict with the uuid: object structure
            # instead of uuid: created_at
            permission['objects'] = {
                k: {'added_to_permission': v, **object_map[k]}
                for k, v in permission['objects'].items()
                if k in object_map
            }
        return render_template('forms/admin/permission.html',
                               permission=permission,
                               dashboard_type=object_type,
                               **self.template_args())


class RoleListing(AdminView):
    def get(self):
        roles_list = roles.list_metadata().json()
        if 'errors' in roles_list:
            roles_list = None
        return render_template('forms/admin/roles.html',
                               table_data=roles_list,
                               **self.template_args())


class RoleView(AdminView):
    def get(self, uuid):
        role = roles.get_metadata(uuid).json()
        if 'errors' in role:
            role = None
        else:
            permission_list = permissions.list_metadata().json()
            permission_map = {perm['permission_id']: perm
                              for perm in permission_list}
            role['permissions'] = {k: {'added_to_role': v, **permission_map[k]}
                                   for k, v in role['permissions'].items()
                                   if k in permission_map}
        return render_template('forms/admin/role.html',
                               role=role,
                               **self.template_args())


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
        user = users.get_metadata(uuid).json()
        if 'errors' in user:
            user = None
        else:
            role_list = roles.list_metadata().json()
            role_map = {role['role_id']: role for role in role_list}
            user['roles'] = {k: {'added_to_user': v, **role_map[k]}
                             for k, v in user['roles'].items()
                             if k in role_map}
        return render_template('forms/admin/user.html',
                               user=user,
                               **self.template_args())


class PermissionsCreation(AdminView):
    allowed_data_types = ['site', 'observation',
                          'forecast', 'cdf_forecast_group']

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
            self.data_type = data_type

    def get(self):
        list_request = self.api_handle.list_metadata()
        table_data = list_request.json()
        return render_template("forms/admin/permissions_form.html",
                               table_data=table_data,
                               data_type=self.data_type,
                               **self.template_args())

    def post(self):
        request.form
        return jsonify(request.form)


class RoleCreation(AdminView):
    def get(self):
        return render_template("forms/admin/role_form.html",
                               **self.template_args())


admin_blp = Blueprint('admin', 'admin', url_prefix='/admin')
admin_blp.add_url_rule('/',
                       view_func=AdminView.as_view(
                           'admin')
                       )
admin_blp.add_url_rule('/permissions/',
                       view_func=PermissionsListing.as_view(
                           'permissions')
                       )
admin_blp.add_url_rule('/permissions/<uuid>',
                       view_func=PermissionView.as_view(
                           'permission_view')
                       )
for data_type in PermissionsCreation.allowed_data_types:
    admin_blp.add_url_rule(f'/permissions/create/{data_type}',
                           view_func=PermissionsCreation.as_view(
                               f'{data_type}_permission',
                               data_type=data_type)
                           )
admin_blp.add_url_rule('/roles/',
                       view_func=RoleListing.as_view('roles'))
admin_blp.add_url_rule('/roles/create',
                       view_func=RoleCreation.as_view('create_role'))
admin_blp.add_url_rule('/roles/<uuid>',
                       view_func=RoleView.as_view('role_view'))
admin_blp.add_url_rule('/users/',
                       view_func=UserListing.as_view('users'))
admin_blp.add_url_rule('/users/<uuid>',
                       view_func=UserView.as_view('user_view'))
