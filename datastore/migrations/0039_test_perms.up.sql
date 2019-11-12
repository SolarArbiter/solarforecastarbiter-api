SET @orgid = (SELECT id FROM organizations WHERE name = 'Organization 1');
SET @grant_permid = UUID_TO_BIN(UUID(), 1);
SET @revoke_permid = UUID_TO_BIN(UUID(), 1);
SET @read_permid = UUID_TO_BIN(UUID(), 1);

INSERT INTO arbiter_data.permissions(id, description, organization_id, action, object_type, applies_to_all) VALUES (
        @grant_permid, 'Role Granter', @orgid, 'grant', 'roles', TRUE), (
        @revoke_permid, 'Role Revoker', @orgid, 'revoke', 'roles', TRUE), (
        @read_permid, 'Read roles', @orgid, 'read', 'roles', TRUE);
        
SET @roleid = (SELECT id FROM roles WHERE name = 'Test user role');
INSERT INTO arbiter_data.role_permission_mapping (role_id, permission_id) VALUES (
    @roleid, @grant_permid),(
    @roleid, @revoke_permid),(
    @roleid, @read_permid);
