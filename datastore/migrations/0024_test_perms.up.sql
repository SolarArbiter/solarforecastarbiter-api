SET @orgid = (SELECT id FROM organizations WHERE name = 'Organization 1');
SET @permid = UUID_TO_BIN(UUID(), 1);
SET @readperm_id = UUID_TO_BIN(UUID(), 1);

INSERT INTO arbiter_data.permissions(id, description, organization_id, action, object_type, applies_to_all) VALUES (
        @permid, 'Role Granter', @orgid, 'create', 'role_grants', FALSE), (
        @readperm_id, 'Read roles', @orgid, 'read', 'roles', TRUE);
        
SET @roleid = (SELECT id FROM roles WHERE name = 'Test user role');
INSERT INTO arbiter_data.role_permission_mapping (role_id, permission_id) VALUES (@roleid, @permid);
