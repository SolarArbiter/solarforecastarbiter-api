DELETE FROM arbiter_data.role_permission_mapping WHERE permission_id in (SELECT id from arbiter_data.permissions WHERE object_type IN ('users', 'roles', 'permissions', 'role_grants'));
