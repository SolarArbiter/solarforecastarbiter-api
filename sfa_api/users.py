from flask import Blueprint, jsonify
from flask.views import MethodView


from sfa_api import spec
from sfa_api.schema import UserSchema
from sfa_api.utils.auth0_info import get_email_of_user, list_user_emails
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
          404:
            $ref: '#/components/responses/404-NotFound'
          401:
            $ref: '#/components/responses/401-Unauthorized'
        """
        storage = get_storage()
        users = storage.list_users()
        emails = list_user_emails([u['auth0_id'] for u in users])
        for u in users:
            u['email'] = emails.get(
                u['auth0_id'], 'Unable to retrieve')
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
          404:
            $ref: '#/components/responses/404-NotFound'
          401:
            $ref: '#/components/responses/401-Unauthorized'
        """
        storage = get_storage()
        user = storage.read_user(user_id)
        user['email'] = get_email_of_user(user['auth0_id'])
        return jsonify(UserSchema().dump(user))

    def delete(self, user_id):
        """
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
          200:
            description: Role Added Successfully.
          404:
            $ref: '#/components/responses/404-NotFound'
          401:
            $ref: '#/components/responses/401-Unauthorized'
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
          200:
            description: Role removed successfully..
          404:
            $ref: '#/components/responses/404-NotFound'
          401:
            $ref: '#/components/responses/401-Unauthorized'
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
          404:
            $ref: '#/components/responses/404-NotFound'
          401:
            $ref: '#/components/responses/401-Unauthorized'
        """
        storage = get_storage()
        user_info = storage.get_current_user_info()
        user_info['email'] = get_email_of_user(
            user_info['auth0_id'])
        return jsonify(UserSchema().dump(user_info))


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
user_blp = Blueprint(
    'users', 'users', url_prefix='/users',
)
user_blp.add_url_rule('/', view_func=AllUsersView.as_view('all'))
user_blp.add_url_rule('/<user_id>', view_func=UserView.as_view('single'))
user_blp.add_url_rule(
    '/<user_id>/roles/<role_id>',
    view_func=UserRolesManagementView.as_view('user_roles_management')
)
user_blp.add_url_rule(
    '/current',
    view_func=CurrentUserView.as_view('current_user'))
