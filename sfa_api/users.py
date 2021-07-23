from flask import Blueprint, jsonify, Response
from flask.views import MethodView


from sfa_api import spec
from sfa_api.schema import (UserSchema, ActionList, ALLOWED_OBJECT_TYPES,
                            UserCreatePerms, ActionsOnTypeList)
from sfa_api.utils.auth0_info import (
    get_email_of_user, get_auth0_id_of_user)
from sfa_api.utils.errors import StorageAuthError, BadAPIRequest
from sfa_api.utils.storage import get_storage


class AllUsersView(MethodView):
    def get(self):
        """
        ---
        summary: List Users.
        description: List all Users that current User has access to.
        tags:
          - Users
        responses:
          200:
            description: A list of Users
            content:
              application/json:
                schema:
                  type: array
                  items:
                    $ref: '#/components/schemas/UserSchema'
          401:
            $ref: '#/components/responses/401-Unauthorized'
        """
        storage = get_storage()
        users = storage.list_users()
        for u in users:
            u['email'] = get_email_of_user(u['auth0_id'])
        return jsonify(UserSchema(many=True).dump(users))


class UserView(MethodView):
    def get(self, user_id):
        """
        ---
        summary: Get User Metadata.
        parameters:
        - user_id
        tags:
          - Users
        responses:
          200:
            description: User successully retrieved.
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/UserSchema'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        storage = get_storage()
        user = storage.read_user(user_id)
        user['email'] = get_email_of_user(user['auth0_id'])
        return jsonify(UserSchema().dump(user))

    def _delete(self, user_id):
        """
        not implemented
        ---
        summary: Delete a User.
        parameters:
        - user_id
        tags:
          - Users
        responses:
          204:
            description: User Deleted successfully.
          404:
            $ref: '#/components/responses/404-NotFound'
          401:
            $ref: '#/components/responses/401-Unauthorized'
        """
        # PROCEDURE: move_user_to_unaffiliated
        pass


class UserRolesManagementView(MethodView):
    def post(self, user_id, role_id):
        """
        ---
        summary: Add a Role to a User.
        parameters:
        - user_id
        - role_id
        tags:
          - Users
          - Roles
        responses:
          204:
            description: Role Added Successfully.
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        storage = get_storage()
        storage.add_role_to_user(user_id, role_id)
        return '', 204

    def delete(self, user_id, role_id):
        """
        ---
        summary: Remove a role from a User.
        parameters:
        - user_id
        - role_id
        tags:
          - Users
          - Roles
        responses:
          204:
            description: Role removed successfully..
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        storage = get_storage()
        storage.remove_role_from_user(user_id, role_id)
        return '', 204


class CurrentUserView(MethodView):
    def get(self):
        """
        ---
        summary: Get current user metadata.
        tags:
          - Users
        responses:
          200:
            description: User successully retrieved.
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/UserSchema'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        storage = get_storage()
        user_info = storage.get_current_user_info()
        user_info['email'] = get_email_of_user(
            user_info['auth0_id'])
        return jsonify(UserSchema().dump(user_info))


class UserIdToEmailView(MethodView):
    def get(self, user_id):
        """
        ---
        summary: Get user email from user id.
        tags:
          - Users
        responses:
          200:
            description: The user's email.
            content:
              text/plain:
                schema:
                  type: string
                  example: testing@solarforecastarbiter.org
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        storage = get_storage()
        auth0_id = storage.read_auth0id(user_id)
        email = get_email_of_user(auth0_id)
        return email


class UserRolesManagementByEmailView(UserRolesManagementView):
    def post(self, email, role_id):
        """
        ---
        summary: Add a Role to a User by email.
        parameters:
        - email
        - role_id
        tags:
          - Users-By-Email
          - Roles
        responses:
          204:
            description: Role Added Successfully.
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        storage = get_storage()
        auth0_id = get_auth0_id_of_user(email)
        user_id = storage.read_user_id(auth0_id)
        return super().post(user_id, role_id)

    def delete(self, email, role_id):
        """
        ---
        summary: Remove a role from a User by email.
        parameters:
        - email
        - role_id
        tags:
          - Users-By-Email
          - Roles
        responses:
          204:
            description: Role removed successfully..
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        storage = get_storage()
        auth0_id = get_auth0_id_of_user(email)
        try:
            user_id = storage.read_user_id(auth0_id)
        except StorageAuthError:
            return '', 204
        return super().delete(user_id, role_id)


class UserByEmailView(MethodView):
    def get(self, email):
        """
        ---
        summary: Get User Metadata by email.
        parameters:
        - email
        tags:
          - Users-By-Email
        responses:
          200:
            description: User successully retrieved.
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/UserSchema'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        storage = get_storage()
        auth0_id = get_auth0_id_of_user(email)
        user_id = storage.read_user_id(auth0_id)
        user = storage.read_user(user_id)
        user['email'] = email
        return jsonify(UserSchema().dump(user))


