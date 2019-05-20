from flask import Blueprint
from flask.views import MethodView


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
        # PROCEDURE: list_users
        pass

    def post(self):
        """
        ---
        summary: Create a new User
        description: >-
          Create a new User by posting metadata containing an auth0_id and
          organization_id.
        tags:
          - Users
        requestBody:
          description: JSON containing fields to create new user.
          required: True
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserPostSchema'
        responses:
          201:
            description: Created the User successfully
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/UserSchema'
          404:
            $ref: '#/components/responses/404-NotFound'
          401:
            $ref: '#/components/responses/401-Unauthorized'
        """
        # PROCEDURE: create_user
        pass


class UserView(MethodView):
    def get(self, user_id):
        """
        ---
        summary: Get User Metadata.
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
        # PROCEDURE: read_user
        pass

    def delete(self, user_id):
        """
        ---
        summary: Delete a User.
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
        # PROCEDURE: no remove_user procedure
        pass


class UserRolesView(MethodView):
    def get(self, user_id):
        """
        ---
        summary: List Roles of User.
        tags:
          - Users
          - Roles
        responses:
          200:
            description: List of User's roles retrieved successfully.
          404:
            $ref: '#/components/responses/404-NotFound'
          401:
            $ref: '#/components/responses/401-Unauthorized'
        """
        # PROCEDURE: list_roles
        pass


class UserRolesManagementView(MethodView):
    def post(self, user_id, role_id):
        """
        ---
        summary: Add a Role to a User.
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
        # PROCEDURE: add_role_to_user
        pass

    def delete(self, user_id, role_id):
        """
        ---
        summary: Remove a role from a User.
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
        # PROCEDURE: remove_role_from_user
        pass


user_blp = Blueprint(
    'users', 'users', url_prefix='/users',
)
user_blp.add_url_rule('/', view_func=AllUsersView.as_view('all'))
user_blp.add_url_rule('/<user_id>', view_func=UserView.as_view('single'))
user_blp.add_url_rule(
    '/<user_id>/roles/',
    view_func=UserRolesView.as_view('user_roles'))
user_blp.add_url_rule(
    '/<user_id>/roles/<role_id>',
    view_func=UserRolesManagementView.as_view('user_roles_management')
)
