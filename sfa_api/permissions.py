from flask import Blueprint, request, jsonify, make_response, url_for
from flask.views import MethodView
from marshmallow import ValidationError


from sfa_api.utils.storage import get_storage
from sfa_api.utils.errors import BadAPIRequest
from sfa_api.schema import (PermissionSchema,
                            PermissionPostSchema)


class AllPermissionsView(MethodView):
    def get(self):
        """
        ---
        summary: List Permissions.
        description: List all Permissionss that the user has access to.
        tags:
          - Permissions
        responses:
          200:
            description: Retrieved permissions successfully.
            content:
              applicaiton/json:
                schema:
                  type: array
                  items:
                    $ref: '#/components/schemas/PermissionSchema'
          404:
            $ref: '#/components/responses/404-NotFound'
          401:
            $ref: '#/components/responses/401-Unauthorized'
        """
        storage = get_storage()
        permissions = storage.list_permissions()
        return jsonify(PermissionSchema(many=True).dump(permissions))

    def post(self):
        """
        ---
        summary: Create a new Permission.
        tags:
          - Permissions
        requestBody:
          description: JSON representation of a Permission.
          required: True
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PermissionPostSchema'
        responses:
          200:
            description: Permission created successfully.
          400:
            $ref: '#/components/responses/400-BadRequest'
          404:
            $ref: '#/components/responses/404-NotFound'
          401:
            $ref: '#/components/responses/401-Unauthorized'
        """
        data = request.get_json()
        try:
            permission = PermissionPostSchema().load(data)
        except ValidationError as err:
            raise BadAPIRequest(err.messages)
        storage = get_storage()
        permission_id = storage.store_permission(permission)
        response = make_response(permission_id, 201)
        response.headers['Location'] = url_for('permissions.single',
                                               permission_id=permission_id)
        return response


class PermissionView(MethodView):
    def get(self, permission_id):
        """
        ---
        summary: Get information about a Permission.
        tags:
          - Permissions
        responses:
          200:
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/PermissionSchema'
          404:
            $ref: '#/components/responses/404-NotFound'
          401:
            $ref: '#/components/responses/401-Unauthorized'
        """
        storage = get_storage()
        permission = storage.read_permission(permission_id)
        return jsonify(PermissionSchema().dump(permission))

    def delete(self, permission_id):
        """
        ---
        summary: Delete a Permission
        tags:
          - Permissions
        responses:
          204:
            description: Permission deleted successfully.
          404:
            $ref: '#/components/responses/404-NotFound'
          401:
            $ref: '#/components/responses/401-Unauthorized'
        """
        storage = get_storage()
        storage.delete_permission(permission_id)
        return '', 204

class PermissionObjectManagementView(MethodView):
    def post(self, permission_id, uuid):
        """
        ---
        summary: Add an object to the permission
        tags:
          - Permissions
        reponses:
          204:
            description: Object added to permission successfilly.
          400:
            $ref: '#/components/responses/400-BadRequest'
          404:
            $ref: '#/components/responses/404-NotFound'
          401:
            $ref: '#/components/responses/401-Unauthorized'
        """
        storage = get_storagE()
        storage.add_object_to_permission(role_id, permission_id)
        return '', 204



permission_blp = Blueprint(
    'permissions', 'permissions', url_prefix='/permissions',
)
permission_blp.add_url_rule('/', view_func=AllPermissionsView.as_view('all'))
permission_blp.add_url_rule(
    '/<permission_id>',
    view_func=PermissionView.as_view('single'))