class UserActionsView(MethodView):
    def get(self, object_id):
        """
        ---
        summary: Available actions on object.
        description: |-
          Get a list of actions the current user is allowed to perform
          on an object.
        parameters:
        - object_id
        tags:
          - Users
        responses:
          200:
            description: List of actions the user can make on the object.
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/ActionList'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        storage = get_storage()
        actions = storage.get_user_actions_on_object(object_id)
        json_response = {'object_id': object_id,
                         'actions': actions}
        return jsonify(ActionList().dump(json_response))


class UserCreatePermissions(MethodView):
    def get(self):
        """
        ---
        summary: List object types user can create.
        description: |-
          Get a list of object types the user can create.
        tags:
          - Users
        responses:
          200:
            description: List of object types the user has permission to create
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/UserCreatePerms'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """

        storage = get_storage()
        object_types = storage.get_user_creatable_types()
        return Response(UserCreatePerms().dumps({'can_create': object_types}),
                        mimetype="application/json")


class UserActionsOnType(MethodView):
    def get(self, object_type):
        """
        ---
        summary: List all permitted actions on all objects of a given type.
        description: |-
          Get a list of object ids and the actions the user is permitted to
          perform on each object.
        parameters:
        - object_type
        tags:
          - Users
        responses:
          200:
            description: List of actions the user can make on the object.
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/ActionsOnTypeList'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        if object_type not in ALLOWED_OBJECT_TYPES:
            raise BadAPIRequest({
                'object_type': 'Must be one of: '
                               f'{", ".join(ALLOWED_OBJECT_TYPES)}'
            })
        storage = get_storage()
        object_dict = storage.list_actions_on_all_objects_of_type(object_type)
        json_response = {'object_type': object_type,
                         'objects': object_dict}
        return Response(ActionsOnTypeList().dumps(json_response),
                        mimetype="application/json")


spec.components.parameter(
    'user_id', 'path',
    {
        'schema': {
            'type': 'string',
            'format': 'uuid'
        },
        'description': "The user's unique identifier",
        'required': 'true',
        'name': 'user_id'
    })
spec.components.parameter(
    'email', 'path',
    {
        'schema': {
            'type': 'string',
            'format': 'email'
        },
        'description': "The user's email address",
        'required': 'true',
        'name': 'email'
    })
spec.components.parameter(
    'object_type', 'path',
    {
        'schema': {
            'type': 'string',
        },
        'description': "The type of object to query for.",
        'required': 'true',
        'name': 'object_type',
    })
user_blp = Blueprint(
    'users', 'users', url_prefix='/users',
)
user_blp.add_url_rule('/', view_func=AllUsersView.as_view('all'))
user_blp.add_url_rule(
    '/<uuid_str:user_id>',
    view_func=UserView.as_view('single')
)
user_blp.add_url_rule(
    '/<uuid_str:user_id>/roles/<uuid_str:role_id>',
    view_func=UserRolesManagementView.as_view('user_roles_management')
)
user_blp.add_url_rule(
    '/current',
    view_func=CurrentUserView.as_view('current_user'))
user_blp.add_url_rule(
    '/<uuid_str:user_id>/email',
    view_func=UserIdToEmailView.as_view('user_email'))
user_blp.add_url_rule(
    '/actions-on/<uuid_str:object_id>',
    view_func=UserActionsView.as_view('user_actions_on_object'))
user_blp.add_url_rule(
    '/can-create/',
    view_func=UserCreatePermissions.as_view('user_create_permissions'))
user_blp.add_url_rule(
    '/actions-on-type/<object_type>',
    view_func=UserActionsOnType.as_view('user_actions_on_type'))

user_email_blp = Blueprint(
    'users-by-email', 'users-by-email', url_prefix='/users-by-email',
)
user_email_blp.add_url_rule(
    '/<email>', view_func=UserByEmailView.as_view('single'))
user_email_blp.add_url_rule(
    '/<email>/roles/<uuid_str:role_id>',
    view_func=UserRolesManagementByEmailView.as_view('user_roles_management'))
