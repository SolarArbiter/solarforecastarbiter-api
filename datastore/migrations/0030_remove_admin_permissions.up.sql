DELETE FROM arbiter_data.role_permission_mapping
    WHERE permission_id in (
        SELECT id from arbiter_data.permissions
            WHERE organization_id = get_organization_id('Organization 1')
            AND object_type IN ('users', 'roles', 'permissions')
            AND action != 'read'
    );
