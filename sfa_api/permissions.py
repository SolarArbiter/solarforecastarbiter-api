from flask import Blueprint, request, jsonify, make_response, url_for
from flask.views import MethodView
from marshmallow import ValidationError


from sfa_api import spec
from sfa_api.utils.storage import get_storage
from sfa_api.utils.errors import BadAPIRequest
from sfa_api.schema import (PermissionSchema,
                            PermissionPostSchema)


class AllPermissionsView(MethodView):
    def get(self):
        """
        ---
        summary: List Permissions.
        description: List all Permissions that the user has access to.
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
          201:
            description: Permission created successfully.
            content:
              application/json:
                schema:
                  type: string
                  format: uuid
                  description: The uuid of the created permission.
            headers:
              Location:
                schema:
                  type: string
                  format: uri
                  description: Url of the created permission.
          400:
            $ref: '#/components/responses/400-BadRequest'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
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
        parameters:
        - permission_id
        tags:
          - Permissions
        responses:
          200:
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/PermissionSchema'
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        storage = get_storage()
        permission = storage.read_permission(permission_id)
        return jsonify(PermissionSchema().dump(permission))

    def delete(self, permission_id):
        """
        ---
        summary: Delete a Permission
        parameters:
        - permission_id
        tags:
          - Permissions
        responses:
          204:
            description: Permission deleted successfully.
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        storage = get_storage()
        storage.delete_permission(permission_id)
        return '', 204


class PermissionObjectManagementView(MethodView):
    def post(self, permission_id, object_id):
        """
        ---
        summary: Add an object to the permission
        parameters:
        - permission_id
        - object_id
        tags:
          - Permissions
        responses:
          204:
            description: Object added to permission successfully.
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        storage = get_storage()
        storage.add_object_to_permission(object_id, permission_id)
        return '', 204

    def delete(self, permission_id, object_id):
        """
        ---
        summary: Remove an object from the permission
        parameters:
        - permission_id
        - object_id
        tags:
          - Permissions
        responses:
          204:
            description: Object removed from permission successfully.
          401:
            $ref: '#/components/responses/401-Unauthorized'
          404:
            $ref: '#/components/responses/404-NotFound'
        """
        storage = get_storage()
        storage.remove_object_from_permission(permission_id, object_id)
        return '', 204


spec.components.parameter(
    'permission_id', 'path',
    {
        'schema': {
            'type': 'string',
            'format': 'uuid',
        },
        'description': "permissions's unique identifier.",
        'required': 'true',
        'name': 'permission_id'
    })
spec.components.parameter(
    'object_id', 'path',
    {
        'schema': {
            'type': 'string',
            'format': 'uuid',
        },
        'description': "Object's unique identifier.",
        'required': 'true',
        'name': 'object_id'
    })


permission_blp = Blueprint(
    'permissions', 'permissions', url_prefix='/permissions',
)
permission_blp.add_url_rule('/', view_func=AllPermissionsView.as_view('all'))
permission_blp.add_url_rule(
    '/<uuid_str:permission_id>',
    view_func=PermissionView.as_view('single'))
permission_blp.add_url_rule(
    '/<uuid_str:permission_id>/objects/<uuid_str:object_id>',
    view_func=PermissionObjectManagementView.as_view('objects'))
