from flask import Blueprint, request, jsonify, make_response, url_for
from flask.views import MethodView
from marshmallow import ValidationError


from sfa_api import spec
from sfa_api.utils.storage import get_storage
from sfa_api.utils.errors import BadAPIRequest
from sfa_api.schema import (RoleSchema,
                            RolePostSchema)


class AllRolesView(MethodView):
    def get(self):
        """
        ---
        summary: List Roles.
        description: List all Roles that the user has access to.
        tags:
          - Roles
        responses:
          200:
            description: Retrieved roles successfully.
            content:
              applicaiton/json:
                schema:
                  type: array
                  items:
                    $ref: '#/components/schemas/RoleSchema'
          404:
            $ref: '#/components/responses/404-NotFound'
          401:
            $ref: '#/components/responses/401-Unauthorized'
        """
        storage = get_storage()
        roles = storage.list_roles()
        return jsonify(RoleSchema(many=True).dump(roles))

    def post(self):
        """
        ---
        summary: Create a new Role.
        tags:
          - Roles
        responses:
          200:
            description: Role created successfully.
            content:
              application/json:
                schema:
                  type: string
                  format: uuid
                  description: The uuid of the created role.
            headers:
              Location:
                schema:
                  type: string
                  format: uri
                  description: Url of the created role.
          400:
            $ref: '#/components/responses/400-BadRequest'
          404:
            $ref: '#/components/responses/404-NotFound'
          401:
            $ref: '#/components/responses/401-Unauthorized'
        """
        data = request.get_json()
        try:
            role = RolePostSchema().load(data)
        except ValidationError as err:
            raise BadAPIRequest(err.messages)
        storage = get_storage()
        role_id = storage.store_role(role)
        response = make_response(role_id, 201)
        response.headers['Location'] = url_for('roles.single',
                                               role_id=role_id)
        return response


class RoleView(MethodView):
    def get(self, role_id):
        """
        ---
        summary: Get information about a Role.
        parameters:
        - role_id
        tags:
          - Roles
        responses:
          200:
            description: Role created successfully.
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/RoleSchema'
          404:
            $ref: '#/components/responses/404-NotFound'
          401:
            $ref: '#/components/responses/401-Unauthorized'
        """
        storage = get_storage()
        role = storage.read_role(role_id)
        return jsonify(RoleSchema().dump(role))

    def delete(self, role_id):
        """
        ---
        summary: Delete a Role
        parameters:
        - role_id
        tags:
          - Roles
        responses:
          204:
            description: Role deleted successfully.
          404:
            $ref: '#/components/responses/404-NotFound'
          401:
            $ref: '#/components/responses/401-Unauthorized'
        """
        storage = get_storage()
        storage.delete_role(role_id)
        return '', 204


class RolePermissionManagementView(MethodView):
    def post(self, role_id, permission_id):
        """
        ---
        summary: Add a permission to a role
        parameters:
        - role_id
        - permission_id
        tags:
          - Roles
          - Permissions
        responses:
          204:
            description: Permission added to role successfully.
          400:
            $ref: '#/components/responses/400-BadRequest'
          404:
            $ref: '#/components/responses/404-NotFound'
          401:
            $ref: '#/components/responses/401-Unauthorized'
        """
        storage = get_storage()
        storage.add_permission_to_role(role_id, permission_id)
        return '', 204

    def delete(self, role_id, permission_id):
        """
        ---
        summary: Remove a permission from a role
        parameters:
        - role_id
        - permission_id
        tags:
          - Roles
          - Permissions
        responses:
          204:
            description: Removed permission successfully.
          404:
            $ref: '#/components/responses/404-NotFound'
          401:
            $ref: '#/components/responses/401-Unauthorized'
        """
        storage = get_storage()
        storage.remove_permission_from_role(role_id, permission_id)
        return '', 204


spec.components.parameter(
    'role_id', 'path',
    {
        'schema': {
            'type': 'string',
            'format': 'uuid'
        },
        'description': "The role's unique identifier",
        'required': 'true',
        'name': 'role_id'
    })

role_blp = Blueprint(
    'roles', 'roles', url_prefix='/roles',
)
role_blp.add_url_rule('/', view_func=AllRolesView.as_view('all'))
role_blp.add_url_rule('/<role_id>', view_func=RoleView.as_view('single'))
role_blp.add_url_rule(
    '/<role_id>/permissions/<permission_id>',
    view_func=RolePermissionManagementView.as_view('permissions')
)
