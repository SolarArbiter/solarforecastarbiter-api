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


user_blp = Blueprint(
    'users', 'users', url_prefix='/users',
)
user_blp.add_url_rule('/', view_func=AllUsersView.as_view('all'))
user_blp.add_url_rule('/<user_id>', view_func=UserView.as_view('single'))
